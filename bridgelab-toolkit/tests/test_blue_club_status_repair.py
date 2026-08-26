from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.blue_club_status_repair import (
    ARTICLE,
    apply_blue_club_status_report,
    build_blue_club_status_report,
)


def article_text(*, newline="\n", status="Advanced", difficulty="Advanced", title="Blue Club"):
    return (
        f"---{newline}title: {title}{newline}description: Exact Blue Club fixture.{newline}"
        f"category: bidding{newline}subcategory: systems{newline}"
        f"difficulty: {difficulty}{newline}tags:{newline}- blue club{newline}- systems{newline}"
        f"systems:{newline}  - blue club{newline}aliases:{newline}- Italian Blue Club{newline}"
        f"acronyms: []{newline}references:{newline}- bidding/systems/systems-index{newline}"
        f"last_updated: '2026-07-27'{newline}status: {status}{newline}"
        f"---{newline}{newline}# Blue Club{newline}{newline}Body unchanged.{newline}"
    )


class BlueClubStatusRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self):
        self.temp.cleanup()

    def target(self, **kwargs):
        path = self.root / ARTICLE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(**kwargs).encode())
        return path

    def invoke(self, *args):
        return self.runner.invoke(
            app, ["repair-blue-club-status", "--root", str(self.root), *args]
        )

    def test_exact_selection_census_exclusion_deterministic_dry_run_and_root_guards(self):
        target = self.target()
        other = self.root / "bidding/systems/other.md"
        other.write_bytes(article_text(status="Draft", title="Other").encode())
        before = {path: path.read_bytes() for path in (target, other)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET STATUS |"), 1)
        self.assertIn("Files selected     : 1", first.output)
        self.assertIn("Files to update    : 1", first.output)
        self.assertIn("Status changes     : 1", first.output)
        self.assertIn("Difficulty changes : 0", first.output)
        self.assertIn("Files to back up   : 1", first.output)
        self.assertFalse(self.backup.exists())
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        extra = self.root / "bidding/systems/extra.md"
        extra.write_bytes(article_text().encode())
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_blue_club_status_report(self.root)
        extra.unlink()
        target.unlink()
        with self.assertRaisesRegex(RuntimeError, "file is missing"):
            build_blue_club_status_report(self.root)
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_blue_club_status_report(wrong)
        stale = self.base / "OneDrive" / "knowledge"
        stale.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "outside OneDrive"):
            build_blue_club_status_report(stale)

    def test_exact_status_only_lf_crlf_and_frozen_difficulty_metadata_body(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline=newline)
                original = target.read_bytes()
                action = build_blue_club_status_report(self.root).actions[0]
                expected = original.replace(
                    f"status: Advanced{newline}".encode(),
                    f"status: Draft{newline}".encode(),
                    1,
                )
                self.assertEqual(action.updated, expected)
                self.assertIn(f"difficulty: Advanced{newline}".encode(), action.updated)
                self.assertIn(f"# Blue Club{newline}{newline}Body unchanged.".encode(), action.updated)

    def test_stale_status_difficulty_and_status_line_rejections(self):
        target = self.target()
        original = target.read_bytes()
        cases = (
            (b"status: Advanced", b"status: Standard", "status precondition"),
            (b"status: Advanced", b"status:  Advanced", "status line precondition"),
            (b"difficulty: Advanced", b"difficulty: Expert", "difficulty precondition"),
            (b"title: Blue Club", b"title: Changed", "title precondition"),
        )
        for old, new, message in cases:
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_blue_club_status_report(self.root)
            target.write_bytes(original)

    def test_apply_guards_backup_stale_bytes_atomic_failure_and_idempotence(self):
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_blue_club_status_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_blue_club_status_report(report, self.root, self.backup)
        self.assertFalse(self.backup.exists())
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_blue_club_status_report(report, self.root, self.backup)
        self.backup.rmdir()

        original = target.read_bytes()
        with patch(
            "metadata.blue_club_status_repair._atomic_write",
            side_effect=OSError("atomic failure"),
        ):
            failed = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(failed.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / ARTICLE).read_bytes(), original)

        fresh = self.base / "fresh" / "knowledge"
        fresh.mkdir(parents=True)
        self.root = fresh
        target = self.target()
        backup = self.base / "fresh-backup"
        result = self.invoke("--apply", "--backup", str(backup))
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual((backup / ARTICLE).read_bytes(), article_text().encode())
        after = target.read_bytes()
        self.assertEqual(build_blue_club_status_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)

    def test_explicit_root_and_cli_help(self):
        self.target()
        self.assertEqual(self.invoke().exit_code, 0)
        help_result = self.runner.invoke(app, ["repair-blue-club-status", "--help"])
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()
