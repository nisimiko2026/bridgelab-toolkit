from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_PROBABILITY_ARTICLE,
    apply_play_probability_category_report,
    build_play_probability_category_report,
)


def article_text(*, newline: str = "\n", extra_tag: str = "") -> str:
    extra = f"- {extra_tag}{newline}" if extra_tag else ""
    return (
        f"---{newline}title: Probability{newline}"
        f"description: Reviewed probability byte-preservation fixture.{newline}"
        f"category: Card Play – Principles{newline}subcategory: declarer-play{newline}"
        f"difficulty: Intermediate to Expert{newline}tags:{newline}"
        f"- card play – principles{newline}- probability{newline}{extra}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}- play/declarer-play/index{newline}"
        f"last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact bytes{newline}---{newline}# Probability{newline}{newline}"
        f"Body  bytes  stay exact.{newline}"
    )


class PlayProbabilityCategoryRepairTests(unittest.TestCase):
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

    def target(self, *, newline: str = "\n", extra_tag: str = "") -> Path:
        return self.write(
            REVIEWED_PROBABILITY_ARTICLE,
            article_text(newline=newline, extra_tag=extra_tag),
        )

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["repair-play-probability-category", "--root", str(self.root), *arguments],
        )

    def test_exact_deterministic_dry_run_excludes_all_other_files(self) -> None:
        target = self.target(newline="\r\n")
        other_probability = self.write("play/declarer-play/probability/other.md", article_text())
        other_declarer = self.write("play/declarer-play/other.md", article_text())
        defence = self.write("play/defence/other.md", article_text())
        bidding = self.write("bidding/other.md", article_text())
        paths = (target, other_probability, other_declarer, defence, bidding)
        before = {path: path.read_bytes() for path in paths}
        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertIn(REVIEWED_PROBABILITY_ARTICLE, first.output)
        self.assertIn("'Card Play – Principles' -> 'play'", first.output)
        self.assertIn("subcategory='declarer-play'", first.output)
        self.assertIn("broad-tag-present=False", first.output)
        self.assertIn("Files selected      : 1", first.output)
        self.assertIn("Files to update     : 1", first.output)
        self.assertNotIn("probability/other.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_is_category_only_with_exact_backup_and_line_endings(self) -> None:
        target = self.target(newline="\r\n")
        original = target.read_bytes()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        expected = original.replace(
            b"category: Card Play \xe2\x80\x93 Principles\r\n",
            b"category: play\r\n",
            1,
        )
        self.assertEqual(target.read_bytes(), expected)
        self.assertEqual((self.backup / REVIEWED_PROBABILITY_ARTICLE).read_bytes(), original)
        for unchanged in (
            b"subcategory: declarer-play\r\n",
            b"- card play \xe2\x80\x93 principles\r\n",
            b"last_updated: 2026-08-17\r\n",
            b"unknown_field: exact bytes\r\n",
            b"Body  bytes  stay exact.\r\n",
        ):
            self.assertIn(unchanged, expected)
        self.assertNotIn(b"- play\r\n", expected)

    def test_apply_requires_backup_and_all_metadata_preconditions(self) -> None:
        target = self.target()
        original = target.read_bytes()
        result = self.invoke("--apply")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--backup is required", result.output)
        self.assertEqual(target.read_bytes(), original)

        cases = (
            (b"subcategory: declarer-play", b"subcategory: defence", "subcategory"),
            (b"- card play \xe2\x80\x93 principles\n", b"- probability\n", "retained-tag"),
        )
        for old, new, message in cases:
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_play_probability_category_report(self.root)
            self.assertFalse(self.backup.exists())
        target.write_bytes(article_text(extra_tag="play").encode())
        with self.assertRaisesRegex(RuntimeError, "broad-tag precondition"):
            build_play_probability_category_report(self.root)

    def test_stale_snapshot_backup_refusal_and_atomic_failure_are_safe(self) -> None:
        target = self.target()
        original = target.read_bytes()
        report = build_play_probability_category_report(self.root)
        target.write_bytes(original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_probability_category_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())
        target.write_bytes(original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_probability_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)
        self.backup.rmdir()
        with patch(
            "metadata.play_endgame_category_repair._atomic_write",
            side_effect=OSError("replace failed"),
        ):
            with self.assertRaisesRegex(OSError, "replace failed"):
                apply_play_probability_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / REVIEWED_PROBABILITY_ARTICLE).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        target = self.target()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = target.read_bytes()
        report = build_play_probability_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(app, ["repair-play-probability-category", "--help"])
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
