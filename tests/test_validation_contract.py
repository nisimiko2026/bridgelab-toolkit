from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.models import Article, Heading, Issue
from core.repository import Repository
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
