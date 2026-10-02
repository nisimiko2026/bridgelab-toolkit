"""A6.9 contract alternative evaluation pipeline tests."""

import pytest

from bridge.alternative_outcome_comparison import AlternativeOutcomeComparison
from bridge.auction import Bid, Contract, Strain
from bridge.contract_alternative_evaluation import (
    ContractAlternative,
    ContractAlternativeEvaluation,
    ContractAlternativeEvaluationPipelineResult,
    evaluate_contract_alternatives,
)
from bridge.deals import generate_deal
from bridge.models import Seat, Vulnerability
from bridge.simulation_outcome import (
    SimulationOutcomeSummary,
    summarize_simulation_outcomes,
)


def contract(level: int, strain: Strain, declarer: Seat = Seat.NORTH) -> Contract:
    return Contract(Bid(level, strain), declarer)


def alternatives():
    return (
        ContractAlternative("3NT", contract(3, Strain.NOTRUMP)),
        ContractAlternative("4S", contract(4, Strain.SPADES)),
    )


def run_pipeline():
    return evaluate_contract_alternatives(
        deal=generate_deal(69),
        vulnerability=Vulnerability.NONE,
        alternatives=alternatives(),
        declarer_tricks={
            "3NT": (8, 9, 9, 10),
            "4S": (9, 10, 10, 11),
        },
    )


def test_contract_alternative_accepts_valid_values() -> None:
    item = ContractAlternative(" 4S ", contract(4, Strain.SPADES))
    assert item.alternative_id == "4S"
    assert item.contract.bid.strain is Strain.SPADES


def test_contract_alternative_rejects_blank_id() -> None:
    with pytest.raises(ValueError, match="non-blank"):
        ContractAlternative(" ", contract(4, Strain.SPADES))


def test_contract_alternative_rejects_invalid_contract() -> None:
    with pytest.raises(TypeError, match="contract must be Contract"):
        ContractAlternative("x", object())


def test_pipeline_scores_and_aggregates_every_alternative() -> None:
    result = run_pipeline()

    assert len(result.evaluations) == 2
    assert all(
        isinstance(item.summary, SimulationOutcomeSummary)
        for item in result.evaluations
    )
    assert result.evaluation("3NT").summary.sample_count == 4
    assert result.evaluation("4S").summary.sample_count == 4


def test_pipeline_preserves_alternative_order() -> None:
    result = run_pipeline()
    assert tuple(x.alternative_id for x in result.evaluations) == ("3NT", "4S")
    assert tuple(x.alternative_id for x in result.comparison.rows) == ("3NT", "4S")


def test_pipeline_builds_existing_comparison_type() -> None:
    result = run_pipeline()
    assert isinstance(result.comparison, AlternativeOutcomeComparison)
    assert result.comparison.equal_sample_counts is True
    assert result.comparison.min_sample_count == 4
    assert result.comparison.max_sample_count == 4


def test_pipeline_uses_fixed_ns_score_perspective() -> None:
    result = evaluate_contract_alternatives(
        deal=generate_deal(70),
        vulnerability=Vulnerability.NONE,
        alternatives=(
            ContractAlternative("north", contract(2, Strain.SPADES, Seat.NORTH)),
            ContractAlternative("east", contract(2, Strain.SPADES, Seat.EAST)),
        ),
        declarer_tricks={
            "north": (8,),
            "east": (8,),
        },
    )

    assert result.evaluation("north").summary.mean_ns_score > 0
    assert result.evaluation("east").summary.mean_ns_score < 0


def test_pipeline_reports_unequal_sample_counts_without_reweighting() -> None:
    result = evaluate_contract_alternatives(
        deal=generate_deal(71),
        vulnerability=Vulnerability.NONE,
        alternatives=alternatives(),
        declarer_tricks={
            "3NT": (9, 9),
            "4S": (10, 10, 10),
        },
    )

    assert result.comparison.equal_sample_counts is False
    assert result.comparison.min_sample_count == 2
    assert result.comparison.max_sample_count == 3


def test_pipeline_accepts_generator_alternatives() -> None:
    items = alternatives()
    result = evaluate_contract_alternatives(
        deal=generate_deal(72),
        vulnerability=Vulnerability.NONE,
        alternatives=(item for item in items),
        declarer_tricks={"3NT": (9,), "4S": (10,)},
    )
    assert len(result.evaluations) == 2


