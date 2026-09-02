from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from commands.backup_cleanup import expired_backups, run


class BackupCleanupTests(unittest.TestCase):
    def test_only_expired_dated_directories_are_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expired = root / "repair-20260101-01"
            current = root / "repair-20260120-01"
            undated = root / "repair-current"
            for path in (expired, current, undated):
                path.mkdir()
            selected = expired_backups(root, 30, today=date(2026, 2, 16))
            self.assertEqual(selected, [expired.resolve()])

    def test_dry_run_preserves_and_apply_removes_expired_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expired = root / "repair-20260101-01"
            expired.mkdir()
            (expired / "article.md").write_text("backup", encoding="utf-8")
            run(root, 30, apply=False, today=date(2026, 2, 16))
            self.assertTrue(expired.exists())
            run(root, 30, apply=True, today=date(2026, 2, 16))
            self.assertFalse(expired.exists())


if __name__ == "__main__":
    unittest.main()
