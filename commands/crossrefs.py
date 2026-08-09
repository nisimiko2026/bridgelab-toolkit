"""
BridgeLab Toolkit
Cross-Reference Command
"""

from pathlib import Path

from rich.console import Console

from config import CROSS_REFERENCE_JSON

from core.repository import Repository

from relationships.analyzer import RelationshipAnalyzer
from relationships.graph import RelationshipGraph
from relationships.matcher import RelationshipMatcher
from relationships.generator import CrossReferenceGenerator
from relationships.validator import CrossReferenceValidator

from reporting.base_reporter import BaseReporter


console = Console()


def run(root: Path):

    console.print()
    console.print("[bold cyan]Cross-Reference Analysis[/bold cyan]")
    console.print()

    # ---------------------------------------------------------
    # Build Repository
    # ---------------------------------------------------------

    repository = Repository(root)

    repository.build()

    # ---------------------------------------------------------
    # Analyze Relationships
    # ---------------------------------------------------------

    analyzer = RelationshipAnalyzer()

    relationships = analyzer.analyze(

        repository.articles

    )

    # ---------------------------------------------------------
    # Build Graph
    # ---------------------------------------------------------

    graph = RelationshipGraph()

    graph.build(

        relationships

    )

    # ---------------------------------------------------------
    # Match Relationships
    # ---------------------------------------------------------

    matcher = RelationshipMatcher()

    matcher.match(

        relationships

    )

    # ---------------------------------------------------------
    # Generate Cross References
    # ---------------------------------------------------------

    generator = CrossReferenceGenerator()

    references = generator.generate(

        relationships

    )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    validator = CrossReferenceValidator()

    issues = validator.validate(

        references

    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    reporter = BaseReporter(

        "Cross-Reference Validation"

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

        CROSS_REFERENCE_JSON,

    )

    console.print()

    console.print(

        "[green]Cross-reference analysis complete.[/green]"

    )
