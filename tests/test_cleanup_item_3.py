from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

import config
from core.repository import Repository
from main import app


def write_article(root: Path) -> Path:
    path = root / "bidding" / "systems" / "precision.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "title: Precision Club System\n"
        "description: Test article description.\n"
        "category: Systems\n"
        "systems:\n"
        "  - precision\n"
        "---\n\n"
        "# Overview\n",
        encoding="utf-8",
    )
    return path


class RepositoryPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "knowledge"
        self.article_path = write_article(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_relative_path_is_a_path_and_id_is_unchanged(self) -> None:
        article = Repository(self.root).build()[0]

        self.assertIsInstance(article.relative_path, Path)
        self.assertEqual(article.id, "bidding/systems/precision")

    def test_json_export_uses_posix_relative_path(self) -> None:
        repository = Repository(self.root)
        article = repository.build()[0]
        output = self.root.parent / "repository.json"

        repository.export_json(output)

        exported = json.loads(output.read_text(encoding="utf-8"))[0]
        self.assertEqual(
            exported["relative_path"],
            "bidding/systems/precision.md",
        )
        self.assertEqual(exported["path"], str(article.path))

    def test_repository_uses_absolute_root_independently_of_cwd(self) -> None:
        original_cwd = Path.cwd()

        try:
            os.chdir(self.root.parent)
            article = Repository(self.root.resolve()).build()[0]
        finally:
            os.chdir(original_cwd)

        self.assertEqual(article.id, "bidding/systems/precision")


class DefaultRepositoryConfigurationTests(unittest.TestCase):
    def tearDown(self) -> None:
        importlib.reload(config)

    def test_environment_override_is_used_as_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            override = Path(temporary_directory) / "knowledge"
            override.mkdir()

            with patch.dict(
                os.environ,
                {"BRIDGELAB_REPOSITORY": str(override)},
                clear=False,
            ):
                loaded_config = importlib.reload(config)

            self.assertEqual(
                loaded_config.REPOSITORY,
                override.resolve(),
            )

    def test_missing_environment_uses_sibling_fallback_from_any_cwd(self) -> None:
        original_cwd = Path.cwd()

        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                with patch.dict(os.environ, {}, clear=True):
                    loaded_config = importlib.reload(config)
            finally:
                os.chdir(original_cwd)

        self.assertEqual(
            loaded_config.REPOSITORY,
            (loaded_config.ROOT.parent / "knowladge").resolve(),
        )


class ExplicitRootCommandTests(unittest.TestCase):
    def test_statistics_uses_explicit_root_from_another_cwd(self) -> None:
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "knowledge"
            write_article(root)
            other_directory = Path(temporary_directory) / "other"
            other_directory.mkdir()

            original_cwd = Path.cwd()
            try:
                os.chdir(other_directory)
                result = runner.invoke(
                    app,
                    ["statistics", "--root", str(root)],
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Articles             : 1", result.output)
