"""A4 hand-verified controls, seat-specific cue history and maximum decisions."""
from dataclasses import replace

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_rules import KnowledgeSource
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Suit, Vulnerability
from bridge.nisim_nily_jacoby_2nt import (
    SLAM_APPROVAL, JacobyDisposition as D, OpenerStrength as Strength,
    OpenerStrengthEvidence, JacobyContinuationIntent as Intent,
    JacobyContinuationEvidence as Evidence,
    assess_jacoby_2nt_slam_continuation as assess,
    assess_jacoby_2nt_responder, assess_jacoby_2nt_conditional_stop,
)
from bridge.nisim_nily_partnership_profile import NISIM_NILY_JACOBY_2NT_PROFILE as PROFILE, NISIM_NILY_PROFILE
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

ACES=Hand.parse('A432.A432.A32.A2')
NO_ACES=Hand.parse('KQJ2.KQJ2.Q32.J2')
SPADE_KING=Hand.parse('K432.Q432.A32.J2')
ACE_KING=Hand.parse('AK32.Q432.A32.32')
SOURCE=KnowledgeSource('test-only/b24a4-assessment')
# Historical side-suit calls are interpreted claims, not supplied hidden hands.
EXAMPLE=('1H','P','2NT','P','3C','P','3D','P','3S','P')


def run(calls,cards=ACES,kind=Intent.CUE_BID,bid='4C',round_number=None,
        classification=None,profile=PROFILE,dealer=Seat.NORTH,api=assess):
    auction=Auction(dealer,calls)
    intent=None if kind is None else Evidence(kind,cards,auction,'Explicit sourced direction and qualification.',(SOURCE,),
        Call.parse(bid) if kind is Intent.CUE_BID else None,round_number,
        Call.parse(bid) if kind is Intent.DIRECT_SLAM else None)
    strength=None if classification is None else OpenerStrengthEvidence(classification,cards,auction,'Explicit strength assessment.',(SOURCE,))
    kwargs=dict(auction=auction,vulnerability=Vulnerability.NONE,profile=profile,intent=intent)
    if api is not assess_jacoby_2nt_responder:
        kwargs['strength']=strength
    return api(cards,**kwargs)


def call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('calls,bid,suit',[
    (('1H','P','2NT','P','3H','P'),'3S',Suit.SPADES),
    (('1S','P','2NT','P','3S','P'),'4H',Suit.HEARTS),
    (('1H','P','2NT','P','3NT','P'),'4C',Suit.CLUBS),
    (('1S','P','2NT','P','3C','P'),'3D',Suit.DIAMONDS),
])
def test_first_cue_shows_actual_ace(calls,bid,suit):
    result=run(calls,bid=bid)
    assert call(result)==bid
    assert result.meaning.control_round==1 and result.meaning.control_basis=='ace'
    assert result.meaning.cue_suit is suit and result.meaning.slam_interest
    assert SLAM_APPROVAL in result.selected.sources and SOURCE in result.selected.sources
    shown=result.control_history[-1]
    assert shown.suit is suit and shown.round==1 and shown.seat is Seat.SOUTH
    assert shown.auction_index==6 and shown.call.serialize()==bid


@pytest.mark.parametrize('api',(assess,assess_jacoby_2nt_responder))
def test_existing_responder_entry_point_cannot_bypass_control_requirement(api):
    result=run(('1H','P','2NT','P','3H','P'),cards=NO_ACES,bid='3S',api=api)
    assert call(result) is None
    assert result.context.evaluation.hcp>13  # HCP never invents a control


def test_second_cue_shows_guarded_king_after_first_round_in_same_suit():
    result=run(EXAMPLE,cards=SPADE_KING,bid='4S',round_number=2)
    assert call(result)=='4S' and result.meaning.control_round==2
    assert result.meaning.control_basis=='guarded king'
    assert [(c.suit,c.round,c.seat,c.auction_index) for c in result.control_history]==[
        (Suit.DIAMONDS,1,Seat.SOUTH,6),(Suit.SPADES,1,Seat.NORTH,8),(Suit.SPADES,2,Seat.SOUTH,10)]
    assert result.control_history[1].basis=='auction control claim'


@pytest.mark.parametrize('round_number',(None,2))
def test_second_control_cannot_be_shown_without_prior_first(round_number):
    result=run(('1H','P','2NT','P','3H','P'),cards=SPADE_KING,bid='3S',round_number=round_number)
    assert call(result) is None


def test_explicit_second_round_request_without_history_rejected_even_with_ace_and_king():
    assert call(run(('1H','P','2NT','P','3H','P'),cards=ACE_KING,bid='3S',round_number=2)) is None


def test_first_control_of_a_different_suit_does_not_authorize_second_spade_control():
    calls=('1H','P','2NT','P','3H','P','4C','P')
    assert call(run(calls,cards=SPADE_KING,bid='4S',round_number=2)) is None