def test_pipeline_requires_at_least_two_alternatives() -> None:
    with pytest.raises(ValueError, match="at least two"):
        evaluate_contract_alternatives(
            deal=generate_deal(73),
            vulnerability=Vulnerability.NONE,
            alternatives=(alternatives()[0],),
            declarer_tricks={"3NT": (9,)},
        )


def test_pipeline_rejects_duplicate_alternative_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        evaluate_contract_alternatives(
            deal=generate_deal(74),
            vulnerability=Vulnerability.NONE,
            alternatives=(
                ContractAlternative("same", contract(3, Strain.NOTRUMP)),
                ContractAlternative("same", contract(4, Strain.SPADES)),
            ),
            declarer_tricks={"same": (9,)},
        )


def test_pipeline_rejects_missing_samples() -> None:
    with pytest.raises(ValueError, match="missing declarer-trick samples"):
        evaluate_contract_alternatives(
            deal=generate_deal(75),
            vulnerability=Vulnerability.NONE,
            alternatives=alternatives(),
            declarer_tricks={"3NT": (9,)},
        )


def test_pipeline_rejects_unexpected_samples() -> None:
    with pytest.raises(ValueError, match="unexpected declarer-trick samples"):
        evaluate_contract_alternatives(
            deal=generate_deal(76),
            vulnerability=Vulnerability.NONE,
            alternatives=alternatives(),
            declarer_tricks={
                "3NT": (9,),
                "4S": (10,),
                "extra": (7,),
            },
        )


def test_pipeline_rejects_non_mapping_samples() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        evaluate_contract_alternatives(
            deal=generate_deal(77),
            vulnerability=Vulnerability.NONE,
            alternatives=alternatives(),
            declarer_tricks=(),
        )


def test_pipeline_rejects_invalid_deal() -> None:
    with pytest.raises(TypeError, match="deal must be Deal"):
        evaluate_contract_alternatives(
            deal=object(),
            vulnerability=Vulnerability.NONE,
            alternatives=alternatives(),
            declarer_tricks={"3NT": (9,), "4S": (10,)},
        )


def test_pipeline_rejects_invalid_vulnerability() -> None:
    with pytest.raises(TypeError, match="vulnerability must be Vulnerability"):
        evaluate_contract_alternatives(
            deal=generate_deal(78),
            vulnerability=object(),
            alternatives=alternatives(),
            declarer_tricks={"3NT": (9,), "4S": (10,)},
        )


def test_pipeline_rejects_non_contract_alternative_entries() -> None:
    with pytest.raises(TypeError, match="all alternatives must be ContractAlternative"):
        evaluate_contract_alternatives(
            deal=generate_deal(79),
            vulnerability=Vulnerability.NONE,
            alternatives=(alternatives()[0], object()),
            declarer_tricks={"3NT": (9,), "x": (10,)},
        )


def test_evaluation_lookup_and_missing_id() -> None:
    result = run_pipeline()
    assert result.evaluation("4S").alternative_id == "4S"
    with pytest.raises(KeyError):
        result.evaluation("missing")


def test_pipeline_does_not_choose_winner_or_best() -> None:
    result = run_pipeline()
    forbidden = ("winner", "best", "recommended", "recommendation", "ranking", "rank")
    for name in forbidden:
        assert not hasattr(result, name)
        assert not hasattr(result.comparison, name)


def test_evaluation_wrapper_validates_summary_type() -> None:
    with pytest.raises(TypeError, match="summary must be SimulationOutcomeSummary"):
        ContractAlternativeEvaluation("x", object())


def test_pipeline_result_requires_matching_comparison_order() -> None:
    a = summarize_simulation_outcomes(
        contract=contract(3, Strain.NOTRUMP),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(9,),
    )
    b = summarize_simulation_outcomes(
        contract=contract(4, Strain.SPADES),
        vulnerability=Vulnerability.NONE,
        declarer_tricks=(10,),
    )
    from bridge.alternative_outcome_comparison import (
        OutcomeAlternative,
        compare_simulation_outcomes,
    )

    comparison = compare_simulation_outcomes(
        (OutcomeAlternative("b", b), OutcomeAlternative("a", a))
    )
    evaluations = (
        ContractAlternativeEvaluation("a", a),
        ContractAlternativeEvaluation("b", b),
    )

    with pytest.raises(ValueError, match="comparison rows must match"):
        ContractAlternativeEvaluationPipelineResult(evaluations, comparison)
