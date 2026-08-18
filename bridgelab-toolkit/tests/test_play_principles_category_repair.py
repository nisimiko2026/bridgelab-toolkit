from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.play_endgame_category_repair import (
    REVIEWED_PRINCIPLES_CATEGORIES,
    apply_play_principles_category_report,
    build_play_principles_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(category: str, *, newline: str = "\n") -> str:
    tag = category.casefold()
    return (
        f"---{newline}title: Principles Fixture{newline}"
        f"description: Reviewed two-file byte-preservation fixture.{newline}"
        f"category: {category}{newline}subcategory: principles{newline}"
        f"difficulty: Intermediate{newline}tags:{newline}  - {tag}{newline}"
        f"  - entries{newline}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - play/principles/index{newline}"
        f"last_updated: 2026-08-17{newline}status: Draft{newline}"
        f"unknown_field: exact bytes{newline}---{newline}# Principles{newline}{newline}"
        f"Body  with  deliberate spacing.{newline}"
    )


class PlayPrinciplesCategoryRepairTests(unittest.TestCase):
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
        result = {}
        for index, (relative, category) in enumerate(
            REVIEWED_PRINCIPLES_CATEGORIES.items()
        ):
            result[relative] = self.write(
                relative, article_text(category, newline="\r\n" if index else "\n")
            )
        return result

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["repair-play-principles-categories", "--root", str(self.root), *arguments],
        )

    def test_exact_two_file_dry_run_is_deterministic_and_read_only(self) -> None:
        targets = self.targets()
        other = self.write("play/principles/other.md", article_text("Card Play – Principles"))
        bidding = self.write("bidding/other.md", article_text("Bidding – Principles"))
        paths = [*targets.values(), other, bidding]
        before = {path: path.read_bytes() for path in paths}

        first = self.invoke()
        second = self.invoke()

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 2)
        self.assertIn("'Card Play – Fundamentals' -> 'play'", first.output)
        self.assertIn("'techniques/card-play' -> 'play'", first.output)
        self.assertIn("Files selected      : 2", first.output)
        self.assertIn("Files to update     : 2", first.output)
        self.assertIn("Tag changes         : 0", first.output)
        self.assertIn("Subcategory changes : 0", first.output)
        self.assertNotIn("play/principles/other.md", first.output)
        self.assertNotIn("bidding/other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_changes_only_categories_and_backs_up_exact_bytes(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}

        result = self.invoke("--apply", "--backup", str(self.backup))

        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in targets.items():
            category = REVIEWED_PRINCIPLES_CATEGORIES[relative]
            original = originals[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                f"category: {category}".encode() + ending,
                b"category: play" + ending,
                1,
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(f"  - {category.casefold()}".encode() + ending, expected)
            self.assertNotIn(b"  - play" + ending, expected)
            self.assertIn(b"subcategory: principles" + ending, expected)
            self.assertIn(b"last_updated: 2026-08-17" + ending, expected)
            self.assertIn(b"unknown_field: exact bytes" + ending, expected)
            self.assertIn(b"Body  with  deliberate spacing." + ending, expected)

    def test_apply_requires_explicit_backup(self) -> None:
        targets = self.targets()
        before = {path: path.read_bytes() for path in targets.values()}
        result = self.invoke("--apply")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--backup is required", result.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)

    def test_each_stale_file_aborts_batch_before_backup_or_write(self) -> None:
        for stale_index in (0, 1):
            with self.subTest(stale_index=stale_index):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "knowledge"
                    root.mkdir()
                    paths = []
                    for relative, category in REVIEWED_PRINCIPLES_CATEGORIES.items():
                        path = root / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(article_text(category).encode())
                        paths.append(path)
                    report = build_play_principles_category_report(root)
                    paths[stale_index].write_bytes(
                        paths[stale_index].read_bytes() + b"external change\n"
                    )
                    before = [path.read_bytes() for path in paths]
                    backup = Path(directory) / "backup"
                    with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
                        apply_play_principles_category_report(report, root, backup)
                    self.assertEqual([path.read_bytes() for path in paths], before)
                    self.assertFalse(backup.exists())

    def test_metadata_preconditions_and_existing_backup_abort_cleanly(self) -> None:
        targets = self.targets()
        second = targets["play/principles/preservation-of-entries.md"]
        second.write_bytes(
            second.read_bytes().replace(
                b"subcategory: principles", b"subcategory: declarer-play", 1
            )
        )
        with self.assertRaisesRegex(RuntimeError, "subcategory precondition"):
            build_play_principles_category_report(self.root)
        self.assertFalse(self.backup.exists())

        second.write_bytes(article_text("techniques/card-play", newline="\r\n").encode())
        report = build_play_principles_category_report(self.root)
        before = {path: path.read_bytes() for path in targets.values()}
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_play_principles_category_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)

    def test_second_replace_failure_is_recoverable_and_not_reported_success(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second replace failed")
            _atomic_write(path, content)

        with patch(
            "metadata.play_endgame_category_repair._atomic_write",
            side_effect=fail_second,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))

        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = list(REVIEWED_PRINCIPLES_CATEGORIES)
        self.assertIn(b"category: play", targets[ordered[0]].read_bytes())
        self.assertEqual(targets[ordered[1]].read_bytes(), originals[ordered[1]])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_help(self) -> None:
        targets = self.targets()
        first = self.invoke("--apply", "--backup", str(self.backup))
        after = {path: path.read_bytes() for path in targets.values()}
        report = build_play_principles_category_report(self.root)
        second = self.invoke("--apply")
        help_result = self.runner.invoke(
            app, ["repair-play-principles-categories", "--help"]
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
