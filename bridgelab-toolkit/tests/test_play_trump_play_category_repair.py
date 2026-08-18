from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_TRUMP_PLAY_CATEGORIES,
    apply_play_trump_play_category_report,
    build_play_trump_play_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(*, newline: str = "\n") -> str:
    return (
        f"---{newline}title: Trump Play Fixture{newline}"
        f"description: Reviewed four-file byte-preservation fixture.{newline}"
        f"category: techniques/declarer-techniques{newline}"
        f"subcategory: declarer-play{newline}difficulty: Advanced{newline}"
        f"tags:{newline}  - techniques/declarer-techniques{newline}  - trump-play{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}  - play/declarer-play/index{newline}"
        f"last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact bytes{newline}---{newline}# Trump Play{newline}{newline}"
        f"Body  with  deliberate spacing.{newline}"
    )


class PlayTrumpPlayCategoryRepairTests(unittest.TestCase):
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
                relative, article_text(newline="\r\n" if index % 2 else "\n")
            )
            for index, relative in enumerate(REVIEWED_TRUMP_PLAY_CATEGORIES)
        }

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["repair-play-trump-play-categories", "--root", str(self.root), *arguments],
        )

    def test_exact_four_file_dry_run_is_deterministic_and_read_only(self) -> None:
        targets = self.targets()
        fifth = self.write("play/declarer-play/trump-play/fifth.md", article_text())
        other = self.write("play/declarer-play/other.md", article_text())
        bidding = self.write("bidding/other.md", article_text())
        paths = [*targets.values(), fifth, other, bidding]
        before = {path: path.read_bytes() for path in paths}

        first = self.invoke()
        second = self.invoke()

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 4)
        self.assertIn("'techniques/declarer-techniques' -> 'play'", first.output)
        self.assertIn("broad-tag-present=False", first.output)
        self.assertIn("Files selected      : 4", first.output)
        self.assertIn("Files to update     : 4", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("trump-play/fifth.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_changes_only_category_and_backs_up_all_exactly(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in targets.items():
            original = originals[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: techniques/declarer-techniques" + ending,
                b"category: play" + ending,
                1,
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            for unchanged in (
                b"subcategory: declarer-play" + ending,
                b"  - techniques/declarer-techniques" + ending,
                b"last_updated: 2026-08-17" + ending,
                b"unknown_field: exact bytes" + ending,
                b"Body  with  deliberate spacing." + ending,
            ):
                self.assertIn(unchanged, expected)
            self.assertNotIn(b"  - play" + ending, expected)

    def test_apply_requires_backup_and_existing_backup_refuses(self) -> None:
        targets = self.targets()
        before = {path: path.read_bytes() for path in targets.values()}
        result = self.invoke("--apply")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--backup is required", result.output)
        report = build_play_trump_play_category_report(self.root)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_trump_play_category_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)

    def test_each_stale_snapshot_aborts_whole_batch_without_backup(self) -> None:
        for stale_index in range(4):
            with self.subTest(stale_index=stale_index), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "knowledge"
                root.mkdir()
                paths = []
                for relative in REVIEWED_TRUMP_PLAY_CATEGORIES:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(article_text().encode())
                    paths.append(path)
                report = build_play_trump_play_category_report(root)
                paths[stale_index].write_bytes(paths[stale_index].read_bytes() + b"stale\n")
                before = [path.read_bytes() for path in paths]
                backup = Path(tmp) / "backup"
                with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
                    apply_play_trump_play_category_report(report, root, backup)
                self.assertEqual([path.read_bytes() for path in paths], before)
                self.assertFalse(backup.exists())

    def test_mid_batch_replace_failure_is_recoverable_not_success(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0

        def fail_third(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("third replace failed")
            _atomic_write(path, content)

        with patch(
            "metadata.play_endgame_category_repair._atomic_write",
            side_effect=fail_third,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = list(REVIEWED_TRUMP_PLAY_CATEGORIES)
        for relative in ordered[:2]:
            self.assertIn(b"category: play", targets[relative].read_bytes())
        for relative in ordered[2:]:
            self.assertEqual(targets[relative].read_bytes(), originals[relative])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        targets = self.targets()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = {path: path.read_bytes() for path in targets.values()}
        report = build_play_trump_play_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(app, ["repair-play-trump-play-categories", "--help"])
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(report.actions, ())
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files selected      : 4", second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertIn("Files to back up    : 0", second.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--root", help_result.output)
        self.assertIn("--backup", help_result.output)
        self.assertIn("--apply", help_result.output)


if __name__ == "__main__":
    unittest.main()
