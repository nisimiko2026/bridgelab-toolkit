from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath

from core.document_roles import DocumentRole, classify_document_role
from core.repository import Repository


DOMAIN_INDEXES = {
    "bidding/bidding-index.md",
    "duplicates/duplicates-index.md",
    "play/play-index.md",
    "references/references-index.md",
}

STRUCTURAL_INDEXES = {
    "bidding/bidding-index.md",
    "bidding/convention-cards/convention-cards-index.md",
    "bidding/conventions/competitive/bid-competitive-index.md",
    "bidding/conventions/conventions-index.md",
    "bidding/conventions/defensive-methods/bid-defence-index.md",
    "bidding/conventions/doubles/doubles-index.md",
    "bidding/conventions/game-invitations/guides/index-guides.md",
    "bidding/conventions/game-invitations/invitations-index.md",
    "bidding/conventions/opening-bids/index-opening-bids.md",
    "bidding/conventions/relay/relay-index.md",
    "bidding/conventions/responses/responses-index.md",
    "bidding/conventions/slam-conventions/slam-bid-index.md",
    "bidding/conventions/transfers/transfers-index.md",
    "bidding/natural-bids/opening-bids/natural-opening-bids-index.md",
    "bidding/natural-bids/rebids/natural-rebids-index.md",
    "bidding/natural-bids/responses/natural-responses-index.md",
    "bidding/principles/bidding-fundamentals/index-fundamental-bids.md",
    "bidding/principles/partnership/partnership-principles-index.md",
    "bidding/principles/principles-index.md",
    "bidding/systems/systems-index.md",
    "bridge-lab-index.md",
    "duplicates/duplicates-index.md",
    "play/counting/counting-index.md",
    "play/declarer-play/coups/coups-index.md",
    "play/declarer-play/deceptive-play/index-deceptive-play.md",
    "play/declarer-play/elimination-and-endplays/elimination-index.md",
    "play/declarer-play/general-techniques/finesses/finesses-index.md",
    "play/declarer-play/general-techniques/general-techniques-index.md",
    "play/declarer-play/index-declarer-play.md",
    "play/declarer-play/notrump-play/index-notrump-play.md",
    "play/declarer-play/planning/planning-index.md",
    "play/declarer-play/probability/probability-index.md",
    "play/declarer-play/squeezes/squeezes-index.md",
    "play/declarer-play/trump-play/index-trump-play.md",
    "play/defence/counting/defence-counting-index.md",
    "play/defence/deception/defence-deception-index.md",
    "play/defence/endgame-defence/endgame-defence-index.md",
    "play/defence/index-defence.md",
    "play/defence/opening-leads/honor-leads/index-honor-leads.md",
    "play/defence/opening-leads/opening-leads-index.md",
    "play/defence/planning/defence-planning-index.md",
    "play/defence/signaling/signaling-index.md",
    "play/defence/techniques/defence-techniques-index.md",
    "play/play-index.md",
    "play/principles/play-principles-index.md",
    "references/references-index.md",
}


