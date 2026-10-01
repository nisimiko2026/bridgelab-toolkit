"""A3.10 evidence-role summary tests."""

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case import DecisionCase
from bridge.decision_case_roles import (
    build_decision_case_role_view,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    EvidenceScope,
)
from bridge.evidence_role_summary import (
    summarize_evidence_roles,
)
from bridge.evidence_roles import EvidenceRole


def bidding_evidence(
    provider_id: str,
    call: str,
    scope: EvidenceScope,
) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )

    return DecisionEvidence(
        result=CapabilityResult(
            provider=descriptor,
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=scope,
    )


def test_empty_view_has_zero_counts():
    view = build_decision_case_role_view(
        DecisionCase(case_id="a310-empty")
    )

    summary = summarize_evidence_roles(view)

    assert summary.total == 0
    assert summary.roles_present == ()

    for role in EvidenceRole:
        assert summary.count(role) == 0


def test_policy_evidence_is_counted():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a310-policy",
            bridgelab=bridge,
        )
    )

    summary = summarize_evidence_roles(view)

    assert summary.total == 1
    assert (
        summary.count(EvidenceRole.POLICY_RECOMMENDATION)
        == 1
    )


def test_multiple_external_recommendations_are_counted():
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )
    brl = bidding_evidence(
        "brl",
        "3H",
        EvidenceScope.PROVIDER,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a310-external",
            external=(ben, brl),
        )
    )

    summary = summarize_evidence_roles(view)

    assert summary.total == 2
    assert (
        summary.count(EvidenceRole.EXTERNAL_RECOMMENDATION)
        == 2
    )


def test_same_bid_is_still_two_distinct_roles():
    bridge = bidding_evidence(
        "bridgelab",
        "4H",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a310-same",
            bridgelab=bridge,
            external=(ben,),
        )
    )

    summary = summarize_evidence_roles(view)

    assert summary.total == 2
    assert (
        summary.count(EvidenceRole.POLICY_RECOMMENDATION)
        == 1
    )
    assert (
        summary.count(EvidenceRole.EXTERNAL_RECOMMENDATION)
        == 1
    )


def test_roles_present_follows_role_definition_order():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a310-order",
            bridgelab=bridge,
            external=(ben,),
        )
    )

    summary = summarize_evidence_roles(view)

    assert summary.roles_present == (
        EvidenceRole.POLICY_RECOMMENDATION,
        EvidenceRole.EXTERNAL_RECOMMENDATION,
    )


def test_summary_does_not_expose_winner_or_score():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )
    ben = bidding_evidence(
        "ben",
        "4H",
        EvidenceScope.PROVIDER,
    )

    summary = summarize_evidence_roles(
        build_decision_case_role_view(
            DecisionCase(
                case_id="a310-passive",
                bridgelab=bridge,
                external=(ben,),
            )
        )
    )

    assert not hasattr(summary, "winner")
    assert not hasattr(summary, "preferred")
    assert not hasattr(summary, "score")
    assert not hasattr(summary, "recommendation")


def test_summary_does_not_modify_view():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a310-immutable",
            bridgelab=bridge,
        )
    )

    original = view.evidence

    summarize_evidence_roles(view)

    assert view.evidence is original
