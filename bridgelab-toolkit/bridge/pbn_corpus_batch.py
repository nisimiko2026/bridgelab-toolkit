"""Batch loading for native PBN corpus sources.

A5.6.2 — PBN Corpus Batch Loader.

This module discovers PBN files beneath a corpus root and loads them
through the native A5.6.1 PBN reader.

Responsibilities:
- recursive PBN discovery
- deterministic file ordering
- per-file failure isolation
- aggregation into CorpusDataset
- preservation of source provenance

It deliberately contains no benchmarking, bidding-policy, convention,
or partnership logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .corpus import CanonicalBoardRecord
from .corpus_dataset import CorpusDataset
from .pbn_corpus_reader import read_pbn_file


@dataclass(frozen=True, slots=True)
class PbnCorpusFileResult:
    """Outcome for one discovered PBN file."""

    path: Path
    records: tuple[CanonicalBoardRecord, ...] = ()
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")

        if not isinstance(self.records, tuple):
            raise TypeError("records must be a tuple")

        for record in self.records:
            if not isinstance(record, CanonicalBoardRecord):
                raise TypeError(
                    "records must contain CanonicalBoardRecord values"
                )

        if self.error is not None:
            if not isinstance(self.error, str):
                raise TypeError("error must be None or a string")

            if not self.error.strip():
                raise ValueError("error must be non-blank")

            if self.records:
                raise ValueError(
                    "failed file result cannot contain records"
                )

    @property
    def succeeded(self) -> bool:
        return self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None

    @property
    def record_count(self) -> int:
        return len(self.records)


@dataclass(frozen=True, slots=True)
class PbnCorpusBatchResult:
    """Aggregate result for a PBN corpus directory."""

    dataset: CorpusDataset
    files: tuple[PbnCorpusFileResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.dataset, CorpusDataset):
            raise TypeError("dataset must be a CorpusDataset")

        if not isinstance(self.files, tuple):
            raise TypeError("files must be a tuple")

        for file_result in self.files:
            if not isinstance(file_result, PbnCorpusFileResult):
                raise TypeError(
                    "files must contain PbnCorpusFileResult values"
                )

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def succeeded_files(self) -> int:
        return sum(
            file_result.succeeded
            for file_result in self.files
        )

    @property
    def failed_files(self) -> int:
        return sum(
            file_result.failed
            for file_result in self.files
        )

    @property
    def record_count(self) -> int:
        return len(self.dataset)

    @property
    def errors(self) -> tuple[PbnCorpusFileResult, ...]:
        return tuple(
            file_result
            for file_result in self.files
            if file_result.failed
        )


def discover_pbn_files(
    root: str | Path,
) -> tuple[Path, ...]:
    """Discover PBN files recursively beneath *root*.

    Matching is case-insensitive so both .pbn and .PBN are accepted.
    Returned paths are sorted deterministically by their relative path.
    """

    root_path = Path(root)

    if not root_path.exists():
        raise FileNotFoundError(
            f"PBN corpus root does not exist: {root_path}"
        )

    if not root_path.is_dir():
        raise NotADirectoryError(
            f"PBN corpus root is not a directory: {root_path}"
        )

    files = [
        path
        for path in root_path.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".pbn"
    ]

    files.sort(
        key=lambda path: path.relative_to(root_path)
        .as_posix()
        .casefold()
    )

    return tuple(files)


def load_pbn_corpus(
    root: str | Path,
    *,
    dataset_id: str,
    description: str | None = None,
    provider: str = "pbn-native",
    provider_version: str | None = None,
) -> PbnCorpusBatchResult:
    """Load all PBN files beneath *root* into one CorpusDataset.

    Each file is processed independently.  A malformed file is retained
    as a failed PbnCorpusFileResult and does not abort the remaining
    corpus.

    The source passed to the native reader is the file's path relative
    to the corpus root.  This keeps provenance stable if the corpus
    directory itself moves to another machine.
    """

    root_path = Path(root)

    files = discover_pbn_files(
        root_path
    )

    all_records: list[
        CanonicalBoardRecord
    ] = []

    file_results: list[
        PbnCorpusFileResult
    ] = []

    for path in files:
        relative_path = path.relative_to(
            root_path
        )

        try:
            records = read_pbn_file(
                path,
                provider=provider,
                provider_version=provider_version,
            )

            # read_pbn_file records the physical path as source.
            # For a batch corpus we want stable corpus-relative
            # provenance. Rebuild only the provenance source while
            # preserving all other canonical record fields.
            normalized_records: list[
                CanonicalBoardRecord
            ] = []

            for record in records:
                provenance = record.provenance

                normalized_record = CanonicalBoardRecord(
                    provenance=type(provenance)(
                        provider=provenance.provider,
                        source=relative_path.as_posix(),
                        record_id=provenance.record_id,
                        language=provenance.language,
                        notation=provenance.notation,
                        provider_version=provenance.provider_version,
                        transformations=provenance.transformations,
                        raw_reference=provenance.raw_reference,
                    ),
                    dealer=record.dealer,
                    vulnerability=record.vulnerability,
                    deal=record.deal,
                    auction=record.auction,
                    contract=record.contract,
                    opening_lead=record.opening_lead,
                    tricks=record.tricks,
                    board_number=record.board_number,
                    ns_system=record.ns_system,
                    ew_system=record.ew_system,
                )

                normalized_records.append(
                    normalized_record
                )

            normalized_tuple = tuple(
                normalized_records
            )

            all_records.extend(
                normalized_tuple
            )

            file_results.append(
                PbnCorpusFileResult(
                    path=relative_path,
                    records=normalized_tuple,
                )
            )

        except Exception as exc:
            file_results.append(
                PbnCorpusFileResult(
                    path=relative_path,
                    error=(
                        f"{type(exc).__name__}: {exc}"
                    ),
                )
            )

    dataset = CorpusDataset(
        dataset_id=dataset_id,
        records=tuple(all_records),
        description=description,
    )

    return PbnCorpusBatchResult(
        dataset=dataset,
        files=tuple(file_results),
    )
