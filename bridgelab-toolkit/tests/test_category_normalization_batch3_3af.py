from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3af import (
    ARTICLES,
    REQUIRED_TAGS,
    _canonical_category_from_path,
    apply_category_normalization_batch3_3af_report,
    build_category_normalization_batch3_3af_report,
)


def article_text(tags, newline="\n", category="Index", subcategory="natural-bids"):
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Index{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}"
        f"difficulty: Intermediate{newline}tags: {newline}{tag_lines}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: 2026-07-22{newline}status: Draft{newline}"
        f"---{newline}# Index{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33afTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.runner = CliRunner()
        self.targets = self.make_family()

    def tearDown(self):
        self.temp.cleanup()

    def make_family(self, newlines=None):
        result = []
        for index, article in enumerate(ARTICLES):
            path = self.root / article
            path.parent.mkdir(parents=True, exist_ok=True)
            newline = newlines[index] if newlines else "\n"
            path.write_bytes(article_text(REQUIRED_TAGS[article], newline).encode())
            result.append(path)
        return result

    def invoke(self, *args):
        return self.runner.invoke(
            app, ["repair-category-normalization-batch3-3af", "--root", str(self.root), *args]
        )

    def test_exact_family_census_play_exclusion_dry_run_and_root_guard(self):
        play = self.root / "play/planning-index.md"
        play.parent.mkdir()
        play.write_bytes(article_text(["index"], category="Index", subcategory="play").encode())
        other = self.root / "bidding/other.md"
        other.write_bytes(article_text(["other"], category="bidding").encode())
        before = {path: path.read_bytes() for path in (*self.targets, play, other)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 3)
        self.assertIn("Files selected      : 3", first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertEqual(_canonical_category_from_path(ARTICLES[0]), "bidding")
        with self.assertRaisesRegex(RuntimeError, "Unrecognized canonical domain"):
            _canonical_category_from_path("play/index.md")
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_category_normalization_batch3_3af_report(wrong)
        extra = self.root / "bidding/extra.md"
        extra.write_bytes(article_text(["index"]).encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3af_report(self.root)
        extra.unlink()
        self.targets[0].unlink()
        with self.assertRaisesRegex(RuntimeError, "file is missing"):
            build_category_normalization_batch3_3af_report(self.root)

    def test_exact_category_only_mixed_line_endings_and_frozen_metadata(self):
        for path in self.targets:
            path.unlink()
        self.targets = self.make_family(["\n", "\r\n", "\n"])
        report = build_category_normalization_batch3_3af_report(self.root)
        for action in report.actions:
            expected = action.original.replace(b"category: Index", b"category: bidding", 1)
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: natural-bids", action.updated)
            self.assertNotIn(b"  - bidding\n", action.updated)

    def test_metadata_and_indivisible_family_rejections(self):
        original = self.targets[0].read_bytes()
        changes = (
            (b"category: Index", b"category: Other", "category precondition"),
            (b"subcategory: natural-bids", b"subcategory: other", "frozen-subcategory"),
            (b"  - index", b"  - changed", "frozen-tag"),
            (b"  - natural-bids", b"  - bidding", "frozen-tag"),
            (b"  - index\n  - natural-bids", b"  - natural-bids\n  - index", "frozen-tag"),
        )
        for old, new, message in changes:
            self.targets[0].write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3af_report(self.root)
            self.targets[0].write_bytes(original)
        self.targets[0].write_bytes(original.replace(b"category: Index", b"category: bidding", 1))
        with self.assertRaisesRegex(RuntimeError, "partially normalized"):
            build_category_normalization_batch3_3af_report(self.root)

    def test_apply_guards_backup_rollback_stale_plan_and_idempotence(self):
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3af_report(self.root)
        originals = [path.read_bytes() for path in self.targets]
        self.targets[1].write_bytes(originals[1] + b"stale")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_category_normalization_batch3_3af_report(report, self.root, self.base / "backup")
        self.targets[1].write_bytes(originals[1])
        backup = self.base / "backup"
        backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3af_report(report, self.root, backup)
        backup.rmdir()
        calls = 0
        from metadata.sentinel_cleanup import _atomic_write as real_atomic

        def fail_second(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("replacement failure")
            real_atomic(path, content)

        with patch("metadata.category_normalization_batch3_3af._atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                apply_category_normalization_batch3_3af_report(report, self.root, self.base / "failed-backup")
        self.assertEqual([path.read_bytes() for path in self.targets], originals)
        applied = self.invoke("--apply", "--backup", str(self.base / "fresh-backup"))
        self.assertEqual(applied.exit_code, 0, applied.output)
        after = [path.read_bytes() for path in self.targets]
        self.assertEqual(build_category_normalization_batch3_3af_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual([path.read_bytes() for path in self.targets], after)

    def test_explicit_root_cli_help_and_path_preserving_backups(self):
        self.assertEqual(self.invoke().exit_code, 0)
        help_result = self.runner.invoke(app, ["repair-category-normalization-batch3-3af", "--help"])
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        backup = self.base / "backups"
        report = build_category_normalization_batch3_3af_report(self.root)
        apply_category_normalization_batch3_3af_report(report, self.root, backup)
        for action in report.actions:
            self.assertEqual((backup / action.article).read_bytes(), action.original)


if __name__ == "__main__":
    unittest.main()
