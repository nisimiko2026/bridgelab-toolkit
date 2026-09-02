from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_1 import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_1,
    apply_category_normalization_batch3_1_report,
    build_category_normalization_batch3_1_report,
)


def article_text(category: str, newline: str = "\n") -> str:
    tag = category.lower()
    return (
        f"---{newline}title: Reviewed{newline}description: Preserve exact bytes.{newline}"
        f"category: {category}{newline}subcategory: systems{newline}"
        f"difficulty: Advanced{newline}tags:{newline}- {tag}{newline}- retained{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: 2026-08-18{newline}status: Draft{newline}unknown_field: exact{newline}"
        f"---{newline}# Reviewed{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch31Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def targets(self) -> dict[str, Path]:
        result = {}
        for index, (relative, category) in enumerate(
            sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_1.items())
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                article_text(category, "\r\n" if index == 0 else "\n").encode()
            )
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-1", "--root", str(self.root), *args],
        )

    def test_dry_run_scope_and_apply_preserve_all_other_bytes(self) -> None:
        targets = self.targets()
        other = self.root / "bidding/systems/other.md"
        other.write_bytes(article_text("bidding").encode())
        before = {path: path.read_bytes() for path in [*targets.values(), other]}
        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 2)
        self.assertIn("Files selected      : 2", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertNotIn("other.md", dry.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        for relative, path in targets.items():
            original = before[path]
            observed = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_1[relative].encode()
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: " + observed + ending, b"category: bidding" + ending, 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_preconditions_stale_report_backup_and_idempotence(self) -> None:
        targets = self.targets()
        report = build_category_normalization_batch3_1_report(self.root)
        stale = targets[sorted(targets)[0]]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_1_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())

        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.targets()
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        self.assertEqual(build_category_normalization_batch3_1_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)

    def test_frozen_tags_apply_requires_backup_and_help(self) -> None:
        targets = self.targets()
        path = targets[sorted(targets)[0]]
        path.write_bytes(path.read_bytes().replace(b"- bidding systems", b"- changed", 1))
        with self.assertRaisesRegex(RuntimeError, "frozen-tag"):
            build_category_normalization_batch3_1_report(self.root)
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-1", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
