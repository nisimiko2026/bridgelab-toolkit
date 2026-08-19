from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3b import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3B,
    apply_category_normalization_batch3_3b_report,
    build_category_normalization_batch3_3b_report,
)


def article_text(subcategory: str, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Reviewed Double{newline}description: Exact fixture.{newline}"
        f"category: Convention{newline}subcategory: {subcategory}{newline}"
        f"difficulty: Expert{newline}tags:{newline}  - competitive{newline}"
        f"  - convention{newline}  - double{newline}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-19{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Reviewed Double{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33bTests(unittest.TestCase):
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
        for index, relative in enumerate(sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3B)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            subcategory = "Doubles" if relative.endswith("action-double.md") else "Competitive"
            path.write_bytes(
                article_text(subcategory, "\r\n" if index == 0 else "\n").encode()
            )
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3b", "--root", str(self.root), *args],
        )

    def test_selection_exclusion_dry_run_and_byte_preserving_apply(self) -> None:
        targets = self.targets()
        other = self.root / "bidding/conventions/doubles/other.md"
        other.write_bytes(article_text("Doubles").encode())
        before = {path: path.read_bytes() for path in [*targets.values(), other]}

        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 2)
        self.assertIn("Files selected      : 2", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertIn("Subcategory changes : 0", dry.output)
        self.assertNotIn("other.md", dry.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        for relative, path in targets.items():
            original = before[path]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: Convention" + ending,
                b"category: bidding" + ending,
                1,
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
        self.assertEqual(other.read_bytes(), before[other])

    def test_stale_plan_and_preconditions_fail_before_backup(self) -> None:
        targets = self.targets()
        report = build_category_normalization_batch3_3b_report(self.root)
        stale = targets[sorted(targets)[1]]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3b_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

        stale.write_bytes(stale.read_bytes().replace(b"- convention", b"- changed", 1))
        with self.assertRaisesRegex(RuntimeError, "frozen-tag"):
            build_category_normalization_batch3_3b_report(self.root)

    def test_fresh_backup_apply_idempotence_explicit_root_and_help(self) -> None:
        self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        self.backup.mkdir()
        self.assertNotEqual(
            self.invoke("--apply", "--backup", str(self.backup)).exit_code,
            0,
        )
        self.backup.rmdir()
        self.assertEqual(
            self.invoke("--apply", "--backup", str(self.backup)).exit_code,
            0,
        )
        self.assertEqual(build_category_normalization_batch3_3b_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3b", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
