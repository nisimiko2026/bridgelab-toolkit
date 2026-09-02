from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


class SpellingRepairTests(unittest.TestCase):
    def test_dry_run_and_apply_directory_and_file_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            reports = base / "reports"
            backup = base / "backup"
            source = root / "topic" / "probabilty" / "article.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Article\n", encoding="utf-8")
            reference = root / "index.md"
            reference.write_text("- topic/probabilty/article\n", encoding="utf-8")
            reports.mkdir()
            plan = reports / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "direct_repairs": [
                            {
                                "old": "topic/probabilty",
                                "new": "topic/probability",
                                "kind": "directory",
                                "confidence": "high",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            original = {source: source.read_bytes(), reference: reference.read_bytes()}

            arguments = [
                "repair-spelling",
                "--root",
                str(root),
                "--plan",
                str(plan),
                "--backup",
                str(backup),
            ]
            dry_run = CliRunner().invoke(app, arguments)
            self.assertEqual(dry_run.exit_code, 0, dry_run.output)
            self.assertIn("Repair groups selected: 1", dry_run.output)
            self.assertEqual(source.read_bytes(), original[source])

            result = CliRunner().invoke(app, [*arguments, "--apply"])
            self.assertEqual(result.exit_code, 0, result.output)
            destination = root / "topic" / "probability" / "article.md"
            self.assertTrue(destination.exists())
            self.assertFalse(source.exists())
            self.assertIn("topic/probability/article", reference.read_text(encoding="utf-8"))
            self.assertEqual((backup / source.relative_to(root)).read_bytes(), original[source])
            self.assertEqual((backup / "index.md").read_bytes(), original[reference])

            repeated = CliRunner().invoke(app, arguments)
            self.assertEqual(repeated.exit_code, 0, repeated.output)
            self.assertIn("Source files to move : 0", repeated.output)

            repeated_apply = CliRunner().invoke(app, [*arguments, "--apply"])
            self.assertEqual(repeated_apply.exit_code, 0, repeated_apply.output)
            self.assertIn("Files moved          : 0", repeated_apply.output)
