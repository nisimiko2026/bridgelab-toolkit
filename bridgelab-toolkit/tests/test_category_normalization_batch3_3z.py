from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3z import (
    ARTICLE,
    REQUIRED_TAGS,
    apply_category_normalization_batch3_3z_report,
    build_category_normalization_batch3_3z_report,
)


def article_text(
    tags: list[str] = REQUIRED_TAGS,
    newline: str = "\n",
    category: str = "Opening Principles",
    subcategory: str = "principles",
) -> str:
    tag_lines = "".join(f"- {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Rule of 22{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}"
        f"difficulty: Beginner to Expert{newline}tags:{newline}{tag_lines}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: '2026-07-27'{newline}status: Standard{newline}---{newline}"
        f"# Rule of 22{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33zTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def target(self, newline: str = "\n") -> Path:
        path = self.root / ARTICLE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(newline=newline).encode())
        return path

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3z", "--root", str(self.root), *args],
        )

    def test_exact_selection_census_exclusions_dry_run_and_root_guard(self) -> None:
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
            build_category_normalization_batch3_3z_report(stale)
        extra = self.root / "bidding/extra.md"
        extra.write_bytes(article_text().encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3z_report(self.root)

    def test_exact_category_only_lf_crlf_and_frozen_metadata(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                action = build_category_normalization_batch3_3z_report(self.root).actions[0]
                expected = original.replace(
                    f"category: Opening Principles{newline}".encode(),
                    f"category: bidding{newline}".encode(),
                    1,
                )
                self.assertEqual(action.updated, expected)
                self.assertIn(f"subcategory: principles{newline}".encode(), expected)
                positions = [expected.index(f"- {tag}".encode()) for tag in REQUIRED_TAGS]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn(f"- bidding{newline}".encode(), expected)

    def test_stale_category_subcategory_and_tag_failures(self) -> None:
        target = self.target("\r\n")
        original = target.read_bytes()
        changes = (
            (b"category: Opening Principles", b"category: Convention", "category precondition"),
            (b"category: Opening Principles", b"category:  Opening Principles", "Unsafe category line"),
            (b"subcategory: principles", b"subcategory: conventions", "frozen-subcategory"),
            (b"- opening principles", b"- changed", "frozen-tag"),
            (b"- principles", b"- bidding", "frozen-tag"),
            (b"- opening\r\n- opening principles", b"- opening principles\r\n- opening", "frozen-tag"),
            (b"- principles\r\n", b"", "frozen-tag"),
        )
        for old, new, message in changes:
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3z_report(self.root)
            target.write_bytes(original)

    def test_apply_backup_stale_plan_atomic_failure_and_idempotence(self) -> None:
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3z_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_category_normalization_batch3_3z_report(report, self.root, self.backup)
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3z_report(report, self.root, self.backup)
        self.backup.rmdir()
        original = target.read_bytes()
        with patch(
            "metadata.category_normalization_batch3_3z._atomic_write",
            side_effect=OSError("atomic replacement failed"),
        ):
            failed = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(failed.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / ARTICLE).read_bytes(), original)
        fresh = self.base / "fresh-backup"
        applied = self.invoke("--apply", "--backup", str(fresh))
        self.assertEqual(applied.exit_code, 0, applied.output)
        after = target.read_bytes()
        self.assertEqual(build_category_normalization_batch3_3z_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)

    def test_explicit_root_and_cli_help(self) -> None:
        self.target()
        self.assertEqual(self.invoke().exit_code, 0)
        result = self.runner.invoke(app, ["repair-category-normalization-batch3-3z", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
