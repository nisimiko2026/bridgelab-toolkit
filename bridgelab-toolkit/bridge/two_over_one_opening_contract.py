"""Phase 30K declarative, non-executable 2/1 base-opening contract.

Only source-level system evidence is recorded here. Partnership choices,
hand assessment, precedence, and opening execution belong to later layers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum

from .system_profiles import SystemProfile


class OpeningContractEvidence(str, Enum):
    EXPLICIT = "EXPLICIT"
    TYPICAL = "TYPICAL"
    APPROXIMATE = "APPROXIMATE"
    VARIABLE = "VARIABLE"
    UNSPECIFIED = "UNSPECIFIED"


_ARTICLE = "bidding/systems/2-over-1"
_FAMILIES = ("opening.1c", "opening.1d", "opening.1h", "opening.1s", "opening.1nt")
_BINDING_KEYS = frozenset({
    "one_level_strength_policy",
    "minor_length_policy",
    "minor_selection_precedence",
    "equal_minor_precedence",
    "five_five_major_precedence",
    "one_notrump_range",
    "one_notrump_five_card_major_policy",
    "one_notrump_shape_policy",
    "suit_vs_notrump_precedence",
    "strong_hand_precedence",
})


def _nonblank(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be blank")
    return value


def _strings(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    normalized = tuple(sorted({_nonblank(value, name) for value in values}))
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class TwoOverOneOpeningFamilyContract:
    family: str
    base_system: SystemProfile
    natural: bool | None
    natural_evidence: OpeningContractEvidence
    minimum_length: int | None
    minimum_length_evidence: OpeningContractEvidence
    hcp_min: int | None
    hcp_max: int | None
    strength_evidence: OpeningContractEvidence
    balanced_required: bool | None
    balanced_evidence: OpeningContractEvidence
    candidate_notrump_ranges: tuple[tuple[int, int], ...]
    required_bindings: tuple[str, ...]
    source_article: str
    source_headings: tuple[str, ...]
    executable: bool = False
    production_adopted: bool = False
    contract_version: str = "30K.1"

    def __post_init__(self) -> None:
        family = _nonblank(self.family, "family").casefold()
        if family not in _FAMILIES:
            raise ValueError("family is outside the five Phase 30K opening families")
        object.__setattr__(self, "family", family)
        if self.base_system is not SystemProfile.TWO_OVER_ONE_GF:
            raise ValueError("family contract requires TWO_OVER_ONE_GF")
        for name in ("natural_evidence", "minimum_length_evidence", "strength_evidence",
                     "balanced_evidence"):
            if not isinstance(getattr(self, name), OpeningContractEvidence):
                raise TypeError(f"{name} must be OpeningContractEvidence")
        for name, evidence_name in (("natural", "natural_evidence"),
                                    ("balanced_required", "balanced_evidence")):
            value = getattr(self, name)
            evidence = getattr(self, evidence_name)
            if value is not None and not isinstance(value, bool):
                raise TypeError(f"{name} must be bool or None")
            if (value is None) is not (evidence is OpeningContractEvidence.UNSPECIFIED):
                raise ValueError(f"{name} and {evidence_name} must agree on unspecified evidence")
        if self.minimum_length is None:
            if self.minimum_length_evidence is not OpeningContractEvidence.UNSPECIFIED:
                raise ValueError("missing minimum length requires UNSPECIFIED evidence")
        elif (not isinstance(self.minimum_length, int) or isinstance(self.minimum_length, bool)
              or not 1 <= self.minimum_length <= 13
              or self.minimum_length_evidence is OpeningContractEvidence.UNSPECIFIED):
            raise ValueError("minimum length requires a card count and evidence")
        if (self.hcp_min is None) != (self.hcp_max is None):
            raise ValueError("HCP bounds must both be present or absent")
        if self.hcp_min is not None:
            if (not isinstance(self.hcp_min, int) or isinstance(self.hcp_min, bool)
                    or not isinstance(self.hcp_max, int) or isinstance(self.hcp_max, bool)
                    or not 0 <= self.hcp_min <= self.hcp_max <= 40):
                raise ValueError("invalid HCP bounds")
        elif self.strength_evidence not in (
                OpeningContractEvidence.UNSPECIFIED, OpeningContractEvidence.VARIABLE):
            raise ValueError("missing HCP bounds require UNSPECIFIED or VARIABLE evidence")
        if not isinstance(self.candidate_notrump_ranges, tuple):
            raise TypeError("candidate_notrump_ranges must be a tuple")
        if self.family != "opening.1nt" and self.candidate_notrump_ranges:
            raise ValueError("only opening.1nt may have notrump range candidates")
        if self.candidate_notrump_ranges:
            if self.strength_evidence is not OpeningContractEvidence.VARIABLE:
                raise ValueError("alternative notrump ranges require VARIABLE evidence")
            if self.hcp_min is not None or self.hcp_max is not None:
                raise ValueError("candidate ranges are not a selected universal HCP range")
            for pair in self.candidate_notrump_ranges:
                if (not isinstance(pair, tuple) or len(pair) != 2
                        or any(not isinstance(value, int) or isinstance(value, bool) for value in pair)
                        or not 0 <= pair[0] <= pair[1] <= 40):
                    raise ValueError("invalid candidate notrump range")
            if len(set(self.candidate_notrump_ranges)) != len(self.candidate_notrump_ranges):
                raise ValueError("duplicate candidate notrump range")
        elif self.family == "opening.1nt":
            raise ValueError("opening.1nt requires source range candidates")
        bindings = _strings(self.required_bindings, "required_bindings")
        if not set(bindings) <= _BINDING_KEYS:
            raise ValueError("unknown required binding")
        object.__setattr__(self, "required_bindings", bindings)
        article = _nonblank(self.source_article, "source_article")
        if article != _ARTICLE:
            raise ValueError("source_article must be the canonical 2/1 article")
        object.__setattr__(self, "source_article", article)
        object.__setattr__(self, "source_headings", _strings(self.source_headings, "source_headings"))
        object.__setattr__(self, "contract_version", _nonblank(self.contract_version, "contract_version"))
        if self.executable or self.production_adopted:
            raise ValueError("Phase 30K family contracts are declarative only")

    def to_dict(self) -> dict:
        return {
            "family": self.family, "base_system": self.base_system.value,
            "natural": self.natural, "natural_evidence": self.natural_evidence.value,
            "minimum_length": self.minimum_length,
            "minimum_length_evidence": self.minimum_length_evidence.value,
            "hcp_min": self.hcp_min, "hcp_max": self.hcp_max,
            "strength_evidence": self.strength_evidence.value,
            "balanced_required": self.balanced_required,
            "balanced_evidence": self.balanced_evidence.value,
            "candidate_notrump_ranges": [list(pair) for pair in self.candidate_notrump_ranges],
            "required_bindings": list(self.required_bindings),
            "source_article": self.source_article,
            "source_headings": list(self.source_headings),
            "executable": self.executable,
            "production_adopted": self.production_adopted,
            "contract_version": self.contract_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class TwoOverOneOpeningContract:
    base_system: SystemProfile
    families: tuple[TwoOverOneOpeningFamilyContract, ...]
    production_bidding_changed: bool = False
    production_adopted: bool = False
    contract_version: str = "30K.1"
    required_bindings: tuple[str, ...] = field(init=False)
    all_required_bindings_resolved: bool = field(init=False)
    ready_for_execution: bool = field(init=False)
    recommended_next_phase: str = field(init=False)

    def __post_init__(self) -> None:
        if self.base_system is not SystemProfile.TWO_OVER_ONE_GF:
            raise ValueError("base contract requires TWO_OVER_ONE_GF")
        if not isinstance(self.families, tuple) or not all(
                isinstance(item, TwoOverOneOpeningFamilyContract) for item in self.families):
            raise TypeError("families must contain TwoOverOneOpeningFamilyContract")
        if {item.family for item in self.families} != set(_FAMILIES) or len(self.families) != len(_FAMILIES):
            raise ValueError("base contract must contain exactly the five scoped families")
        if any(item.base_system is not self.base_system for item in self.families):
            raise ValueError("family base system differs from contract")
        families = tuple(sorted(self.families, key=lambda item: item.family))
        object.__setattr__(self, "families", families)
        required = tuple(sorted({key for item in families for key in item.required_bindings}))
        object.__setattr__(self, "required_bindings", required)
        # A system-level source contract intentionally selects no partnership
        # values. Every required binding remains unresolved here.
        resolved = not required
        object.__setattr__(self, "all_required_bindings_resolved", resolved)
        ready = resolved and all(item.executable for item in families)
        object.__setattr__(self, "ready_for_execution", ready)
        next_phase = (
            "30L_NISIM_NILY_OPENING_CONTRACT_BINDING" if not resolved else
            "30L_TWO_OVER_ONE_OPENING_ENGINE" if not ready else
            "30L_OPENING_INTEGRATION"
        )
        object.__setattr__(self, "recommended_next_phase", next_phase)
        object.__setattr__(self, "contract_version", _nonblank(self.contract_version, "contract_version"))
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30K cannot claim production activation")

    def family(self, family: str) -> TwoOverOneOpeningFamilyContract | None:
        key = _nonblank(family, "family").casefold()
        return next((item for item in self.families if item.family == key), None)

    def to_dict(self) -> dict:
        return {
            "base_system": self.base_system.value,
            "families": [item.to_dict() for item in self.families],
            "required_bindings": list(self.required_bindings),
            "all_required_bindings_resolved": self.all_required_bindings_resolved,
            "ready_for_execution": self.ready_for_execution,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "recommended_next_phase": self.recommended_next_phase,
            "contract_version": self.contract_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class TwoOverOneOpeningContractCapability:
    base_contract_defined: bool
    source_evidence_typed: bool
    required_bindings_explicit: bool
    partnership_binding_ready: bool
    all_required_bindings_resolved: bool
    opening_execution_ready: bool
    production_bidding_changed: bool = False
    production_adopted: bool = False
    version: str = "30K.1"

    def __post_init__(self) -> None:
        if self.production_bidding_changed or self.production_adopted:
            raise ValueError("Phase 30K cannot claim production activation")

    def to_dict(self) -> dict:
        return {
            "base_contract_defined": self.base_contract_defined,
            "source_evidence_typed": self.source_evidence_typed,
            "required_bindings_explicit": self.required_bindings_explicit,
            "partnership_binding_ready": self.partnership_binding_ready,
            "all_required_bindings_resolved": self.all_required_bindings_resolved,
            "opening_execution_ready": self.opening_execution_ready,
            "production_bidding_changed": self.production_bidding_changed,
            "production_adopted": self.production_adopted,
            "version": self.version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def capability_for_two_over_one_opening_contract(
    contract: TwoOverOneOpeningContract,
) -> TwoOverOneOpeningContractCapability:
    if not isinstance(contract, TwoOverOneOpeningContract):
        raise TypeError("contract must be TwoOverOneOpeningContract")
    return TwoOverOneOpeningContractCapability(
        base_contract_defined=len(contract.families) == len(_FAMILIES),
        source_evidence_typed=all(
            isinstance(item.natural_evidence, OpeningContractEvidence)
            and isinstance(item.minimum_length_evidence, OpeningContractEvidence)
            and isinstance(item.strength_evidence, OpeningContractEvidence)
            and isinstance(item.balanced_evidence, OpeningContractEvidence)
            for item in contract.families),
        required_bindings_explicit=bool(contract.required_bindings),
        partnership_binding_ready=bool(contract.required_bindings),
        all_required_bindings_resolved=contract.all_required_bindings_resolved,
        opening_execution_ready=contract.ready_for_execution,
    )


def build_two_over_one_opening_contract() -> TwoOverOneOpeningContract:
    """Return source claims and missing binding slots, independent of profile."""
    E = OpeningContractEvidence
    common = dict(base_system=SystemProfile.TWO_OVER_ONE_GF,
                  source_article=_ARTICLE, executable=False)
    minor_bindings = (
        "one_level_strength_policy", "minor_length_policy",
        "minor_selection_precedence", "equal_minor_precedence",
        "suit_vs_notrump_precedence", "strong_hand_precedence",
    )
    major_bindings = (
        "one_level_strength_policy", "five_five_major_precedence",
        "suit_vs_notrump_precedence", "strong_hand_precedence",
    )
    families = (
        TwoOverOneOpeningFamilyContract(
            family="opening.1c", natural=True, natural_evidence=E.EXPLICIT,
            minimum_length=3, minimum_length_evidence=E.TYPICAL,
            hcp_min=None, hcp_max=None, strength_evidence=E.UNSPECIFIED,
            balanced_required=None, balanced_evidence=E.UNSPECIFIED,
            candidate_notrump_ranges=(), required_bindings=minor_bindings,
            source_headings=("System Requirements", "Opening Requirements / 1♣"), **common),
        TwoOverOneOpeningFamilyContract(
            family="opening.1d", natural=True, natural_evidence=E.EXPLICIT,
            minimum_length=4, minimum_length_evidence=E.TYPICAL,
            hcp_min=None, hcp_max=None, strength_evidence=E.UNSPECIFIED,
            balanced_required=None, balanced_evidence=E.UNSPECIFIED,
            candidate_notrump_ranges=(), required_bindings=minor_bindings,
            source_headings=("System Requirements", "Opening Requirements / 1♦"), **common),
        TwoOverOneOpeningFamilyContract(
            family="opening.1h", natural=True, natural_evidence=E.EXPLICIT,
            minimum_length=5, minimum_length_evidence=E.EXPLICIT,
            hcp_min=12, hcp_max=21, strength_evidence=E.APPROXIMATE,
            balanced_required=None, balanced_evidence=E.UNSPECIFIED,
            candidate_notrump_ranges=(), required_bindings=major_bindings,
            source_headings=("System Requirements", "Opening Requirements / 1♥"), **common),
        TwoOverOneOpeningFamilyContract(
            family="opening.1s", natural=True, natural_evidence=E.EXPLICIT,
            minimum_length=5, minimum_length_evidence=E.EXPLICIT,
            hcp_min=12, hcp_max=21, strength_evidence=E.APPROXIMATE,
            balanced_required=None, balanced_evidence=E.UNSPECIFIED,
            candidate_notrump_ranges=(), required_bindings=major_bindings,
            source_headings=("System Requirements", "Opening Requirements / 1♠"), **common),
        TwoOverOneOpeningFamilyContract(
            family="opening.1nt", natural=None, natural_evidence=E.UNSPECIFIED,
            minimum_length=None, minimum_length_evidence=E.UNSPECIFIED,
            hcp_min=None, hcp_max=None, strength_evidence=E.VARIABLE,
            balanced_required=True, balanced_evidence=E.TYPICAL,
            candidate_notrump_ranges=((15, 17), (14, 16), (16, 18)),
            required_bindings=("one_notrump_range", "one_notrump_five_card_major_policy",
                               "one_notrump_shape_policy", "suit_vs_notrump_precedence",
                               "strong_hand_precedence"),
            source_headings=("System Requirements", "Opening Requirements / 1NT",
                             "Partnership Agreements / Notrump Range"), **common),
    )
    return TwoOverOneOpeningContract(SystemProfile.TWO_OVER_ONE_GF, families)
