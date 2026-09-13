"""Narrow audit of source-authority registry coverage for current bidding sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from benchmarks.phase21b_provenance_coverage_audit import run_audit
from bridge.source_authority import (
    DEFAULT_SOURCE_AUTHORITY_REGISTRY,
    SourceAuthorityClassification,
    SourceCoverageClassification,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GIT_ROOT = PROJECT_ROOT.parent


@dataclass(frozen=True, slots=True)
class SourceAuthorityRegistryAudit:
    article_ids: tuple[str, ...]
    missing_articles: tuple[str, ...]
    unexpected_authority: tuple[str, ...]
    unexpected_coverage: tuple[str, ...]
    audit_status: str


def _bidding_article_ids() -> tuple[str, ...]:
    audit = run_audit()

    article_ids = {
        item.declared_path.removeprefix("knowledge/").removesuffix(".md")
        for item in audit.source_artifacts
        if item.source_kind == "KNOWLEDGE_SOURCE_REFERENCE"
        and item.declared_path.startswith("knowledge/bidding/")
    }

    return tuple(sorted(article_ids))


def run_source_authority_registry_audit() -> SourceAuthorityRegistryAudit:
    article_ids = _bidding_article_ids()

    missing_articles = tuple(
        article_id
        for article_id in article_ids
        if not (GIT_ROOT / "knowledge" / f"{article_id}.md").is_file()
    )

    unexpected_authority = tuple(
        article_id
        for article_id in article_ids
        if DEFAULT_SOURCE_AUTHORITY_REGISTRY.record_for(
            article_id
        ).authority
        is not SourceAuthorityClassification.UNKNOWN
    )

    unexpected_coverage = tuple(
        article_id
        for article_id in article_ids
        if DEFAULT_SOURCE_AUTHORITY_REGISTRY.record_for(
            article_id
        ).coverage
        is not SourceCoverageClassification.NOT_ESTABLISHED
    )

    passed = (
        len(article_ids) == 16
        and not missing_articles
        and not unexpected_authority
        and not unexpected_coverage
    )

    return SourceAuthorityRegistryAudit(
        article_ids,
        missing_articles,
        unexpected_authority,
        unexpected_coverage,
        "PASS" if passed else "FAIL",
    )


def main() -> int:
    audit = run_source_authority_registry_audit()

    print("SOURCE AUTHORITY REGISTRY AUDIT")
    print(f"bidding_article_ids = {len(audit.article_ids)}")
    print(f"missing_articles = {len(audit.missing_articles)}")
    print(
        "unexpected_authority_classifications = "
        f"{len(audit.unexpected_authority)}"
    )
    print(
        "unexpected_coverage_classifications = "
        f"{len(audit.unexpected_coverage)}"
    )
    print(f"audit status = {audit.audit_status}")

    return 0 if audit.audit_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())