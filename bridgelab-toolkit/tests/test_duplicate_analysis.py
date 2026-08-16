from __future__ import annotations

import unittest

from analysis.duplicates import DuplicateAnalyzer


class DuplicateAnalysisTests(unittest.TestCase):
    def test_normalization_preserves_suit_identity(self) -> None:
        keys = {
            DuplicateAnalyzer._normalize(title)
            for title in (
                "1♣ Opening Bid",
                "1♦ Opening Bid",
                "1♥ Opening Bid",
                "1♠ Opening Bid",
            )
        }

        self.assertEqual(len(keys), 4)

    def test_normalization_still_groups_formatting_variants(self) -> None:
        self.assertEqual(
            DuplicateAnalyzer._normalize("Transfer-Bids"),
            DuplicateAnalyzer._normalize("Transfer Bids"),
        )
