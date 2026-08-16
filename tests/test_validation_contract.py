from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.models import Article, Heading, Issue
from core.repository import Repository
from metadata.validator import MetadataValidator
from validator.directory_check import DirectoryCheck
from validator.duplicate_check import DuplicateCheck
from validator.filename_check import FilenameCheck
from validator.heading_check import HeadingCheck
from validator.validator import RepositoryValidator


def article(
    relative_path: str,
    *,
    filename: str | None = None,
    headings: list[str] | None = None,
) -> Article:
    path = Path(relative_path)
    item = Article(
        id=path.with_suffix("").as_posix(),
        filename=filename or path.name,
        path=path,
        relative_path=path,
        directory=path.parent.as_posix(),
    )
    item.headings = [Heading(level=1, title=title) for title in headings or []]
    return item


def article_with_complete_metadata(
    relative_path: str,
    difficulty: str,
) -> Article:
    item = article(relative_path)
    item.metadata.title = "Article"
    item.metadata.description = "A sufficiently long description for validation."
    item.metadata.category = "Conventions"
    item.metadata.difficulty = difficulty
    item.metadata.last_updated = "2026-08-15"
    return item


class LegacyValidationContractTests(unittest.TestCase):
    def assert_issues(self, issues: list[Issue]) -> None:
        self.assertTrue(issues)
        self.assertTrue(all(isinstance(issue, Issue) for issue in issues))

    def test_filename_check_returns_canonical_issue(self) -> None:
        issues = FilenameCheck().run(
            [article("bidding/Invalid_Name.md")]
        )

        self.assert_issues(issues)
        self.assertEqual(issues[0].severity, "Error")
        self.assertEqual(issues[0].article, "bidding/Invalid_Name.md")
        self.assertEqual(issues[0].category, "Filename")
        self.assertEqual(
            issues[0].message,
            "Invalid filename: Invalid_Name.md",
        )

    def test_duplicate_filename_check_returns_stable_subject(self) -> None:
        issues = DuplicateCheck().run(
            [
                article("zeta/repeated.md"),
                article("alpha/repeated.md"),
            ]
        )

        self.assert_issues(issues)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "Error")
        self.assertEqual(issues[0].article, "alpha/repeated.md")
        self.assertEqual(issues[0].category, "Filename")
        self.assertEqual(
            issues[0].message,
            "Duplicate filename: repeated.md",
        )

    def test_heading_check_reports_missing_overview_and_summary(self) -> None:
        issues = HeadingCheck().run([article("guide/article.md")])

        self.assert_issues(issues)
        self.assertEqual(
            [(issue.severity, issue.article, issue.category, issue.message)
             for issue in issues],
            [
                (
                    "Warning",
                    "guide/article.md",
                    "Heading",
                    "Missing heading 'Overview'",
                ),
                (
                    "Warning",
                    "guide/article.md",
                    "Heading",
                    "Missing heading 'Summary'",
                ),
            ],
        )

    def test_directory_check_reports_missing_index_without_absolute_path(self) -> None:
        issues = DirectoryCheck().run([article("guide/article.md")])

        self.assert_issues(issues)
        self.assertEqual(issues[0].severity, "Warning")
        self.assertEqual(issues[0].article, "guide")
        self.assertEqual(issues[0].category, "Directory")
        self.assertEqual(issues[0].message, "No index file")
        self.assertFalse(Path(issues[0].article).is_absolute())

    def test_repository_validator_aggregates_issues_without_yaml_checks(self) -> None:
        first = article("alpha/Invalid_Name.md")
        second = article("beta/Invalid_Name.md")

        issues = RepositoryValidator([first, second]).validate()

        self.assert_issues(issues)
        self.assertTrue(all(isinstance(issue, Issue) for issue in issues))
        self.assertTrue(
            any(issue.message == "Duplicate filename: Invalid_Name.md"
                for issue in issues)
        )
        self.assertFalse(
            any("missing title" in issue.message.lower()
                or "missing description" in issue.message.lower()
                for issue in issues)
        )

    def test_validation_does_not_mutate_markdown_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown = root / "guide" / "article.md"
            markdown.parent.mkdir()
            original = "# Overview\n"
            markdown.write_text(original, encoding="utf-8")

            articles = Repository(root).build()
            RepositoryValidator(articles).validate()

            self.assertEqual(markdown.read_text(encoding="utf-8"), original)

    def test_yaml_null_metadata_values_are_missing_not_literal_none(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown = root / "index.md"
            original = (
                "---\n"
                "title: null\n"
                "description: null\n"
                "category: null\n"
                "subcategory: null\n"
                "difficulty: null\n"
                "last_updated: null\n"
                "status: null\n"
                "tags: []\n"
                "systems: []\n"
                "aliases: []\n"
                "acronyms: []\n"
                "references: []\n"
                "---\n"
                "# Overview\n\n# Summary\n"
            )
            markdown.write_text(original, encoding="utf-8")

            article = Repository(root).build()[0]
            issues = MetadataValidator().validate([article])

            self.assertEqual(article.metadata.title, "")
            self.assertEqual(article.metadata.description, "")
            self.assertEqual(article.metadata.difficulty, "")
            self.assertFalse(
                any(issue.message == "Invalid difficulty" for issue in issues)
            )
            self.assertFalse(
                any(issue.message == "Description too short" for issue in issues)
            )
            self.assertEqual(
                {
                    issue.message
                    for issue in issues
                    if issue.severity == "Error"
                },
                {
                    "Missing title",
                    "Missing description",
                    "Missing category",
                    "Missing difficulty",
                    "Missing last_updated",
                },
            )
            self.assertEqual(markdown.read_text(encoding="utf-8"), original)

    def test_literal_none_metadata_values_are_treated_as_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown = root / "index.md"
            markdown.write_text(
                "---\n"
                "title: Article\n"
                "description: None\n"
                "category: Conventions\n"
                "difficulty: None\n"
                "last_updated: '2026-08-15'\n"
                "tags: []\n"
                "systems: []\n"
                "aliases: []\n"
                "acronyms: []\n"
                "references: []\n"
                "---\n"
                "# Overview\n\n# Summary\n",
                encoding="utf-8",
            )

            article = Repository(root).build()[0]
            issues = MetadataValidator().validate([article])

            self.assertEqual(article.metadata.description, "")
            self.assertEqual(article.metadata.difficulty, "")
            self.assertEqual(
                {
                    issue.message
                    for issue in issues
                    if issue.severity == "Error"
                },
                {"Missing description", "Missing difficulty"},
            )
            self.assertFalse(
                any(issue.message == "Invalid difficulty" for issue in issues)
            )
            self.assertFalse(
                any(issue.message == "Description too short" for issue in issues)
            )

    def test_metadata_validator_uses_repository_relative_issue_subjects(self) -> None:
        issues = MetadataValidator().validate(
            [article("nested/topic.md")]
        )

        self.assert_issues(issues)
        self.assertTrue(
            all(issue.article == "nested/topic.md" for issue in issues)
        )

    def test_difficulty_policy_for_generated_reference_and_index_documents(self) -> None:
        generated = article_with_complete_metadata("acronyms.md", "")
        reference = article_with_complete_metadata("references/terms.md", "")
        index = article_with_complete_metadata(
            "guide/topic-index.md",
            "Beginner to Expert",
        )
        substantive = article_with_complete_metadata(
            "guide/topic.md",
            "Beginner to Expert",
        )
        missing_index = article_with_complete_metadata(
            "guide/index.md",
            "",
        )

        generated_issues = MetadataValidator().validate([generated])
        reference_issues = MetadataValidator().validate([reference])
        index_issues = MetadataValidator().validate([index])
        substantive_issues = MetadataValidator().validate([substantive])
        missing_index_issues = MetadataValidator().validate([missing_index])

        self.assertFalse(
            any(issue.category == "difficulty" for issue in generated_issues)
        )
        self.assertFalse(
            any(issue.category == "difficulty" for issue in reference_issues)
        )
        self.assertFalse(
            any(issue.message == "Invalid difficulty" for issue in index_issues)
        )
        self.assertTrue(
            any(
                issue.message == "Invalid difficulty"
                for issue in substantive_issues
            )
        )
        self.assertTrue(
            any(
                issue.message == "Missing difficulty"
                for issue in missing_index_issues
            )
        )
