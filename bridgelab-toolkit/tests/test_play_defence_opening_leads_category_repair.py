from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES,
    apply_play_defence_opening_leads_category_report,
    build_play_defence_opening_leads_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(category: str, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Opening Lead{newline}description: Exact fixture bytes.{newline}"
        f"category: {category}{newline}subcategory: defence{newline}"
        f"difficulty: Intermediate{newline}tags:{newline}- {category.casefold()}{newline}"
        f"- opening-lead{newline}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact{newline}---{newline}# Opening Lead{newline}{newline}"
        f"Body exact.{newline}"
    )


class PlayDefenceOpeningLeadsRepairTests(unittest.TestCase):
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
            relative: self.write(relative, article_text(category, "\r\n" if index == 1 else "\n"))
            for index, (relative, category) in enumerate(
                REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES.items()
            )
        }

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-play-defence-opening-leads-categories", "--root", str(self.root), *args],
        )

    def test_dry_run_exact_scope_and_apply_byte_preservation(self) -> None:
        targets = self.targets()
        other = self.write(
            "play/defence/opening-leads/other.md", article_text("defence/opening-leads")
        )
        before = {path: path.read_bytes() for path in [*targets.values(), other]}
        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 10)
        self.assertIn("Files selected      : 10", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertNotIn("opening-leads/other.md", dry.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        for relative, path in targets.items():
            original = before[path]
            category = REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                f"category: {category}".encode() + ending, b"category: play" + ending, 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"subcategory: defence" + ending, expected)
            self.assertIn(f"- {category.casefold()}".encode() + ending, expected)
            self.assertNotIn(b"- play" + ending, expected)

    def test_backup_required_and_stale_preflight(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_play_defence_opening_leads_category_report(self.root)
        stale = list(targets.values())[5]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_play_defence_opening_leads_category_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

    def test_mid_batch_failure_has_all_backups_and_no_false_success(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0

        def fail_fifth(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 5:
                raise OSError("fifth failed")
            _atomic_write(path, content)

        with patch("metadata.play_endgame_category_repair._atomic_write", side_effect=fail_fifth):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = list(REVIEWED_DEFENCE_OPENING_LEADS_CATEGORIES)
        for relative in ordered[:4]:
            self.assertIn(b"category: play", targets[relative].read_bytes())
        for relative in ordered[4:]:
            self.assertEqual(targets[relative].read_bytes(), originals[relative])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        targets = self.targets()
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_play_defence_opening_leads_category_report(self.root).actions, ())
        second = self.invoke("--apply")
        help_result = self.runner.invoke(
            app, ["repair-play-defence-opening-leads-categories", "--help"]
        )
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files selected      : 10", second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
