from __future__ import annotations

import hashlib
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.sentinel_cleanup import _atomic_write as real_atomic_write
from metadata.title_h1_content_repair_batch3 import (
    REVIEWED_CONTENT_REPAIRS,
    apply_title_h1_content_repair_batch3_report,
    build_title_h1_content_repair_batch3_report,
)


def article_text(source: str, *, newline: str = "\n") -> bytes:
    return (
        f"---{newline}title: {source}{newline}description: Exact Batch 3 fixture.{newline}"
        f"category: bidding{newline}subcategory: conventions{newline}"
        f"difficulty: Advanced{newline}tags:{newline}- bidding{newline}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: '2026-07-27'{newline}status: Draft{newline}---{newline}{newline}"
        f"# Objectives{newline}{newline}Opening prose unchanged.{newline}{newline}"
        f"```{newline}1S - 3S{newline}```{newline}{newline}# Major Section{newline}{newline}"
        f"## Existing Child{newline}{newline}Body unchanged.{newline}"
    ).encode("utf-8")


def expected_post(original: bytes, source: str, target: str) -> bytes:
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    updated = original.replace(
        f"title: {source}".encode(), f"title: {target}".encode(), 1
    )
    return updated.replace(
        b"# Objectives",
        f"# {target}".encode("utf-8") + newline + newline + b"# Objectives",
        1,
    )


def headings(content: bytes) -> list[tuple[int, str]]:
    text = content.decode("utf-8")
    return [
        (len(match.group(1)), match.group(2))
        for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.MULTILINE)
    ]


