from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


def write_article(root: Path, relative_path: str, references: list[str]) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    reference_lines = "\n".join(f"  - {item}" for item in references) or " []"
    path.write_text(
        "---\n"
        f"title: '{path.stem}'\n"
        "description: 'A sufficiently long test description.'\n"
        "category: 'Test'\n"
        "difficulty: 'Beginner'\n"
        "tags: []\n"
        "systems: []\n"
        "aliases: []\n"
        "acronyms: []\n"
        "references:\n"
        f"{reference_lines}\n"
        "last_updated: '2026-08-16'\n"
        "---\n\n# Overview\n",
        encoding="utf-8",
    )
    return path


class OrphanPlanCommandTests(unittest.TestCase):
    def test_exports_parent_index_proposals_without_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "knowledge"
            output = Path(temporary_directory) / "reports"
            index = write_article(root, "guide/guide-index.md", [])
            target = write_article(root, "guide/target.md", [])
            original = {path: path.read_bytes() for path in (index, target)}

            result = CliRunner().invoke(
                app,
                [
                    "orphan-plan",
                    "--root",
                    str(root),
                    "--output-directory",
                    str(output),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Actionable proposals: 1", result.output)
            data = json.loads(
                (output / "orphan_repair_plan.json").read_text(encoding="utf-8")
            )
            self.assertEqual(data["summary"]["total_candidates"], 2)
            target_proposal = next(
                item for item in data["proposals"] if item["target"] == "guide/target"
            )
            self.assertEqual(target_proposal["parent_index"], "guide/guide-index")
            self.assertEqual(target_proposal["confidence"], "high")
            self.assertTrue((output / "orphan_repair_plan.md").exists())
            self.assertEqual(
                {path: path.read_bytes() for path in (index, target)},
                original,
            )
