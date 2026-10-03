"""Stable benchmark case identity and replay references.

A8.2 keeps synthetic replay (seed + canonical deal) separate from real-corpus
identity (dataset + record).  It does not infer one form from the other.
"""
from __future__ import annotations
from dataclasses import dataclass
from .benchmark_manifest import DatasetIdentity, DatasetKind
from .deals import Deal

def _text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-blank string")
    return value.strip()

@dataclass(frozen=True, slots=True)
class SyntheticReplay:
    seed: int
    deal: str
    def __post_init__(self):
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")
        object.__setattr__(self, "deal", _text("deal", self.deal))
        Deal.parse(self.deal)

    def replay_deal(self) -> Deal:
        return Deal.parse(self.deal)

@dataclass(frozen=True, slots=True)
class CorpusReplay:
    record_id: str
    source: str | None = None
    def __post_init__(self):
        object.__setattr__(self, "record_id", _text("record_id", self.record_id))
        if self.source is not None:
            object.__setattr__(self, "source", _text("source", self.source))

@dataclass(frozen=True, slots=True)
class BenchmarkCaseIdentity:
    case_id: str
    dataset: DatasetIdentity
    synthetic: SyntheticReplay | None = None
    corpus: CorpusReplay | None = None

    def __post_init__(self):
        object.__setattr__(self, "case_id", _text("case_id", self.case_id))
        if not isinstance(self.dataset, DatasetIdentity):
            raise TypeError("dataset must be DatasetIdentity")
        if self.dataset.kind is DatasetKind.SYNTHETIC:
            if not isinstance(self.synthetic, SyntheticReplay) or self.corpus is not None:
                raise ValueError("synthetic dataset requires synthetic replay only")
        elif self.dataset.kind is DatasetKind.REAL:
            if not isinstance(self.corpus, CorpusReplay) or self.synthetic is not None:
                raise ValueError("real dataset requires corpus replay only")

    @classmethod
    def for_synthetic(cls, case_id, dataset, *, seed, deal):
        if not isinstance(deal, Deal):
            raise TypeError("deal must be Deal")
        return cls(case_id, dataset, synthetic=SyntheticReplay(seed, deal.serialize()))

    @classmethod
    def for_corpus(cls, case_id, dataset, *, record_id, source=None):
        return cls(case_id, dataset, corpus=CorpusReplay(record_id, source))

    @property
    def replay_key(self) -> str:
        if self.synthetic is not None:
            return f"{self.dataset.dataset_id}@{self.dataset.version}:seed:{self.synthetic.seed}"
        assert self.corpus is not None
        return f"{self.dataset.dataset_id}@{self.dataset.version}:record:{self.corpus.record_id}"