class TitleH1ContentRepairBatch3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.runner = CliRunner()
        self.paths, source_hashes, post_hashes = self.write_family()
        self.source_patch = patch(
            "metadata.title_h1_content_repair_batch3.REVIEWED_SOURCE_SHA256",
            source_hashes,
        )
        self.post_patch = patch(
            "metadata.title_h1_content_repair_batch3.REVIEWED_POST_SHA256",
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
        for article, (source, target) in REVIEWED_CONTENT_REPAIRS.items():
            path = self.root / article
            path.parent.mkdir(parents=True, exist_ok=True)
            content = article_text(source, newline=newline)
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
            ["repair-title-h1-content-repair-batch3", "--root", str(self.root), *args],
        )

    def test_exact_census_order_exclusion_determinism_and_dry_run(self):
        unrelated = self.root / "play/unrelated.md"
        unrelated.parent.mkdir()
        unrelated.write_bytes(article_text("Unrelated").replace(b"# Objectives", b"# Different", 1))
        before = {path: path.read_bytes() for path in (*self.paths.values(), unrelated)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET TITLE + INSERT H1 |"), 2)
        for expected in (
            "Files selected     : 2",
            "Files to update    : 2",
            "Title changes      : 2",
            "Document H1 inserts: 2",
            "Files to back up   : 2",
        ):
            self.assertIn(expected, first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((self.base / "backup").exists())
        report = build_title_h1_content_repair_batch3_report(self.root)
        self.assertEqual([action.article for action in report.actions], list(REVIEWED_CONTENT_REPAIRS))

    def test_missing_selected_missing_defect_extra_and_unrelated_mismatch(self):
        article = next(iter(REVIEWED_CONTENT_REPAIRS))
        source, target = REVIEWED_CONTENT_REPAIRS[article]
        path, original = self.paths[article], self.paths[article].read_bytes()
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "census mismatch|file is missing"):
            build_title_h1_content_repair_batch3_report(self.root)
        path.write_bytes(original)
        path.write_bytes(expected_post(original, source, target))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_content_repair_batch3_report(self.root)
        path.write_bytes(original)
        extra = self.root / "play/extra.md"
        extra.parent.mkdir(exist_ok=True)
        extra.write_bytes(article_text("Extra"))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_content_repair_batch3_report(self.root)
        extra.unlink()
        unrelated = self.root / "play/unrelated.md"
        unrelated.write_bytes(article_text("Other").replace(b"# Objectives", b"# Different", 1))
        self.assertEqual(
            len(build_title_h1_content_repair_batch3_report(self.root).actions), 2
        )

    def test_all_complete_byte_preconditions_fail_closed(self):
        article = next(iter(REVIEWED_CONTENT_REPAIRS))
        source, target = REVIEWED_CONTENT_REPAIRS[article]
        path, original = self.paths[article], self.paths[article].read_bytes()
        cases = (
            (f"title: {source}".encode(), b"title: Stale", "census mismatch|title precondition"),
            (b"# Objectives", b"# Stale", "census mismatch|first-H1"),
            (b"# Objectives", f"# {target}\n\n# Objectives".encode(), "census mismatch|title precondition"),
            (b"Body unchanged.", b"Body changed.", "complete-byte source"),
            (b"status: Draft", b"status: Standard", "complete-byte source"),
            (b"# Major Section", b"# Changed Section", "complete-byte source"),
            (b"Opening prose", b"Opening  prose", "complete-byte source"),
        )
        for old, new, message in cases:
            with self.subTest(message=message):
                path.write_bytes(original.replace(old, new, 1))
                with self.assertRaisesRegex(RuntimeError, message):
                    build_title_h1_content_repair_batch3_report(self.root)
                path.write_bytes(original)

    def test_exact_lf_crlf_mutation_and_heading_debt_regression(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                self.paths, source_hashes, post_hashes = self.write_family(newline=newline)
                with (
                    patch(
                        "metadata.title_h1_content_repair_batch3.REVIEWED_SOURCE_SHA256",
                        source_hashes,
                    ),
                    patch(
                        "metadata.title_h1_content_repair_batch3.REVIEWED_POST_SHA256",
                        post_hashes,
                    ),
                ):
                    report = build_title_h1_content_repair_batch3_report(self.root)
                for action in report.actions:
                    expected = expected_post(
                        action.original, action.original_title, action.proposed_title
                    )
                    self.assertEqual(action.updated, expected)
                    old_headings = headings(action.original)
                    new_headings = headings(action.updated)
                    self.assertEqual(new_headings[0], (1, action.proposed_title))
                    self.assertEqual(new_headings[1:], old_headings)
                    self.assertIn(b"# Objectives", action.updated)
                    self.assertIn(b"```", action.updated)
                    self.assertIn(b"Opening prose unchanged.", action.updated)
                    self.assertIn(b"status: Draft", action.updated)

    def test_apply_guards_backup_preflight_rollback_and_idempotence(self):
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_title_h1_content_repair_batch3_report(self.root)
        backup = self.base / "backup"
        stale = report.actions[-1]
        stale.path.write_bytes(stale.original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_title_h1_content_repair_batch3_report(report, self.root, backup)
        self.assertFalse(backup.exists())
        stale.path.write_bytes(stale.original)
        backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_title_h1_content_repair_batch3_report(report, self.root, backup)
        backup.rmdir()
        with self.assertRaisesRegex(RuntimeError, "outside canonical knowledge"):
            apply_title_h1_content_repair_batch3_report(report, self.root, self.root / "backup")

        calls = 0

        def fail_second(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("atomic failure")
            real_atomic_write(path, content)

        with patch(
            "metadata.title_h1_content_repair_batch3._atomic_write", side_effect=fail_second
        ):
            with self.assertRaisesRegex(OSError, "atomic failure"):
                apply_title_h1_content_repair_batch3_report(report, self.root, backup)
        self.assertTrue(all(action.path.read_bytes() == action.original for action in report.actions))

        fresh = self.base / "fresh/knowledge"
        fresh.mkdir(parents=True)
        self.root = fresh
        self.paths, source_hashes, post_hashes = self.write_family()
        final_backup = self.base / "fresh-backup"
        with (
            patch(
                "metadata.title_h1_content_repair_batch3.REVIEWED_SOURCE_SHA256",
                source_hashes,
            ),
            patch(
                "metadata.title_h1_content_repair_batch3.REVIEWED_POST_SHA256",
                post_hashes,
            ),
        ):
            result = self.invoke("--apply", "--backup", str(final_backup))
            self.assertEqual(result.exit_code, 0, result.output)
            after = {path: path.read_bytes() for path in self.paths.values()}
            idempotent = self.invoke()
        self.assertIn("Files to update    : 0", idempotent.output)
        self.assertEqual({path: path.read_bytes() for path in self.paths.values()}, after)
        self.assertEqual(
            sorted(path.relative_to(final_backup).as_posix() for path in final_backup.rglob("*.md")),
            sorted(REVIEWED_CONTENT_REPAIRS),
        )

    def test_roots_help_and_title_sort_contract(self):
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_title_h1_content_repair_batch3_report(wrong)
        stale = self.base / "OneDrive/knowledge"
        stale.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "outside OneDrive"):
            build_title_h1_content_repair_batch3_report(stale)
        help_result = self.runner.invoke(app, ["repair-title-h1-content-repair-batch3", "--help"])
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        titles = [
            ("club", "1 Club", "1♣ Opening Bid"),
            ("nt", "1NT Opening Bid", "1NT Opening Bid"),
            ("spade", "1♠ Opening Bid", "1♠ Opening Bid"),
            ("preempt", "Preemptive.Raise", "Preemptive Raise"),
        ]
        before = [key for key, old, _ in sorted(titles, key=lambda item: item[1].casefold())]
        after = [key for key, _, new in sorted(titles, key=lambda item: item[2].casefold())]
        self.assertEqual(before, ["club", "nt", "spade", "preempt"])
        self.assertEqual(after, ["nt", "spade", "club", "preempt"])


if __name__ == "__main__":
    unittest.main()
