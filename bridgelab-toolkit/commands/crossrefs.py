"""
BridgeLab Toolkit
Cross-Reference Command
"""

from pathlib import Path

from rich.console import Console

from config import (
    CROSS_REFERENCE_JSON,
)

from core.repository import Repository

from relationships.analyzer import RelationshipAnalyzer
from relationships.graph import RelationshipGraph
from relationships.matcher import RelationshipMatcher
from relationships.generator import CrossReferenceGenerator
from relationships.validator import CrossReferenceValidator

from reporting.cross_reference_reporter import CrossReferenceReporter


console = Console()


def run(root: Path):

    console.print()

    console.print(
        "[bold cyan]Cross-Reference Analysis[/bold cyan]"
    )

    console.print()

    # ---------------------------------------------------------
    # Build repository
    # ---------------------------------------------------------

    repository = Repository(root)

    repository.build()

    # ---------------------------------------------------------
    # Analyze relationships
    # ---------------------------------------------------------

    analyzer = RelationshipAnalyzer()

    relationships = analyzer.analyze(
        repository.articles
    )

    # ---------------------------------------------------------
    # Build graph
    # ---------------------------------------------------------

    graph = RelationshipGraph()

    graph.build(
        relationships
    )

    # ---------------------------------------------------------
    # Match relationships
    # ---------------------------------------------------------

    matcher = RelationshipMatcher()

    matcher.match(
        relationships
    )

    # ---------------------------------------------------------
    # Generate cross references
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

    reporter = CrossReferenceReporter()

    reporter.report(
        issues
    )

    reporter.export(

        issues,

        CROSS_REFERENCE_JSON,

    )

    console.print()

    console.print(
        "[green]Cross-reference analysis complete.[/green]"
    )
