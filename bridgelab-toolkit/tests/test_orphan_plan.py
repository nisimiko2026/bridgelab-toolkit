from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from analysis.orphan_plan import OrphanRepairPlanner
from core.repository import Repository
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
    def proposals(self, root: Path):
        return OrphanRepairPlanner().build(Repository(root).build())

    def test_canonical_roles_control_parent_index_candidates(self) -> None:
        cases = (
            ("guide/guide-index.md", "guide/target.md", "high"),
            ("guide/index-guide.md", "guide/target.md", "high"),
            ("guide/index.md", "guide/target.md", "high"),
            ("DOMAIN/INDEX-GUIDE.MD", "DOMAIN/target.md", "high"),
            ("domain/domain-index.md", "domain/topic/target.md", "medium"),
        )
        for index_path, target_path, confidence in cases:
            with self.subTest(index_path=index_path), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "knowledge"
                write_article(root, index_path, [])
                write_article(root, target_path, [])
                target = target_path.removesuffix(".md")
                proposal = next(
                    item for item in self.proposals(root) if item.target == target
                )
                self.assertEqual(
                    proposal.parent_index,
                    Path(index_path).with_suffix("").as_posix(),
                )
                self.assertEqual(proposal.confidence, confidence)

    def test_index_substrings_are_not_parent_index_candidates(self) -> None:
        for filename in ("fooindex.md", "indexing.md", "indexical.md", "foo-indexing.md"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "knowledge"
                write_article(root, f"guide/{filename}", [])
                write_article(root, "guide/target.md", [])
                proposal = next(
                    item for item in self.proposals(root)
                    if item.target == "guide/target"
                )
                self.assertIsNone(proposal.parent_index)
                self.assertEqual(proposal.reason, "no parent index found")

    def test_multiple_parent_indexes_remain_sorted_and_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            write_article(root, "guide/z-index.md", [])
            write_article(root, "guide/a-index.md", [])
            write_article(root, "guide/target.md", [])
            proposal = next(
                item for item in self.proposals(root)
                if item.target == "guide/target"
            )
            self.assertIsNone(proposal.parent_index)
            self.assertEqual(proposal.confidence, "manual")
            self.assertEqual(
                proposal.candidates,
                ("guide/a-index", "guide/z-index"),
            )

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

    def test_guarded_apply_backs_up_parent_and_adds_high_confidence_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "knowledge"
            output = base / "reports"
            backup = base / "backup"
            index = write_article(root, "guide/guide-index.md", [])
            target = write_article(root, "guide/target.md", [])
            original_index = index.read_bytes()

            plan_result = CliRunner().invoke(
                app,
                [
                    "orphan-plan",
                    "--root",
                    str(root),
                    "--output-directory",
                    str(output),
                ],
            )
            self.assertEqual(plan_result.exit_code, 0, plan_result.output)

            dry_run = CliRunner().invoke(
                app,
                [
                    "orphan-apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(output / "orphan_repair_plan.json"),
                    "--backup",
                    str(backup),
                ],
            )
            self.assertEqual(dry_run.exit_code, 0, dry_run.output)
            self.assertIn("Proposals selected: 1", dry_run.output)
            self.assertEqual(index.read_bytes(), original_index)

            apply_result = CliRunner().invoke(
                app,
                [
                    "orphan-apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(output / "orphan_repair_plan.json"),
                    "--backup",
                    str(backup),
                    "--apply",
                ],
            )
            self.assertEqual(apply_result.exit_code, 0, apply_result.output)
            self.assertIn("Proposals applied: 1", apply_result.output)
            self.assertEqual((backup / "guide/guide-index.md").read_bytes(), original_index)
            self.assertIn("guide/target", index.read_text(encoding="utf-8"))
            self.assertEqual(target.read_text(encoding="utf-8").count("guide/target"), 0)
