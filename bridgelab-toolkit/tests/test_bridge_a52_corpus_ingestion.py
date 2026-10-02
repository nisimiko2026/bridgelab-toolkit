"""A5.2 corpus batch ingestion tests."""

from typing import Any, Mapping

import pytest

from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.corpus_ingestion import (
    CorpusIngestionEntry,
    CorpusIngestionResult,
    ingest_corpus,
)
from bridge.corpus_providers import (
    BridgeDealsNormalizedAdapter,
    PbnNormalizedAdapter,
)
from bridge.corpus_validation import ValidationStatus
from bridge.models import Seat, Vulnerability


def normalized_raw(
    record_id: str,
    *,
    dealer: str = "N",
    vulnerability: str = "None",
) -> dict[str, object]:
    return {
        "record_id": record_id,
        "source": "a52-test",
        "dealer": dealer,
        "vulnerability": vulnerability,
    }


def test_ingests_normalized_bridge_deals_records():
    result = ingest_corpus(
        dataset_id="bridge-deals",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw("1"),
            normalized_raw("2"),
        ),
    )

    assert isinstance(result, CorpusIngestionResult)
    assert result.total == 2
    assert result.accepted == 2
    assert result.rejected == 0
    assert len(result.dataset) == 2

    assert tuple(
        record.provenance.record_id
        for record in result.dataset
    ) == (
        "1",
        "2",
    )


def test_missing_deal_and_auction_are_accepted_with_warnings():
    result = ingest_corpus(
        dataset_id="warnings",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw("1"),
        ),
    )

    entry = result.entries[0]

    assert entry.accepted is True
    assert (
        entry.validation.status
        is ValidationStatus.ACCEPT_WITH_WARNINGS
    )
    assert entry.validation.issues == (
        "deal missing",
        "auction missing",
    )

    assert result.warnings == 1


def test_pbn_provider_identity_survives_ingestion():
    result = ingest_corpus(
        dataset_id="pbn",
        adapter=PbnNormalizedAdapter(),
        raw_records=(
            normalized_raw("17"),
        ),
    )

    assert len(result.dataset) == 1
    assert (
        result.dataset[0].provenance.provider
        == "pbn-normalized"
    )


def test_input_order_is_preserved():
    result = ingest_corpus(
        dataset_id="ordered",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw("3"),
            normalized_raw("1"),
            normalized_raw("2"),
        ),
    )

    assert tuple(
        record.provenance.record_id
        for record in result.dataset
    ) == (
        "3",
        "1",
        "2",
    )

    assert tuple(
        entry.index
        for entry in result.entries
    ) == (
        0,
        1,
        2,
    )


def test_adapter_exception_is_retained_as_rejected_entry():
    result = ingest_corpus(
        dataset_id="adapter-error",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw(
                "bad",
                dealer="INVALID",
            ),
            normalized_raw("good"),
        ),
    )

    assert result.total == 2
    assert result.accepted == 1
    assert result.rejected == 1

    failed = result.entries[0]

    assert failed.record is None
    assert failed.validation is None
    assert failed.error is not None

    assert tuple(
        record.provenance.record_id
        for record in result.dataset
    ) == (
        "good",
    )


def test_non_mapping_raw_record_is_rejected_without_stopping_batch():
    raw_records = (
        normalized_raw("1"),
        "not-a-mapping",
        normalized_raw("2"),
    )

    result = ingest_corpus(
        dataset_id="mixed",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=raw_records,
    )

    assert result.total == 3
    assert result.accepted == 2
    assert result.rejected == 1

    assert result.entries[1].error == (
        "raw record must be a mapping"
    )


def test_description_flows_to_dataset():
    result = ingest_corpus(
        dataset_id="described",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(),
        description="  Tournament corpus  ",
    )

    assert result.dataset.description == "Tournament corpus"


def test_empty_input_produces_empty_dataset():
    result = ingest_corpus(
        dataset_id="empty",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(),
    )

    assert result.total == 0
    assert result.accepted == 0
    assert result.rejected == 0
    assert result.warnings == 0
    assert result.dataset.is_empty is True


def test_unknown_systems_remain_unknown():
    result = ingest_corpus(
        dataset_id="unknown-system",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw("1"),
        ),
    )

    record = result.dataset[0]

    assert record.ns_system is None
    assert record.ew_system is None


def test_explicit_system_metadata_is_preserved():
    raw = normalized_raw("1")
    raw["ns_system"] = "2/1"
    raw["ew_system"] = "SAYC"

    result = ingest_corpus(
        dataset_id="known-system",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(raw,),
    )

    record = result.dataset[0]

    assert record.ns_system == "2/1"
    assert record.ew_system == "SAYC"


def test_blank_dataset_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="dataset_id must be a non-blank string",
    ):
        ingest_corpus(
            dataset_id=" ",
            adapter=BridgeDealsNormalizedAdapter(),
            raw_records=(),
        )


def test_adapter_without_provider_name_is_rejected():
    class InvalidAdapter:
        def adapt(
            self,
            raw: Mapping[str, Any],
        ) -> CanonicalBoardRecord:
            raise AssertionError("must not be called")

    with pytest.raises(
        TypeError,
        match="adapter must provide provider_name",
    ):
        ingest_corpus(
            dataset_id="invalid-adapter",
            adapter=InvalidAdapter(),
            raw_records=(),
        )


def test_adapter_without_adapt_method_is_rejected():
    class InvalidAdapter:
        provider_name = "invalid"

    with pytest.raises(
        TypeError,
        match=r"adapter must provide adapt\(raw\)",
    ):
        ingest_corpus(
            dataset_id="invalid-adapter",
            adapter=InvalidAdapter(),
            raw_records=(),
        )


def test_adapter_returning_wrong_type_is_rejected_per_record():
    class WrongTypeAdapter:
        provider_name = "wrong-type"

        def adapt(
            self,
            raw: Mapping[str, Any],
        ) -> object:
            return object()

    result = ingest_corpus(
        dataset_id="wrong-type",
        adapter=WrongTypeAdapter(),
        raw_records=(
            {"record_id": "1"},
        ),
    )

    assert result.total == 1
    assert result.accepted == 0
    assert result.rejected == 1
    assert result.dataset.is_empty is True

    assert result.entries[0].error == (
        "adapter did not return CanonicalBoardRecord"
    )


def test_ingestion_entry_accepted_property_requires_accepted_status():
    record = CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider="test",
            source="test",
            record_id="1",
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
    )

    result = ingest_corpus(
        dataset_id="entry-property",
        adapter=BridgeDealsNormalizedAdapter(),
        raw_records=(
            normalized_raw("1"),
        ),
    )

    entry = result.entries[0]

    assert isinstance(entry, CorpusIngestionEntry)
    assert entry.record is not None
    assert entry.accepted is True
