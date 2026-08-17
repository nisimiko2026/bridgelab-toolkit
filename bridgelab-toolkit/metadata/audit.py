"""Read-only raw YAML metadata auditing."""

from __future__ import annotations

import datetime as dt
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FIELDS = (
    "title",
    "description",
    "category",
    "subcategory",
    "difficulty",
    "tags",
    "systems",
    "aliases",
    "acronyms",
    "references",
    "last_updated",
    "status",
)
LIST_FIELDS = {"tags", "systems", "aliases", "acronyms", "references"}
SCALAR_FIELDS = set(FIELDS) - LIST_FIELDS
REQUIRED_SCALARS = {"title", "description", "category", "last_updated", "status"}
DIFFICULTIES = {
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert",
    "All Levels",
    "Beginner to Intermediate",
    "Beginner to Expert",
    "Intermediate to Expert",
    "Advanced to Expert",
}
PROVISIONAL_CATEGORIES = {"bidding", "play", "duplicate", "reference"}
PROVISIONAL_SUBCATEGORIES = {
    "bidding": {
        "convention-cards",
        "conventions",
        "natural-bids",
        "principles",
        "systems",
    },
    "play": {"counting", "declarer-play", "defence", "principles"},
    "duplicate": {"scoring"},
    "reference": {"acronyms", "bibliography", "glossary", "laws", "terminology"},
}
CATEGORY_GROUPS = {
    "bidding": "bidding",
    "bidding method": "bidding",
    "bidding principles": "bidding",
    "bidding system": "bidding",
    "bidding systems": "bidding",
    "convention": "bidding",
    "conventions": "bidding",
    "natural bidding": "bidding",
    "natural bids": "bidding",
    "systems": "bidding",
    "card play": "play",
    "declarer play": "play",
    "defensive play": "play",
    "play": "play",
    "probability": "play",
    "duplicates": "duplicate",
    "bridge formats": "duplicate",
    "reference": "reference",
    "references": "reference",
}
FRONT_MATTER_RE = re.compile(
    r"\A(?:\ufeff)?---[ \t]*(?:\r\n|\n)(.*?)(?:\r\n|\n)" r"---[ \t]*(?=\r\n|\n|\Z)",
    re.DOTALL,
)
REFERENCE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SEVERITY_ORDER = {"Error": 0, "Warning": 1, "Info": 2}


@dataclass(frozen=True, slots=True)
class AuditFinding:
    article: str
    field: str
    observed: str
    rule: str
    severity: str
    message: str
    suggested_canonical_group: str = ""

    def sort_key(self) -> tuple[object, ...]:
        return (
            self.article.casefold(),
            self.field,
            self.rule,
            SEVERITY_ORDER[self.severity],
            self.observed,
            self.message,
        )


@dataclass(frozen=True, slots=True)
class RawArticleMetadata:
    article: str
    path: Path
    text: str
    data: dict[str, Any] | None
    error: str = ""


