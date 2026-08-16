import json
import tempfile
import unittest
from pathlib import Path

from generators.systems_manual_repair_plan import generate


class SystemsManualRepairPlanTests(unittest.TestCase):
    def test_omits_retain_only_entries(self):
        review = {"entries": [
            {"path": "remove.md", "current_systems": ["precision"], "remove": [{"value": "precision", "reason": "false_positive"}], "proposed_systems": []},
            {"path": "retain.md", "current_systems": ["acol"], "remove": [], "proposed_systems": ["acol"]},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "review.json", root / "plan.json"
            source.write_text(json.dumps(review), encoding="utf-8")
            plan = generate(source, output)
            self.assertEqual(plan["summary"], {"files_to_update": 1, "assignments_to_remove": 1})
            self.assertEqual(plan["proposals"][0]["path"], "remove.md")


if __name__ == "__main__":
    unittest.main()
