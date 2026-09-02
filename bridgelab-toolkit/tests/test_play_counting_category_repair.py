from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_COUNTING_ARTICLE,
    apply_play_counting_category_report,
    build_play_counting_category_report,
)


def article_text(*, category: str = "Card Play – Defence", newline: str = "\n") -> str:
    return (
        f"---{newline}title: Defensive Counting{newline}"
        f"description: Reviewed fixture preserving all unrelated bytes exactly.{newline}"
        f"category: {category}{newline}subcategory: defence{newline}"
        f"difficulty: Intermediate to Expert{newline}"
        f"tags: {newline}  - card play – defence{newline}  - counting{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: {newline}  - play/counting/counting-index{newline}"
        f"last_updated: 2026-08-16{newline}status: Draft{newline}"
        f"unknown_field: preserve exactly{newline}---{newline}"
        f"# Defensive Counting{newline}{newline}Body  bytes  stay exact.{newline}"
    )


class PlayCountingCategoryRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "explicit-backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
        return path

    def target(self, *, newline: str = "\n") -> Path:
        return self.write(REVIEWED_COUNTING_ARTICLE, article_text(newline=newline))

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["repair-play-counting-category", "--root", str(self.root), *arguments],
        )

    def test_dry_run_selects_only_counting_and_writes_nothing(self) -> None:
        target = self.target(newline="\r\n")
        other = self.write("play/defence/other.md", article_text())
        bidding = self.write("bidding/other.md", article_text())
        before = {path: path.read_bytes() for path in (target, other, bidding)}

        first = self.invoke()
        second = self.invoke()

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertIn(REVIEWED_COUNTING_ARTICLE, first.output)
        self.assertIn("Files selected      : 1", first.output)
        self.assertIn("Files to update     : 1", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("play/defence/other.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_is_one_line_only_and_backup_is_exact(self) -> None:
        target = self.target(newline="\r\n")
        original = target.read_bytes()

        result = self.invoke("--apply", "--backup", str(self.backup))

        self.assertEqual(result.exit_code, 0, result.output)
        expected = original.replace(
            b"category: Card Play \xe2\x80\x93 Defence\r\n",
            b"category: play\r\n",
            1,
        )
        self.assertEqual(target.read_bytes(), expected)
        self.assertEqual((self.backup / REVIEWED_COUNTING_ARTICLE).read_bytes(), original)
        for unchanged in (
            b"subcategory: defence\r\n",
            b"  - card play \xe2\x80\x93 defence\r\n",
            b"last_updated: 2026-08-16\r\n",
            b"unknown_field: preserve exactly\r\n",
            b"Body  bytes  stay exact.\r\n",
        ):
            self.assertIn(unchanged, expected)
        self.assertNotIn(b"  - play\r\n", expected)

    def test_apply_requires_backup_and_stale_plan_creates_nothing(self) -> None:
        target = self.target()
        original = target.read_bytes()
        missing_backup = self.invoke("--apply")
        self.assertNotEqual(missing_backup.exit_code, 0)
        self.assertIn("--backup is required", missing_backup.output)
        self.assertEqual(target.read_bytes(), original)

        report = build_play_counting_category_report(self.root)
        target.write_bytes(original + b"external change\n")
        stale = target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_counting_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), stale)
        self.assertFalse(self.backup.exists())

    def test_backup_refusal_and_atomic_failure_preserve_source(self) -> None:
        target = self.target()
        original = target.read_bytes()
        report = build_play_counting_category_report(self.root)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_counting_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)

        self.backup.rmdir()
        with patch(
            "metadata.play_endgame_category_repair._atomic_write",
            side_effect=OSError("replace failed"),
        ):
            with self.assertRaisesRegex(OSError, "replace failed"):
                apply_play_counting_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / REVIEWED_COUNTING_ARTICLE).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        target = self.target()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = target.read_bytes()
        report = build_play_counting_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(app, ["repair-play-counting-category", "--help"])

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(report.actions, ())
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertIn("Files to back up    : 0", second.output)
        self.assertEqual(target.read_bytes(), after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--root", help_result.output)
        self.assertIn("--backup", help_result.output)
        self.assertIn("--apply", help_result.output)


if __name__ == "__main__":
    unittest.main()
