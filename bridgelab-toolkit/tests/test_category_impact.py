from __future__ import annotations

import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import yaml
from typer.testing import CliRunner

from analysis.category_impact import (
    PLAY_SUBGROUP_SCOPES,
    analyze_category_impact,
    analyze_cumulative_play_impact,
    project_category_impact,
)
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
            self.write(
                "bidding/existing.md",
                category="bidding",
                subcategory="conventions",
                tags=[],
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

    def test_bidding_scope_and_hypotheses_do_not_mutate_tags_or_subcategory(self) -> None:
        self.fixtures()
        articles = Repository(self.root).build()
        original = {article.id: asdict(article.metadata) for article in articles}

        report = analyze_category_impact(articles, scope="bidding")
        h1 = project_category_impact(articles, "bidding", "keep")
        h2 = project_category_impact(articles, "bidding", "remove")
        h3 = project_category_impact(articles, "bidding", "replace")
        projections = [
            {article.relative_path.as_posix(): article for article in projected}
            for projected in (h1, h2, h3)
        ]
        path = "bidding/conventions/breadcrumb.md"
        play_path = "play/defence/play-breadcrumb.md"

        self.assertEqual([item.path for item in report.items], [path])
        self.assertEqual(report.selected_relationship_articles_affected, 1)
        self.assertGreater(report.nonselected_relationship_articles_affected, 0)
        self.assertEqual(projections[0][path].metadata.category, "bidding")
        self.assertIn("bidding – principles", projections[0][path].metadata.tags)
        self.assertNotIn("bidding", projections[0][path].metadata.tags)
        self.assertNotIn("bidding – principles", projections[1][path].metadata.tags)
        self.assertNotIn("bidding", projections[1][path].metadata.tags)
        self.assertNotIn("bidding – principles", projections[2][path].metadata.tags)
        self.assertIn("bidding", projections[2][path].metadata.tags)
        self.assertEqual(
            [projected[path].metadata.subcategory for projected in projections],
            ["conventions", "conventions", "conventions"],
        )
        self.assertEqual(
            [projected[play_path].metadata.category for projected in projections],
            ["Card Play – Defence", "Card Play – Defence", "Card Play – Defence"],
        )
        self.assertEqual({article.id: asdict(article.metadata) for article in articles}, original)

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
        self.assertIn("--scope", result.output)
        self.assertNotIn("--apply", result.output)

    def test_cli_bidding_scope_excludes_play_and_is_deterministic(self) -> None:
        paths = self.fixtures()
        before = {path: path.read_bytes() for path in paths}
        runner = CliRunner()

        first = runner.invoke(
            app,
            ["category-impact", "--scope", "bidding", "--root", str(self.root)],
        )
        second = runner.invoke(
            app,
            ["category-impact", "--scope", "bidding", "--root", str(self.root)],
        )

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertIn("scope=bidding", first.output)
        self.assertIn("Selected structural files       : 1", first.output)
        self.assertIn("bidding/conventions/breadcrumb.md", first.output)
        self.assertNotIn("play/defence/play-breadcrumb.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_play_scope_and_subgroups_are_exact_and_keep_h1_metadata(self) -> None:
        paths = self.fixtures()
        nonstructural = self.write(
            "play/defence/already-canonical.md",
            category="play",
            subcategory="defence",
            tags=["play"],
        )
        articles = Repository(self.root).build()
        before_models = [asdict(article.metadata) for article in articles]
        before_bytes = {path: path.read_bytes() for path in [*paths, nonstructural]}

        play = analyze_category_impact(articles, scope="play")
        defence = analyze_category_impact(articles, scope="play:defence-counting")
        declarer = analyze_category_impact(articles, scope="play:declarer-squeezes")
        h1 = project_category_impact(articles, "play:defence-counting", "keep")
        h2 = project_category_impact(articles, "play:defence-counting", "remove")
        h3 = project_category_impact(articles, "play:defence-counting", "replace")
        by_projection = [
            {item.relative_path.as_posix(): item for item in projection}
            for projection in (h1, h2, h3)
        ]
        target = "play/defence/play-breadcrumb.md"

        self.assertEqual(len(PLAY_SUBGROUP_SCOPES), 15)
        self.assertEqual([item.path for item in play.items], [
            "play/declarer-play/slash.md",
            target,
        ])
        self.assertEqual(defence.items, ())
        self.assertEqual(declarer.items, ())
        self.assertEqual(
            [projection[target].metadata.category for projection in by_projection],
            ["Card Play – Defence"] * 3,
        )
        self.assertEqual([asdict(article.metadata) for article in articles], before_models)
        self.assertEqual(
            {path: path.read_bytes() for path in [*paths, nonstructural]}, before_bytes
        )

    def test_subgroup_hypotheses_spillover_and_cumulative_are_deterministic(self) -> None:
        paths = self.fixtures()
        self.write(
            "play/defence/counting/reviewed.md",
            category="Card Play – Defence",
            subcategory="defence",
            tags=["card play – defence"],
        )
        self.write(
            "play/existing.md",
            category="play",
            subcategory="defence",
            tags=[],
        )
        articles = Repository(self.root).build()
        before = [asdict(article.metadata) for article in articles]

        report = analyze_category_impact(articles, "play:defence-counting")
        h1 = project_category_impact(articles, "play:defence-counting", "keep")
        h2 = project_category_impact(articles, "play:defence-counting", "remove")
        h3 = project_category_impact(articles, "play:defence-counting", "replace")
        first = analyze_cumulative_play_impact(articles)
        second = analyze_cumulative_play_impact(articles)
        target = "play/defence/counting/reviewed.md"
        projections = [
            {item.relative_path.as_posix(): item for item in value}
            for value in (h1, h2, h3)
        ]

        self.assertEqual([item.path for item in report.items], [target])
        self.assertGreater(report.category_edges_added, 0)
        self.assertGreater(report.nonselected_relationship_articles_affected, 0)
        self.assertIn("card play – defence", projections[0][target].metadata.tags)
        self.assertNotIn("card play – defence", projections[1][target].metadata.tags)
        self.assertNotIn("play", projections[1][target].metadata.tags)
        self.assertIn("play", projections[2][target].metadata.tags)
        self.assertEqual(
            [projection[target].metadata.subcategory for projection in projections],
            ["defence"] * 3,
        )
        self.assertEqual(first, second)
        self.assertEqual(first[-1].cumulative_files, 1)
        self.assertEqual([asdict(article.metadata) for article in articles], before)
        self.assertTrue(all(path.exists() for path in paths))

    def test_cli_play_subgroup_scope_is_read_only_and_repeatable(self) -> None:
        paths = self.fixtures()
        target = self.write(
            "play/defence/counting/reviewed.md",
            category="Card Play – Defence",
            subcategory="defence",
            tags=["card play – defence"],
        )
        before = {path: path.read_bytes() for path in [*paths, target]}
        runner = CliRunner()
        arguments = [
            "category-impact",
            "--scope",
            "play:defence-counting",
            "--root",
            str(self.root),
        ]

        first = runner.invoke(app, arguments)
        second = runner.invoke(app, arguments)

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertIn("Selected structural files       : 1", first.output)
        self.assertIn("play/defence/counting/reviewed.md", first.output)
        self.assertNotIn("bidding/conventions/breadcrumb.md", first.output)
        self.assertNotIn("--apply", first.output)
        self.assertEqual({path: path.read_bytes() for path in [*paths, target]}, before)
        self.assertFalse(any("backup" in path.name for path in self.base.rglob("*")))
        self.assertFalse(any(path.suffix == ".json" for path in self.base.rglob("*")))


if __name__ == "__main__":
    unittest.main()
