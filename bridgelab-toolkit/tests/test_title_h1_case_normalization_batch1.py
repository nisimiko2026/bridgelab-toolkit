from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.sentinel_cleanup import _atomic_write as real_atomic_write
from metadata.title_h1_case_normalization_batch1 import (
    REVIEWED_TITLE_CHANGES,
    apply_title_h1_case_normalization_batch1_report,
    build_title_h1_case_normalization_batch1_report,
)


def article_text(source: str, target: str, *, newline: str = "\n") -> bytes:
    return (
        f"---{newline}title: {source}{newline}description: Exact reviewed title fixture.{newline}"
        f"category: play{newline}subcategory: principles{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}- play{newline}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references: []{newline}last_updated: '2026-07-27'{newline}"
        f"status: Draft{newline}---{newline}{newline}# {target}{newline}{newline}Body unchanged.{newline}"
    ).encode()


class TitleH1CaseNormalizationBatch1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()
        self.hashes = {}
        self.paths = self.write_family()
        self.hash_patch = patch(
            "metadata.title_h1_case_normalization_batch1.REVIEWED_SOURCE_SHA256",
            self.hashes,
        )
        self.hash_patch.start()

    def tearDown(self):
        self.hash_patch.stop()
        self.temp.cleanup()

    def write_family(self, *, newline: str = "\n") -> dict[str, Path]:
        paths = {}
        self.hashes = {}
        for article, (source, target) in REVIEWED_TITLE_CHANGES.items():
            path = self.root / article
            path.parent.mkdir(parents=True, exist_ok=True)
            content = article_text(source, target, newline=newline)
            path.write_bytes(content)
            paths[article] = path
            self.hashes[article] = hashlib.sha256(content).hexdigest()
        return paths

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-title-h1-case-normalization-batch1", "--root", str(self.root), *args],
        )

    def test_exact_selection_census_exclusion_determinism_and_dry_run_immutability(self):
        other = self.root / "play/other.md"
        other.parent.mkdir(exist_ok=True)
        other.write_bytes(article_text("Other", "Different"))
        before = {path: path.read_bytes() for path in (*self.paths.values(), other)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET TITLE |"), 12)
        for expected in (
            "Files selected   : 12",
            "Files to update  : 12",
            "Title changes    : 12",
            "H1 changes       : 0",
            "Files to back up : 12",
        ):
            self.assertIn(expected, first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse(self.backup.exists())
        self.assertEqual(
            [action.article for action in build_title_h1_case_normalization_batch1_report(self.root).actions],
            list(REVIEWED_TITLE_CHANGES),
        )

    def test_missing_file_missing_defect_extra_case_only_and_unrelated_mismatch(self):
        article = next(iter(REVIEWED_TITLE_CHANGES))
        path = self.paths[article]
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "census mismatch|file is missing"):
            build_title_h1_case_normalization_batch1_report(self.root)
        path.write_bytes(original)

        source, target = REVIEWED_TITLE_CHANGES[article]
        path.write_bytes(original.replace(f"title: {source}".encode(), f"title: {target}".encode(), 1))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_case_normalization_batch1_report(self.root)
        path.write_bytes(original)

        extra = self.root / "play/extra.md"
        extra.write_bytes(article_text("Case Only", "case only"))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_case_normalization_batch1_report(self.root)

    def test_title_h1_and_complete_source_preconditions(self):
        article = next(iter(REVIEWED_TITLE_CHANGES))
        source, target = REVIEWED_TITLE_CHANGES[article]
        path = self.paths[article]
        original = path.read_bytes()
        cases = (
            (f"title: {source}".encode(), b"title: Stale", "census mismatch|title precondition"),
            (f"# {target}".encode(), b"# Stale", "census mismatch|H1 precondition"),
            (b"Body unchanged.", b"Body changed.", "complete-byte source"),
            (b"status: Draft", b"status: Standard", "complete-byte source"),
        )
        for old, new, message in cases:
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_title_h1_case_normalization_batch1_report(self.root)
            path.write_bytes(original)

    def test_exact_title_only_lf_crlf_h1_body_and_metadata_frozen(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                self.write_family(newline=newline)
                with patch(
                    "metadata.title_h1_case_normalization_batch1.REVIEWED_SOURCE_SHA256",
                    self.hashes,
                ):
                    report = build_title_h1_case_normalization_batch1_report(self.root)
                for action in report.actions:
                    expected = action.original.replace(
                        f"title: {action.original_title}{newline}".encode(),
                        f"title: {action.proposed_title}{newline}".encode(),
                        1,
                    )
                    self.assertEqual(action.updated, expected)
                    self.assertIn(f"# {action.proposed_title}{newline}".encode(), action.updated)
                    self.assertIn(b"Body unchanged.", action.updated)
                    self.assertIn(b"status: Draft", action.updated)

    def test_apply_guards_backups_atomic_rollback_stale_plan_and_idempotence(self):
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_title_h1_case_normalization_batch1_report(self.root)
        stale = report.actions[-1]
        stale.path.write_bytes(stale.original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_title_h1_case_normalization_batch1_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())
        stale.path.write_bytes(stale.original)

        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_title_h1_case_normalization_batch1_report(report, self.root, self.backup)
        self.backup.rmdir()
        with self.assertRaisesRegex(RuntimeError, "outside canonical knowledge"):
            apply_title_h1_case_normalization_batch1_report(
                report, self.root, self.root / "backup"
            )

        calls = 0

        def fail_second(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("atomic failure")
            real_atomic_write(path, content)

        with patch(
            "metadata.title_h1_case_normalization_batch1._atomic_write",
            side_effect=fail_second,
        ):
            with self.assertRaisesRegex(OSError, "atomic failure"):
                apply_title_h1_case_normalization_batch1_report(report, self.root, self.backup)
        self.assertTrue(all(action.path.read_bytes() == action.original for action in report.actions))
        self.assertTrue(all((self.backup / action.article).is_file() for action in report.actions))

        fresh = self.base / "fresh" / "knowledge"
        fresh.mkdir(parents=True)
        self.root = fresh
        self.paths = self.write_family()
        backup = self.base / "fresh-backup"
        with patch(
            "metadata.title_h1_case_normalization_batch1.REVIEWED_SOURCE_SHA256",
            self.hashes,
        ):
            result = self.invoke("--apply", "--backup", str(backup))
            self.assertEqual(result.exit_code, 0, result.output)
            after = {path: path.read_bytes() for path in self.paths.values()}
            idempotent = self.invoke()
        self.assertIn("Files to update  : 0", idempotent.output)
        self.assertEqual({path: path.read_bytes() for path in self.paths.values()}, after)
        self.assertEqual(
            sorted(path.relative_to(backup).as_posix() for path in backup.rglob("*.md")),
            sorted(REVIEWED_TITLE_CHANGES),
        )

    def test_root_guards_explicit_root_and_cli_help(self):
        self.assertEqual(self.invoke().exit_code, 0)
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_title_h1_case_normalization_batch1_report(wrong)
        stale = self.base / "OneDrive" / "knowledge"
        stale.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "outside OneDrive"):
            build_title_h1_case_normalization_batch1_report(stale)
        help_result = self.runner.invoke(
            app, ["repair-title-h1-case-normalization-batch1", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
