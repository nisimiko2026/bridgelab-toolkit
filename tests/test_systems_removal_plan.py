from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from generators.systems_removal_plan import generate


class SystemsRemovalPlanTests(unittest.TestCase):
    def test_generator_removes_only_non_bidding_or_outside_taxonomy_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            database = base / "repository.json"
            json_output = base / "plan.json"
            markdown_output = base / "plan.md"
            database.write_text(
                json.dumps(
                    [
                        {
                            "relative_path": "play/example.md",
                            "metadata": {"systems": ["precision"]},
                        },
                        {
                            "relative_path": "bidding/example.md",
                            "metadata": {"systems": ["precision", "jacoby"]},
                        },
                    ]
                ),
                encoding="utf-8",
            )

            generate(database, json_output, markdown_output)

            plan = json.loads(json_output.read_text(encoding="utf-8"))
            self.assertEqual(plan["summary"]["files_with_removals"], 2)
            self.assertEqual(plan["summary"]["assignments_to_remove"], 2)
            self.assertEqual(plan["summary"]["non_bidding_assignments"], 1)
            self.assertEqual(plan["summary"]["outside_taxonomy_assignments"], 1)
            bidding = next(
                proposal
                for proposal in plan["proposals"]
                if proposal["path"] == "bidding/example.md"
            )
            self.assertEqual(bidding["proposed_systems"], ["precision"])
            self.assertTrue(markdown_output.exists())
