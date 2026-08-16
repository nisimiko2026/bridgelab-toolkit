import unittest

from generators.systems_manual_review import REMOVALS


class SystemsManualReviewTests(unittest.TestCase):
    def test_review_contains_24_exact_removals(self):
        self.assertEqual(sum(len(values) for values in REMOVALS.values()), 24)
        self.assertEqual(len(REMOVALS), 13)


if __name__ == "__main__":
    unittest.main()
