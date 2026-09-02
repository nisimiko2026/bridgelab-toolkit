import json
import tempfile
import unittest
from pathlib import Path

from generators.systems_applicability_repair_plan import generate


class SystemsApplicabilityRepairPlanTests(unittest.TestCase):
    def test_includes_only_high_confidence_removals(self):
        audit = {
            "entries": [
                {"path": "high.md", "confidence": "high", "reason": "cross_label", "current_systems": ["acol", "precision"], "proposed_remove": ["precision"], "proposed_systems": ["acol"]},
                {"path": "medium.md", "confidence": "medium", "reason": "bundle", "current_systems": ["acol"], "proposed_remove": ["acol"], "proposed_systems": []},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "audit.json", root / "plan.json"
            source.write_text(json.dumps(audit), encoding="utf-8")
            plan = generate(source, output)
            self.assertEqual(plan["summary"], {"files_to_update": 1, "assignments_to_remove": 1})
            self.assertEqual(plan["proposals"][0]["path"], "high.md")


if __name__ == "__main__":
    unittest.main()
