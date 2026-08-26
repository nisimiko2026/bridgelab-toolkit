from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from main import app
from core.repository import Repository
from metadata.audit import (
    APPROVED_CATEGORY_EXCEPTIONS,
    TITLE_H1_PRESENTATIONAL_SUFFIXES,
    MetadataAuditor,
)
from metadata.validator import MetadataValidator

FIELDS = {
    "title": "Article",
    "description": "A sufficiently long description for metadata auditing.",
    "category": "bidding",
    "subcategory": "conventions",
    "difficulty": "Intermediate",
    "tags": ["bidding"],
    "systems": [],
    "aliases": [],
    "acronyms": [],
    "references": [],
    "last_updated": "2026-08-17",
    "status": "Draft",
}

REVIEWED_PRESENTATIONAL_SUFFIX_PATHS = frozenset(
    {
        "bidding/conventions/slam-conventions/last-train.md",
        "bidding/conventions/slam-conventions/serious-3nt.md",
        "bidding/systems/carrot-club.md",
        "bidding/systems/culbertson.md",
        "play/counting/counting-losers.md",
        "play/counting/counting-winners.md",
        "play/declarer-play/coups/bath-coup.md",
        "play/declarer-play/coups/coup-en-passant.md",
        "play/declarer-play/coups/merrimac-coup.md",
        "play/declarer-play/coups/scissors-coup.md",
        "play/declarer-play/coups/trump-coup.md",
        "play/declarer-play/coups/vienna-coup.md",
        "play/declarer-play/general-techniques/avoidance-play.md",
        "play/declarer-play/general-techniques/ducking.md",
        "play/declarer-play/general-techniques/finesses/deep-finesse.md",
        "play/declarer-play/general-techniques/finesses/double-finesse.md",
        "play/declarer-play/general-techniques/finesses/finesse.md",
        "play/declarer-play/general-techniques/finesses/ruffing-finesse.md",
        "play/declarer-play/general-techniques/safety-play.md",
        "play/declarer-play/probability/percentage-plays.md",
        "play/declarer-play/squeezes/double-squeeze.md",
        "play/declarer-play/squeezes/strip-squeeze.md",
        "play/declarer-play/trump-play/dummy-reversal.md",
        "play/defence/deception/false-carding.md",
        "play/defence/planning/entry-killing.md",
        "play/defence/signaling/italian-discard.md",
        "play/defence/techniques/surrounding-play.md",
        "play/defence/techniques/uppercut.md",
    }
)


class MetadataAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.systems = self.base / "systems.yaml"
        self.taxonomy = self.base / "taxonomy.yaml"
        self.systems.write_text("- precision\n- sayc\n", encoding="utf-8")
        self.taxonomy.write_text(
            "bidding:\n  conventions:\n    - stayman\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(
        self,
        relative: str,
        data: dict | None = None,
        *,
        raw: str = "",
        heading: str = "Article",
    ) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if raw:
            content = raw
        else:
            content = (
                "---\n"
                + yaml.safe_dump(data or FIELDS, sort_keys=False)
                + f"---\n# {heading}\n"
            )
        path.write_text(content, encoding="utf-8")
        return path

    def audit(self):
        return MetadataAuditor(
            self.root, systems_file=self.systems, taxonomy_file=self.taxonomy
        ).audit()

    def test_raw_values_distinguish_missing_null_empty_literal_none_and_types(
        self,
    ) -> None:
        data = dict(FIELDS)
        del data["description"]
        data["subcategory"] = None
        data["difficulty"] = "None"
        data["status"] = ""
        data["tags"] = "not-a-list"
        self.write("bidding/topic.md", data)

        _, findings = self.audit()
        rules = {(item.field, item.rule, item.severity) for item in findings}

        self.assertIn(("description", "field.missing", "Error"), rules)
        self.assertIn(("subcategory", "value.yaml-null", "Warning"), rules)
        self.assertIn(("difficulty", "value.literal-none", "Warning"), rules)
        self.assertIn(("status", "value.empty", "Error"), rules)
        self.assertIn(("tags", "type.list", "Error"), rules)

    def test_rule_families_cover_lists_systems_dates_references_and_status(
        self,
    ) -> None:
        target = dict(FIELDS)
        target.update(
            tags=["none", "bidding/path", "dup", "Dup", " spaced "],
            systems=["Precision", "unknown"],
            references=["Missing.md", "bidding/topic"],
            last_updated="2026-02-30",
            status="Advanced",
        )
        self.write("bidding/topic.md", target, heading="Different H1")

        _, findings = self.audit()
        rules = {item.rule for item in findings}

        self.assertTrue(
            {
                "tags.sentinel",
                "tags.structural-form",
                "list.case-duplicate",
                "list.whitespace",
                "systems.noncanonical",
                "systems.unknown",
                "references.syntax",
                "references.missing-target",
                "references.self",
                "date.invalid",
                "status.difficulty-value",
                "title.h1-mismatch",
            }.issubset(rules)
        )

    def test_exact_presentational_suffixes_emit_one_dedicated_info_finding(self) -> None:
        self.assertEqual(
            TITLE_H1_PRESENTATIONAL_SUFFIXES,
            (" Technique", " System", " Convention"),
        )
        cases = {
            "bidding/technique.md": ("Finesse", "Finesse Technique"),
            "bidding/system.md": ("Culbertson", "Culbertson System"),
            "bidding/convention.md": ("Serious 3NT", "Serious 3NT Convention"),
            "bidding/unicode.md": (
                "Système Français",
                "Système Français System",
            ),
            "play/coup.md": ("Coup en Passant", "Coup en Passant Technique"),
        }
        for article, (title, heading) in cases.items():
            data = dict(FIELDS)
            data["title"] = title
            self.write(article, data, heading=heading)

        _, findings = self.audit()
        title_findings = [item for item in findings if item.field == "title"]

        self.assertEqual(len(title_findings), len(cases))
        self.assertEqual(
            {item.article for item in title_findings},
            set(cases),
        )
        self.assertTrue(
            all(
                item.rule == "title.h1-presentational-suffix"
                and item.severity == "Info"
                and "approved presentation suffix" in item.message
                for item in title_findings
            )
        )

    def test_presentational_suffix_near_misses_remain_generic(self) -> None:
        cases = {
            "bidding/case-prefix.md": ("Serious 3Nt", "Serious 3NT Convention"),
            "bidding/punctuation-prefix.md": (
                "Coup En Passant",
                "Coup en Passant Technique",
            ),
            "bidding/extra-space.md": ("Finesse", "Finesse  Technique"),
            "bidding/lower-suffix.md": ("Finesse", "Finesse technique"),
            "bidding/unapproved.md": ("Finesse", "Finesse Method"),
            "bidding/parenthetical.md": ("EHAA", "EHAA (Every Hand An Adventure)"),
            "bidding/trailing.md": (
                "Finesse",
                "Finesse Technique for Declarer",
            ),
            "bidding/changed-prefix.md": ("Simple Squeeze", "Squeeze Technique"),
        }
        for article, (title, heading) in cases.items():
            data = dict(FIELDS)
            data["title"] = title
            self.write(article, data, heading=heading)

        _, findings = self.audit()
        title_findings = [item for item in findings if item.field == "title"]

        self.assertEqual(len(title_findings), len(cases))
        self.assertEqual({item.article for item in title_findings}, set(cases))
        self.assertTrue(all(item.rule == "title.h1-mismatch" for item in title_findings))

    def test_presentational_suffix_role_boundaries_and_missing_h1_behavior(self) -> None:
        data = dict(FIELDS)
        data["title"] = "Example"
        self.write("bidding/topic.md", data, heading="Example Technique")
        self.write("bidding/topic-index.md", data, heading="Example Technique")
        self.write("bidding/bidding-index.md", data, heading="Example Technique")
        self.write(
            "bidding/missing.md",
            raw="---\n" + yaml.safe_dump(data, sort_keys=False) + "---\nBody only.\n",
        )

        _, findings = self.audit()
        title_findings = {
            item.article: item.rule for item in findings if item.field == "title"
        }

        self.assertEqual(
            title_findings,
            {
                "bidding/topic.md": "title.h1-presentational-suffix",
                "bidding/topic-index.md": "title.h1-mismatch",
                "bidding/bidding-index.md": "title.h1-mismatch",
            },
        )
        self.assertNotIn("bidding/missing.md", title_findings)

    def test_historical_title_defects_remain_generic_mismatches(self) -> None:
        cases = {
            "bidding/batch1.md": ("Sos Redouble", "SOS Redouble"),
            "bidding/batch2.md": (
                "Lead Directing Double",
                "Lead-Directing Double",
            ),
            "bidding/batch3.md": ("Preemptive.Raise", "Objectives"),
            "bidding/pre-batch7-nt.md": (
                "Serious 3Nt",
                "Serious 3NT Convention",
            ),
            "play/pre-batch7-coup.md": (
                "Coup En Passant",
                "Coup en Passant Technique",
            ),
        }
        for article, (title, heading) in cases.items():
            data = dict(FIELDS)
            data["title"] = title
            self.write(article, data, heading=heading)

        _, findings = self.audit()
        title_findings = [item for item in findings if item.field == "title"]

        self.assertEqual({item.article for item in title_findings}, set(cases))
        self.assertTrue(all(item.rule == "title.h1-mismatch" for item in title_findings))

    def test_live_presentational_suffix_census_and_audit_accounting(self) -> None:
        project = Path(__file__).resolve().parents[1]
        knowledge = project.parent / "knowledge"
        auditor = MetadataAuditor(
            knowledge,
            systems_file=project / "data/systems.yaml",
            taxonomy_file=project / "data/taxonomy.yaml",
        )

        records, first = auditor.audit()
        _, second = auditor.audit()
        presentation = {
            item.article
            for item in first
            if item.rule == "title.h1-presentational-suffix"
        }
        rules = [item.rule for item in first]

        self.assertEqual(len(records), 446)
        self.assertEqual(presentation, set(REVIEWED_PRESENTATIONAL_SUFFIX_PATHS))
        self.assertEqual(len(presentation), 28)
        self.assertEqual(rules.count("title.h1-mismatch"), 60)
        self.assertEqual(rules.count("title.h1-presentational-suffix"), 28)
        self.assertEqual(len(first), 274)
        self.assertEqual(sum(item.severity == "Info" for item in first), 274)
        self.assertFalse(any(item.severity in {"Error", "Warning"} for item in first))
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first, key=type(first[0]).sort_key))

    def test_status_has_no_provisional_vocabulary_rule(self) -> None:
        paths = []
        for filename, status in (
            ("draft.md", "Draft"),
            ("standard.md", "Standard"),
            ("reviewed-locally.md", "Reviewed Locally"),
        ):
            data = dict(FIELDS)
            data["status"] = status
            paths.append(self.write(f"bidding/{filename}", data))
        before = {path: path.read_bytes() for path in paths}

        _, findings = self.audit()

        self.assertFalse(any(item.rule == "status.provisional" for item in findings))
        self.assertFalse(any(item.field == "status" for item in findings))
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_status_difficulty_value_remains_a_warning(self) -> None:
        data = dict(FIELDS)
        data["status"] = "Advanced"
        source = self.write("bidding/advanced.md", data)
        before = source.read_bytes()

        _, findings = self.audit()
        status_findings = [item for item in findings if item.field == "status"]

        self.assertEqual(len(status_findings), 1)
        self.assertEqual(status_findings[0].rule, "status.difficulty-value")
        self.assertEqual(status_findings[0].severity, "Warning")
        self.assertEqual(source.read_bytes(), before)

    def test_status_structural_findings_are_unchanged(self) -> None:
        cases = {
            "missing.md": (None, "field.missing", "Error"),
            "null.md": (None, "value.yaml-null", "Warning"),
            "empty.md": ("", "value.empty", "Error"),
            "type.md": (["Draft"], "type.scalar", "Error"),
        }
        paths = []
        for filename, (value, _, _) in cases.items():
            data = dict(FIELDS)
            if filename == "missing.md":
                del data["status"]
            else:
                data["status"] = value
            paths.append(self.write(f"bidding/{filename}", data))
        before = {path: path.read_bytes() for path in paths}

        _, findings = self.audit()
        observed = {
            (Path(item.article).name, item.rule, item.severity)
            for item in findings
            if item.field == "status"
        }

        for filename, (_, rule, severity) in cases.items():
            self.assertIn((filename, rule, severity), observed)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_findings_are_deterministic_and_provisional_taxonomy_is_not_error(
        self,
    ) -> None:
        data = dict(FIELDS)
        data["category"] = "Card Play – Defence"
        data["subcategory"] = "Defensive Techniques"
        self.write("play/defence/topic.md", data)

        _, first = self.audit()
        _, second = self.audit()

        self.assertEqual(first, second)
        taxonomy = [
            item
            for item in first
            if "provisional" in item.rule or "alignment" in item.rule
        ]
        self.assertTrue(taxonomy)
        self.assertTrue(all(item.severity == "Info" for item in taxonomy))

    def test_exact_root_reference_exceptions_are_narrow_and_reduce_only_four_info(
        self,
    ) -> None:
        approved = {
            "acronyms.md",
            "bibliography.md",
            "bridge-lab-index.md",
            "glossary.md",
        }
        self.assertEqual(
            APPROVED_CATEGORY_EXCEPTIONS,
            frozenset((article, "Reference") for article in approved),
        )
        for article in sorted(approved):
            data = dict(FIELDS)
            data["category"] = "Reference"
            self.write(article, data)

        nonapproved = {
            "fifth.md",
            "nested/acronyms.md",
            "nested/glossary-copy.md",
            "bidding/acronyms.md",
            "play/bibliography.md",
            "duplicates/bridge-lab-index.md",
            "references/glossary.md",
        }
        for article in sorted(nonapproved):
            data = dict(FIELDS)
            data["category"] = "Reference"
            self.write(article, data)
        _, enabled = self.audit()
        with patch("metadata.audit.APPROVED_CATEGORY_EXCEPTIONS", frozenset()):
            _, disabled = self.audit()

        enabled_drift = {
            item.article
            for item in enabled
            if item.rule == "category.provisional-drift"
        }
        self.assertTrue(nonapproved <= enabled_drift)
        self.assertFalse(approved & enabled_drift)

        suppressed = [item for item in disabled if item not in enabled]
        self.assertEqual(
            {(item.article, item.rule, item.severity) for item in suppressed},
            {
                (article, "category.provisional-drift", "Info")
                for article in approved
            },
        )
        self.assertEqual(enabled, sorted(enabled, key=type(enabled[0]).sort_key))
        self.assertEqual(enabled, self.audit()[1])

    def test_exception_matching_is_exact_and_separator_safe(self) -> None:
        match = MetadataAuditor._is_approved_category_exception
        self.assertTrue(match("acronyms.md", "Reference"))
        self.assertFalse(match("acronyms.md", "reference"))
        self.assertFalse(match("./acronyms.md", "Reference"))
        self.assertFalse(match("nested/acronyms.md", "Reference"))
        self.assertFalse(match("nested\\acronyms.md", "Reference"))

    def test_approved_path_with_changed_category_uses_ordinary_audit(self) -> None:
        data = dict(FIELDS)
        data["category"] = "Unexpected"
        self.write("acronyms.md", data)
        _, findings = self.audit()
        drift = [
            item
            for item in findings
            if item.article == "acronyms.md"
            and item.rule == "category.provisional-drift"
        ]
        self.assertEqual(len(drift), 1)

    def test_all_six_deferred_play_category_findings_remain_visible(self) -> None:
        deferred = {
            "play/counting/counting-index.md": "Card Play",
            "play/declarer-play/index-declarer-play.md": "Card Play",
            "play/declarer-play/planning/planning-index.md": "Index",
            "play/declarer-play/trump-play/index-trump-play.md": "Index",
            "play/defence/index-defence.md": "Card Play",
            "play/play-index.md": "Card Play",
        }
        for article, category in deferred.items():
            data = dict(FIELDS)
            data["category"] = category
            self.write(article, data)
        unrelated = dict(FIELDS)
        unrelated["category"] = "Unexpected"
        self.write("bidding/unrelated.md", unrelated)

        _, findings = self.audit()
        drift = {
            item.article
            for item in findings
            if item.rule == "category.provisional-drift"
        }
        self.assertEqual(drift, {*deferred, "bidding/unrelated.md"})

    def test_live_exception_table_matches_the_reviewed_corpus(self) -> None:
        knowledge = Path(__file__).resolve().parents[2] / "knowledge"
        observed = set()
        for article, category in APPROVED_CATEGORY_EXCEPTIONS:
            path = knowledge / article
            self.assertTrue(path.is_file(), f"Orphaned category exception: {article}")
            data = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
            self.assertEqual(data.get("category"), category, article)
            self.assertEqual(path.relative_to(knowledge).as_posix(), article)
            observed.add((article, data.get("category")))
        self.assertEqual(observed, set(APPROVED_CATEGORY_EXCEPTIONS))

    def test_cli_is_registered_console_only_and_preserves_markdown_bytes(self) -> None:
        source = self.write("bidding/topic.md")
        before = source.read_bytes()
        runner = CliRunner()

        help_result = runner.invoke(app, ["metadata-audit", "--help"])
        result = runner.invoke(app, ["metadata-audit", "--root", str(self.root)])

        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Articles Checked: 1", result.output)
        self.assertIn("No source files were modified", result.output)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_repository_wide_empty_acronyms_is_one_informational_finding(self) -> None:
        self.write("bidding/one.md")
        self.write("bidding/two.md")

        _, findings = self.audit()
        acronym_findings = [item for item in findings if item.rule == "acronyms.unused"]

        self.assertEqual(len(acronym_findings), 1)
        self.assertEqual(acronym_findings[0].severity, "Info")
        self.assertEqual(acronym_findings[0].article, "[repository]")

    def test_quoted_and_unquoted_dates_have_identical_semantics(self) -> None:
        quoted = self.write(
            "bidding/quoted.md",
            raw=(
                "---\n"
                + yaml.safe_dump(FIELDS, sort_keys=False)
                + "---\n# Article\n"
            ),
        )
        unquoted_text = quoted.read_text(encoding="utf-8").replace(
            "last_updated: '2026-08-17'", "last_updated: 2026-08-17"
        )
        unquoted = self.write("bidding/unquoted.md", raw=unquoted_text)
        before = {path: path.read_bytes() for path in (quoted, unquoted)}

        articles = Repository(self.root).build()
        dates = {article.filename: article.metadata.last_updated for article in articles}
        validation = MetadataValidator().validate(articles)
        _, findings = self.audit()

        self.assertEqual(
            dates,
            {"quoted.md": "2026-08-17", "unquoted.md": "2026-08-17"},
        )
        self.assertFalse(any(issue.category == "last_updated" for issue in validation))
        self.assertFalse(any(item.field == "last_updated" for item in findings))
        self.assertTrue(all(json.dumps(asdict(article.metadata)) for article in articles))
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_date_audit_rejects_format_datetime_and_unrelated_scalar_types(self) -> None:
        cases = {
            "malformed.md": ("'2026-8-17'", "date.format"),
            "impossible.md": ("'2026-02-30'", "date.invalid"),
            "datetime.md": ("2026-08-17T12:34:56", "type.scalar"),
            "integer.md": ("20260817", "type.scalar"),
        }
        template = "---\n" + yaml.safe_dump(FIELDS, sort_keys=False) + "---\n# Article\n"
        for filename, (raw_date, _) in cases.items():
            self.write(
                f"bidding/{filename}",
                raw=template.replace(
                    "last_updated: '2026-08-17'", f"last_updated: {raw_date}"
                ),
            )

        _, findings = self.audit()
        rules = {
            (Path(item.article).name, item.rule)
            for item in findings
            if item.field == "last_updated"
        }

        for filename, (_, rule) in cases.items():
            self.assertIn((filename, rule), rules)


if __name__ == "__main__":
    unittest.main()
