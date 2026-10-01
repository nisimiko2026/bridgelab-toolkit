"""A3.7 multi-external evidence composition tests."""

import pytest

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case_composition import (
    compose_multi_external_bidding_decision_case,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
)


def evidence(
    provider_id: str,
    call: str,
    *,
    scope: EvidenceScope = EvidenceScope.PROVIDER,
    system_id: str | None = None,
    partnership_id: str | None = None,
) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )

    result = CapabilityResult(
        provider=descriptor,
        status=ProviderStatus.SUCCESS,
        recommendation=Call.parse(call),
        explanation=f"{provider_id} recommendation.",
    )

    return DecisionEvidence(
        result=result,
        scope=scope,
        system_id=system_id,
        partnership_id=partnership_id,
    )


def bridgelab_evidence(call: str = "3C") -> DecisionEvidence:
    return evidence(
        "bridgelab",
        call,
        scope=EvidenceScope.PARTNERSHIP,
        system_id="TWO_OVER_ONE_GF",
        partnership_id="nisim-nily",
    )


def test_composes_multiple_external_observations():
    bridge = bridgelab_evidence("3C")
    ben = evidence("ben", "4H")
    brl = evidence("brl", "3H")

    case = compose_multi_external_bidding_decision_case(
        case_id="a37-001",
        bridgelab=bridge,
        external=(ben, brl),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert case.bridgelab is bridge
    assert case.external == (ben, brl)
    assert len(case.disagreements) == 2


def test_each_external_is_compared_with_bridgelab():
    case = compose_multi_external_bidding_decision_case(
        case_id="a37-002",
        bridgelab=bridgelab_evidence("3C"),
        external=(
            evidence("ben", "4H"),
            evidence("brl", "3H"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert case.disagreements[0].left_provider_id == "bridgelab"
    assert case.disagreements[0].right_provider_id == "ben"

    assert case.disagreements[1].left_provider_id == "bridgelab"
    assert case.disagreements[1].right_provider_id == "brl"


def test_different_unknown_external_systems_are_classified_independently():
    case = compose_multi_external_bidding_decision_case(
        case_id="a37-003",
        bridgelab=bridgelab_evidence("3C"),
        external=(
            evidence("ben", "4H"),
            evidence("brl", "3H"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert tuple(
        disagreement.kind
        for disagreement in case.disagreements
    ) == (
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
    )


def test_agreement_and_disagreement_can_coexist():
    case = compose_multi_external_bidding_decision_case(
        case_id="a37-004",
        bridgelab=bridgelab_evidence("3C"),
        external=(
            evidence("ben", "3C"),
            evidence("brl", "3H"),
        ),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert case.disagreements[0].kind is DisagreementKind.AGREEMENT
    assert (
        case.disagreements[1].kind
        is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM
    )


def test_external_order_is_preserved():
    ben = evidence("ben", "4H")
    brl = evidence("brl", "3H")
    expert = evidence("expert-corpus", "4H")

    case = compose_multi_external_bidding_decision_case(
        case_id="a37-005",
        bridgelab=bridgelab_evidence("3C"),
        external=(ben, brl, expert),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert case.external == (ben, brl, expert)
    assert tuple(
        item.right_provider_id
        for item in case.disagreements
    ) == (
        "ben",
        "brl",
        "expert-corpus",
    )


def test_duplicate_provider_ids_are_not_collapsed():
    ben_v1 = evidence("ben", "4H")
    ben_v2 = evidence("ben", "3H")

    case = compose_multi_external_bidding_decision_case(
        case_id="a37-006",
        bridgelab=bridgelab_evidence("3C"),
        external=(ben_v1, ben_v2),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
            DisagreementContext(external_system_known=False),
        ),
    )

    assert len(case.external) == 2
    assert case.external[0] is ben_v1
    assert case.external[1] is ben_v2
    assert len(case.disagreements) == 2


def test_empty_external_collection_is_valid():
    bridge = bridgelab_evidence("3C")

    case = compose_multi_external_bidding_decision_case(
        case_id="a37-007",
        bridgelab=bridge,
        external=(),
        disagreement_contexts=(),
    )

    assert case.bridgelab is bridge
    assert case.external == ()
    assert case.disagreements == ()


def test_context_count_must_match_external_count():
    with pytest.raises(
        ValueError,
        match="external and disagreement_contexts must have equal length",
    ):
        compose_multi_external_bidding_decision_case(
            case_id="a37-008",
            bridgelab=bridgelab_evidence("3C"),
            external=(
                evidence("ben", "4H"),
                evidence("brl", "3H"),
            ),
            disagreement_contexts=(
                DisagreementContext(external_system_known=False),
            ),
        )


def test_notes_are_preserved():
    case = compose_multi_external_bidding_decision_case(
        case_id="a37-009",
        bridgelab=bridgelab_evidence("3C"),
        external=(evidence("ben", "4H"),),
        disagreement_contexts=(
            DisagreementContext(external_system_known=False),
        ),
        notes=("Multiple external observations retained.",),
    )

    assert case.notes == (
        "Multiple external observations retained.",
    )
