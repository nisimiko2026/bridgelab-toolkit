from dataclasses import FrozenInstanceError

import pytest

from bridge.source_authority import (
    DEFAULT_SOURCE_AUTHORITY_REGISTRY,
    SourceAuthorityClassification,
    SourceAuthorityRecord,
    SourceAuthorityRegistry,
    SourceCoverageClassification,
    SourceIdentity,
    SourceType,
)


def test_source_authority_taxonomies_are_exact():
    assert {item.value for item in SourceAuthorityClassification} == {
        "UNKNOWN",
        "SUPPORTING_ONLY",
        "PARTNERSHIP_DEPENDENT",
        "EXISTING_AUTHENTICATED_CLASSIFICATION",
    }

    assert {item.value for item in SourceCoverageClassification} == {
        "EXACT",
        "PARTIAL",
        "NOT_ESTABLISHED",
        "UNKNOWN",
    }

    assert {item.value for item in SourceType} == {
        "OFFICIAL_LAWS",
        "OFFICIAL_ORGANIZATION_PUBLICATION",
        "SYSTEM_DOCUMENTATION",
        "PUBLISHED_BOOK",
        "TECHNICAL_ARTICLE",
        "EDUCATIONAL_REFERENCE",
        "INTERNAL_BRIDGELAB_KNOWLEDGE",
        "HISTORICAL_REPOSITORY_ARTIFACT",
        "PARTNERSHIP_AGREEMENT",
        "UNKNOWN_SOURCE_TYPE",
    }


def test_source_identity_is_immutable_and_normalizes_optional_strings():
    identity = SourceIdentity(
        SourceType.PUBLISHED_BOOK,
        title="  Example Book  ",
        author_or_organization="  Example Author  ",
        isbn="   ",
    )

    assert identity.title == "Example Book"
    assert identity.author_or_organization == "Example Author"
    assert identity.isbn is None

    with pytest.raises(FrozenInstanceError):
        identity.title = "changed"

    with pytest.raises(TypeError):
        SourceIdentity("PUBLISHED_BOOK")


def test_source_authority_record_defaults_are_conservative():
    record = SourceAuthorityRecord(
        r"bidding\systems\sayc.md"
    )

    assert record.article_id == "bidding/systems/sayc"
    assert record.authority is SourceAuthorityClassification.UNKNOWN
    assert (
        record.coverage
        is SourceCoverageClassification.NOT_ESTABLISHED
    )
    assert record.identity is None


def test_source_authority_record_rejects_invalid_values():
    with pytest.raises(ValueError):
        SourceAuthorityRecord("   ")

    with pytest.raises(TypeError):
        SourceAuthorityRecord(
            "bidding/systems/sayc",
            authority="UNKNOWN",
        )

    with pytest.raises(TypeError):
        SourceAuthorityRecord(
            "bidding/systems/sayc",
            coverage="NOT_ESTABLISHED",
        )

    with pytest.raises(TypeError):
        SourceAuthorityRecord(
            "bidding/systems/sayc",
            identity="not-an-identity",
        )


def test_registry_returns_registered_record():
    record = SourceAuthorityRecord(
        "bidding/systems/sayc",
        authority=SourceAuthorityClassification.SUPPORTING_ONLY,
        coverage=SourceCoverageClassification.PARTIAL,
        identity=SourceIdentity(
            SourceType.INTERNAL_BRIDGELAB_KNOWLEDGE,
            title="SAYC",
        ),
    )

    registry = SourceAuthorityRegistry((record,))

    assert registry.record_for(
        r"bidding\systems\sayc.md"
    ) is record
    assert registry.registered_article_ids == (
        "bidding/systems/sayc",
    )


def test_registry_missing_lookup_returns_conservative_record():
    record = DEFAULT_SOURCE_AUTHORITY_REGISTRY.record_for(
        "bidding/systems/sayc"
    )

    assert record.article_id == "bidding/systems/sayc"
    assert record.authority is SourceAuthorityClassification.UNKNOWN
    assert (
        record.coverage
        is SourceCoverageClassification.NOT_ESTABLISHED
    )
    assert record.identity is None


def test_registry_rejects_duplicate_normalized_article_ids():
    first = SourceAuthorityRecord(
        "bidding/systems/sayc"
    )
    duplicate = SourceAuthorityRecord(
        r"bidding\systems\sayc.md"
    )

    with pytest.raises(ValueError):
        SourceAuthorityRegistry((first, duplicate))