from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES,
    apply_play_defence_techniques_category_report,
    build_play_defence_techniques_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(category: str, *, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Defence Techniques{newline}"
        f"description: Reviewed two-file byte-preservation fixture.{newline}"
        f"category: {category}{newline}subcategory: defence{newline}"
        f"difficulty: Advanced{newline}tags:{newline}- {category.casefold()}{newline}"
        f"- defence{newline}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}- play/defence/index-defence{newline}"
        f"last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact bytes{newline}---{newline}# Defence Techniques{newline}{newline}"
        f"Body  bytes  stay exact.{newline}"
    )


class PlayDefenceTechniquesRepairTests(unittest.TestCase):
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

    def targets(self) -> dict[str, Path]:
        return {
            relative: self.write(
                relative, article_text(category, newline="\r\n" if index else "\n")
            )
            for index, (relative, category) in enumerate(
                REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES.items()
            )
        }

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            [
                "repair-play-defence-techniques-categories",
                "--root",
                str(self.root),
                *arguments,
            ],
        )

    def test_exact_two_file_dry_run_is_deterministic_and_read_only(self) -> None:
        targets = self.targets()
        other = self.write("play/defence/techniques/other.md", article_text("Card Play – Defence"))
        other_play = self.write("play/defence/other.md", article_text("Card Play – Defence"))
        bidding = self.write("bidding/other.md", article_text("Bidding – Principles"))
        paths = [*targets.values(), other, other_play, bidding]
        before = {path: path.read_bytes() for path in paths}
        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 2)
        self.assertIn("'Card Play – Defence' -> 'play'", first.output)
        self.assertIn("'techniques/defensive-techniques' -> 'play'", first.output)
        self.assertIn("broad-tag-present=False", first.output)
        self.assertIn("Files selected      : 2", first.output)
        self.assertIn("Files to update     : 2", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("techniques/other.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_changes_only_category_and_backups_are_exact(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in targets.items():
            original = originals[relative]
            category = REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                f"category: {category}".encode() + ending,
                b"category: play" + ending,
                1,
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"subcategory: defence" + ending, expected)
            self.assertIn(f"- {category.casefold()}".encode() + ending, expected)
            self.assertNotIn(b"- play" + ending, expected)
            self.assertIn(b"last_updated: 2026-08-17" + ending, expected)
            self.assertIn(b"unknown_field: exact bytes" + ending, expected)
            self.assertIn(b"Body  bytes  stay exact." + ending, expected)

    def test_apply_requires_backup_and_preconditions_are_strict(self) -> None:
        targets = self.targets()
        before = {path: path.read_bytes() for path in targets.values()}
        result = self.invoke("--apply")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--backup is required", result.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)

        second = targets["play/defence/techniques/trump-promotion.md"]
        original = second.read_bytes()
        for old, new, message in (
            (b"subcategory: defence", b"subcategory: declarer-play", "subcategory"),
            (b"- techniques/defensive-techniques", b"- defence", "retained-tag"),
        ):
            second.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_play_defence_techniques_category_report(self.root)
            self.assertFalse(self.backup.exists())
        second.write_bytes(original.replace(b"- defence\r\n", b"- defence\r\n- play\r\n", 1))
        with self.assertRaisesRegex(RuntimeError, "broad-tag precondition"):
            build_play_defence_techniques_category_report(self.root)

    def test_each_stale_snapshot_aborts_batch_before_backup(self) -> None:
        for stale_index in range(2):
            with self.subTest(stale_index=stale_index), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "knowledge"
                root.mkdir()
                paths = []
                for relative, category in REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(article_text(category).encode())
                    paths.append(path)
                report = build_play_defence_techniques_category_report(root)
                paths[stale_index].write_bytes(paths[stale_index].read_bytes() + b"stale\n")
                before = [path.read_bytes() for path in paths]
                backup = Path(tmp) / "backup"
                with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
                    apply_play_defence_techniques_category_report(report, root, backup)
                self.assertEqual([path.read_bytes() for path in paths], before)
                self.assertFalse(backup.exists())

    def test_backup_refusal_and_partial_failure_are_recoverable(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_play_defence_techniques_category_report(self.root)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_defence_techniques_category_report(report, self.root, self.backup)
        self.assertEqual({p: path.read_bytes() for p, path in targets.items()}, originals)
        self.backup.rmdir()
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second replace failed")
            _atomic_write(path, content)

        with patch("metadata.play_endgame_category_repair._atomic_write", side_effect=fail_second):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = list(REVIEWED_DEFENCE_TECHNIQUES_CATEGORIES)
        self.assertIn(b"category: play", targets[ordered[0]].read_bytes())
        self.assertEqual(targets[ordered[1]].read_bytes(), originals[ordered[1]])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        targets = self.targets()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = {path: path.read_bytes() for path in targets.values()}
        report = build_play_defence_techniques_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(
            app, ["repair-play-defence-techniques-categories", "--help"]
        )
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(report.actions, ())
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files selected      : 2", second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertIn("Files to back up    : 0", second.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--root", help_result.output)
        self.assertIn("--backup", help_result.output)
        self.assertIn("--apply", help_result.output)


if __name__ == "__main__":
    unittest.main()
