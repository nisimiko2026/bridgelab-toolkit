from dataclasses import FrozenInstanceError, fields

import pytest

from benchmarks.opening_lead_policy_architecture import (
    FOURTH, RUSINOW, run_opening_lead_policy_architecture_benchmark,
)
from bridge import (
    OPENING_LEAD_POLICY_OPTION, KnowledgeSource, OpeningLeadHonorStyle,
    OpeningLeadLengthMethod, OpeningLeadPolicy, OpeningLeadTopOfNothing,
    PolicyRegistry, assess_opening_lead_policy,
)


def test_policy_and_metadata_are_immutable():
    policy = OpeningLeadPolicy("fixture", sources=(FOURTH,))
    with pytest.raises(FrozenInstanceError):
        policy.policy_id = "changed"
    with pytest.raises(FrozenInstanceError):
        assess_opening_lead_policy(policy).explanation = "changed"


def test_only_three_source_backed_dimensions_exist():
    names = {item.name for item in fields(OpeningLeadPolicy)}
    assert names == {"policy_id", "length_method", "honor_style", "top_of_nothing", "explanation", "sources"}


def test_enum_contracts_are_exact_and_unknown_is_first_class():
    assert [item.name for item in OpeningLeadLengthMethod] == ["FOURTH_BEST", "THIRD_AND_FIFTH", "OTHER", "UNKNOWN"]
    assert [item.name for item in OpeningLeadHonorStyle] == ["STANDARD", "RUSINOW", "UNKNOWN"]
    assert [item.name for item in OpeningLeadTopOfNothing] == ["ENABLED", "DISABLED", "UNKNOWN"]


def test_missing_policy_is_allowed_and_never_implies_standard():
    result = assess_opening_lead_policy(None)
    assert result.policy_id is None and not result.is_resolved
    assert result.honor_style is OpeningLeadHonorStyle.UNKNOWN
    assert result.sources == ()


def test_explicit_source_backed_choices_and_evidence_are_preserved():
    policy = OpeningLeadPolicy(
        "fixture", OpeningLeadLengthMethod.FOURTH_BEST,
        OpeningLeadHonorStyle.RUSINOW, OpeningLeadTopOfNothing.ENABLED,
        "Explicit fixture.", (FOURTH, RUSINOW),
    )
    result = assess_opening_lead_policy(policy)
    assert result.length_method is OpeningLeadLengthMethod.FOURTH_BEST
    assert result.honor_style is OpeningLeadHonorStyle.RUSINOW
    assert result.top_of_nothing is OpeningLeadTopOfNothing.ENABLED
    assert result.sources == (FOURTH, RUSINOW)


@pytest.mark.parametrize("field,value", [
    ("length_method", "fourth-best"), ("honor_style", "standard"),
    ("top_of_nothing", "enabled"), ("sources", [FOURTH]),
])
def test_invalid_policy_values_are_rejected(field, value):
    with pytest.raises(TypeError):
        OpeningLeadPolicy("fixture", **{field: value})


def test_policy_architecture_has_no_card_or_state_surface():
    names = {item.name for item in fields(OpeningLeadPolicy)}
    assert not names.intersection({"card", "hand", "contract", "lead", "recommendation"})
    assert not hasattr(assess_opening_lead_policy(OpeningLeadPolicy("fixture")), "card")


def test_registry_default_and_backward_compatibility():
    assert OPENING_LEAD_POLICY_OPTION == "opening_lead_policy"
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert PolicyRegistry().opening_lead_policy("missing") is None
    assert PolicyRegistry.from_policies().opening_lead_policy_ids == ()


def test_registry_accepts_explicit_policy_and_rejects_duplicates():
    policy = OpeningLeadPolicy("Fixture", sources=(KnowledgeSource("source"),))
    registry = PolicyRegistry.from_policies(opening_lead_policies=(policy,))
    assert registry.opening_lead_policy_ids == ("Fixture",)
    assert registry.opening_lead_policy("fixture") is policy
    with pytest.raises(ValueError):
        PolicyRegistry.from_opening_lead_policies((policy, OpeningLeadPolicy("fixture")))


def test_assessment_is_deterministic():
    policy = OpeningLeadPolicy("fixture", explanation="Stable.", sources=(FOURTH,))
    assert assess_opening_lead_policy(policy) == assess_opening_lead_policy(policy)


def test_benchmark_exact_guards():
    result = run_opening_lead_policy_architecture_benchmark()
    assert (result.policy_fixtures, result.explicit_policies, result.unknown_policies) == (10, 8, 2)
    assert result.source_backed_policy_dimensions == 3
    assert result.invalid_policies == result.recommendations_generated == 0
    assert result.architecture["opening_lead_recommendations"] == 0
    assert result.architecture["defensive_recommendations"] == 0
    assert result.architecture["bidding_recommendations"] == 2
    assert result.architecture["declarer_recommendations"] == 2
    assert result.architecture["total_positions_or_requests"] == 80
