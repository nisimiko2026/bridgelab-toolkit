"""A5.1 provider-neutral corpus dataset tests."""

import pytest

from bridge.corpus import (
    CanonicalBoardRecord,
    SourceProvenance,
)
from bridge.corpus_dataset import (
    CorpusDataset,
    corpus_dataset,
)
from bridge.models import Seat, Vulnerability


def make_record(
    record_id: str,
    *,
    provider: str = "test-provider",
    ns_system: str | None = None,
    ew_system: str | None = None,
) -> CanonicalBoardRecord:
    return CanonicalBoardRecord(
        provenance=SourceProvenance(
            provider=provider,
            source="a51-test-source",
            record_id=record_id,
        ),
        dealer=Seat.NORTH,
        vulnerability=Vulnerability.NONE,
        ns_system=ns_system,
        ew_system=ew_system,
    )


def test_dataset_preserves_identity_and_records():
    first = make_record("1")
    second = make_record("2")

    dataset = CorpusDataset(
        dataset_id="expert-boards",
        records=(first, second),
    )

    assert dataset.dataset_id == "expert-boards"
    assert dataset.records == (first, second)


def test_dataset_id_is_trimmed():
    dataset = CorpusDataset(
        dataset_id="  expert-boards  ",
        records=(),
    )

    assert dataset.dataset_id == "expert-boards"


def test_dataset_supports_len_iteration_and_indexing():
    first = make_record("1")
    second = make_record("2")

    dataset = CorpusDataset(
        dataset_id="ordered",
        records=(first, second),
    )

    assert len(dataset) == 2
    assert tuple(dataset) == (first, second)
    assert dataset[0] is first
    assert dataset[1] is second


def test_empty_dataset_is_valid():
    dataset = CorpusDataset(
        dataset_id="empty",
        records=(),
    )

    assert len(dataset) == 0
    assert dataset.is_empty is True


def test_nonempty_dataset_reports_not_empty():
    dataset = CorpusDataset(
        dataset_id="nonempty",
        records=(make_record("1"),),
    )

    assert dataset.is_empty is False


def test_factory_materializes_iterable_once():
    source = (
        make_record(str(index))
        for index in range(3)
    )

    dataset = corpus_dataset(
        dataset_id="generated",
        records=source,
    )

    assert len(dataset) == 3
    assert tuple(
        record.provenance.record_id
        for record in dataset
    ) == (
        "0",
        "1",
        "2",
    )


def test_description_is_optional_and_trimmed():
    dataset = CorpusDataset(
        dataset_id="described",
        records=(),
        description="  Expert tournament boards  ",
    )

    assert dataset.description == "Expert tournament boards"


def test_dataset_preserves_provider_provenance():
    record = make_record(
        "board-17",
        provider="bridge-deals-db",
    )

    dataset = CorpusDataset(
        dataset_id="provenance",
        records=(record,),
    )

    assert dataset[0].provenance.provider == "bridge-deals-db"
    assert dataset[0].provenance.record_id == "board-17"


def test_dataset_does_not_infer_unknown_systems():
    record = make_record("unknown-system")

    dataset = CorpusDataset(
        dataset_id="unknown-systems",
        records=(record,),
    )

    assert dataset[0].ns_system is None
    assert dataset[0].ew_system is None


def test_dataset_preserves_explicit_system_metadata():
    record = make_record(
        "known-system",
        ns_system="2/1",
        ew_system="SAYC",
    )

    dataset = CorpusDataset(
        dataset_id="known-systems",
        records=(record,),
    )

    assert dataset[0].ns_system == "2/1"
    assert dataset[0].ew_system == "SAYC"


@pytest.mark.parametrize(
    "dataset_id",
    (
        "",
        " ",
        "\t",
    ),
)
def test_blank_dataset_id_is_rejected(dataset_id):
    with pytest.raises(
        ValueError,
        match="dataset_id must be a non-blank string",
    ):
        CorpusDataset(
            dataset_id=dataset_id,
            records=(),
        )


def test_non_string_dataset_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="dataset_id must be a non-blank string",
    ):
        CorpusDataset(
            dataset_id=123,
            records=(),
        )


def test_records_must_be_tuple_for_direct_constructor():
    with pytest.raises(
        TypeError,
        match="records must be a tuple",
    ):
        CorpusDataset(
            dataset_id="invalid",
            records=[],
        )


def test_wrong_record_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="records entries must be CanonicalBoardRecord",
    ):
        CorpusDataset(
            dataset_id="invalid-record",
            records=(object(),),
        )


@pytest.mark.parametrize(
    "description",
    (
        "",
        " ",
    ),
)
def test_blank_description_is_rejected(description):
    with pytest.raises(
        ValueError,
        match=(
            "description must be None or a non-blank string"
        ),
    ):
        CorpusDataset(
            dataset_id="invalid-description",
            records=(),
            description=description,
        )


def test_non_string_description_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "description must be None or a non-blank string"
        ),
    ):
        CorpusDataset(
            dataset_id="invalid-description",
            records=(),
            description=123,
        )
