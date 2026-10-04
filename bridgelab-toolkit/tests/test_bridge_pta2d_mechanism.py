"""Exact small physical-play oracles and PT-A2D boundary guards."""
from dataclasses import replace
from pathlib import Path
import inspect
import pytest
from bridge.models import Card,Seat,Suit,Hand
from bridge.deals import Deal
from bridge.auction_information import AuctionInformationState
from bridge.shortness_mechanism import (PlayPosition,MechanismOracle,DDSOptimalMoves,
    Restriction,Status,BudgetExceeded,bounded_studied_paths)
from benchmarks.pta2d_mechanism_validation import fixture,FIXTURES
from benchmarks.pta2c_target_validation import paired_metrics


@pytest.fixture(scope='module')
def measured():
    rows={}
    for name in FIXTURES:
        p=fixture(name)
        o=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=500000)
        a=o.analyze(p)
        restrictions={r:MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=500000).restricted(p,r,unrestricted=a.optimum) for r in Restriction}
        rows[name]=(a,restrictions)
    return rows


def test_one_unavoidable_ruff_adds_one(measured):
    a,r=measured['crossruff_void']
    assert a.studied_ruff_bounds==(1,1) and a.every_optimal_line_requires_studied_ruff
    assert a.optimum==3 and r[Restriction.STRICT].value==2 and r[Restriction.STRICT].loss==1


def test_two_independent_ruff_capacity_adds_two_under_strict_policy(measured):
    a,r=measured['two_ruff_capacity']
    assert (2,2,0) in a.profiles
    assert a.optimum==3 and r[Restriction.STRICT].value==1 and r[Restriction.STRICT].loss==2
    # Two ruffs can be realized, but are not present in every optimal line.
    assert a.studied_ruff_bounds==(0,2)
    assert r[Restriction.DISCARD_IF_POSSIBLE].loss==1
    assert r[Restriction.NO_CREDIT].loss==2


def test_zero_effect_singleton_with_winning_trumps(measured):
    a,r=measured['zero_singleton']
    assert a.optimum==3 and a.studied_ruff_bounds==(0,0)
    assert all(x.loss==0 for x in r.values())
    assert sum(c.suit==Suit.DIAMONDS for c in fixture('zero_singleton').hands[2])==1


def test_void_is_exact_card_information(measured):
    assert all(c.suit!=Suit.DIAMONDS for c in fixture('crossruff_void').hands[2])
    assert measured['crossruff_void'][0].studied_ruff_bounds==(1,1)


def test_crossruff_joint_occurrence_not_product_of_marginal_maxima(measured):
    a,_=measured['crossruff_void']
    assert a.profiles==((1,1,1),) and a.reciprocal_ruff_presence==(True,True)


def test_multiple_optimal_lines_retain_range(measured):
    a,r=measured['ambiguous_singleton']
    assert a.studied_ruff_bounds==(0,1) and a.optimal_line_count==608
    assert a.every_optimal_line_requires_studied_ruff is False
    assert r[Restriction.STRICT].loss==0


def test_option_threat_different_from_observed_ruff(measured):
    a,r=measured['ruff_option_threat']
    assert a.studied_ruff_bounds==(0,1)
    assert r[Restriction.DISCARD_IF_POSSIBLE].loss==1
    assert (0,0,0) in a.profiles


def test_infeasible_prohibition_is_not_zero(measured):
    _,r=measured['one_ruff']
    a=r[Restriction.STRICT]
    assert a.status==Status.INFEASIBLE and a.value is None and a.loss is None
    assert r[Restriction.DISCARD_IF_POSSIBLE].loss==1


@pytest.mark.parametrize('seat',tuple(Seat))
def test_seat_orientation(seat,measured):
    p=fixture('crossruff_void'); shift=(tuple(Seat).index(seat)-2)%4
    seats=tuple(Seat);hands=[None]*4
    for i,h in enumerate(p.hands):hands[(i+shift)%4]=h
    rotated=PlayPosition(tuple(hands),seats[(seats.index(p.leader)+shift)%4],p.trump)
    r=MechanismOracle(seat,Suit.DIAMONDS,p.trump).analyze(rotated)
    assert r==measured['crossruff_void'][0]


def test_follow_suit_and_physical_card_conservation():
    p=fixture('crossruff_void'); before=frozenset(c for h in p.hands for c in h)
    p,_,_=p.advance(Card.parse('3D'))
    assert p.legal()==(Card.parse('KD'),)
    with pytest.raises(ValueError):p.advance(Card.parse('AC'))
    assert frozenset(c for h in p.hands for c in h)|frozenset(p.trick)==before


def test_overruff_only_winning_hand_is_counted():
    p=PlayPosition(tuple(frozenset([Card.parse(c)]) for c in ('2D','2S','3S','4S')),Seat.NORTH,Suit.SPADES)
    r=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).analyze(p)
    assert r.optimum==0 and r.studied_ruff_bounds==(0,0)


def test_budget_exhaustion_is_typed_and_not_zero():
    r=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=1).analyze(fixture('one_ruff'))
    assert r.status==Status.BUDGET and r.optimum is None and r.studied_ruff_bounds==(0,2)
    assert r.every_optimal_line_requires_studied_ruff is None


def test_restricted_budget_never_promoted_to_exact():
    r=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=1).restricted(fixture('one_ruff'),Restriction.STRICT)
    assert r.status==Status.BUDGET and r.value is None and r.loss is None


