from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import yaml
from typer.testing import CliRunner

from main import app
from core.repository import Repository
from metadata.audit import MetadataAuditor
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
