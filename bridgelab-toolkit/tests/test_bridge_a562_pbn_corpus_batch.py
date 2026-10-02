from pathlib import Path

import pytest

from bridge.corpus import CanonicalBoardRecord
from bridge.corpus_dataset import CorpusDataset
from bridge.pbn_corpus_batch import (
    PbnCorpusBatchResult,
    PbnCorpusFileResult,
    discover_pbn_files,
    load_pbn_corpus,
)


VALID_PBN = """\
% PBN 2.1

[Event "A5.6.2 Test"]
[Board "129"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Declarer "N"]
[Contract "3NT"]
[Result "12"]
[Auction "N"]
1C Pass 1D 3C
3NT AP
"""


SECOND_VALID_PBN = """\
% PBN 2.1

[Event "A5.6.2 Test"]
[Board "130"]
[Dealer "E"]
[Vulnerable "NS"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Declarer "N"]
[Contract "3NT"]
[Result "10"]
[Auction "E"]
Pass 1C Pass 1D
Pass 3NT AP
"""


INVALID_PBN = """\
% PBN 2.1

[Event "Broken"]
[Board "999"]
[Dealer "N"]
[Vulnerable "Impossible"]
[Deal "W:95.98.T98.AKJ974 AK4.AQ4.AKJ5.QT3 JT8.T7652.Q3.652 Q7632.KJ3.7642.8"]
[Auction "N"]
Pass Pass Pass Pass
"""