def test_no_transformed_deal_required_and_extreme_holding():
    import json
    d=Deal.parse(json.loads(Path('output/pta2c_targets/impossible_reference_census.json').read_text(encoding='utf-8'))['cases'][1]['source'])
    before=d.serialize();p=PlayPosition.from_deal(d,Seat.NORTH,Suit.SPADES)
    class Limited:
        def optimal(self,*args):raise BudgetExceeded()
    r,_=bounded_studied_paths(p,Seat.SOUTH,Suit.DIAMONDS,Limited())
    assert d.serialize()==before
    assert p.hands[2]==d.hand(Seat.SOUTH).cards
    assert r.status==Status.BUDGET and r.maximum_upper_bound==12
    assert r.optimum is None


def test_exchange_unevaluable_is_valid_physical_position():
    import json
    from bridge.counterfactual_calibration import diagnose
    item=json.loads(Path('output/pta2c_targets/case_analysis.json').read_text(encoding='utf-8'))['newly_defined']
    # The saved case has a source deal, even though its exchange control is absent.
    source=Deal.parse(item['source_deal_id'])
    assert not diagnose(source,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).evaluable
    p=PlayPosition.from_deal(source,Seat.NORTH,Suit.SPADES)
    MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)._validate(p)


def test_prior_target_comparison_has_correct_sign_and_ranks():
    r=paired_metrics([0,1,2],[1,0,2])
    assert r['mean_difference']==0 and r['median_difference']==0
    assert r['sign_disagreements']==2 and r['pearson']==pytest.approx(.5)
    assert r['spearman']==pytest.approx(.5)
    assert paired_metrics([None],[2])=={'n':0}


def test_deterministic_results_and_memoization(measured):
    p=fixture('one_ruff');o=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    assert o.analyze(p)==measured['one_ruff'][0]
    count=o.nodes
    assert o.analyze(p)==measured['one_ruff'][0] and o.nodes==count
    assert o.cache_hits>0


def test_leakage_boundary_no_auction_time_entry_point():
    import bridge.shortness_mechanism as module
    state=AuctionInformationState.start(Seat.SOUTH,Hand.parse('AKQ42.9876.3.J76'),Seat.SOUTH)
    with pytest.raises(TypeError):PlayPosition.from_deal(state,Seat.NORTH,Suit.SPADES)
    text=Path(module.__file__).read_text(encoding='utf-8')
    assert 'ConditionalSampler' not in text and 'AuctionInformationState' not in text
    # There is no mixed visible-state/actual-hidden-source estimator to leak cards.
    assert not hasattr(module,'expected_shortness')


def test_no_production_integration():
    from bridge.sayc_route_configuration import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes)==47
    for name in ('sayc.py','engine_router.py','sayc_route_configuration.py'):
        assert 'shortness_mechanism' not in (Path('bridge')/name).read_text(encoding='utf-8')


@pytest.mark.parametrize('name',tuple(FIXTURES))
def test_dds_optimum_and_first_actions_agree_with_independent_minimax(name):
    pytest.importorskip('endplay')
    p=fixture(name);o=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,max_nodes=500000)
    exact=o._optimal(p)
    assert DDSOptimalMoves().optimal(p,Seat.SOUTH)==exact


def test_all_tied_dds_paths_match_independent_oracle(measured):
    pytest.importorskip('endplay')
    o=MechanismOracle(Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,dds=DDSOptimalMoves(5000))
    assert o.analyze(fixture('ambiguous_singleton'))==measured['ambiguous_singleton'][0]


def test_safe_bounds_contain_exact_endgame_result(measured):
    pytest.importorskip('endplay')
    exact=measured['crossruff_void'][0].studied_ruff_bounds
    limited,_=bounded_studied_paths(fixture('crossruff_void'),Seat.SOUTH,Suit.DIAMONDS,DDSOptimalMoves(2))
    assert limited.minimum_lower_bound<=exact[0]<=exact[1]<=limited.maximum_upper_bound
    complete,_=bounded_studied_paths(fixture('crossruff_void'),Seat.SOUTH,Suit.DIAMONDS,DDSOptimalMoves(2000))
    assert complete.extrema_exact and (complete.minimum_lower_bound,complete.maximum_upper_bound)==exact


def test_invalid_position_and_scope_rejected():
    p=fixture('one_ruff')
    with pytest.raises(ValueError):replace(p,hands=(p.hands[0],)*4)
    with pytest.raises(ValueError):MechanismOracle(Seat.SOUTH,Suit.SPADES,Suit.SPADES)
    with pytest.raises(ValueError):MechanismOracle(Seat.NORTH,Suit.DIAMONDS,Suit.SPADES).analyze(fixture('ambiguous_singleton'))

def test_interval_comparisons_preserve_unidentified_correlations():
    from benchmarks.pta2d_mechanism_validation import interval_comparison
    rows=[{'bounds':{'minimum_lower_bound':0,'maximum_upper_bound':2},'prior':{'A':1},'source':'x'},
          {'bounds':{'minimum_lower_bound':0,'maximum_upper_bound':0},'prior':{'A':-2},'source':'y'}]
    r=interval_comparison(rows,'A')
    assert r['mean_difference_envelope']==[.5,1.5]
    assert r['median_difference_envelope']==[.5,1.5]
    assert r['sign_disagreement_count_bounds']==[1,2]
    assert r['pearson'] is None and r['spearman'] is None
    assert r['certain_large_disagreements']==['y']
    assert r['possible_large_disagreements']==['y']
    assert interval_comparison(rows,'undefined')=={'n':0}