def test_history_alone_does_not_supply_missing_king_to_current_hand():
    assert call(run(EXAMPLE,cards=ACES,bid='4S')) is None


def test_wrong_control_round_and_third_cue_are_not_arbitrary_repetition():
    assert call(run(EXAMPLE,cards=ACE_KING,bid='4S',round_number=1)) is None
    third=EXAMPLE+('4S','P')
    assert call(run(third,cards=ACE_KING,bid='5S')) is None
    after_third=third+('5S','P')
    result=run(after_third,kind=Intent.ACE_ASK)
    assert call(result) is None and 'Third control cue' in result.blockers[0]


def test_opener_can_show_first_control_and_then_the_other_partner_second():
    opener=run(EXAMPLE[:-2],bid='3S')
    assert call(opener)=='3S' and opener.control_history[-1].seat is Seat.NORTH
    responder=run(EXAMPLE,cards=SPADE_KING,bid='4S')
    assert call(responder)=='4S' and responder.control_history[-1].seat is Seat.SOUTH


def test_same_player_may_later_show_a_different_round_with_actual_king():
    calls=('1H','P','2NT','P','3H','P','3S','P','4C','P')
    result=run(calls,cards=ACE_KING,bid='4S')
    assert call(result)=='4S'
    assert result.control_history[0].seat is result.control_history[-1].seat is Seat.SOUTH


def test_shortness_is_not_a_prior_ace_control_claim():
    calls=('1H','P','2NT','P','3S','P','4H','P')
    result=run(calls,cards=SPADE_KING,bid='4S',round_number=2,classification=Strength.MAXIMUM)
    assert call(result) is None and result.continuation_needed
    assert not result.control_history


def test_core_void_and_singleton_controls_are_explicit_not_fabricated_honors():
    void=Hand.parse('AKQJ32.KQJ2.432.-')
    first=run(('1H','P','2NT','P','3H','P'),cards=void,bid='4C')
    assert call(first)=='4C' and first.meaning.control_basis=='void'
    singleton=Hand.parse('AKQJ2.QJ32.432.2')
    second=run(('1H','P','2NT','P','3H','P','4C','P'),cards=singleton,bid='5C')
    assert call(second)=='5C' and second.meaning.control_basis=='singleton'
    assert second.meaning.control_round==2


@pytest.mark.parametrize('opening,shortness', [('1H','3C'),('1H','3S'),('1S','3H')])
@pytest.mark.parametrize('api',(assess,assess_jacoby_2nt_conditional_stop))
def test_maximum_opener_can_ask_aces(opening,shortness,api):
    calls=(opening,'P','2NT','P',shortness,'P','4'+opening[-1],'P')
    result=run(calls,kind=Intent.ACE_ASK,classification=Strength.MAXIMUM,api=api)
    assert call(result)=='4NT' and result.meaning.ace_ask and not result.continuation_needed


@pytest.mark.parametrize('shortness',('3C','3D','3S'))
def test_heart_trump_maximum_can_cue_legal_4s_with_first_control(shortness):
    calls=('1H','P','2NT','P',shortness,'P','4H','P')
    result=run(calls,bid='4S',classification=Strength.MAXIMUM)
    assert call(result)=='4S' and result.meaning.control_round==1
    assert result.control_history[-1].seat is Seat.NORTH
    assert SLAM_APPROVAL in result.selected.sources and SOURCE in result.selected.sources


@pytest.mark.parametrize('cards',(NO_ACES,SPADE_KING))
def test_maximum_cannot_invent_spade_ace_from_strength(cards):
    calls=('1H','P','2NT','P','3C','P','4H','P')
    result=run(calls,cards=cards,bid='4S',classification=Strength.MAXIMUM)
    assert call(result) is None and result.continuation_needed


def test_4s_is_not_a_side_cue_when_spades_are_trump():
    calls=('1S','P','2NT','P','3H','P','4S','P')
    result=run(calls,bid='4S',classification=Strength.MAXIMUM)
    assert call(result) is None and result.continuation_needed


@pytest.mark.parametrize('opening,shortness', [('1H','3C'),('1S','3H')])
@pytest.mark.parametrize('level',('6','7'))
def test_sourced_sufficiently_strong_maximum_can_bid_direct_trump_slam(opening,shortness,level):
    calls=(opening,'P','2NT','P',shortness,'P','4'+opening[-1],'P')
    result=run(calls,kind=Intent.DIRECT_SLAM,bid=level+opening[-1],classification=Strength.MAXIMUM)
    assert call(result)==level+opening[-1] and result.meaning.direct_slam
    assert SOURCE in result.selected.sources


