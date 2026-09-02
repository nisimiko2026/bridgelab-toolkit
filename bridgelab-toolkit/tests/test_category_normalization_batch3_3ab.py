from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3ab import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AB,
    apply_category_normalization_batch3_3ab_report,
    build_category_normalization_batch3_3ab_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(tags, newline="\n", category="Partnership Agreements", subcategory="principles"):
    tag_lines = "".join(f"- {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Partnership Fixture{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Expert{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: '2026-07-27'{newline}status: Standard{newline}"
        f"---{newline}# Partnership Fixture{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33abTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self):
        self.temp.cleanup()

    def targets(self):
        result = {}
        for index, (relative, tags) in enumerate(sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AB.items())):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(tags, "\r\n" if index == 0 else "\n").encode())
            result[relative] = path
        return result

    def invoke(self, *args):
        return self.runner.invoke(app, ["repair-category-normalization-batch3-3ab", "--root", str(self.root), *args])

    def test_selection_census_exclusions_dry_run_and_root_guard(self):
        targets = self.targets()
        other = self.root / "bidding/other.md"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_bytes(article_text(next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AB.values())), category="bidding").encode())
        paths = [*targets.values(), other]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 2)
        self.assertIn("Files selected      : 2", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        stale = self.base / "knowladge"
        stale.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_category_normalization_batch3_3ab_report(stale)
        extra = self.root / "bidding/extra.md"
        extra.write_bytes(article_text(next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AB.values()))).encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3ab_report(self.root)
        extra.unlink()
        targets[sorted(targets)[0]].unlink()
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3ab_report(self.root)

    def test_category_only_lf_crlf_and_frozen_metadata(self):
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_category_normalization_batch3_3ab_report(self.root)
        self.assertEqual(len(report.actions), 2)
        for action in report.actions:
            original = originals[action.article]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(b"category: Partnership Agreements" + ending, b"category: bidding" + ending, 1)
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: principles" + ending, expected)
            tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3AB[action.article]
            positions = [expected.index(f"- {tag}".encode()) for tag in tags]
            self.assertEqual(positions, sorted(positions))
            self.assertNotIn(b"- bidding" + ending, expected)

    def test_stale_category_subcategory_and_tag_failures(self):
        targets = self.targets()
        relative = sorted(targets)[0]
        path = targets[relative]
        original = path.read_bytes()
        changes = (
            (b"category: Partnership Agreements", b"category: Other", "completeness mismatch"),
            (b"category: Partnership Agreements", b"category:  Partnership Agreements", "Unsafe category line"),
            (b"subcategory: principles", b"subcategory: methods", "frozen-subcategory"),
            (b"- partnership agreements", b"- changed", "frozen-tag"),
            (b"- principles", b"- bidding", "frozen-tag"),
            (b"- blackwood\r\n- cappelletti", b"- cappelletti\r\n- blackwood", "frozen-tag"),
            (b"- walsh\r\n", b"", "frozen-tag"),
        )
        for old, new, message in changes:
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3ab_report(self.root)
            path.write_bytes(original)

    def test_apply_guards_backups_atomic_failure_and_idempotence(self):
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3ab_report(self.root)
        stale = targets[sorted(targets)[-1]]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_category_normalization_batch3_3ab_report(report, self.root, self.backup)
        stale.write_bytes(report.actions[-1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3ab_report(report, self.root, self.backup)
        self.backup.rmdir()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0
        def fail_second(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("atomic replacement failed")
            _atomic_write(path, content)
        with patch("metadata.category_normalization_batch3_3ab._atomic_write", side_effect=fail_second):
            failed = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(failed.exit_code, 0)
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)
        fresh_root = self.base / "fresh" / "knowledge"
        fresh_root.mkdir(parents=True)
        self.root = fresh_root
        targets = self.targets()
        fresh_backup = self.base / "fresh-backup"
        applied = self.invoke("--apply", "--backup", str(fresh_backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_category_normalization_batch3_3ab_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)

    def test_explicit_root_and_cli_help(self):
        self.targets()
        self.assertEqual(self.invoke().exit_code, 0)
        result = self.runner.invoke(app, ["repair-category-normalization-batch3-3ab", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
