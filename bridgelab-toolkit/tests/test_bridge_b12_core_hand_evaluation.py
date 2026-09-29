"""B1.2 raw facts and compatibility of the single core evaluator."""
from dataclasses import FrozenInstanceError, asdict, fields
import ast
import inspect
from pathlib import Path

import pytest

from bridge.evaluation import (
    HandEvaluation, Shortness, ShapeClass, SUIT_ORDER, classify_shape, controls,
    distribution, evaluate_hand, high_card_points, suit_lengths,
)
from bridge.models import Card, Hand, Rank, Suit


def with_spades(holding):
    cards = [Card(Suit.SPADES, Rank.parse(r)) for r in holding]
    remaining = [Card(s, r) for s in (Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS) for r in Rank]
    return Hand.from_cards(cards + remaining[:13-len(cards)])


def test_hcp_total_and_suit_breakdown_preserve_legacy_controls():
    hand = Hand.parse('AK84.QJ6.A75.K92')
    facts = evaluate_hand(hand)
    assert facts.hcp == high_card_points(hand) == 17
    assert facts.hcp_by_suit == (7, 3, 4, 3)
    assert sum(facts.hcp_by_suit) == facts.hcp
    assert facts.controls == controls(hand) == 6
    assert facts.honor_evidence(Suit.SPADES).hcp == 7


@pytest.mark.parametrize('text,shape,kind', [
    ('AKQJ.KQJ.876.543', (4,3,3,3), ShapeClass.BALANCED),
    ('AKQJ.KQJ9.876.54', (4,4,3,2), ShapeClass.BALANCED),
    ('AKQJ9.KQJ.876.54', (5,3,3,2), ShapeClass.BALANCED),
    ('AKQJ9.KQJ9.87.54', (5,4,2,2), ShapeClass.SEMI_BALANCED),
    ('AKQJ98.KQJ.87.54', (6,3,2,2), ShapeClass.SEMI_BALANCED),
    ('AKQJT98765.K2.3.-', (10,2,1,0), ShapeClass.UNBALANCED),
])
def test_exact_and_normalized_shapes_preserve_existing_classification(text,shape,kind):
    hand=Hand.parse(text);facts=evaluate_hand(hand)
    assert facts.suit_lengths == suit_lengths(hand) == hand.shape
    assert facts.distribution == distribution(hand) == shape
    assert facts.shape_class is classify_shape(hand) is kind
    assert sum(facts.suit_lengths)==13


@pytest.mark.parametrize('text,hcp,score', [
    ('KQ987.AJ76.32.54',10,19),
    ('KQJ98.AJ76.32.54',11,20),
    ('KQJ98.AQ76.32.54',12,21),
])
def test_rule20_raw_arithmetic_and_existing_policy_compatibility(text,hcp,score):
    from bridge.nisim_nily_opening_policy import assess_rule_of_20
    hand=Hand.parse(text);raw=evaluate_hand(hand).rule_of_20
    assert (raw.hcp,raw.longest_suit_length,raw.second_longest_suit_length,raw.score)==(hcp,5,4,score)
    assert not hasattr(raw,'qualifies') and not hasattr(raw,'recommended_call')
    old=assess_rule_of_20(hand)
    assert old.score==score and old.qualifies==(score>=20)
    assert old.intended_11_hcp_use==(hcp==11)
    assert old.selects_opening_call is False and old.failure_implies_pass is False


@pytest.mark.parametrize('holding,first,second,guarded', [
    ('',True,False,False), ('2',False,True,False), ('A',True,True,False),
    ('K',False,True,False), ('K2',False,True,True), ('Q2',False,False,False),
    ('A32',True,False,False), ('AK2',True,True,True), ('Q32',False,False,False),
])
def test_control_patterns_separate_honor_and_shortness_bases(holding,first,second,guarded):
    facts=evaluate_hand(with_spades(holding));evidence=facts.honor_evidence(Suit.SPADES)
    assert evidence.first_round_control is first
    assert evidence.second_round_control is second
    assert evidence.has_guarded_king is guarded
    assert (Suit.SPADES in facts.first_round_controls) is first
    assert (Suit.SPADES in facts.second_round_controls) is second
    # A void has no honor points, and a singleton king is not a guarded king.
    assert evidence.hcp==sum({Rank.ACE:4,Rank.KING:3,Rank.QUEEN:2,Rank.JACK:1}.get(r,0) for r in evidence.honors)


