from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3a import (
    REVIEWED_ARTICLE,
    apply_category_normalization_batch3_3a_report,
    build_category_normalization_batch3_3a_report,
)


def article_text(newline: str = "\n") -> str:
    return (
        f"---{newline}title: Gambling 3NT{newline}description: Exact fixture.{newline}"
        f"category: Convention{newline}subcategory: conventions{newline}"
        f"difficulty: Expert{newline}tags:{newline}  - convention{newline}"
        f"  - retained{newline}systems:{newline}  - precision{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-18{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Gambling 3NT{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33aTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.path = self.root / REVIEWED_ARTICLE
        self.path.parent.mkdir(parents=True)
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, content: str) -> None:
        self.path.write_bytes(content.encode())

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3a", "--root", str(self.root), *args],
        )

    def test_dry_run_and_apply_preserve_every_unrelated_byte(self) -> None:
        self.write(article_text("\r\n"))
        other = self.root / "bidding/conventions/opening-bids/other.md"
        other.write_bytes(article_text().replace("Convention", "bidding", 1).encode())
        original = self.path.read_bytes()
        other_original = other.read_bytes()
        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 1)
        self.assertIn("Files selected      : 1", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(other.read_bytes(), other_original)

        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        expected = original.replace(
            b"category: Convention\r\n", b"category: bidding\r\n", 1
        )
        self.assertEqual(self.path.read_bytes(), expected)
        self.assertEqual((self.backup / REVIEWED_ARTICLE).read_bytes(), original)
        self.assertEqual(other.read_bytes(), other_original)

    def test_preconditions_backup_requirement_and_stale_report(self) -> None:
        self.write(article_text())
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3a_report(self.root)
        self.path.write_bytes(self.path.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3a_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())

        self.write(article_text().replace("  - convention", "  - changed"))
        with self.assertRaisesRegex(RuntimeError, "frozen-tag"):
            build_category_normalization_batch3_3a_report(self.root)

    def test_idempotence_explicit_root_and_help(self) -> None:
        self.write(article_text())
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        after = self.path.read_bytes()
        self.assertEqual(build_category_normalization_batch3_3a_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(self.path.read_bytes(), after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3a", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
