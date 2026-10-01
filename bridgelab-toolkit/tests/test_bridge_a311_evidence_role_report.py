"""A3.11 evidence-role report tests."""

import json

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
from bridge.evidence_role_report import (
    build_evidence_role_report,
)
from bridge.evidence_role_summary import (
    summarize_evidence_roles,
)


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


def test_empty_case_report():
    view = build_decision_case_role_view(
        DecisionCase(case_id="a311-empty")
    )

    report = build_evidence_role_report(view)

    assert report.case_id == "a311-empty"
    assert report.total == 0
    assert report.roles_present == ()

    assert all(
        count == 0
        for _, count in report.counts
    )


def test_report_contains_policy_and_external_counts():
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
    brl = bidding_evidence(
        "brl",
        "3H",
        EvidenceScope.PROVIDER,
    )

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a311-mixed",
            bridgelab=bridge,
            external=(ben, brl),
        )
    )

    report = build_evidence_role_report(view)

    counts = dict(report.counts)

    assert report.total == 3
    assert counts["policy_recommendation"] == 1
    assert counts["external_recommendation"] == 2


def test_report_uses_stable_string_role_names():
    bridge = bidding_evidence(
        "bridgelab",
        "3C",
        EvidenceScope.PARTNERSHIP,
    )

    report = build_evidence_role_report(
        build_decision_case_role_view(
            DecisionCase(
                case_id="a311-names",
                bridgelab=bridge,
            )
        )
    )

    assert report.roles_present == (
        "policy_recommendation",
    )

    assert tuple(
        role
        for role, _ in report.counts
    ) == (
        "policy_recommendation",
        "external_recommendation",
        "observed_action",
        "outcome_measurement",
        "statistical_estimate",
    )


def test_as_dict_is_json_friendly():
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

    report = build_evidence_role_report(
        build_decision_case_role_view(
            DecisionCase(
                case_id="a311-json",
                bridgelab=bridge,
                external=(ben,),
            )
        )
    )

    payload = report.as_dict()

    encoded = json.dumps(payload)

    assert isinstance(encoded, str)
    assert payload["case_id"] == "a311-json"
    assert payload["total"] == 2
    assert payload["counts"]["policy_recommendation"] == 1
    assert payload["counts"]["external_recommendation"] == 1


def test_same_bid_does_not_merge_roles():
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

    report = build_evidence_role_report(
        build_decision_case_role_view(
            DecisionCase(
                case_id="a311-same",
                bridgelab=bridge,
                external=(ben,),
            )
        )
    )

    counts = dict(report.counts)

    assert report.total == 2
    assert counts["policy_recommendation"] == 1
    assert counts["external_recommendation"] == 1


def test_precomputed_summary_can_be_used():
    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a311-summary",
            bridgelab=bidding_evidence(
                "bridgelab",
                "3C",
                EvidenceScope.PARTNERSHIP,
            ),
        )
    )

    summary = summarize_evidence_roles(view)

    report = build_evidence_role_report(
        view,
        summary=summary,
    )

    assert report.total == summary.total
    assert report.roles_present == tuple(
        role.value
        for role in summary.roles_present
    )


def test_report_has_no_winner_or_scoring_fields():
    report = build_evidence_role_report(
        build_decision_case_role_view(
            DecisionCase(
                case_id="a311-passive",
                bridgelab=bidding_evidence(
                    "bridgelab",
                    "3C",
                    EvidenceScope.PARTNERSHIP,
                ),
                external=(
                    bidding_evidence(
                        "ben",
                        "4H",
                        EvidenceScope.PROVIDER,
                    ),
                ),
            )
        )
    )

    assert not hasattr(report, "winner")
    assert not hasattr(report, "preferred")
    assert not hasattr(report, "score")
    assert not hasattr(report, "recommendation")


def test_building_report_does_not_modify_view_or_summary():
    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a311-immutable",
            bridgelab=bidding_evidence(
                "bridgelab",
                "3C",
                EvidenceScope.PARTNERSHIP,
            ),
        )
    )

    summary = summarize_evidence_roles(view)

    original_evidence = view.evidence
    original_counts = summary.counts

    build_evidence_role_report(
        view,
        summary=summary,
    )

    assert view.evidence is original_evidence
    assert summary.counts is original_counts