@pytest.mark.parametrize('holding,losers', [
    ('',0),('A',0),('K',1),('Q',1),('2',1),
    ('AK',0),('AQ',1),('KQ',1),('A2',1),('K2',1),('Q2',2),('32',2),
    ('AKQ',0),('AK2',1),('AQ2',1),('KQ2',1),('A32',2),('K32',2),('Q32',3),('432',3),
    ('AKQJT98',0),('QJT98',3),('KQJT98',1),
])
def test_documented_raw_loser_convention(holding,losers):
    facts=evaluate_hand(with_spades(holding))
    assert facts.honor_evidence(Suit.SPADES).losers==losers
    assert facts.losers_by_suit[0]==losers
    assert facts.losers==sum(facts.losers_by_suit)
    assert 0<=facts.losers<=12


def test_shortness_is_suit_specific_with_no_value_bonus():
    facts=evaluate_hand(Hand.parse('AKQJT98765.K2.3.-'))
    assert facts.shortness_by_suit==(Shortness.NONE,Shortness.DOUBLETON,Shortness.SINGLETON,Shortness.VOID)
    assert (facts.voids,facts.singletons,facts.doubletons)==(1,1,1)
    assert facts.hcp==13 and facts.controls==4
    assert facts.honor_evidence(Suit.CLUBS).shortness is Shortness.VOID
    for name in ('shortness_bonus','distribution_points','erv','adjusted_playing_tricks'):
        assert not hasattr(facts,name)


def test_playing_trick_evidence_reuses_raw_quality_evidence_without_valuation():
    facts=evaluate_hand(Hand.parse('AKQJ9.KQJ.876.54'))
    assert facts.natural_playing_trick_evidence is facts.suit_quality_evidence
    evidence=facts.natural_playing_trick_evidence[0]
    assert evidence is facts.quality_evidence(Suit.SPADES)
    assert evidence.ranks==(Rank.ACE,Rank.KING,Rank.QUEEN,Rank.JACK,Rank.NINE)
    assert evidence.sequences==((Rank.ACE,Rank.KING,Rank.QUEEN,Rank.JACK),)
    assert not hasattr(facts,'natural_playing_tricks')


def test_deterministic_frozen_results_and_legacy_constructor_serialization():
    hand=Hand.parse('AK84.QJ6.A75.K92')
    a=evaluate_hand(hand);b=evaluate_hand(Hand.from_cards(reversed(sorted(hand.cards))))
    assert a==b and hash(a)==hash(b)
    assert a.rule_of_20==b.rule_of_20
    assert a.first_round_controls==b.first_round_controls
    legacy=('hcp','controls','suit_lengths','distribution','shape_class','voids','singletons',
            'doubletons','longest_length','longest_suits','suit_honor_evidence','suit_quality_evidence')
    assert tuple(f.name for f in fields(HandEvaluation))==legacy
    assert HandEvaluation(*(getattr(a,name) for name in legacy))==a
    assert tuple(asdict(a))==legacy
    for value,name in ((a,'hcp'),(a.rule_of_20,'hcp'),(a.honor_evidence(Suit.SPADES),'length')):
        with pytest.raises(FrozenInstanceError):setattr(value,name,0)


@pytest.mark.parametrize('system', ['SAYC','TWO_OVER_ONE_GF','Precision','Blue Club','nisim-nily'])
def test_existing_context_evaluation_is_system_and_profile_independent(system):
    from bridge.auction import Auction
    from bridge.bidding_rules import BiddingContext,SystemContext
    from bridge.models import Seat,Vulnerability
    hand=Hand.parse('AK84.QJ6.A75.K92')
    expected=evaluate_hand(hand)
    context=BiddingContext.create(hand=hand,auction=Auction(Seat.NORTH),vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(system,{'partnership_profile':'arbitrary-pair'}))
    assert context.evaluation==expected
    assert context.evaluation.losers==expected.losers
    assert tuple(inspect.signature(evaluate_hand).parameters)==('hand',)


def test_core_dependencies_remain_system_neutral():
    import bridge.evaluation as module
    tree=ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
    imported={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
    assert imported <= {'__future__','dataclasses','enum','models'}