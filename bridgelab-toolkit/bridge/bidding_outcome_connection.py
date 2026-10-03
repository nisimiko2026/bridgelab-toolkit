"""Connect bidding evidence to A6 contract-outcome alternatives.

A7.7 — Outcome Connection.

Bidding recommendations are not automatically final contracts: a bid may be
an intermediate auction action and declarer is not implied by the call alone.
The caller therefore supplies an explicit Contract for each evidence source
that should enter outcome measurement. This layer preserves provenance and
deduplicates identical contracts for measurement only; it does not rank,
vote, or change bidding policy.
"""
from __future__ import annotations

from dataclasses import dataclass

from .auction import Contract
from .contract_alternative_evaluation import ContractAlternative
from .decision_evidence import DecisionEvidence
from .multi_adviser_disagreement import MultiAdviserDisagreementResult


@dataclass(frozen=True, slots=True)
class EvidenceContract:
    provider_id: str
    contract: Contract

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self, "provider_id", self.provider_id.strip())
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")


@dataclass(frozen=True, slots=True)
class OutcomeCandidate:
    alternative: ContractAlternative
    provider_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.alternative, ContractAlternative):
            raise TypeError("alternative must be ContractAlternative")
        if not isinstance(self.provider_ids, tuple) or not self.provider_ids:
            raise ValueError("provider_ids must be a non-empty tuple")
        if not all(isinstance(x, str) and x.strip() for x in self.provider_ids):
            raise ValueError("provider_ids must contain non-blank strings")

    @property
    def contract(self) -> Contract:
        return self.alternative.contract


@dataclass(frozen=True, slots=True)
class BiddingOutcomeCandidates:
    candidates: tuple[OutcomeCandidate, ...]

    @property
    def alternatives(self) -> tuple[ContractAlternative, ...]:
        return tuple(x.alternative for x in self.candidates)


def build_bidding_outcome_candidates(
    *,
    analysis: MultiAdviserDisagreementResult,
    contracts: tuple[EvidenceContract, ...],
) -> BiddingOutcomeCandidates:
    """Build unique A6 alternatives from explicit evidence-to-contract mappings."""
    if not isinstance(analysis, MultiAdviserDisagreementResult):
        raise TypeError("analysis must be MultiAdviserDisagreementResult")
    if not isinstance(contracts, tuple):
        raise TypeError("contracts must be a tuple")
    if not all(isinstance(x, EvidenceContract) for x in contracts):
        raise TypeError("contracts must contain EvidenceContract")

    evidence = (analysis.decision_case.bridgelab,) + analysis.decision_case.external
    evidence_ids = tuple(x.result.provider.provider_id for x in evidence)
    evidence_keys = {x.casefold() for x in evidence_ids}

    mapping = {}
    for item in contracts:
        key = item.provider_id.casefold()
        if key not in evidence_keys:
            raise ValueError(f"contract provider is not present in evidence: {item.provider_id}")
        if key in mapping:
            raise ValueError(f"duplicate contract mapping for provider: {item.provider_id}")
        mapping[key] = item.contract

    # Preserve evidence order. Providers without an explicit contract mapping are
    # omitted: no final contract is fabricated from a bidding call.
    grouped: list[tuple[Contract, list[str]]] = []
    for item in evidence:
        provider_id = item.result.provider.provider_id
        contract = mapping.get(provider_id.casefold())
        if contract is None:
            continue
        for existing, providers in grouped:
            if existing == contract:
                providers.append(provider_id)
                break
        else:
            grouped.append((contract, [provider_id]))

    candidates = []
    for index, (contract, providers) in enumerate(grouped, start=1):
        # Stable neutral ID; provider provenance is stored separately because
        # multiple advisers may map to the same measurable contract.
        alternative = ContractAlternative(f"candidate-{index}", contract)
        candidates.append(OutcomeCandidate(alternative, tuple(providers)))

    return BiddingOutcomeCandidates(tuple(candidates))
