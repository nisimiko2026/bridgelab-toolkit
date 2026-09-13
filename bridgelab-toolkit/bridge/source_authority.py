"""Conservative source-authority metadata contract and registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceAuthorityClassification(str, Enum):
    UNKNOWN = "UNKNOWN"
    SUPPORTING_ONLY = "SUPPORTING_ONLY"
    PARTNERSHIP_DEPENDENT = "PARTNERSHIP_DEPENDENT"
    EXISTING_AUTHENTICATED_CLASSIFICATION = (
        "EXISTING_AUTHENTICATED_CLASSIFICATION"
    )


class SourceCoverageClassification(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    UNKNOWN = "UNKNOWN"


class SourceType(str, Enum):
    OFFICIAL_LAWS = "OFFICIAL_LAWS"
    OFFICIAL_ORGANIZATION_PUBLICATION = "OFFICIAL_ORGANIZATION_PUBLICATION"
    SYSTEM_DOCUMENTATION = "SYSTEM_DOCUMENTATION"
    PUBLISHED_BOOK = "PUBLISHED_BOOK"
    TECHNICAL_ARTICLE = "TECHNICAL_ARTICLE"
    EDUCATIONAL_REFERENCE = "EDUCATIONAL_REFERENCE"
    INTERNAL_BRIDGELAB_KNOWLEDGE = "INTERNAL_BRIDGELAB_KNOWLEDGE"
    HISTORICAL_REPOSITORY_ARTIFACT = "HISTORICAL_REPOSITORY_ARTIFACT"
    PARTNERSHIP_AGREEMENT = "PARTNERSHIP_AGREEMENT"
    UNKNOWN_SOURCE_TYPE = "UNKNOWN_SOURCE_TYPE"


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    source_type: SourceType
    title: str | None = None
    author_or_organization: str | None = None
    publisher_or_issuer: str | None = None
    edition_or_version: str | None = None
    publication_or_revision_date: str | None = None
    external_identifier: str | None = None
    isbn: str | None = None
    stable_url: str | None = None
    retrieval_date: str | None = None
    repository_snapshot: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, SourceType):
            raise TypeError("source type must be a SourceType")

        for field_name in (
            "title",
            "author_or_organization",
            "publisher_or_issuer",
            "edition_or_version",
            "publication_or_revision_date",
            "external_identifier",
            "isbn",
            "stable_url",
            "retrieval_date",
            "repository_snapshot",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string or None")
            normalized = value.strip()
            object.__setattr__(
                self,
                field_name,
                normalized if normalized else None,
            )


@dataclass(frozen=True, slots=True)
class SourceAuthorityRecord:
    article_id: str
    authority: SourceAuthorityClassification = (
        SourceAuthorityClassification.UNKNOWN
    )
    coverage: SourceCoverageClassification = (
        SourceCoverageClassification.NOT_ESTABLISHED
    )
    identity: SourceIdentity | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.article_id, str):
            raise TypeError("article id must be a string")

        normalized = self.article_id.strip().replace("\\", "/")
        if normalized.endswith(".md"):
            normalized = normalized[:-3]
        normalized = normalized.strip("/")

        if not normalized:
            raise ValueError("article id must not be blank")

        object.__setattr__(self, "article_id", normalized)

        if not isinstance(
            self.authority,
            SourceAuthorityClassification,
        ):
            raise TypeError(
                "authority must be a SourceAuthorityClassification"
            )

        if not isinstance(
            self.coverage,
            SourceCoverageClassification,
        ):
            raise TypeError(
                "coverage must be a SourceCoverageClassification"
            )

        if self.identity is not None and not isinstance(
            self.identity,
            SourceIdentity,
        ):
            raise TypeError("identity must be a SourceIdentity or None")


@dataclass(frozen=True, slots=True)
class SourceAuthorityRegistry:
    registrations: tuple[SourceAuthorityRecord, ...] = ()

    def __post_init__(self) -> None:
        article_ids = tuple(
            record.article_id for record in self.registrations
        )

        if len(article_ids) != len(set(article_ids)):
            raise ValueError(
                "source authority registry contains duplicate article ids"
            )

    def record_for(self, article_id: str) -> SourceAuthorityRecord:
        probe = SourceAuthorityRecord(article_id)

        for record in self.registrations:
            if record.article_id == probe.article_id:
                return record

        return probe

    @property
    def registered_article_ids(self) -> tuple[str, ...]:
        return tuple(
            record.article_id for record in self.registrations
        )


DEFAULT_SOURCE_AUTHORITY_REGISTRY = SourceAuthorityRegistry()