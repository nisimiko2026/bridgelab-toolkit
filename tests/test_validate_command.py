from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app


def write_article(
    root: Path,
    relative_path: str,
    *,
    title: str = "Article",
    description: str = "A sufficiently long article description for validation.",
    category: str = "Conventions",
    difficulty: str = "Beginner",
    last_updated: str = "2026-08-15",
    headings: tuple[str, ...] = ("Overview", "Summary"),
    tags: tuple[str, ...] = (),
) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    heading_text = "\n\n".join(f"# {heading}" for heading in headings)
    tag_text = "\n".join(f"  - {tag}" for tag in tags) or " []"
    path.write_text(
        "---\n"
        f"title: {title!r}\n"
        f"description: {description!r}\n"
        f"category: {category!r}\n"
        f"difficulty: {difficulty!r}\n"
        f"last_updated: {last_updated!r}\n"
        "tags:\n"
        f"{tag_text}\n"
        "systems: []\n"
        "aliases: []\n"
        "acronyms: []\n"
        "references: []\n"
        "---\n\n"
        f"{heading_text}\n",
        encoding="utf-8",
    )
    return path


class ValidateCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            ["validate", *arguments, "--root", str(self.root)],
        )

    def test_validate_appears_in_help(self) -> None:
        result = self.runner.invoke(app, ["--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("validate", result.output)

    def test_clean_repository_exits_zero_and_is_read_only(self) -> None:
        source = write_article(self.root, "index.md")
        original = source.read_bytes()

        result = self.invoke()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Articles Checked", result.output)
        self.assertIn("Total Issues", result.output)
        self.assertNotIn("Errors\n", result.output)
        self.assertNotIn("Warnings\n", result.output)
        self.assertEqual(source.read_bytes(), original)

    def test_warnings_only_exit_zero_and_display_warnings(self) -> None:
        write_article(self.root, "topic.md", headings=("Overview",))

        result = self.invoke()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Warnings", result.output)
        self.assertIn("Missing heading 'Summary'", result.output)

    def test_invalid_filename_exits_one_and_displays_errors(self) -> None:
        write_article(self.root, "Invalid_Name.md")

        result = self.invoke()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Errors", result.output)
        self.assertIn("Invalid filename: Invalid_Name.md", result.output)

    def test_duplicate_filename_exits_one(self) -> None:
        write_article(self.root, "alpha/repeated.md")
        write_article(self.root, "beta/repeated.md")

        result = self.invoke()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Duplicate filename: repeated.md", result.output)

    def test_missing_metadata_exits_one_through_metadata_validator(self) -> None:
        write_article(self.root, "index.md", description="")

        result = self.invoke()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Missing description", result.output)

    def test_mixed_issues_are_counted_by_severity(self) -> None:
        write_article(
            self.root,
            "Invalid_Name.md",
            title="",
            description="",
            category="",
            difficulty="",
            last_updated="",
            headings=(),
            tags=("duplicate", "duplicate"),
        )

        result = self.invoke()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Articles Checked: 1", result.output)
        self.assertIn("Errors      : 6", result.output)
        self.assertIn("Warnings    : 4", result.output)
        self.assertIn("Total Issues: 10", result.output)
        self.assertIn("Missing description", result.output)
        self.assertIn("Missing heading 'Overview'", result.output)
        self.assertIn("Duplicate tags", result.output)

    def test_explicit_root_works_from_another_current_directory(self) -> None:
        write_article(self.root, "index.md")

        with tempfile.TemporaryDirectory() as other_directory:
            original_directory = Path.cwd()
            os.chdir(other_directory)
            try:
                result = self.invoke()
            finally:
                os.chdir(original_directory)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Articles Checked", result.output)
