from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from analysis.graph import KnowledgeGraph
from analysis.related import RelatedAnalyzer
from core.models import Article
from main import app


def article(
    article_id: str,
    title: str,
    relative_path: str,
    *,
    category: str = "",
    systems: list[str] | None = None,
    tags: list[str] | None = None,
    references: list[str] | None = None,
) -> Article:
    item = Article(
        id=article_id,
        filename=Path(relative_path).name,
        path=Path(relative_path),
        relative_path=Path(relative_path),
        directory=Path(relative_path).parent.as_posix(),
    )
    item.metadata.title = title
    item.metadata.category = category
    item.metadata.systems = systems or []
    item.metadata.tags = tags or []
    item.metadata.references = references or []
    return item


def write_article(
    root: Path,
    relative_path: str,
    title: str,
    *,
    systems: list[str] | None = None,
    references: list[str] | None = None,
) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    systems_yaml = "\n".join(f"  - {system}" for system in systems or [])
    references_yaml = "\n".join(
        f"  - {reference}" for reference in references or []
    )
    path.write_text(
        "---\n"
        f"title: {title}\n"
        "description: Test article description.\n"
        "category: Systems\n"
        "tags:\n"
        "  - system\n"
        "systems:\n"
        f"{systems_yaml or ' []'}\n"
        "references:\n"
        f"{references_yaml or ' []'}\n"
        "---\n\n"
        "# Overview\n",
        encoding="utf-8",
    )


class KnowledgeGraphFindArticleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.precision = article(
            "bidding/systems/precision",
            "Precision Club System",
            "bidding/systems/precision.md",
        )
        self.graph = KnowledgeGraph([self.precision])

    def test_finds_supported_identifier_forms(self) -> None:
        for query in [
            "bidding/systems/precision",
            "precision.md",
            "precision",
            "Precision Club System",
            "bidding/systems/precision.md",
            "  PRECISION  ",
            "BIDDING\\SYSTEMS\\PRECISION.MD",
        ]:
            with self.subTest(query=query):
                self.assertIs(self.graph.find_article(query), self.precision)

    def test_returns_none_for_unknown_query(self) -> None:
        self.assertIsNone(self.graph.find_article("unknown article"))


class RelatedAnalyzerTests(unittest.TestCase):
    def test_returns_article_score_pairs_in_descending_score_order(self) -> None:
        source = article(
            "source",
            "Source",
            "source.md",
            category="Systems",
            systems=["precision"],
            tags=["system", "club"],
            references=["high"],
        )
        high = article(
            "high",
            "High",
            "high.md",
            category="Systems",
            systems=["precision"],
            tags=["system", "club"],
        )
        low = article(
            "low",
            "Low",
            "low.md",
            category="Systems",
        )

        results = RelatedAnalyzer(
            KnowledgeGraph([source, high, low])
        ).related(source)

        self.assertEqual([item[0] for item in results], [high, low])
        self.assertTrue(
            all(isinstance(item[0], Article) for item in results)
        )
        self.assertEqual(
            [score for _, score in results],
            sorted(
                [score for _, score in results],
                reverse=True,
            ),
        )


class CommandSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        write_article(
            self.root,
            "bidding/systems/precision.md",
            "Precision Club System",
            systems=["precision"],
            references=["bidding/systems/related"],
        )
        write_article(
            self.root,
            "bidding/systems/related.md",
            "Related Precision",
            systems=["precision"],
        )
        write_article(
            self.root,
            "bidding/systems/empty.md",
            "No System",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            [*arguments, "--root", str(self.root)],
        )

    def test_debug_counts_empty_and_non_empty_systems(self) -> None:
        result = self.invoke("debug")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Articles with systems : 2", result.output)

    def test_related_resolves_precision_filename_stem(self) -> None:
        result = self.invoke("related", "precision")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Related Articles: Precision Club System", result.output)
        self.assertIn("bidding/systems/related.md", result.output)

    def test_learning_path_resolves_precision_filename_stem(self) -> None:
        result = self.invoke("learning-path", "precision")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Learning Path: Precision Club System", result.output)
        self.assertIn("bidding/systems/related.md", result.output)
