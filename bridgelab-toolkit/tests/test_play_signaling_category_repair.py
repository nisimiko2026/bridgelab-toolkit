from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_SIGNALING_ARTICLE,
    apply_play_signaling_category_report,
    build_play_signaling_category_report,
)


def article_text(*, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Defensive Signalling{newline}"
        f"description: Reviewed signaling byte-preservation fixture.{newline}"
        f"category: Card Play – Defence{newline}subcategory: defence{newline}"
        f"difficulty: Beginner to Expert{newline}tags:{newline}"
        f"- card play – defence{newline}- signal{newline}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references:{newline}"
        f"- play/defence/index-defence{newline}last_updated: 2026-08-17{newline}"
        f"status: Draft{newline}unknown_field: exact bytes{newline}---{newline}"
        f"# Defensive Signalling{newline}{newline}Body  bytes  stay exact.{newline}"
    )


class PlaySignalingCategoryRepairTests(unittest.TestCase):
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
        return self.write(REVIEWED_SIGNALING_ARTICLE, article_text(newline=newline))

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["repair-play-signaling-category", "--root", str(self.root), *arguments],
        )

    def test_exact_deterministic_dry_run_selects_nothing_else(self) -> None:
        target = self.target(newline="\r\n")
        other_signal = self.write("play/defence/signaling/other.md", article_text())
        other_play = self.write("play/defence/other.md", article_text())
        bidding = self.write("bidding/other.md", article_text())
        paths = (target, other_signal, other_play, bidding)
        before = {path: path.read_bytes() for path in paths}
        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertIn(REVIEWED_SIGNALING_ARTICLE, first.output)
        self.assertIn("'Card Play – Defence' -> 'play'", first.output)
        self.assertIn("broad-tag-present=False", first.output)
        self.assertIn("Files selected      : 1", first.output)
        self.assertIn("Files to update     : 1", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("signaling/other.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_changes_one_line_and_backup_is_exact(self) -> None:
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
        self.assertEqual((self.backup / REVIEWED_SIGNALING_ARTICLE).read_bytes(), original)
        for unchanged in (
            b"subcategory: defence\r\n",
            b"- card play \xe2\x80\x93 defence\r\n",
            b"last_updated: 2026-08-17\r\n",
            b"unknown_field: exact bytes\r\n",
            b"Body  bytes  stay exact.\r\n",
        ):
            self.assertIn(unchanged, expected)
        self.assertNotIn(b"- play\r\n", expected)

    def test_backup_required_and_metadata_preconditions_abort_before_write(self) -> None:
        target = self.target()
        original = target.read_bytes()
        result = self.invoke("--apply")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--backup is required", result.output)
        self.assertEqual(target.read_bytes(), original)

        target.write_bytes(original.replace(b"- card play \xe2\x80\x93 defence\n", b"- defence\n"))
        with self.assertRaisesRegex(RuntimeError, "retained-tag precondition"):
            build_play_signaling_category_report(self.root)
        self.assertFalse(self.backup.exists())

    def test_stale_snapshot_backup_refusal_and_atomic_failure_are_safe(self) -> None:
        target = self.target()
        original = target.read_bytes()
        report = build_play_signaling_category_report(self.root)
        target.write_bytes(original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_signaling_category_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())
        target.write_bytes(original)

        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_signaling_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)
        self.backup.rmdir()
        with patch(
            "metadata.play_endgame_category_repair._atomic_write",
            side_effect=OSError("replace failed"),
        ):
            with self.assertRaisesRegex(OSError, "replace failed"):
                apply_play_signaling_category_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / REVIEWED_SIGNALING_ARTICLE).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        target = self.target()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = target.read_bytes()
        report = build_play_signaling_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(app, ["repair-play-signaling-category", "--help"])
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
