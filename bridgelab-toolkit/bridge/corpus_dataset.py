"""Provider-neutral dataset boundary for canonical bridge corpora.

A CorpusDataset is an ordered collection of CanonicalBoardRecord objects.
It provides stable dataset identity and simple iteration without parsing,
system inference, filtering policy, benchmarking, or evidence ranking.

External corpus providers should normalize records through the A1 ingestion
boundary before constructing a CorpusDataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from .corpus import CanonicalBoardRecord


@dataclass(frozen=True, slots=True)
class CorpusDataset:
    """Immutable ordered collection of canonical corpus records."""

    dataset_id: str
    records: tuple[CanonicalBoardRecord, ...]
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise ValueError("dataset_id must be a non-blank string")

        object.__setattr__(
            self,
            "dataset_id",
            self.dataset_id.strip(),
        )

        if not isinstance(self.records, tuple):
            raise TypeError("records must be a tuple")

        for record in self.records:
            if not isinstance(record, CanonicalBoardRecord):
                raise TypeError(
                    "records entries must be CanonicalBoardRecord"
                )

        if self.description is not None:
            if (
                not isinstance(self.description, str)
                or not self.description.strip()
            ):
                raise ValueError(
                    "description must be None or a non-blank string"
                )

            object.__setattr__(
                self,
                "description",
                self.description.strip(),
            )

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self) -> Iterator[CanonicalBoardRecord]:
        return iter(self.records)

    def __getitem__(
        self,
        index: int,
    ) -> CanonicalBoardRecord:
        return self.records[index]

    @property
    def is_empty(self) -> bool:
        return not self.records


def corpus_dataset(
    *,
    dataset_id: str,
    records: Iterable[CanonicalBoardRecord],
    description: str | None = None,
) -> CorpusDataset:
    """Materialize canonical records into an immutable dataset."""

    return CorpusDataset(
        dataset_id=dataset_id,
        records=tuple(records),
        description=description,
    )
