from __future__ import annotations

import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import yaml
from typer.testing import CliRunner

from analysis.category_impact import analyze_category_impact
from core.repository import Repository
from main import app


class CategoryImpactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(
        self,
        relative: str,
        *,
        category: str,
        subcategory: str,
        tags: list[str],
    ) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "title": path.stem,
            "description": "A sufficiently detailed temporary category impact fixture.",
            "category": category,
            "subcategory": subcategory,
            "difficulty": "Intermediate",
            "tags": tags,
            "systems": [],
            "aliases": [],
            "acronyms": [],
            "references": [],
            "last_updated": "2026-08-17",
            "status": "Draft",
        }
        path.write_text(
            "---\n"
            + yaml.safe_dump(data, sort_keys=False)
            + f"---\n# {path.stem}\n",
            encoding="utf-8",
        )
        return path

    def fixtures(self) -> list[Path]:
        return [
            self.write(
                "bidding/conventions/breadcrumb.md",
                category="Bidding – Principles",
                subcategory="conventions",
                tags=["bidding – principles"],
            ),
            self.write(
                "play/defence/play-breadcrumb.md",
                category="Card Play – Defence",
                subcategory="defence",
                tags=["card play – defence", "play"],
            ),
            self.write(
                "play/declarer-play/slash.md",
                category="techniques/squeezes",
                subcategory="declarer-play",
                tags=["techniques/squeezes"],
            ),
            self.write(
                "bidding/conventions/unrelated.md",
                category="Conventions",
                subcategory="conventions",
                tags=["conventions"],
            ),
            self.write(
                "references/legacy-peer.md",
                category="techniques/squeezes",
                subcategory="reference",
                tags=["techniques/squeezes"],
            ),
        ]

    def test_selection_tags_rankings_and_input_objects_are_read_only(self) -> None:
        self.fixtures()
        articles = Repository(self.root).build()
        before = [asdict(article.metadata) for article in articles]

        report = analyze_category_impact(articles)

        self.assertEqual(len(report.items), 3)
        self.assertEqual(
            [(item.path, item.proposed_category) for item in report.items],
            [
                ("bidding/conventions/breadcrumb.md", "bidding"),
                ("play/declarer-play/slash.md", "play"),
                ("play/defence/play-breadcrumb.md", "play"),
            ],
        )
        self.assertEqual(report.old_tags_present, 3)
        self.assertEqual(report.canonical_tags_present, 1)
        self.assertEqual(report.canonical_tags_to_add, 2)
        self.assertGreater(report.category_pairs_added, 0)
        self.assertGreater(report.tag_pair_scores_decreased, 0)
        self.assertEqual([asdict(article.metadata) for article in articles], before)
        self.assertNotIn(
            "bidding/conventions/unrelated.md",
            {item.path for item in report.items},
        )

    def test_execution_is_deterministic_and_preserves_all_files(self) -> None:
        paths = self.fixtures()
        before = {path: path.read_bytes() for path in paths}
        before_tree = sorted(path.relative_to(self.base) for path in self.base.rglob("*"))
        runner = CliRunner()

        first = runner.invoke(app, ["category-impact", "--root", str(self.root)])
        second = runner.invoke(app, ["category-impact", "--root", str(self.root)])

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertEqual(first.output, second.output)
        self.assertIn("Selected structural files       : 3", first.output)
        self.assertIn("No source files were modified", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)
        self.assertEqual(
            sorted(path.relative_to(self.base) for path in self.base.rglob("*")),
            before_tree,
        )
        self.assertFalse(any("backup" in path.name for path in self.base.rglob("*")))
        self.assertFalse(any(path.suffix == ".json" for path in self.base.rglob("*")))

    def test_cli_registration_and_help_have_no_apply_option(self) -> None:
        result = CliRunner().invoke(app, ["category-impact", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--root", result.output)
        self.assertNotIn("--apply", result.output)


if __name__ == "__main__":
    unittest.main()
