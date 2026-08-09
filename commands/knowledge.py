"""
BridgeLab Toolkit
Knowledge Command
"""

from pathlib import Path

from config import (
    OUTPUT,
)

from core.repository import Repository

from knowledge.extractor import EntityExtractor
from knowledge.validator import KnowledgeValidator

from reporting.base_reporter import BaseReporter


def run(root: Path):

    # ---------------------------------------------------------
    # Repository
    # ---------------------------------------------------------

    repository = Repository(root)

    repository.build()

    # ---------------------------------------------------------
    # Extract
    # ---------------------------------------------------------

    extractor = EntityExtractor()

    entities = extractor.extract(

        repository.articles

    )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    validator = KnowledgeValidator()

    issues = validator.validate(

        entities

    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    reporter = BaseReporter(

        "Knowledge Validation"

    )

    reporter.report(

        columns=[

            "Severity",

            "Article",

            "Category",

            "Message",

        ],

        rows=reporter.issue_rows(

            issues

        ),

    )

    reporter.summary(

        Errors=sum(

            issue.severity == "Error"

            for issue in issues

        ),

        Warnings=sum(

            issue.severity == "Warning"

            for issue in issues

        ),

        Total=len(issues),

    )

    reporter.export(

        [

            {

                "severity": issue.severity,

                "article": issue.article,

                "category": issue.category,

                "message": issue.message,

            }

            for issue in issues

        ],

        OUTPUT / "knowledge_validation.json",

    )
