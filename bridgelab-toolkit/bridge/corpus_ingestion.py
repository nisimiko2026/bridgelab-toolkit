"""Batch ingestion from provider adapters into canonical corpus datasets.

This module connects the A1 CorpusAdapter boundary to the A5 CorpusDataset
boundary.

It does not parse provider-specific file formats, infer bidding systems,
repair conflicting records, rank providers, or silently discard validation
results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .corpus import CanonicalBoardRecord
from .corpus_adapters import CorpusAdapter
from .corpus_dataset import CorpusDataset
from .corpus_validation import (
    ValidationResult,
    ValidationStatus,
    validate_record,
)


@dataclass(frozen=True, slots=True)
class CorpusIngestionEntry:
    """Result of adapting and validating one raw provider record."""

    index: int
    record: CanonicalBoardRecord | None
    validation: ValidationResult | None
    error: str | None = None

    @property
    def accepted(self) -> bool:
        return (
            self.record is not None
            and self.validation is not None
            and self.validation.status
            in {
                ValidationStatus.ACCEPT,
                ValidationStatus.ACCEPT_WITH_WARNINGS,
            }
        )


@dataclass(frozen=True, slots=True)
class CorpusIngestionResult:
    """Immutable result of one provider batch ingestion."""

    dataset: CorpusDataset
    entries: tuple[CorpusIngestionEntry, ...]

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def accepted(self) -> int:
        return sum(
            entry.accepted
            for entry in self.entries
        )

    @property
    def rejected(self) -> int:
        return self.total - self.accepted

    @property
    def warnings(self) -> int:
        return sum(
            entry.validation is not None
            and entry.validation.status
            is ValidationStatus.ACCEPT_WITH_WARNINGS
            for entry in self.entries
        )


def ingest_corpus(
    *,
    dataset_id: str,
    adapter: CorpusAdapter,
    raw_records: Iterable[Mapping[str, Any]],
    description: str | None = None,
) -> CorpusIngestionResult:
    """Adapt, validate, and collect accepted canonical records.

    Adapter exceptions are retained as rejected ingestion entries.

    Validation REJECT results are retained in the audit trail but are not
    inserted into the canonical dataset.
    """

    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError(
            "dataset_id must be a non-blank string"
        )

    if not hasattr(adapter, "provider_name"):
        raise TypeError(
            "adapter must provide provider_name"
        )

    if not callable(getattr(adapter, "adapt", None)):
        raise TypeError(
            "adapter must provide adapt(raw)"
        )

    entries: list[CorpusIngestionEntry] = []
    accepted_records: list[CanonicalBoardRecord] = []

    for index, raw in enumerate(raw_records):
        if not isinstance(raw, Mapping):
            entries.append(
                CorpusIngestionEntry(
                    index=index,
                    record=None,
                    validation=None,
                    error="raw record must be a mapping",
                )
            )
            continue

        try:
            record = adapter.adapt(raw)
        except Exception as exc:
            entries.append(
                CorpusIngestionEntry(
                    index=index,
                    record=None,
                    validation=None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        if not isinstance(record, CanonicalBoardRecord):
            entries.append(
                CorpusIngestionEntry(
                    index=index,
                    record=None,
                    validation=None,
                    error=(
                        "adapter did not return "
                        "CanonicalBoardRecord"
                    ),
                )
            )
            continue

        validation = validate_record(record)

        entry = CorpusIngestionEntry(
            index=index,
            record=record,
            validation=validation,
        )
        entries.append(entry)

        if entry.accepted:
            accepted_records.append(record)

    dataset = CorpusDataset(
        dataset_id=dataset_id,
        records=tuple(accepted_records),
        description=description,
    )

    return CorpusIngestionResult(
        dataset=dataset,
        entries=tuple(entries),
    )
