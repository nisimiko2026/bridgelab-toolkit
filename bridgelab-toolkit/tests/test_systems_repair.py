from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


class SystemsRepairTests(unittest.TestCase):
    def test_reviewed_removals_are_guarded_backed_up_and_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            source = root / "bidding/example.md"
            source.parent.mkdir(parents=True)
            original = (
                "---\ntitle: Example\nsystems:\n"
                "- precision\n- jacoby\naliases: []\n---\n# Example\n"
            )
            source.write_text(original, encoding="utf-8")
            plan = base / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "proposals": [
                            {
                                "path": "bidding/example.md",
                                "current_systems": ["precision", "jacoby"],
                                "remove": [
                                    {
                                        "value": "jacoby",
                                        "reason": "outside_system_taxonomy",
                                    }
                                ],
                                "proposed_systems": ["precision"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            backup = base / "backup"
            arguments = [
                "repair-systems",
                "--root",
                str(root),
                "--plan",
                str(plan),
                "--backup",
                str(backup),
            ]

            dry_run = CliRunner().invoke(app, arguments)
            self.assertEqual(dry_run.exit_code, 0, dry_run.output)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

            result = CliRunner().invoke(app, [*arguments, "--apply"])
            self.assertEqual(result.exit_code, 0, result.output)
            updated = source.read_text(encoding="utf-8")
            self.assertIn("systems:\n  - precision\n", updated)
            self.assertNotIn("jacoby", updated)
            self.assertEqual(
                (backup / "bidding/example.md").read_text(encoding="utf-8"),
                original,
            )

    def test_metadata_drift_aborts_without_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            source = root / "example.md"
            source.parent.mkdir(parents=True)
            source.write_text("systems:\n  - acol\n", encoding="utf-8")
            plan = base / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "proposals": [
                            {
                                "path": "example.md",
                                "current_systems": ["precision"],
                                "remove": [{"value": "precision"}],
                                "proposed_systems": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            backup = base / "backup"

            result = CliRunner().invoke(
                app,
                [
                    "repair-systems",
                    "--root",
                    str(root),
                    "--plan",
                    str(plan),
                    "--backup",
                    str(backup),
                    "--apply",
                ],
            )

            self.assertNotEqual(result.exit_code, 0)
            self.assertFalse(backup.exists())
            self.assertIn("  - acol", source.read_text(encoding="utf-8"))
