from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.bidding_category_repair import (
    REVIEWED_BIDDING_CATEGORIES,
    apply_bidding_category_report,
    build_bidding_category_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(category: str, *, newline: str = "\n") -> str:
    old_tag = category.casefold()
    return (
        f"---{newline}"
        f"title: Reviewed Fixture{newline}"
        f"description: Exact metadata and body bytes must remain unchanged.{newline}"
        f"category: {category}{newline}"
        f"subcategory: conventions{newline}"
        f"difficulty: Intermediate{newline}"
        f"tags:{newline}  - {old_tag}{newline}  - opening{newline}"
        f"systems:{newline}  - precision{newline}"
        f"aliases:{newline}  - Existing Alias{newline}"
        f"acronyms: []{newline}"
        f"references:{newline}  - bidding/target{newline}"
        f"last_updated: 2026-07-23{newline}"
        f"status: Draft{newline}"
        f"unknown_field: preserve exactly{newline}"
        f"---{newline}"
        f"# Reviewed Fixture{newline}{newline}"
        f"Body  with  deliberate spacing.{newline}"
    )


class BiddingCategoryRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
        return path

    def write_reviewed(self) -> dict[str, Path]:
        result = {}
        for index, (relative, category) in enumerate(
            sorted(REVIEWED_BIDDING_CATEGORIES.items())
        ):
            result[relative] = self.write(
                relative,
                article_text(category, newline="\r\n" if index == 0 else "\n"),
            )
        return result

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            [
                "repair-bidding-categories",
                "--root",
                str(self.root),
                "--backup",
                str(self.backup),
                *arguments,
            ],
        )

    def test_dry_run_selects_only_reviewed_19_and_writes_nothing(self) -> None:
        reviewed = self.write_reviewed()
        play = self.write(
            "play/topic.md",
            article_text("Card Play – Defence"),
        )
        unrelated = self.write(
            "bidding/unrelated.md",
            article_text("Conventions"),
        )
        all_paths = [*reviewed.values(), play, unrelated]
        before = {path: path.read_bytes() for path in all_paths}

        result = self.invoke()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Files selected      : 19", result.output)
        self.assertIn("Files to update     : 19", result.output)
        self.assertIn("Category changes    : 19", result.output)
        self.assertIn("Tag changes         : 0", result.output)
        self.assertIn("Subcategory changes : 0", result.output)
        self.assertIn("tags frozen", result.output)
        self.assertNotIn("play/topic.md", result.output)
        self.assertNotIn("bidding/unrelated.md", result.output)
        self.assertEqual({path: path.read_bytes() for path in all_paths}, before)
        self.assertFalse(self.backup.exists())

    def test_apply_changes_only_category_and_preserves_exact_backups(self) -> None:
        reviewed = self.write_reviewed()
        originals = {relative: path.read_bytes() for relative, path in reviewed.items()}

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in reviewed.items():
            original = originals[relative]
            category = REVIEWED_BIDDING_CATEGORIES[relative]
            expected = original.replace(
                f"category: {category}".encode(), b"category: bidding", 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertIn(f"  - {category.casefold()}".encode(), path.read_bytes())
            self.assertNotIn(b"  - bidding\n", path.read_bytes())
            self.assertIn(b"subcategory: conventions", path.read_bytes())
            self.assertIn(b"last_updated: 2026-07-23", path.read_bytes())
            self.assertIn(b"unknown_field: preserve exactly", path.read_bytes())
            self.assertIn(b"Body  with  deliberate spacing.", path.read_bytes())
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_stale_precondition_aborts_entire_batch_before_backup_or_write(self) -> None:
        reviewed = self.write_reviewed()
        report = build_bidding_category_report(self.root)
        stale_path = reviewed[sorted(reviewed)[0]]
        stale_path.write_bytes(stale_path.read_bytes() + b"external change\n")
        before = {relative: path.read_bytes() for relative, path in reviewed.items()}

        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_bidding_category_report(report, self.root, self.backup)

        self.assertEqual(
            {relative: path.read_bytes() for relative, path in reviewed.items()}, before
        )
        self.assertFalse(self.backup.exists())

    def test_backup_overwrite_is_refused_without_source_changes(self) -> None:
        reviewed = self.write_reviewed()
        report = build_bidding_category_report(self.root)
        before = {relative: path.read_bytes() for relative, path in reviewed.items()}
        self.backup.mkdir()

        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_bidding_category_report(report, self.root, self.backup)

        self.assertEqual(
            {relative: path.read_bytes() for relative, path in reviewed.items()}, before
        )

    def test_apply_uses_atomic_writes_and_is_idempotent(self) -> None:
        reviewed = self.write_reviewed()
        report = build_bidding_category_report(self.root)
        with patch(
            "metadata.bidding_category_repair._atomic_write",
            wraps=_atomic_write,
        ) as atomic:
            apply_bidding_category_report(report, self.root, self.backup)

        second_report = build_bidding_category_report(self.root)
        second = self.invoke("--apply")

        self.assertEqual(atomic.call_count, 19)
        self.assertEqual(second_report.actions, ())
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertIn("Files to back up    : 0", second.output)
        self.assertTrue(all(b"category: bidding" in p.read_bytes() for p in reviewed.values()))

    def test_help_registration_and_explicit_root(self) -> None:
        self.write_reviewed()

        help_result = self.runner.invoke(app, ["repair-bidding-categories", "--help"])
        dry_run = self.invoke()

        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--root", help_result.output)
        self.assertIn("--backup", help_result.output)
        self.assertIn("--apply", help_result.output)
        self.assertEqual(dry_run.exit_code, 0, dry_run.output)


if __name__ == "__main__":
    unittest.main()