class MetadataAuditor:
    """Inspect raw front matter without constructing or writing Articles."""

    def __init__(
        self,
        root: Path,
        *,
        systems_file: Path,
        taxonomy_file: Path,
    ) -> None:
        self.root = root.resolve()
        self.systems_file = systems_file
        self.taxonomy_file = taxonomy_file
        self.known_systems = self._load_systems(systems_file)
        self.taxonomy_terms = self._load_taxonomy_terms(taxonomy_file)

    def audit(self) -> tuple[list[RawArticleMetadata], list[AuditFinding]]:
        records = [self._read(path) for path in sorted(self.root.rglob("*.md"))]
        targets = {
            record.path.relative_to(self.root).with_suffix("").as_posix().casefold()
            for record in records
        }
        findings: list[AuditFinding] = []

        for record in records:
            findings.extend(self._audit_record(record, targets))

        if records and all(
            record.data is not None and record.data.get("acronyms") == []
            for record in records
        ):
            findings.append(
                AuditFinding(
                    article="[repository]",
                    field="acronyms",
                    observed=f"{len(records)}/{len(records)} empty lists",
                    rule="acronyms.unused",
                    severity="Info",
                    message="The acronyms field is uniformly empty; its editorial semantics remain unresolved.",
                )
            )

        return records, sorted(findings, key=AuditFinding.sort_key)

    def _read(self, path: Path) -> RawArticleMetadata:
        article = path.relative_to(self.root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            return RawArticleMetadata(article, path, "", None, str(error))

        match = FRONT_MATTER_RE.match(text)
        if not match:
            return RawArticleMetadata(
                article, path, text, None, "Missing or malformed front matter"
            )

        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as error:
            return RawArticleMetadata(
                article, path, text, None, f"Malformed YAML: {error}"
            )

        if not isinstance(data, dict):
            return RawArticleMetadata(
                article, path, text, None, "Front matter must be a mapping"
            )

        return RawArticleMetadata(article, path, text, data)

    def _audit_record(
        self,
        record: RawArticleMetadata,
        targets: set[str],
    ) -> list[AuditFinding]:
        if record.error:
            return [
                self._finding(
                    record,
                    "front_matter",
                    record.error,
                    "front_matter.invalid",
                    "Error",
                    record.error,
                )
            ]

        assert record.data is not None
        findings: list[AuditFinding] = []
        data = record.data

        for field in FIELDS:
            if field not in data:
                findings.append(
                    self._finding(
                        record,
                        field,
                        "[missing]",
                        "field.missing",
                        "Error",
                        "Required metadata key is missing.",
                    )
                )
                continue
            value = data[field]
            if value is None:
                findings.append(
                    self._finding(
                        record,
                        field,
                        "null",
                        "value.yaml-null",
                        "Warning",
                        "YAML null is distinct from an intentional empty value.",
                    )
                )
                continue
            if field in LIST_FIELDS:
                findings.extend(self._audit_list(record, field, value, targets))
            else:
                findings.extend(self._audit_scalar(record, field, value))

        findings.extend(self._audit_title(record))
        return findings

    def _audit_scalar(
        self, record: RawArticleMetadata, field: str, value: Any
    ) -> list[AuditFinding]:
        if (
            field == "last_updated"
            and isinstance(value, dt.date)
            and not isinstance(value, dt.datetime)
        ):
            return [
                self._finding(
                    record,
                    field,
                    value.isoformat(),
                    "date.yaml-type",
                    "Warning",
                    "Date is an unquoted YAML date; canonical serialization is an ISO date string.",
                )
            ]
        if not isinstance(value, str):
            return [
                self._finding(
                    record,
                    field,
                    self._display(value),
                    "type.scalar",
                    "Error",
                    "Field must be a string.",
                )
            ]

        findings: list[AuditFinding] = []
        if value != value.strip():
            findings.append(
                self._finding(
                    record,
                    field,
                    value,
                    "value.whitespace",
                    "Warning",
                    "Scalar has leading or trailing whitespace.",
                )
            )
        if value.strip().casefold() == "none":
            findings.append(
                self._finding(
                    record,
                    field,
                    value,
                    "value.literal-none",
                    "Warning",
                    'Literal "None" is a sentinel, not an intentional empty value.',
                )
            )
            return findings
        if not value:
            required = field in REQUIRED_SCALARS or (
                field == "difficulty" and self._requires_difficulty(record.article)
            )
            findings.append(
                self._finding(
                    record,
                    field,
                    "[empty]",
                    "value.empty",
                    "Error" if required else "Info",
                    (
                        "Required value is empty."
                        if required
                        else "Optional value is empty."
                    ),
                )
            )
            return findings

        if field == "category":
            findings.extend(self._audit_category(record, value))
        elif field == "subcategory":
            findings.extend(self._audit_subcategory(record, value))
        elif field == "difficulty" and value not in DIFFICULTIES:
            findings.append(
                self._finding(
                    record,
                    field,
                    value,
                    "difficulty.invalid",
                    "Warning",
                    "Value is outside the evidence-based difficulty vocabulary.",
                )
            )
        elif field == "last_updated":
            findings.extend(self._audit_date(record, value))
        elif field == "status":
            if value in DIFFICULTIES:
                findings.append(
                    self._finding(
                        record,
                        field,
                        value,
                        "status.difficulty-value",
                        "Warning",
                        "Status contains a difficulty value; status semantics remain provisional.",
                    )
                )
            elif value != "Draft":
                findings.append(
                    self._finding(
                        record,
                        field,
                        value,
                        "status.provisional",
                        "Info",
                        "Non-Draft status observed; the controlled status vocabulary is unresolved.",
                    )
                )
        return findings

    def _audit_list(
        self,
        record: RawArticleMetadata,
        field: str,
        value: Any,
        targets: set[str],
    ) -> list[AuditFinding]:
        if not isinstance(value, list):
            return [
                self._finding(
                    record,
                    field,
                    self._display(value),
                    "type.list",
                    "Error",
                    "Field must be a list of strings.",
                )
            ]

        findings: list[AuditFinding] = []
        strings: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str):
                findings.append(
                    self._finding(
                        record,
                        field,
                        self._display(item),
                        "type.list-item",
                        "Error",
                        f"List item {index} must be a string.",
                    )
                )
                continue
            strings.append(item)
            if item != item.strip():
                findings.append(
                    self._finding(
                        record,
                        field,
                        item,
                        "list.whitespace",
                        "Warning",
                        f"List item {index} has leading or trailing whitespace.",
                    )
                )
            if not item.strip():
                findings.append(
                    self._finding(
                        record,
                        field,
                        item,
                        "list.empty-item",
                        "Warning",
                        f"List item {index} is empty.",
                    )
                )

        exact = Counter(strings)
        for item in sorted(item for item, count in exact.items() if count > 1):
            findings.append(
                self._finding(
                    record,
                    field,
                    item,
                    "list.duplicate",
                    "Warning",
                    "List contains an exact duplicate.",
                )
            )
        folded = Counter(item.casefold() for item in strings)
        for item in sorted(
            item
            for item, count in folded.items()
            if count > 1 and exact.get(item, 0) < count
        ):
            findings.append(
                self._finding(
                    record,
                    field,
                    item,
                    "list.case-duplicate",
                    "Warning",
                    "List contains a case-insensitive duplicate.",
                )
            )

        if field == "tags":
            for item in strings:
                if item.casefold() == "none":
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "tags.sentinel",
                            "Warning",
                            'Tag "none" is a leaked sentinel value.',
                        )
                    )
                if self._is_path_or_breadcrumb(item):
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "tags.structural-form",
                            "Info",
                            "Tag resembles a path or breadcrumb copied from structural metadata.",
                        )
                    )
        elif field == "systems":
            for item in strings:
                canonical = self.known_systems.get(item.casefold())
                if canonical is None:
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "systems.unknown",
                            "Warning",
                            "System is not present in systems.yaml.",
                        )
                    )
                elif item != canonical:
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "systems.noncanonical",
                            "Warning",
                            "System spelling or case differs from systems.yaml.",
                            canonical,
                        )
                    )
        elif field == "references":
            source = (
                record.path.relative_to(self.root).with_suffix("").as_posix().casefold()
            )
            for item in strings:
                normalized = item.removesuffix(".md").replace("\\", "/").casefold()
                if not REFERENCE_RE.fullmatch(item):
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "references.syntax",
                            "Warning",
                            "Reference must be a lowercase POSIX article ID without .md.",
                        )
                    )
                if normalized == source:
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "references.self",
                            "Warning",
                            "Reference points to its own article.",
                        )
                    )
                elif normalized not in targets:
                    findings.append(
                        self._finding(
                            record,
                            field,
                            item,
                            "references.missing-target",
                            "Error",
                            "Reference target does not exist.",
                        )
                    )
        return findings

    def _audit_category(
        self, record: RawArticleMetadata, value: str
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        folded = value.casefold()
        group = self._category_group(value)
        if value not in PROVISIONAL_CATEGORIES:
            message = (
                "Category differs from the provisional top-level audit vocabulary."
            )
            if folded in self.taxonomy_terms:
                message += " It does match a term in taxonomy.yaml."
            findings.append(
                self._finding(
                    record,
                    "category",
                    value,
                    "category.provisional-drift",
                    "Info",
                    message,
                    group,
                )
            )
        if self._is_path_or_breadcrumb(value):
            findings.append(
                self._finding(
                    record,
                    "category",
                    value,
                    "category.structural-form",
                    "Warning",
                    "Category is path-like or hierarchical; replacement requires editorial approval.",
                    group,
                )
            )
        path_group = self._path_category(record.article)
        if path_group and group and group != path_group:
            findings.append(
                self._finding(
                    record,
                    "category",
                    value,
                    "category.path-alignment",
                    "Info",
                    f"Observed category group differs from provisional path group '{path_group}'.",
                    path_group,
                )
            )
        return findings

    def _audit_subcategory(
        self, record: RawArticleMetadata, value: str
    ) -> list[AuditFinding]:
        path_group = self._path_category(record.article)
        allowed = PROVISIONAL_SUBCATEGORIES.get(path_group, set())
        if value not in allowed:
            return [
                self._finding(
                    record,
                    "subcategory",
                    value,
                    "subcategory.provisional-drift",
                    "Info",
                    "Subcategory differs from the provisional path-based audit vocabulary.",
                    self._path_subcategory(record.article),
                )
            ]
        return []

    def _audit_date(self, record: RawArticleMetadata, value: str) -> list[AuditFinding]:
        if not DATE_RE.fullmatch(value):
            return [
                self._finding(
                    record,
                    "last_updated",
                    value,
                    "date.format",
                    "Error",
                    "Date must use YYYY-MM-DD.",
                )
            ]
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            return [
                self._finding(
                    record,
                    "last_updated",
                    value,
                    "date.invalid",
                    "Error",
                    "Value is not a valid calendar date.",
                )
            ]
        return []

    def _audit_title(self, record: RawArticleMetadata) -> list[AuditFinding]:
        if record.data is None or not isinstance(record.data.get("title"), str):
            return []
        match = re.search(r"^#\s+(.+?)\s*$", record.text, re.MULTILINE)
        if match and match.group(1) != record.data["title"]:
            return [
                self._finding(
                    record,
                    "title",
                    record.data["title"],
                    "title.h1-mismatch",
                    "Info",
                    f"Title differs from first H1: {match.group(1)!r}.",
                )
            ]
        return []

    @staticmethod
    def _load_systems(path: Path) -> dict[str, str]:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(
            isinstance(item, str) for item in data
        ):
            raise ValueError("systems.yaml must contain a list of strings")
        return {item.casefold(): item for item in data}

    @classmethod
    def _load_taxonomy_terms(cls, path: Path) -> set[str]:
        terms: set[str] = set()

        def visit(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    terms.add(str(key).casefold())
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    terms.add(str(child).casefold())

        visit(yaml.safe_load(path.read_text(encoding="utf-8")))
        return terms

    @staticmethod
    def _requires_difficulty(article: str) -> bool:
        path = Path(article)
        return path.name not in {"acronyms.md", "bibliography.md", "glossary.md"} and (
            not path.parts or path.parts[0] != "references"
        )

    @staticmethod
    def _path_category(article: str) -> str:
        first = Path(article).parts[0] if Path(article).parts else ""
        return {"duplicates": "duplicate", "references": "reference"}.get(
            first,
            (
                first
                if first in {"bidding", "play"}
                else "reference" if len(Path(article).parts) == 1 else ""
            ),
        )

    @staticmethod
    def _path_subcategory(article: str) -> str:
        parts = Path(article).parts
        return parts[1] if len(parts) > 2 else ""

    @staticmethod
    def _is_path_or_breadcrumb(value: str) -> bool:
        return "/" in value or " – " in value or " — " in value

    @staticmethod
    def _category_group(value: str) -> str:
        folded = value.casefold()
        if MetadataAuditor._is_path_or_breadcrumb(value):
            first = re.split(r"/| – | — ", folded, maxsplit=1)[0]
            return CATEGORY_GROUPS.get(
                first, "play" if first in {"card-play", "techniques", "defence"} else ""
            )
        return CATEGORY_GROUPS.get(folded, "")

    @staticmethod
    def _display(value: Any) -> str:
        return repr(value)

    @staticmethod
    def _finding(
        record: RawArticleMetadata,
        field: str,
        observed: str,
        rule: str,
        severity: str,
        message: str,
        suggested: str = "",
    ) -> AuditFinding:
        return AuditFinding(
            record.article, field, str(observed), rule, severity, message, suggested
        )