def write(
    path: Path,
    text: str,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

    return path


def test_file_result_requires_path():
    with pytest.raises(
        TypeError,
        match="path must be a Path",
    ):
        PbnCorpusFileResult(  # type: ignore[arg-type]
            path="a.pbn",
        )


def test_file_result_records_must_be_tuple(
    tmp_path,
):
    path = write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    record = load_pbn_corpus(
        tmp_path,
        dataset_id="x",
    ).dataset[0]

    with pytest.raises(
        TypeError,
        match="records must be a tuple",
    ):
        PbnCorpusFileResult(  # type: ignore[arg-type]
            path=Path("a.pbn"),
            records=[record],
        )


def test_file_result_rejects_non_record():
    with pytest.raises(
        TypeError,
        match="CanonicalBoardRecord",
    ):
        PbnCorpusFileResult(  # type: ignore[arg-type]
            path=Path("a.pbn"),
            records=("bad",),
        )


def test_file_result_rejects_blank_error():
    with pytest.raises(
        ValueError,
        match="non-blank",
    ):
        PbnCorpusFileResult(
            path=Path("a.pbn"),
            error="   ",
        )


def test_failed_file_cannot_have_records(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    record = load_pbn_corpus(
        tmp_path,
        dataset_id="x",
    ).dataset[0]

    with pytest.raises(
        ValueError,
        match="cannot contain records",
    ):
        PbnCorpusFileResult(
            path=Path("a.pbn"),
            records=(record,),
            error="broken",
        )


def test_file_result_success_properties(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="x",
    ).files[0]

    assert result.succeeded
    assert not result.failed
    assert result.record_count == 1


def test_file_result_failure_properties():
    result = PbnCorpusFileResult(
        path=Path("bad.pbn"),
        error="ValueError: broken",
    )

    assert result.failed
    assert not result.succeeded
    assert result.record_count == 0


def test_discover_requires_existing_root(
    tmp_path,
):
    missing = tmp_path / "missing"

    with pytest.raises(
        FileNotFoundError,
        match="does not exist",
    ):
        discover_pbn_files(
            missing
        )


def test_discover_requires_directory(
    tmp_path,
):
    path = write(
        tmp_path / "file.pbn",
        VALID_PBN,
    )

    with pytest.raises(
        NotADirectoryError,
        match="not a directory",
    ):
        discover_pbn_files(
            path
        )


def test_discover_empty_directory(
    tmp_path,
):
    assert (
        discover_pbn_files(
            tmp_path
        )
        == ()
    )


def test_discover_recursively(
    tmp_path,
):
    first = write(
        tmp_path / "2024" / "a.pbn",
        VALID_PBN,
    )

    second = write(
        tmp_path
        / "2025"
        / "event"
        / "b.pbn",
        SECOND_VALID_PBN,
    )

    discovered = discover_pbn_files(
        tmp_path
    )

    assert first in discovered
    assert second in discovered
    assert len(discovered) == 2


def test_discover_case_insensitive_extension(
    tmp_path,
):
    path = write(
        tmp_path / "UPPER.PBN",
        VALID_PBN,
    )

    assert discover_pbn_files(
        tmp_path
    ) == (path,)


def test_discover_ignores_other_files(
    tmp_path,
):
    write(
        tmp_path / "a.txt",
        VALID_PBN,
    )

    write(
        tmp_path / "b.json",
        "{}",
    )

    assert discover_pbn_files(
        tmp_path
    ) == ()


def test_discover_is_deterministic(
    tmp_path,
):
    write(
        tmp_path / "z.pbn",
        VALID_PBN,
    )

    write(
        tmp_path / "A.pbn",
        VALID_PBN,
    )

    write(
        tmp_path / "middle.pbn",
        VALID_PBN,
    )

    names = tuple(
        path.name
        for path in discover_pbn_files(
            tmp_path
        )
    )

    assert names == (
        "A.pbn",
        "middle.pbn",
        "z.pbn",
    )


def test_batch_returns_result(
    tmp_path,
):
    result = load_pbn_corpus(
        tmp_path,
        dataset_id="dataset",
    )

    assert isinstance(
        result,
        PbnCorpusBatchResult,
    )

    assert isinstance(
        result.dataset,
        CorpusDataset,
    )


def test_batch_empty_directory(
    tmp_path,
):
    result = load_pbn_corpus(
        tmp_path,
        dataset_id="empty",
    )

    assert len(result.dataset) == 0
    assert result.file_count == 0
    assert result.succeeded_files == 0
    assert result.failed_files == 0


def test_batch_loads_one_file(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="one",
    )

    assert result.file_count == 1
    assert result.succeeded_files == 1
    assert result.failed_files == 0
    assert result.record_count == 1


def test_batch_loads_multiple_files(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    write(
        tmp_path / "b.pbn",
        SECOND_VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="two",
    )

    assert result.file_count == 2
    assert result.succeeded_files == 2
    assert result.record_count == 2


def test_batch_preserves_board_order(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    write(
        tmp_path / "b.pbn",
        SECOND_VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="ordered",
    )

    assert tuple(
        record.board_number
        for record in result.dataset
    ) == (
        129,
        130,
    )


def test_batch_uses_relative_source(
    tmp_path,
):
    write(
        tmp_path
        / "2024"
        / "event"
        / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="relative",
    )

    assert (
        result.dataset[0]
        .provenance.source
        == "2024/event/a.pbn"
    )


def test_batch_preserves_provider(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="provider",
        provider="bridge-deals-db-pbn",
    )

    assert (
        result.dataset[0]
        .provenance.provider
        == "bridge-deals-db-pbn"
    )


def test_batch_preserves_provider_version(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="version",
        provider_version="2.0",
    )

    assert (
        result.dataset[0]
        .provenance.provider_version
        == "2.0"
    )


def test_batch_preserves_record_id(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="record-id",
    )

    assert (
        result.dataset[0]
        .provenance.record_id
        == "129"
    )


def test_batch_preserves_transformations(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="transformations",
    )

    assert (
        "parsed-native-pbn"
        in result.dataset[0]
        .provenance.transformations
    )


def test_bad_file_does_not_abort_batch(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    write(
        tmp_path / "bad.pbn",
        INVALID_PBN,
    )

    write(
        tmp_path / "c.pbn",
        SECOND_VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="mixed",
    )

    assert result.file_count == 3
    assert result.succeeded_files == 2
    assert result.failed_files == 1
    assert result.record_count == 2


def test_bad_file_retains_error(
    tmp_path,
):
    write(
        tmp_path / "bad.pbn",
        INVALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="bad",
    )

    assert result.failed_files == 1
    assert len(result.errors) == 1

    failure = result.errors[0]

    assert failure.path == Path(
        "bad.pbn"
    )

    assert "ValueError" in failure.error
    assert "vulnerability" in failure.error


def test_failed_file_not_added_to_dataset(
    tmp_path,
):
    write(
        tmp_path / "bad.pbn",
        INVALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="bad-only",
    )

    assert len(result.dataset) == 0


def test_description_passes_to_dataset(
    tmp_path,
):
    result = load_pbn_corpus(
        tmp_path,
        dataset_id="described",
        description="Bridge deals PBN corpus",
    )

    assert (
        result.dataset.description
        == "Bridge deals PBN corpus"
    )


def test_dataset_id_passes_to_dataset(
    tmp_path,
):
    result = load_pbn_corpus(
        tmp_path,
        dataset_id="bridge-deals-db",
    )

    assert (
        result.dataset.dataset_id
        == "bridge-deals-db"
    )


def test_batch_records_are_canonical(
    tmp_path,
):
    write(
        tmp_path / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="canonical",
    )

    assert isinstance(
        result.dataset[0],
        CanonicalBoardRecord,
    )


def test_file_result_uses_relative_path(
    tmp_path,
):
    write(
        tmp_path
        / "year"
        / "event"
        / "a.pbn",
        VALID_PBN,
    )

    result = load_pbn_corpus(
        tmp_path,
        dataset_id="paths",
    )

    assert (
        result.files[0].path
        == Path(
            "year/event/a.pbn"
        )
    )
