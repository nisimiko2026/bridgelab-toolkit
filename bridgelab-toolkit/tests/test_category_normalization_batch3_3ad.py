from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3ad import (
    ARTICLE,
    REQUIRED_TAGS,
    _canonical_category_from_path,
    apply_category_normalization_batch3_3ad_report,
    build_category_normalization_batch3_3ad_report,
)


def article_text(tags=REQUIRED_TAGS, newline="\n", category="Bridge Formats", subcategory=""):
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Duplicate Bridge{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: '{subcategory}'{newline}difficulty: Intermediate{newline}"
        f"tags: {newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: 2026-07-22{newline}status: Draft{newline}"
        f"---{newline}# Duplicate Bridge{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33adTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self):
        self.temp.cleanup()

    def target(self, newline="\n"):
        path = self.root / ARTICLE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(newline=newline).encode())
        return path

    def invoke(self, *args):
        return self.runner.invoke(app, ["repair-category-normalization-batch3-3ad", "--root", str(self.root), *args])

    def test_selection_census_domain_exclusions_dry_run_and_root_guard(self):
        target = self.target()
        self.assertEqual(_canonical_category_from_path(ARTICLE), "duplicate")
        with self.assertRaisesRegex(RuntimeError, "Unrecognized canonical domain"):
            _canonical_category_from_path("play/duplicates-index.md")
        other = self.root / "duplicates/other.md"
        other.write_bytes(article_text(category="duplicate").encode())
        before = {p: p.read_bytes() for p in (target, other)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 1)
        self.assertIn("Files selected      : 1", first.output)
        self.assertEqual({p: p.read_bytes() for p in (target, other)}, before)
        stale = self.base / "knowladge"
        stale.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_category_normalization_batch3_3ad_report(stale)
        extra = self.root / "duplicates/extra.md"
        extra.write_bytes(article_text().encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3ad_report(self.root)
        extra.unlink()
        target.unlink()
        with self.assertRaisesRegex(RuntimeError, "file is missing"):
            build_category_normalization_batch3_3ad_report(self.root)

    def test_category_only_lf_crlf_and_frozen_metadata(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                action = build_category_normalization_batch3_3ad_report(self.root).actions[0]
                expected = original.replace(
                    f"category: Bridge Formats{newline}".encode(),
                    f"category: duplicate{newline}".encode(), 1,
                )
                self.assertEqual(action.updated, expected)
                self.assertIn(f"subcategory: ''{newline}".encode(), expected)
                positions = [expected.index(f"  - {tag}".encode()) for tag in REQUIRED_TAGS]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn(f"  - duplicate{newline}".encode(), expected)

    def test_stale_category_subcategory_and_tag_failures(self):
        target = self.target("\r\n")
        original = target.read_bytes()
        changes = (
            (b"category: Bridge Formats", b"category: Other", "category precondition"),
            (b"category: Bridge Formats", b"category:  Bridge Formats", "Unsafe category line"),
            (b"subcategory: ''", b"subcategory: formats", "frozen-subcategory"),
            (b"  - bridge formats", b"  - changed", "frozen-tag"),
            (b"  - bridge formats", b"  - duplicate", "frozen-tag"),
            (b"  - bridge formats\r\n  - competitive", b"  - competitive\r\n  - bridge formats", "frozen-tag"),
            (b"  - competitive\r\n", b"", "frozen-tag"),
        )
        for old, new, message in changes:
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3ad_report(self.root)
            target.write_bytes(original)

    def test_apply_guards_backup_atomic_failure_and_idempotence(self):
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3ad_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_category_normalization_batch3_3ad_report(report, self.root, self.backup)
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3ad_report(report, self.root, self.backup)
        self.backup.rmdir()
        original = target.read_bytes()
        with patch("metadata.category_normalization_batch3_3ad._atomic_write", side_effect=OSError("atomic failure")):
            failed = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(failed.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / ARTICLE).read_bytes(), original)
        fresh_root = self.base / "fresh" / "knowledge"
        fresh_root.mkdir(parents=True)
        self.root = fresh_root
        target = self.target()
        applied = self.invoke("--apply", "--backup", str(self.base / "fresh-backup"))
        self.assertEqual(applied.exit_code, 0, applied.output)
        after = target.read_bytes()
        self.assertEqual(build_category_normalization_batch3_3ad_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)

    def test_explicit_root_and_cli_help(self):
        self.target()
        self.assertEqual(self.invoke().exit_code, 0)
        result = self.runner.invoke(app, ["repair-category-normalization-batch3-3ad", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
