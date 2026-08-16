from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


def write_article(
    root: Path,
    relative_path: str,
    *,
    description: str,
    difficulty: str,
    body: str,
) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"title: '{path.stem}'\n"
        f"description: '{description}'\n"
        "category: 'Conventions'\n"
        f"difficulty: '{difficulty}'\n"
        "tags: []\n"
        "systems: []\n"
        "aliases: []\n"
        "acronyms: []\n"
        "references: []\n"
        "last_updated: '2026-08-16'\n"
        "---\n"
        f"# {path.stem}\n\n{body}\n",
        encoding="utf-8",
    )
    return path


class RepairPlanCommandTests(unittest.TestCase):
    def test_plan_exports_proposals_without_modifying_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "knowledge"
            output = Path(temporary_directory) / "reports"
            target = write_article(
                root,
                "guide/target.md",
                description="",
                difficulty="",
                body="Target explains a useful bridge convention in practical detail.",
            )
            write_article(
                root,
                "guide/peer.md",
                description="A sufficiently long peer description.",
                difficulty="Intermediate",
                body="Peer article.",
            )
            original = target.read_bytes()

            result = CliRunner().invoke(
                app,
                [
                    "repair-plan",
                    "--root",
                    str(root),
                    "--output-directory",
                    str(output),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Total proposals      : 2", result.output)
            self.assertIn("No source files were modified", result.output)
            self.assertEqual(target.read_bytes(), original)

            data = json.loads(
                (output / "metadata_repair_plan.json").read_text(encoding="utf-8")
            )
            self.assertEqual(data["summary"]["total_proposals"], 2)
            proposals = {item["field"]: item for item in data["proposals"]}
            self.assertEqual(
                proposals["description"]["proposed"],
                "Target explains a useful bridge convention in practical detail.",
            )
            self.assertEqual(proposals["difficulty"]["proposed"], "Intermediate")
            self.assertTrue((output / "metadata_repair_plan.md").exists())

    def test_complete_article_needs_no_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "knowledge"
            output = Path(temporary_directory) / "reports"
            write_article(
                root,
                "complete.md",
                description="A sufficiently long complete description.",
                difficulty="Beginner",
                body="Complete article.",
            )

            result = CliRunner().invoke(
                app,
                [
                    "repair-plan",
                    "--root",
                    str(root),
                    "--output-directory",
                    str(output),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            data = json.loads(
                (output / "metadata_repair_plan.json").read_text(encoding="utf-8")
            )
            self.assertEqual(data["summary"]["total_proposals"], 0)
