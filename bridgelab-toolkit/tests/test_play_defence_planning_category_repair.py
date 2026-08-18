from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    apply_play_defence_planning_category_report,
    build_play_defence_planning_category_report,
)


def article_text(newline: str = "\n") -> str:
    return (
        f"---{newline}title: Defence Planning{newline}description: Exact fixture bytes.{newline}"
        f"category: Card Play – Defence{newline}subcategory: defence{newline}"
        f"difficulty: Intermediate{newline}tags:{newline}- card play – defence{newline}"
        f"- planning{newline}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact{newline}---{newline}# Defence Planning{newline}{newline}"
        f"Body exact.{newline}"
    )


class PlayDefencePlanningRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.target = self.write(
            "play/defence/planning/defence-planning-index.md", article_text("\r\n")
        )
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
        return path

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-play-defence-planning-category", "--root", str(self.root), *args],
        )

    def test_dry_run_exact_scope_and_apply_byte_preservation(self) -> None:
        other = self.write("play/defence/planning/other.md", article_text())
        before = {self.target: self.target.read_bytes(), other: other.read_bytes()}
        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 1)
        self.assertIn("Files selected      : 1", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertNotIn("planning/other.md", dry.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        expected = before[self.target].replace(
            "category: Card Play – Defence\r\n".encode(), b"category: play\r\n", 1
        )
        self.assertEqual(self.target.read_bytes(), expected)
        self.assertEqual(
            (self.backup / "play/defence/planning/defence-planning-index.md").read_bytes(),
            before[self.target],
        )
        self.assertIn("- card play – defence\r\n".encode(), expected)
        self.assertIn(b"subcategory: defence\r\n", expected)
        self.assertNotIn(b"- play\r\n", expected)

    def test_apply_requires_backup_and_stale_report_refuses_write(self) -> None:
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_play_defence_planning_category_report(self.root)
        self.target.write_bytes(self.target.read_bytes() + b"stale\r\n")
        before = self.target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_defence_planning_category_report(report, self.root, self.backup)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertFalse(self.backup.exists())

    def test_preconditions_reject_related_metadata_drift(self) -> None:
        cases = (
            (b"subcategory: defence", b"subcategory: declarer-play", "subcategory"),
            ("- card play – defence".encode(), b"- unrelated", "retained-tag"),
            (b"- planning", b"- planning\r\n- play", "broad-tag"),
        )
        original = self.target.read_bytes()
        for old, new, message in cases:
            self.target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_play_defence_planning_category_report(self.root)
        self.target.write_bytes(original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        after = self.target.read_bytes()
        self.assertEqual(build_play_defence_planning_category_report(self.root).actions, ())
        second = self.invoke("--apply")
        help_result = self.runner.invoke(
            app, ["repair-play-defence-planning-category", "--help"]
        )
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files selected      : 1", second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertEqual(self.target.read_bytes(), after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
