from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.sentinel_cleanup import _atomic_write as real_atomic_write
from metadata.title_h1_metadata_case_repair_batch7 import (
    REVIEWED_TITLE_CHANGES,
    apply_title_h1_metadata_case_repair_batch7_report,
    build_title_h1_metadata_case_repair_batch7_report,
)


def article_text(source: str, h1: str, *, newline: str = "\n") -> bytes:
    return (
        f"---{newline}title: {source}{newline}description: Exact Batch 7 fixture.{newline}"
        f"category: bidding{newline}subcategory: conventions{newline}"
        f"difficulty: Advanced{newline}tags:{newline}- bidding{newline}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: '2026-07-27'{newline}status: Draft{newline}---{newline}{newline}"
        f"# {h1}{newline}{newline}Opening prose unchanged.{newline}{newline}"
        f"## Existing Child{newline}{newline}Body unchanged.{newline}"
    ).encode("utf-8")


def expected_post(original: bytes, source: str, target: str) -> bytes:
    return original.replace(
        f"title: {source}".encode("utf-8"), f"title: {target}".encode("utf-8"), 1
    )


class TitleH1MetadataCaseRepairBatch7Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.runner = CliRunner()
        self.paths, source_hashes, post_hashes = self.write_family()
        self.source_patch = patch(
            "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_SOURCE_SHA256",
            source_hashes,
        )
        self.post_patch = patch(
            "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_POST_SHA256",
            post_hashes,
        )
        self.source_patch.start()
        self.post_patch.start()

    def tearDown(self):
        self.post_patch.stop()
        self.source_patch.stop()
        self.temp.cleanup()

    def write_family(self, *, newline: str = "\n"):
        paths, source_hashes, post_hashes = {}, {}, {}
        for article, (source, target, h1) in REVIEWED_TITLE_CHANGES.items():
            path = self.root / article
            path.parent.mkdir(parents=True, exist_ok=True)
            content = article_text(source, h1, newline=newline)
            path.write_bytes(content)
            paths[article] = path
            source_hashes[article] = hashlib.sha256(content).hexdigest()
            post_hashes[article] = hashlib.sha256(
                expected_post(content, source, target)
            ).hexdigest()
        return paths, source_hashes, post_hashes

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-title-h1-metadata-case-repair-batch7", "--root", str(self.root), *args],
        )

    def test_exact_census_deterministic_dry_run_and_unicode_h1(self):
        unrelated = self.root / "play/unrelated.md"
        unrelated.parent.mkdir(exist_ok=True)
        unrelated.write_bytes(article_text("Unrelated", "Different"))
        before = {path: path.read_bytes() for path in (*self.paths.values(), unrelated)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET TITLE |"), 4)
        for expected in (
            "Files selected : 4",
            "Files to update: 4",
            "Title changes  : 4",
            "H1 changes     : 0",
            "Files to back up: 4",
        ):
            self.assertIn(expected, first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((self.base / "backup").exists())
        self.assertIn(
            "# SEF (Système d'Enseignement Français)".encode("utf-8"),
            self.paths["bidding/systems/sef.md"].read_bytes(),
        )
        report = build_title_h1_metadata_case_repair_batch7_report(self.root)
        self.assertEqual([action.article for action in report.actions], list(REVIEWED_TITLE_CHANGES))

    def test_missing_extra_title_h1_and_role_preconditions(self):
        article = next(iter(REVIEWED_TITLE_CHANGES))
        source, _, h1 = REVIEWED_TITLE_CHANGES[article]
        path, original = self.paths[article], self.paths[article].read_bytes()
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "census mismatch|file is missing"):
            build_title_h1_metadata_case_repair_batch7_report(self.root)
        path.write_bytes(original)
        extra = self.root / "play/extra.md"
        extra.parent.mkdir(exist_ok=True)
        extra.write_bytes(article_text("Extra name", "Extra Name Technique"))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_metadata_case_repair_batch7_report(self.root)
        extra.unlink()
        for old, new, message in (
            (f"title: {source}".encode(), b"title: Stale", "census mismatch|title precondition"),
            (f"# {h1}".encode(), b"# Stale", "census mismatch|first-H1"),
            (b"Body unchanged.", b"Body changed.", "complete-byte source"),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_title_h1_metadata_case_repair_batch7_report(self.root)
            path.write_bytes(original)
        role_path = self.root / "bidding/systems/ehaa.md"
        role_original = role_path.read_bytes()
        with patch(
            "metadata.title_h1_metadata_case_repair_batch7.classify_document_role"
        ) as classify:
            from core.document_roles import DocumentRole

            classify.return_value = DocumentRole.SECTION_INDEX
            with self.assertRaisesRegex(RuntimeError, "document-role"):
                build_title_h1_metadata_case_repair_batch7_report(self.root)
        self.assertEqual(role_path.read_bytes(), role_original)

    def test_exact_title_only_lf_crlf_mutation_and_frozen_h1(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                self.paths, source_hashes, post_hashes = self.write_family(newline=newline)
                with (
                    patch(
                        "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_SOURCE_SHA256",
                        source_hashes,
                    ),
                    patch(
                        "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_POST_SHA256",
                        post_hashes,
                    ),
                ):
                    report = build_title_h1_metadata_case_repair_batch7_report(self.root)
                for action in report.actions:
                    expected = expected_post(
                        action.original, action.original_title, action.proposed_title
                    )
                    self.assertEqual(action.updated, expected)
                    self.assertEqual(len(action.updated), len(action.original))
                    self.assertIn(f"# {action.expected_h1}".encode("utf-8"), action.updated)
                    restored = action.updated.replace(
                        f"title: {action.proposed_title}".encode("utf-8"),
                        f"title: {action.original_title}".encode("utf-8"),
                        1,
                    )
                    self.assertEqual(restored, action.original)

    def test_apply_guards_backup_verification_preflight_rollback_and_idempotence(self):
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_title_h1_metadata_case_repair_batch7_report(self.root)
        backup = self.base / "backup"
        stale = report.actions[-1]
        stale.path.write_bytes(stale.original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_title_h1_metadata_case_repair_batch7_report(report, self.root, backup)
        self.assertFalse(backup.exists())
        stale.path.write_bytes(stale.original)
        backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_title_h1_metadata_case_repair_batch7_report(report, self.root, backup)
        backup.rmdir()
        with self.assertRaisesRegex(RuntimeError, "outside canonical knowledge"):
            apply_title_h1_metadata_case_repair_batch7_report(
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
            "metadata.title_h1_metadata_case_repair_batch7._atomic_write",
            side_effect=fail_second,
        ):
            with self.assertRaisesRegex(OSError, "atomic failure"):
                apply_title_h1_metadata_case_repair_batch7_report(report, self.root, backup)
        self.assertTrue(all(action.path.read_bytes() == action.original for action in report.actions))
        self.assertEqual(
            sorted(path.relative_to(backup).as_posix() for path in backup.rglob("*.md")),
            sorted(REVIEWED_TITLE_CHANGES),
        )
        for action in report.actions:
            self.assertEqual((backup / action.article).read_bytes(), action.original)

        fresh = self.base / "fresh/knowledge"
        fresh.mkdir(parents=True)
        self.root = fresh
        self.paths, source_hashes, post_hashes = self.write_family()
        final_backup = self.base / "fresh-backup"
        with (
            patch(
                "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_SOURCE_SHA256",
                source_hashes,
            ),
            patch(
                "metadata.title_h1_metadata_case_repair_batch7.REVIEWED_POST_SHA256",
                post_hashes,
            ),
        ):
            result = self.invoke("--apply", "--backup", str(final_backup))
            self.assertEqual(result.exit_code, 0, result.output)
            after = {path: path.read_bytes() for path in self.paths.values()}
            idempotent = self.invoke()
        self.assertIn("Files to update: 0", idempotent.output)
        self.assertEqual({path: path.read_bytes() for path in self.paths.values()}, after)

    def test_wrong_roots_help_and_backup_copy_failure_cleanup(self):
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_title_h1_metadata_case_repair_batch7_report(wrong)
        stale = self.base / "OneDrive/knowledge"
        stale.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "outside OneDrive"):
            build_title_h1_metadata_case_repair_batch7_report(stale)
        help_result = self.runner.invoke(
            app, ["repair-title-h1-metadata-case-repair-batch7", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        report = build_title_h1_metadata_case_repair_batch7_report(self.root)
        backup = self.base / "failed-backup"
        with patch(
            "metadata.title_h1_metadata_case_repair_batch7.shutil.copy2",
            side_effect=OSError("copy failure"),
        ):
            with self.assertRaisesRegex(OSError, "copy failure"):
                apply_title_h1_metadata_case_repair_batch7_report(report, self.root, backup)
        self.assertFalse(backup.exists())
        self.assertTrue(all(action.path.read_bytes() == action.original for action in report.actions))


if __name__ == "__main__":
    unittest.main()