class DocumentRoleTests(unittest.TestCase):
    def test_structural_filename_forms_at_each_depth(self) -> None:
        for filename in ("foo-index.md", "index-foo.md", "index.md"):
            with self.subTest(filename=filename, depth="root"):
                self.assertEqual(
                    classify_document_role(filename), DocumentRole.SECTION_INDEX
                )
            with self.subTest(filename=filename, depth="domain"):
                self.assertEqual(
                    classify_document_role(f"domain/{filename}"),
                    DocumentRole.DOMAIN_INDEX,
                )
            with self.subTest(filename=filename, depth="nested"):
                self.assertEqual(
                    classify_document_role(f"domain/topic/{filename}"),
                    DocumentRole.SECTION_INDEX,
                )

    def test_non_structural_filename_forms_are_articles(self) -> None:
        for filename in (
            "fooindex.md",
            "indexing.md",
            "indexical.md",
            "foo-indexing.md",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(
                    classify_document_role(filename), DocumentRole.ARTICLE
                )

    def test_non_markdown_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Markdown"):
            classify_document_role("index-card.md.backup")

    def test_matching_is_case_insensitive(self) -> None:
        self.assertEqual(
            classify_document_role("DOMAIN/INDEX-FOO.MD"),
            DocumentRole.DOMAIN_INDEX,
        )

    def test_windows_and_posix_paths_are_equivalent(self) -> None:
        expected = DocumentRole.SECTION_INDEX
        for value in (
            "domain/topic/index.md",
            r"domain\topic\index.md",
            PurePosixPath("domain/topic/index.md"),
            PureWindowsPath(r"domain\topic\index.md"),
        ):
            with self.subTest(value=value):
                self.assertEqual(classify_document_role(value), expected)

    def test_absolute_drive_unc_and_traversal_paths_are_rejected(self) -> None:
        invalid = (
            "/absolute/path.md",
            r"C:\absolute\path.md",
            "C:/absolute/path.md",
            r"\\server\share\index.md",
            "../index.md",
            "domain/../index.md",
            "C:index.md",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                classify_document_role(value)

    def test_empty_and_noncanonical_paths_are_rejected(self) -> None:
        for value in ("", ".", "domain//index.md", "./index.md", "index.md/"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                classify_document_role(value)

    def test_unknown_domains_require_no_registration(self) -> None:
        self.assertEqual(
            classify_document_role("new-domain/new-domain-index.md"),
            DocumentRole.DOMAIN_INDEX,
        )
        self.assertEqual(
            classify_document_role("new-domain/topic/index.md"),
            DocumentRole.SECTION_INDEX,
        )


class LiveDocumentRoleCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.knowledge = Path(__file__).resolve().parents[2] / "knowledge"
        cls.articles = Repository(cls.knowledge).build()
        cls.by_path = {
            article.relative_path.as_posix(): classify_document_role(
                article.relative_path
            )
            for article in cls.articles
        }

    def test_exact_live_census(self) -> None:
        self.assertEqual(len(self.by_path), 446)
        self.assertEqual(
            Counter(self.by_path.values()),
            {
                DocumentRole.ARTICLE: 400,
                DocumentRole.SECTION_INDEX: 42,
                DocumentRole.DOMAIN_INDEX: 4,
            },
        )

    def test_exact_domain_index_set(self) -> None:
        self.assertEqual(
            {path for path, role in self.by_path.items() if role is DocumentRole.DOMAIN_INDEX},
            DOMAIN_INDEXES,
        )

    def test_exact_complete_structural_index_set(self) -> None:
        self.assertEqual(
            {path for path, role in self.by_path.items() if role is not DocumentRole.ARTICLE},
            STRUCTURAL_INDEXES,
        )
        self.assertEqual(len(STRUCTURAL_INDEXES), 46)

    def test_deferred_play_roles(self) -> None:
        expected = {
            "play/play-index.md": DocumentRole.DOMAIN_INDEX,
            "play/counting/counting-index.md": DocumentRole.SECTION_INDEX,
            "play/declarer-play/index-declarer-play.md": DocumentRole.SECTION_INDEX,
            "play/declarer-play/planning/planning-index.md": DocumentRole.SECTION_INDEX,
            "play/declarer-play/trump-play/index-trump-play.md": DocumentRole.SECTION_INDEX,
            "play/defence/index-defence.md": DocumentRole.SECTION_INDEX,
        }
        self.assertEqual({path: self.by_path[path] for path in expected}, expected)

    def test_root_reference_roles(self) -> None:
        expected = {
            "acronyms.md": DocumentRole.ARTICLE,
            "bibliography.md": DocumentRole.ARTICLE,
            "bridge-lab-index.md": DocumentRole.SECTION_INDEX,
            "glossary.md": DocumentRole.ARTICLE,
        }
        self.assertEqual({path: self.by_path[path] for path in expected}, expected)

    def test_role_is_independent_of_all_metadata(self) -> None:
        article = next(
            item for item in self.articles
            if item.relative_path.as_posix() == "play/play-index.md"
        )
        before = classify_document_role(article.relative_path)
        article.metadata.category = "unrelated"
        article.metadata.subcategory = "unrelated"
        article.metadata.tags[:] = ["unrelated"]
        article.metadata.title = "Unrelated"
        self.assertEqual(classify_document_role(article.relative_path), before)

    def test_classification_is_deterministic(self) -> None:
        first = tuple(sorted(self.by_path.items()))
        second = tuple(
            sorted(
                (path, classify_document_role(path))
                for path in self.by_path
            )
        )
        self.assertEqual(first, second)
