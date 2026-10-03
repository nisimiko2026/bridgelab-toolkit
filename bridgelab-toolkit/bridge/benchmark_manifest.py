"""Deterministic identity contract for large-scale BridgeLab benchmarks."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

def _text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-blank string")
    return value.strip()

class DatasetKind(str, Enum):
    REAL = "real"
    SYNTHETIC = "synthetic"

@dataclass(frozen=True, slots=True)
class DatasetIdentity:
    dataset_id: str
    version: str
    kind: DatasetKind
    source: str
    record_count: int | None = None
    def __post_init__(self):
        object.__setattr__(self, "dataset_id", _text("dataset_id", self.dataset_id))
        object.__setattr__(self, "version", _text("version", self.version))
        object.__setattr__(self, "source", _text("source", self.source))
        if not isinstance(self.kind, DatasetKind):
            raise TypeError("kind must be DatasetKind")
        if self.record_count is not None:
            if not isinstance(self.record_count, int) or isinstance(self.record_count, bool):
                raise TypeError("record_count must be an integer or None")
            if self.record_count < 0:
                raise ValueError("record_count must be non-negative")

@dataclass(frozen=True, slots=True)
class BenchmarkProfileIdentity:
    system_id: str
    system_version: str
    partnership_id: str | None = None
    partnership_version: str | None = None
    resolved_profile_id: str | None = None
    resolved_profile_version: str | None = None
    def __post_init__(self):
        for n in ("system_id", "system_version"):
            object.__setattr__(self, n, _text(n, getattr(self, n)))
        for n in ("partnership_id","partnership_version","resolved_profile_id","resolved_profile_version"):
            v=getattr(self,n)
            if v is not None: object.__setattr__(self,n,_text(n,v))
        if (self.partnership_id is None) != (self.partnership_version is None):
            raise ValueError("partnership_id and partnership_version must be supplied together")
        if (self.resolved_profile_id is None) != (self.resolved_profile_version is None):
            raise ValueError("resolved_profile_id and resolved_profile_version must be supplied together")

@dataclass(frozen=True, slots=True)
class AdviserIdentity:
    provider_id: str
    implementation: str
    version: str
    model_id: str | None = None
    def __post_init__(self):
        for n in ("provider_id","implementation","version"):
            object.__setattr__(self,n,_text(n,getattr(self,n)))
        if self.model_id is not None: object.__setattr__(self,"model_id",_text("model_id",self.model_id))

@dataclass(frozen=True, slots=True)
class SolverIdentity:
    solver_id: str
    version: str
    def __post_init__(self):
        object.__setattr__(self,"solver_id",_text("solver_id",self.solver_id))
        object.__setattr__(self,"version",_text("version",self.version))

@dataclass(frozen=True, slots=True)
class BenchmarkManifest:
    benchmark_id: str
    benchmark_version: str
    dataset: DatasetIdentity
    profile: BenchmarkProfileIdentity
    advisers: tuple[AdviserIdentity,...] = ()
    solvers: tuple[SolverIdentity,...] = ()
    seeds: tuple[int,...] = ()
    engine_version: str | None = None
    source_revision: str | None = None
    notes: tuple[str,...] = ()
    def __post_init__(self):
        object.__setattr__(self,"benchmark_id",_text("benchmark_id",self.benchmark_id))
        object.__setattr__(self,"benchmark_version",_text("benchmark_version",self.benchmark_version))
        if not isinstance(self.dataset,DatasetIdentity): raise TypeError("dataset must be DatasetIdentity")
        if not isinstance(self.profile,BenchmarkProfileIdentity): raise TypeError("profile must be BenchmarkProfileIdentity")
        if not isinstance(self.advisers,tuple) or not all(isinstance(x,AdviserIdentity) for x in self.advisers): raise TypeError("advisers must contain AdviserIdentity")
        if not isinstance(self.solvers,tuple) or not all(isinstance(x,SolverIdentity) for x in self.solvers): raise TypeError("solvers must contain SolverIdentity")
        if not isinstance(self.seeds,tuple) or not all(isinstance(x,int) and not isinstance(x,bool) for x in self.seeds): raise TypeError("seeds must contain integers")
        if len(set(self.seeds)) != len(self.seeds): raise ValueError("seeds must be unique")
        if len({x.provider_id.casefold() for x in self.advisers}) != len(self.advisers): raise ValueError("adviser provider_id values must be unique")
        if len({x.solver_id.casefold() for x in self.solvers}) != len(self.solvers): raise ValueError("solver_id values must be unique")
        for n in ("engine_version","source_revision"):
            v=getattr(self,n)
            if v is not None: object.__setattr__(self,n,_text(n,v))
        if not isinstance(self.notes,tuple) or not all(isinstance(x,str) and x.strip() for x in self.notes): raise TypeError("notes must be a tuple of non-blank strings")
    @property
    def deterministic(self):
        return self.dataset.kind is DatasetKind.REAL or bool(self.seeds)
