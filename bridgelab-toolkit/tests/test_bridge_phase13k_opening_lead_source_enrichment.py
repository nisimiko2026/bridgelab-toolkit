from dataclasses import asdict
from pathlib import Path

from benchmarks.opening_lead_source_enrichment import run_opening_lead_source_enrichment_benchmark
from benchmarks.opening_lead_source_readiness_audit import run_opening_lead_source_readiness_audit
from bridge import PolicyRegistry, create_standard_sayc_router


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "knowledge/play/defence/opening-leads/fourth-best.md"
RESULT = run_opening_lead_source_enrichment_benchmark()


def test_enriched_contract_has_every_required_section():
    text = SOURCE.read_text(encoding="utf-8")
    for heading in ("Rule name", "Scope", "Policy dependency", "Trigger", "Card choice",
                    "Exceptions and unresolved boundaries", "Precedence", "Source evidence",
                    "Implementation status"):
        assert f"### {heading}" in text


def test_suit_selection_and_card_treatment_are_not_conflated():
    text = SOURCE.read_text(encoding="utf-8")
    assert "card-within-suit" in text
    assert "not a suit-selection rule" in text
    assert "does not choose among multiple suits" in text


def test_contract_scope_policy_and_unknown_boundaries_are_explicit():
    text = SOURCE.read_text(encoding="utf-8")
    assert "opening lead only" in text and "primarily notrump" in text
    assert "FOURTH_BEST" in text and "Missing or unknown policy does not imply fourth-best" in text
    assert "Suit-contract use is unresolved" in text


def test_trigger_card_exceptions_and_precedence_are_source_bounded():
    text = SOURCE.read_text(encoding="utf-8")
    assert "at least four cards" in text and "fourth-highest card" in text
    assert "touching honor sequence" in text and "within the selected suit" in text
    assert "does not establish a universal priority" in text
    assert "introduces no external bridge rule" in text


def test_reaudit_remains_honest_and_generates_no_recommendation():
    historical = run_opening_lead_source_readiness_audit()
    assert historical.candidate_rules == 10 and historical.candidate_fixtures == 15
    assert (RESULT.executable_candidates_before, RESULT.executable_candidates_after) == (0, 0)
    assert RESULT.policy_executable_candidates_after == RESULT.recommendations_generated == 0


def test_policy_state_routes_and_cumulative_counts_are_unchanged():
    assert PolicyRegistry().opening_lead_policy_ids == ()
    assert len(create_standard_sayc_router().routes) == 45
    assert RESULT.architecture["cumulative_positions_or_requests"] == 110
    assert RESULT.architecture["opening_lead_recommendations"] == 0
    assert RESULT.architecture["defensive_recommendations"] == 0


def test_enrichment_is_deterministic_and_selects_closure_audit():
    assert asdict(RESULT) == asdict(run_opening_lead_source_enrichment_benchmark())
    assert RESULT.phase13l_direction == "E. PHASE 13 COVERAGE / CLOSURE AUDIT"
