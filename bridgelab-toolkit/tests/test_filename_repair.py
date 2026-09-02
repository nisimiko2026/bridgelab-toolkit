from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from commands.repair_filenames import RENAMES
from main import app


class FilenameRepairTests(unittest.TestCase):
    def test_apply_renames_updates_references_and_backs_up(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            backup = base / "backup"

            for old in RENAMES:
                source = root / Path(old)
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"# {source.stem}\n", encoding="utf-8")

            reference = root / "index.md"
            old_reference = next(iter(RENAMES)).removesuffix(".md")
            new_reference = next(iter(RENAMES.values())).removesuffix(".md")
            reference.write_text(f"- {old_reference}\n", encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "repair-filenames",
                    "--root",
                    str(root),
                    "--backup",
                    str(backup),
                    "--apply",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Files renamed     : 6", result.output)
            self.assertIn(new_reference, reference.read_text(encoding="utf-8"))
            for old, new in RENAMES.items():
                self.assertTrue((root / Path(new)).exists())
                self.assertTrue((backup / Path(old)).exists())
                actual_names = {
                    child.name
                    for child in (root / Path(new).parent).iterdir()
                }
                self.assertIn(Path(new).name, actual_names)
                if Path(old).name != Path(new).name:
                    self.assertNotIn(Path(old).name, actual_names)
