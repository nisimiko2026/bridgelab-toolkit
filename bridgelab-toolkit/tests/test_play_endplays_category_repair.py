from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_ENDPLAYS_CATEGORIES,
    apply_play_endplays_category_report,
    build_play_endplays_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(category: str, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Endplays{newline}description: Exact fixture bytes.{newline}"
        f"category: {category}{newline}subcategory: declarer-play{newline}"
        f"difficulty: Advanced{newline}tags:{newline}- {category.casefold()}{newline}"
        f"- endplay{newline}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact{newline}---{newline}# Endplays{newline}{newline}"
        f"Body  stays exact.{newline}"
    )


class PlayEndplaysRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
        return path

    def targets(self) -> dict[str, Path]:
        return {
            relative: self.write(
                relative, article_text(category, "\r\n" if index == 1 else "\n")
            )
            for index, (relative, category) in enumerate(REVIEWED_ENDPLAYS_CATEGORIES.items())
        }

    def invoke(self, *args: str):
        return self.runner.invoke(
            app, ["repair-play-endplays-categories", "--root", str(self.root), *args]
        )

    def test_exact_deterministic_dry_run_selects_only_three(self) -> None:
        targets = self.targets()
        other = self.write("play/declarer-play/elimination-and-endplays/other.md", article_text("techniques/endplays"))
        bidding = self.write("bidding/other.md", article_text("Bidding – Principles"))
        paths = [*targets.values(), other, bidding]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 3)
        self.assertIn("Files selected      : 3", first.output)
        self.assertIn("Files to update     : 3", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("endplays/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_apply_is_category_only_with_exact_backups(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in targets.items():
            original = originals[relative]
            category = REVIEWED_ENDPLAYS_CATEGORIES[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                f"category: {category}".encode() + ending, b"category: play" + ending, 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"subcategory: declarer-play" + ending, expected)
            self.assertIn(f"- {category.casefold()}".encode() + ending, expected)
            self.assertNotIn(b"- play" + ending, expected)
            self.assertIn(b"last_updated: 2026-08-17" + ending, expected)
            self.assertIn(b"Body  stays exact." + ending, expected)

    def test_explicit_backup_and_stale_batch_preflight(self) -> None:
        targets = self.targets()
        before = {path: path.read_bytes() for path in targets.values()}
        missing = self.invoke("--apply")
        self.assertNotEqual(missing.exit_code, 0)
        report = build_play_endplays_category_report(self.root)
        stale = list(targets.values())[1]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        stale_before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_endplays_category_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, stale_before)
        self.assertFalse(self.backup.exists())
        self.assertNotEqual(before, stale_before)

    def test_backup_refusal_and_mid_batch_failure_are_recoverable(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_play_endplays_category_report(self.root)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_endplays_category_report(report, self.root, self.backup)
        self.backup.rmdir()
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second failed")
            _atomic_write(path, content)

        with patch("metadata.play_endgame_category_repair._atomic_write", side_effect=fail_second):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = list(REVIEWED_ENDPLAYS_CATEGORIES)
        self.assertIn(b"category: play", targets[ordered[0]].read_bytes())
        self.assertEqual(targets[ordered[1]].read_bytes(), originals[ordered[1]])
        self.assertEqual(targets[ordered[2]].read_bytes(), originals[ordered[2]])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_root_and_help(self) -> None:
        targets = self.targets()
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_play_endplays_category_report(self.root).actions, ())
        second = self.invoke("--apply")
        help_result = self.runner.invoke(app, ["repair-play-endplays-categories", "--help"])
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files selected      : 3", second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertIn("Files to back up    : 0", second.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--root", help_result.output)
        self.assertIn("--backup", help_result.output)
        self.assertIn("--apply", help_result.output)


if __name__ == "__main__":
    unittest.main()
