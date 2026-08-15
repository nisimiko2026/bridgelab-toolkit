from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from core.repository import Repository
from enrichment.generator import MetadataGenerator
from enrichment.reference_detector import ReferenceDetector
from enrichment.system_detector import SystemDetector
from enrichment.tagger import TagGenerator
from enrichment.writer import MetadataWriter
from main import app


def write_article(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")
    return path


def read_raw_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as source:
        return source.read()


def build_generator(articles):
    return MetadataGenerator(
        tagger=TagGenerator(),
        system_detector=SystemDetector(),
        reference_detector=ReferenceDetector(articles),
    )


class MetadataEnrichmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_dry_run_does_not_write_source_files(self) -> None:
        source = write_article(
            self.root,
            "precision.md",
            "# Precision\n\nPrecision uses an opening system.\n",
        )
        original = source.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            app,
            ["enrich", "--root", str(self.root)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Dry run:", result.output)
        self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_apply_writes_metadata_and_preserves_article_id(self) -> None:
        source = write_article(
            self.root,
            "bidding/systems/precision.md",
            "# Precision\n\nPrecision is an opening system.\n",
        )
        original_id = Repository(self.root).build()[0].id

        result = CliRunner().invoke(
            app,
            ["enrich", "--apply", "--root", str(self.root)],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Updated articles : 1", result.output)
        self.assertTrue(source.read_text(encoding="utf-8").startswith("---\n"))
        self.assertEqual(Repository(self.root).build()[0].id, original_id)

    def test_malformed_yaml_is_skipped_without_writing(self) -> None:
        source = write_article(
            self.root,
            "broken.md",
            "---\ntitle: [broken\n---\n# Broken\n",
        )
        original = source.read_text(encoding="utf-8")
        repository = Repository(self.root)
        articles = repository.build()
        build_generator(articles).enrich_all(articles)
        writer = MetadataWriter()

        self.assertEqual(writer.preview_all(articles), 0)
        self.assertEqual(writer.write_all(articles), 0)
        self.assertTrue(writer.skipped)
        self.assertIn("Malformed YAML front matter", writer.skipped[0][1])
        self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_safe_serialization_preserves_unknown_fields_and_body(self) -> None:
        body = "\r\n# Body\r\n\r\nText with  two spaces.  \r\n"
        source = write_article(
            self.root,
            "article.md",
            "---\n"
            "title: 'Quoted: # title'\n"
            "description: |\n"
            "  First: # value\n"
            "  Second line\n"
            "tags: []\n"
            "systems: []\n"
            "references: []\n"
            "unknown_field:\n"
            "  nested: true\n"
            "---\n"
            + body,
        )
        repository = Repository(self.root)
        articles = repository.build()
        article = articles[0]
        article.metadata.title = "Quoted: # title"
        article.metadata.description = "First: # value\nSecond line\n"
        writer = MetadataWriter()

        self.assertTrue(writer.write(article))
        rewritten = read_raw_text(source)
        yaml_text, rewritten_body = rewritten.split("---\n", 2)[1:]
        parsed = yaml.safe_load(yaml_text)

        self.assertEqual(parsed["title"], "Quoted: # title")
        self.assertEqual(parsed["description"], "First: # value\nSecond line\n")
        self.assertEqual(parsed["tags"], [])
        self.assertEqual(parsed["unknown_field"], {"nested": True})
        self.assertEqual(rewritten_body, body)

    def test_generated_values_merge_with_manual_values_deterministically(self) -> None:
        write_article(
            self.root,
            "target.md",
            "---\ntitle: Target Topic\n---\n# Target\n",
        )
        write_article(
            self.root,
            "source.md",
            "---\n"
            "title: Source\n"
            "tags:\n  - custom-tag\n"
            "systems:\n  - manual-system\n"
            "references:\n  - manual/reference\n"
            "---\n"
            "# Source\n\nPrecision is an opening. Target Topic.\n",
        )
        repository = Repository(self.root)
        articles = repository.build()
        source = next(article for article in articles if article.id == "source")

        build_generator(articles).enrich(source)

        self.assertEqual(source.metadata.systems, ["manual-system", "precision"])
        self.assertEqual(source.metadata.tags, sorted(source.metadata.tags))
        self.assertIn("custom-tag", source.metadata.tags)
        self.assertIn("opening", source.metadata.tags)
        self.assertEqual(
            source.metadata.references,
            ["manual/reference", "target"],
        )

    def test_repeated_apply_is_byte_identical(self) -> None:
        source = write_article(
            self.root,
            "precision.md",
            "# Precision\n\nPrecision is an opening system.\n",
        )
        repository = Repository(self.root)
        articles = repository.build()
        build_generator(articles).enrich_all(articles)
        writer = MetadataWriter()

        self.assertEqual(writer.write_all(articles), 1)
        first = source.read_bytes()

        articles = Repository(self.root).build()
        build_generator(articles).enrich_all(articles)

        self.assertEqual(writer.write_all(articles), 0)
        self.assertEqual(source.read_bytes(), first)

    def test_atomic_write_failure_leaves_original_file_intact(self) -> None:
        source = write_article(
            self.root,
            "article.md",
            "# Article\n",
        )
        original = source.read_text(encoding="utf-8")
        article = Repository(self.root).build()[0]
        article.metadata.title = "Article"

        with patch("enrichment.writer.os.replace", side_effect=OSError("fail")):
            with self.assertRaises(OSError):
                MetadataWriter().write(article)

        self.assertEqual(source.read_text(encoding="utf-8"), original)