@pytest.mark.parametrize('bid',('5H','6NT','6S'))
def test_unapproved_direct_slam_strains_or_levels_remain_unresolved(bid):
    calls=('1H','P','2NT','P','3C','P','4H','P')
    result=run(calls,kind=Intent.DIRECT_SLAM,bid=bid,classification=Strength.MAXIMUM)
    assert call(result) is None and result.continuation_needed


@pytest.mark.parametrize('classification',(None,Strength.UNKNOWN,Strength.EXTRAS))
def test_direct_slam_intent_does_not_invent_maximum_classification(classification):
    result=run(('1H','P','2NT','P','3C','P','4H','P'),kind=Intent.DIRECT_SLAM,bid='6H',classification=classification)
    assert call(result) is None


def test_maximum_without_direction_remains_explicit_continuation_needed():
    result=run(('1H','P','2NT','P','3C','P','4H','P'),kind=None,classification=Strength.MAXIMUM)
    assert call(result) is None and result.continuation_needed


@pytest.mark.parametrize('opening,shortness', [('1H','3C'),('1S','3H')])
def test_minimum_still_passes_conditional_4m(opening,shortness):
    result=run((opening,'P','2NT','P',shortness,'P','4'+opening[-1],'P'),kind=None,classification=Strength.MINIMUM)
    assert call(result)=='P' and result.meaning.minimum and result.meaning.signoff


def test_conditional_4m_meaning_is_preserved():
    result=run(('1H','P','2NT','P','3C','P'),cards=NO_ACES,kind=Intent.CONDITIONAL_STOP)
    assert call(result)=='4H' and result.meaning.conditional_stop and not result.meaning.signoff


def test_no_cue_fallback_only_when_control_cue_is_unavailable():
    calls=('1S','P','2NT','P','3H','P')
    result=run(calls,cards=NO_ACES,kind=Intent.GOOD_NO_CUE)
    assert call(result)=='3S' and result.meaning.no_suitable_cue
    assert call(run(calls,cards=ACES,kind=Intent.GOOD_NO_CUE)) is None
    assert call(run(('1H','P','2NT','P','3S','P'),cards=NO_ACES,kind=Intent.GOOD_NO_CUE)) is None


@pytest.mark.parametrize('calls', [EXAMPLE,EXAMPLE[:-2],('1S','P','2NT','P','3H','P','3S','P')])
def test_both_players_can_ask_aces_in_approved_slam_exploration(calls):
    result=run(calls,kind=Intent.ACE_ASK)
    assert call(result)=='4NT' and result.meaning.ace_ask


@pytest.mark.parametrize('tail', [('4NT','P'),('5D','P'),('4H','P')])
def test_no_unapproved_ace_answers_third_suit_rounds_or_signoff_continuations(tail):
    # 4NT terminates this API's scope; 5D is a legal cue, but a later 4NT is unavailable.
    calls=EXAMPLE+tail
    assert call(run(calls,kind=Intent.ACE_ASK)) is None


@pytest.mark.parametrize('profile',[NISIM_NILY_PROFILE,replace(PROFILE,profile_id='other'),replace(PROFILE,base_system=SystemProfile.SAYC)])
def test_profile_isolation_for_repeated_cues_and_maximum_options(profile):
    assert call(run(EXAMPLE,cards=SPADE_KING,bid='4S',profile=profile)) is None
    maximum=run(('1H','P','2NT','P','3C','P','4H','P'),kind=Intent.ACE_ASK,classification=Strength.MAXIMUM,profile=profile)
    assert call(maximum) is None and not maximum.continuation_needed


@pytest.mark.parametrize('dealer',tuple(Seat))
def test_deterministic_history_tracks_actual_seats_and_core_facts(dealer):
    first=run(EXAMPLE,cards=SPADE_KING,bid='4S',dealer=dealer)
    second=run(EXAMPLE,cards=SPADE_KING,bid='4S',dealer=dealer)
    assert first.control_history==second.control_history and first.selected==second.selected
    assert first.control_history[1].seat is dealer
    assert first.control_history[-1].seat is dealer.partner()
    assert first.context.evaluation==evaluate_hand(SPADE_KING)


def test_interference_blocks_replayed_cue_history():
    calls=('1H','P','2NT','P','3C','P','3D','X')
    assert call(run(calls,bid='3S')) is None


def test_router_remains_45_and_unadopted():
    before=create_standard_sayc_router().routes
    result=run(EXAMPLE,cards=SPADE_KING,bid='4S')
    assert call(result)=='4S' and not result.production_adopted
    assert create_standard_sayc_router().match(result.context) is None
    after=create_standard_sayc_router().routes
    assert len(before)==len(after)==45
    assert [(r.route_id,r.priority,r.policy_dependencies) for r in before]==[
        (r.route_id,r.priority,r.policy_dependencies) for r in after]
