"""A9.1 evidence-review contract.

Defines a conservative review vocabulary for replayable benchmark evidence.
The contract records what the evidence supports; it does not itself change
bidding policy, infer partnership agreements, rank gaps, or choose a bid.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewClassification(str, Enum):
    EXPECTED_ABSTENTION = "expected-abstention"
    CORE_GAP = "core-gap"
    SYSTEM_DEPENDENT = "system-dependent"
    UNKNOWN_CONVENTION = "unknown-convention"
    KNOWN_CONVENTION_MISSING_TREATMENT = "known-convention-missing-treatment"
    PARTNERSHIP_AGREEMENT = "partnership-agreement"
    JUDGMENT = "judgment"
    POSSIBLE_ENGINE_DEFECT = "possible-engine-defect"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"


class ReviewDisposition(str, Enum):
    NO_CHANGE = "no-change"
    NEEDS_MORE_EVIDENCE = "needs-more-evidence"
    CANDIDATE_KNOWLEDGE_WORK = "candidate-knowledge-work"
    CANDIDATE_ENGINE_INVESTIGATION = "candidate-engine-investigation"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    source_id: str
    statement: str

    def __post_init__(self):
        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if not self.statement.strip():
            raise ValueError("statement must be non-empty")


@dataclass(frozen=True, slots=True)
class EvidenceReview:
    replay_key: str
    classification: ReviewClassification
    disposition: ReviewDisposition
    rationale: str
    evidence: tuple[EvidenceReference, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.replay_key.strip():
            raise ValueError("replay_key must be non-empty")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")

        if self.classification is ReviewClassification.INSUFFICIENT_EVIDENCE:
            if self.disposition is not ReviewDisposition.NEEDS_MORE_EVIDENCE:
                raise ValueError(
                    "insufficient evidence must remain needs-more-evidence"
                )

        if self.classification is ReviewClassification.POSSIBLE_ENGINE_DEFECT:
            if self.disposition not in (
                ReviewDisposition.NEEDS_MORE_EVIDENCE,
                ReviewDisposition.CANDIDATE_ENGINE_INVESTIGATION,
            ):
                raise ValueError(
                    "possible engine defect may only request evidence or investigation"
                )

        if self.disposition in (
            ReviewDisposition.CANDIDATE_KNOWLEDGE_WORK,
            ReviewDisposition.CANDIDATE_ENGINE_INVESTIGATION,
        ) and not self.evidence:
            raise ValueError("candidate work requires explicit evidence")


def review(
    *,
    replay_key: str,
    classification: ReviewClassification,
    disposition: ReviewDisposition,
    rationale: str,
    evidence: tuple[EvidenceReference, ...] = (),
    notes: tuple[str, ...] = (),
) -> EvidenceReview:
    """Create an explicit evidence review.

    No classification is inferred from route frequency, abstention count,
    benchmark depth, or observed external bidding.
    """
    return EvidenceReview(
        replay_key=replay_key,
        classification=classification,
        disposition=disposition,
        rationale=rationale,
        evidence=evidence,
        notes=notes,
    )
