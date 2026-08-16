from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


class PrinciplesRepairTests(unittest.TestCase):
    def test_guarded_migration_moves_files_and_normalizes_exact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            backup = base / "backup"
            source = root / "topic" / "principals" / "principals-index.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nsubcategory: principals\ntags:\n  - principals\n---\n"
                "# Principles\nA school principal remains unchanged.\n",
                encoding="utf-8",
            )
            reference = root / "index.md"
            reference.write_text("- topic/principals/principals-index\n", encoding="utf-8")
            plan = base / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "directory_moves": [
                            {"old": "topic/principals", "new": "topic/principles"}
                        ],
                        "nested_file_moves": [
                            {
                                "old": "topic/principals/principals-index.md",
                                "new": "topic/principles/principles-index.md",
                                "confidence": "high",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            arguments = [
                "repair-principles",
                "--root",
                str(root),
                "--plan",
                str(plan),
                "--backup",
                str(backup),
            ]
            original = source.read_bytes()

            dry_run = CliRunner().invoke(app, arguments)
            self.assertEqual(dry_run.exit_code, 0, dry_run.output)
            self.assertEqual(source.read_bytes(), original)

            result = CliRunner().invoke(app, [*arguments, "--apply"])
            self.assertEqual(result.exit_code, 0, result.output)
            destination = root / "topic" / "principles" / "principles-index.md"
            migrated = destination.read_text(encoding="utf-8")
            self.assertIn("subcategory: principles", migrated)
            self.assertIn("  - principles", migrated)
            self.assertIn("school principal", migrated)
            self.assertIn("topic/principles/principles-index", reference.read_text(encoding="utf-8"))
            self.assertEqual((backup / source.relative_to(root)).read_bytes(), original)

    def test_medium_nested_rename_can_run_after_directory_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            backup = base / "backup"
            source = root / "topic/principles/index-principal-partnership.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "id: topic/principles/index-principal-partnership\n",
                encoding="utf-8",
            )
            reference = root / "reference.md"
            reference.write_text(
                "topic/principles/index-principal-partnership\n",
                encoding="utf-8",
            )
            plan = base / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "directory_moves": [
                            {"old": "topic/principals", "new": "topic/principles"}
                        ],
                        "nested_file_moves": [
                            {
                                "old": "topic/principals/index-principal-partnership.md",
                                "new": "topic/principles/partnership-principles-index.md",
                                "confidence": "medium",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            arguments = [
                "repair-principles",
                "--root",
                str(root),
                "--plan",
                str(plan),
                "--backup",
                str(backup),
                "--include-medium-confidence",
                "--apply",
            ]

            result = CliRunner().invoke(app, arguments)

            self.assertEqual(result.exit_code, 0, result.output)
            destination = root / "topic/principles/partnership-principles-index.md"
            self.assertFalse(source.exists())
            self.assertTrue(destination.exists())
            self.assertIn(
                "topic/principles/partnership-principles-index",
                destination.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "topic/principles/partnership-principles-index",
                reference.read_text(encoding="utf-8"),
            )
            self.assertTrue(
                (backup / "topic/principles/index-principal-partnership.md").exists()
            )
