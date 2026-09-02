import json
import tempfile
import unittest
from pathlib import Path

from generators.systems_applicability_audit import classify, generate


class SystemsApplicabilityAuditTests(unittest.TestCase):
    def test_uses_canonical_document_roles(self):
        structural = (
            "foo-index.md",
            "index-foo.md",
            "index.md",
            "domain/domain-index.md",
            "domain/topic/topic-index.md",
            "DOMAIN/INDEX-FOO.MD",
            "bidding/systems/future-index.md",
            "bidding/systems/index-future.md",
        )
        for relative in structural:
            with self.subTest(relative=relative):
                self.assertEqual(
                    classify(relative, ["acol"]),
                    ("high", "index_page_reference_labels", ["acol"]),
                )

        for relative in ("fooindex.md", "indexing.md", "foo-indexing.md"):
            with self.subTest(relative=relative):
                self.assertEqual(
                    classify(relative, ["acol"]),
                    (
                        "manual",
                        "limited_assignment_set_requires_semantic_review",
                        [],
                    ),
                )

    def test_systems_index_behavior_is_not_filename_specific(self):
        expected = ("high", "index_page_reference_labels", ["acol"])
        self.assertEqual(classify("bidding/systems/systems-index.md", ["acol"]), expected)
        self.assertEqual(classify("bidding/systems/other-index.md", ["acol"]), expected)

    def test_classifies_profiles_bundles_and_small_sets(self):
        articles = [
            {"relative_path": "bidding/systems/acol.md", "metadata": {"title": "Acol", "systems": ["acol", "precision"]}},
            {"relative_path": "bidding/topic.md", "metadata": {"title": "Topic", "systems": ["acol", "precision", "sayc", "standard american"]}},
            {"relative_path": "bidding/other.md", "metadata": {"title": "Other", "systems": ["sayc"]}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database, json_out, md_out = root / "db.json", root / "audit.json", root / "audit.md"
            database.write_text(json.dumps(articles), encoding="utf-8")
            audit = generate(database, json_out, md_out)
            self.assertEqual(audit["summary"]["high_confidence_removals"], 1)
            self.assertEqual(audit["summary"]["medium_confidence_removals"], 4)
            self.assertEqual(audit["summary"]["manual_review_assignments"], 1)
            self.assertTrue(json_out.exists())
            self.assertIn("No source article was modified", md_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
