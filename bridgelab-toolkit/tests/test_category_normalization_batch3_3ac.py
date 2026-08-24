from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3ac import (
    ARTICLE,
    REQUIRED_TAGS,
    apply_category_normalization_batch3_3ac_report,
    build_category_normalization_batch3_3ac_report,
)


def article_text(tags=REQUIRED_TAGS, newline="\n", category="Principles", subcategory="Bidding Principles"):
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Game Invitations{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags: {newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: 2026-07-21{newline}status: Draft{newline}"
        f"---{newline}# Game Invitations{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33acTests(unittest.TestCase):
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
        return self.runner.invoke(app, ["repair-category-normalization-batch3-3ac", "--root", str(self.root), *args])

    def test_selection_census_exclusions_dry_run_and_root_guard(self):
        target = self.target()
        other = self.root / "bidding/other.md"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_bytes(article_text(category="bidding").encode())
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
            build_category_normalization_batch3_3ac_report(stale)
        extra = self.root / "bidding/extra.md"
        extra.write_bytes(article_text().encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3ac_report(self.root)
        extra.unlink()
        target.unlink()
        with self.assertRaisesRegex(RuntimeError, "file is missing"):
            build_category_normalization_batch3_3ac_report(self.root)

    def test_category_only_lf_crlf_and_frozen_metadata(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                action = build_category_normalization_batch3_3ac_report(self.root).actions[0]
                expected = original.replace(
                    f"category: Principles{newline}".encode(), f"category: bidding{newline}".encode(), 1
                )
                self.assertEqual(action.updated, expected)
                self.assertIn(f"subcategory: Bidding Principles{newline}".encode(), expected)
                positions = [expected.index(f"  - {tag}".encode()) for tag in REQUIRED_TAGS]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn(f"  - bidding{newline}".encode(), expected)

    def test_stale_category_subcategory_and_tag_failures(self):
        target = self.target("\r\n")
        original = target.read_bytes()
        changes = (
            (b"category: Principles", b"category: Other", "category precondition"),
            (b"category: Principles", b"category:  Principles", "Unsafe category line"),
            (b"subcategory: Bidding Principles", b"subcategory: conventions", "frozen-subcategory"),
            (b"  - bidding principles", b"  - changed", "frozen-tag"),
            (b"  - principles", b"  - bidding", "frozen-tag"),
            (b"  - bidding principles\r\n  - drury", b"  - drury\r\n  - bidding principles", "frozen-tag"),
            (b"  - two over one\r\n", b"", "frozen-tag"),
        )
        for old, new, message in changes:
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3ac_report(self.root)
            target.write_bytes(original)

    def test_apply_guards_backup_atomic_failure_and_idempotence(self):
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3ac_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_category_normalization_batch3_3ac_report(report, self.root, self.backup)
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3ac_report(report, self.root, self.backup)
        self.backup.rmdir()
        original = target.read_bytes()
        with patch("metadata.category_normalization_batch3_3ac._atomic_write", side_effect=OSError("atomic failure")):
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
        self.assertEqual(build_category_normalization_batch3_3ac_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)

    def test_explicit_root_and_cli_help(self):
        self.target()
        self.assertEqual(self.invoke().exit_code, 0)
        result = self.runner.invoke(app, ["repair-category-normalization-batch3-3ac", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
