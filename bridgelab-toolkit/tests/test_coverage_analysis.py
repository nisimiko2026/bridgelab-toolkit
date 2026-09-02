from __future__ import annotations

import unittest
from types import SimpleNamespace

from analysis.coverage import CoverageAnalyzer


class CoverageAnalysisTests(unittest.TestCase):
    def test_report_contains_all_summary_counts(self) -> None:
        complete = SimpleNamespace(
            metadata=SimpleNamespace(
                category="Play",
                systems=["Natural"],
                tags=["planning"],
                references=["play/play-index"],
                description="Complete article.",
            )
        )
        missing = SimpleNamespace(
            metadata=SimpleNamespace(
                category="",
                systems=[],
                tags=[],
                references=[],
                description="",
            )
        )
        analyzer = CoverageAnalyzer(
            SimpleNamespace(articles=[complete, missing])
        )

        report = analyzer.report()

        self.assertEqual(len(report), 6)
        self.assertIn("Articles                  2", report)
        self.assertIn("Missing Categories        1", report)
        self.assertIn("Missing Systems           1", report)
        self.assertIn("Missing Tags              1", report)
        self.assertIn("Missing References        1", report)
        self.assertIn("Missing Descriptions      1", report)
