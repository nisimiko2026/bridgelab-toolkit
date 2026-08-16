from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from commands.resolve_duplicates import CONSOLIDATIONS, RENAMES
from main import app


class DuplicateResolutionTests(unittest.TestCase):
    def test_reviewed_resolution_is_backed_up_and_updates_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            backup = base / "backup"
            for path in {*RENAMES, *CONSOLIDATIONS, *CONSOLIDATIONS.values()}:
                source = root / Path(path)
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"# {source.stem}\n", encoding="utf-8")

            reference = root / "index.md"
            old = next(iter(RENAMES)).removesuffix(".md")
            new = next(iter(RENAMES.values())).removesuffix(".md")
            reference.write_text(f"- {old}\n", encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "resolve-duplicates", "--root", str(root),
                    "--backup", str(backup), "--apply",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Duplicates removed  : 1", result.output)
            self.assertIn(new, reference.read_text(encoding="utf-8"))
            for old_path, new_path in RENAMES.items():
                self.assertFalse((root / Path(old_path)).exists())
                self.assertTrue((root / Path(new_path)).exists())
                self.assertTrue((backup / Path(old_path)).exists())
            for removed in CONSOLIDATIONS:
                self.assertFalse((root / Path(removed)).exists())
                self.assertTrue((backup / Path(removed)).exists())
