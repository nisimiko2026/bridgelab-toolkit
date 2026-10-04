"""B2.4A3 approved meanings with explicit direction and no new thresholds."""
from dataclasses import FrozenInstanceError, replace

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_rules import KnowledgeSource
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Suit, Vulnerability
from bridge.nisim_nily_jacoby_2nt import (
    CONTINUATION_APPROVAL, JacobyDisposition as D,
    OpenerStrength as Strength, OpenerStrengthEvidence,
    ResponderIntent as Intent, ResponderContinuationEvidence,
    assess_jacoby_2nt_responder, assess_jacoby_2nt_conditional_stop,
)
from bridge.nisim_nily_partnership_profile import (
    NISIM_NILY_JACOBY_2NT_PROFILE as PROFILE, NISIM_NILY_PROFILE,
    JACOBY_2NT_FAMILY as FAMILY,
)
from bridge.partnership_profiles import AgreementSelection, AgreementResolution as R
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

HAND = Hand.parse('KQJ2.KQJ2.Q32.J2')
CUE_HAND = Hand.parse('A432.A432.A32.A2')
OPENER = Hand.parse('KQ2.AKJ32.4.Q432')
SOURCE = KnowledgeSource('test-only/b24a3-direction')


def auction_for(opening, rebid, dealer=Seat.NORTH):
    return Auction(dealer, (opening, 'P', '2NT', 'P', rebid, 'P'))


def responder(opening, rebid, kind=None, cue=None, profile=PROFILE, cards=HAND, dealer=Seat.NORTH):
    # A4 now checks actual controls; direction-only fixtures need an Ace.
    if kind is Intent.CUE_BID and cards is HAND:
        cards = CUE_HAND
    auction = auction_for(opening, rebid, dealer)
    evidence = None if kind is None else ResponderContinuationEvidence(
        kind, cards, auction, 'Explicit test direction, no numeric classification.',
        (SOURCE,), None if cue is None else Call.parse(cue))
    return assess_jacoby_2nt_responder(cards, auction=auction, vulnerability=Vulnerability.NONE,
                                      profile=profile, intent=evidence)


def conditional(opening='1H', rebid='3D', classification=None, profile=PROFILE, dealer=Seat.NORTH):
    auction = auction_for(opening, rebid, dealer)
    auction.add('4'+opening[-1])
    auction.add('P')
    evidence = None if classification is None else OpenerStrengthEvidence(
        classification, OPENER, auction, 'Explicit minimum/maximum assessment.', (SOURCE,))
    return assess_jacoby_2nt_conditional_stop(OPENER, auction=auction,
        vulnerability=Vulnerability.NONE, profile=profile, strength=evidence)


def call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening,rebid,cue', [
    ('1H','3H','3S'), ('1H','3H','4C'), ('1H','3H','4D'),
    ('1S','3S','4C'), ('1S','3S','4D'), ('1S','3S','4H'),
])
def test_extras_to_responder_cue_path(opening, rebid, cue):
    result = responder(opening, rebid, Intent.CUE_BID, cue)
    assert call(result) == cue and result.meaning.cue_suit is Suit.parse(cue[-1])
    assert result.meaning.slam_interest and result.meaning.artificial and result.meaning.game_forcing
    assert CONTINUATION_APPROVAL in result.selected.sources and SOURCE in result.selected.sources
    assert not result.meaning.signoff and not result.meaning.conditional_stop


@pytest.mark.parametrize('opening', ('1H','1S'))
@pytest.mark.parametrize('kind', (Intent.SIGNOFF, Intent.GOOD_NO_CUE, Intent.CONDITIONAL_STOP))
def test_no_extra_signoff_or_trump_meaning_after_3m(opening, kind):
    result = responder(opening, '3'+opening[-1], kind)
    assert result.disposition is D.ABSTAIN and call(result) is None


@pytest.mark.parametrize('opening', ('1H','1S'))
def test_balanced_to_game_signoff(opening):
    result = responder(opening, '3NT', Intent.SIGNOFF)
    assert call(result) == '4'+opening[-1]
    assert result.meaning.signoff and not result.meaning.conditional_stop


@pytest.mark.parametrize('opening,rebid', [
    ('1H','3H'), ('1S','3S'), ('1H','3NT'), ('1S','3NT'),
    ('1H','3C'), ('1H','3D'), ('1H','3S'), ('1S','3C'), ('1S','3D'), ('1S','3H'),
])
def test_all_approved_branches_to_ace_ask(opening, rebid):
    result = responder(opening, rebid, Intent.ACE_ASK)
    assert call(result) == '4NT' and result.meaning.ace_ask
    assert result.meaning.artificial and result.meaning.slam_interest
    assert 'no response scheme or keycard variant' in result.reason


@pytest.mark.parametrize('opening,cue', [('1H','4C'),('1H','4D'),('1H','4S'),
                                         ('1S','4C'),('1S','4D'),('1S','4H')])
def test_balanced_to_new_suit_cue(opening, cue):
    assert call(responder(opening, '3NT', Intent.CUE_BID, cue)) == cue


@pytest.mark.parametrize('opening,rebid,cue', [
    ('1H','3C','3D'),('1H','3C','3S'),('1H','3D','4C'),('1H','3S','4D'),
    ('1S','3C','3D'),('1S','3D','3H'),('1S','3H','4C'),('1S','3H','4D'),
])
def test_shortness_to_available_new_suit_cue(opening, rebid, cue):
    result = responder(opening, rebid, Intent.CUE_BID, cue)
    assert call(result) == cue and result.meaning.cue_suit is Suit.parse(cue[-1])
    assert result.meaning.slam_interest


@pytest.mark.parametrize('opening,rebid', [('1H','3C'),('1H','3D'),('1S','3C'),('1S','3D'),('1S','3H')])
def test_shortness_to_legal_3m_good_hand_no_cue(opening, rebid):
    result = responder(opening, rebid, Intent.GOOD_NO_CUE)
    assert call(result) == '3'+opening[-1]
    assert result.meaning.good_hand and result.meaning.slam_interest and result.meaning.no_suitable_cue
    assert not result.meaning.signoff


def test_3h_after_spade_shortness_is_unavailable_and_does_not_fall_back():
    result = responder('1H','3S', Intent.GOOD_NO_CUE)
    assert result.disposition is D.ABSTAIN and call(result) is None
    assert 'not available' in result.engine_result.decisions[0].explanation


@pytest.mark.parametrize('opening,rebid', [('1H','3C'),('1H','3D'),('1H','3S'),('1S','3C'),('1S','3D'),('1S','3H')])
def test_shortness_to_conditional_4m_is_not_a_hard_signoff(opening, rebid):
    result = responder(opening, rebid, Intent.CONDITIONAL_STOP)
    assert call(result) == '4'+opening[-1]
    assert result.meaning.conditional_stop and not result.meaning.signoff
    assert 'minimum passes' in result.reason and 'maximum must continue' in result.reason
    assert call(responder(opening, rebid, Intent.SIGNOFF)) is None


@pytest.mark.parametrize('opening,rebid', [('1H','3C'),('1H','3D'),('1H','3S'),('1S','3C'),('1S','3D'),('1S','3H')])
def test_minimum_opener_passes_conditional_stop(opening, rebid):
    result = conditional(opening, rebid, Strength.MINIMUM)
    assert call(result) == 'P' and result.meaning.minimum and result.meaning.signoff
    assert not result.continuation_needed
    assert SOURCE in result.selected.sources and CONTINUATION_APPROVAL in result.selected.sources


@pytest.mark.parametrize('opening,rebid', [('1H','3D'),('1S','3H')])
def test_maximum_is_explicit_continuation_required_without_an_invented_call(opening, rebid):
    result = conditional(opening, rebid, Strength.MAXIMUM)
    assert result.disposition is D.ABSTAIN and call(result) is None and result.meaning is None
    assert result.continuation_needed
    assert SOURCE in result.continuation_sources and CONTINUATION_APPROVAL in result.continuation_sources
    assert 'must continue' in result.reason and 'approved direction must be supplied' in result.blockers[0]


@pytest.mark.parametrize('classification', (None, Strength.UNKNOWN, Strength.EXTRAS))
def test_no_default_pass_or_equating_extras_with_maximum(classification):
    result = conditional(classification=classification)
    assert call(result) is None and not result.continuation_needed
    assert 'unresolved' in result.blockers[0]


@pytest.mark.parametrize('opening,rebid', [('1H','3H'),('1S','3S'),('1H','3NT'),('1S','3NT'),('1H','3C'),('1S','3H')])
def test_missing_direction_never_guesses_from_own_hand(opening, rebid):
    result = responder(opening, rebid)
    assert result.disposition is D.ABSTAIN and call(result) is None
    assert 'direction' in ' '.join(result.blockers)


@pytest.mark.parametrize('opening,rebid,cue', [
    ('1H','3H','4H'), ('1S','3S','4S'), # trump is not a new suit
    ('1H','3C','4C'), ('1S','3D','4D'), # previously shown shortness suit is not new
    ('1H','3NT','4NT'), ('1S','3H','P'), # cue intent does not relabel NT or Pass
    ('1H','3NT','3S'), ('1S','3H','3D'), # unavailable lower call
])
def test_cue_must_be_a_legal_new_suit(opening, rebid, cue):
    result = responder(opening, rebid, Intent.CUE_BID, cue)
    assert call(result) is None


@pytest.mark.parametrize('profile', [
    NISIM_NILY_PROFILE, replace(PROFILE, profile_id='another-pair'),
    replace(PROFILE, base_system=SystemProfile.SAYC),
    replace(PROFILE, agreements=tuple(a for a in PROFILE.agreements if a.family != FAMILY)
            +(AgreementSelection(FAMILY, R.DISABLE),)),
])
def test_partnership_isolation_covers_responder_and_conditional_stop(profile):
    assert call(responder('1S','3NT',Intent.ACE_ASK,profile=profile)) is None
    assert call(conditional(classification=Strength.MINIMUM,profile=profile)) is None
    maximum = conditional(classification=Strength.MAXIMUM,profile=profile)
    assert call(maximum) is None and not maximum.continuation_needed


@pytest.mark.parametrize('calls', [
    ('1S','P','2NT','P'), ('1S','P','2NT','P','4S','P'),
    ('1S','X','2NT','P','3H','P'), ('1S','P','2NT','3C','3H','P'),
    ('1S','P','2NT','P','3H','X'), ('1H','P','2C','P','3C','P'),
    ('P','1S','P','2NT','P','3H','P'),
])
def test_responder_scope_excludes_unapproved_positions(calls):
    auction = Auction(Seat.NORTH,calls)
    intent = ResponderContinuationEvidence(Intent.ACE_ASK,HAND,auction,'Explicit',(SOURCE,))
    result = assess_jacoby_2nt_responder(HAND,auction=auction,vulnerability=Vulnerability.NONE,profile=PROFILE,intent=intent)
    assert call(result) is None


@pytest.mark.parametrize('calls', [
    ('1H','P','2NT','P','3H','P','4H','P'),
    ('1H','P','2NT','P','3NT','P','4H','P'),
    ('1H','P','2NT','P','3D','P','4NT','P'),
    ('1H','P','2NT','P','3D','P','4H','X'),
])
def test_minimum_pass_rule_only_applies_to_shortness_conditional_4m(calls):
    auction=Auction(Seat.NORTH,calls)
    strength=OpenerStrengthEvidence(Strength.MINIMUM,OPENER,auction,'Explicit',(SOURCE,))
    result=assess_jacoby_2nt_conditional_stop(OPENER,auction=auction,vulnerability=Vulnerability.NONE,profile=PROFILE,strength=strength)
    assert call(result) is None


@pytest.mark.parametrize('kwargs,error', [
    ({'sources':()},ValueError), ({'explanation':''},ValueError),
    ({'sources':('not-a-source',)},TypeError), ({'intent':'ACE_ASK'},TypeError),
    ({'cue_call':Call.parse('4C')},ValueError), ({'intent':Intent.CUE_BID},TypeError),
])
def test_intent_requires_typed_sourced_unambiguous_choice(kwargs,error):
    values=dict(intent=Intent.ACE_ASK,hand=HAND,auction=auction_for('1S','3H'),explanation='Explicit',sources=(SOURCE,))
    values.update(kwargs)
    with pytest.raises(error):
        ResponderContinuationEvidence(**values)


def test_intent_is_bound_to_exact_hand_dealer_and_auction_snapshot():
    auction=auction_for('1S','3H')
    intent=ResponderContinuationEvidence(Intent.ACE_ASK,HAND,auction,'Explicit',(SOURCE,))
    for cards, other in ((OPENER,auction),(HAND,auction_for('1S','3H',Seat.EAST)),(HAND,auction_for('1S','3NT'))):
        with pytest.raises(ValueError,match='different hand or auction'):
            assess_jacoby_2nt_responder(cards,auction=other,vulnerability=Vulnerability.NONE,profile=PROFILE,intent=intent)
    auction.add('4C')
    auction.add('P')
    with pytest.raises(ValueError,match='different hand or auction'):
        assess_jacoby_2nt_responder(HAND,auction=auction,vulnerability=Vulnerability.NONE,profile=PROFILE,intent=intent)


def test_opener_evidence_from_previous_turn_cannot_be_reused():
    earlier=Auction(Seat.NORTH,('1H','P','2NT','P'))
    strength=OpenerStrengthEvidence(Strength.MINIMUM,OPENER,earlier,'Explicit',(SOURCE,))
    current=Auction(Seat.NORTH,('1H','P','2NT','P','3D','P','4H','P'))
    with pytest.raises(ValueError,match='different hand or auction'):
        assess_jacoby_2nt_conditional_stop(OPENER,auction=current,vulnerability=Vulnerability.NONE,profile=PROFILE,strength=strength)


@pytest.mark.parametrize('dealer',tuple(Seat))
def test_deterministic_immutable_core_facts_and_correct_seat(dealer):
    first=responder('1S','3H',Intent.GOOD_NO_CUE,dealer=dealer)
    second=responder('1S','3H',Intent.GOOD_NO_CUE,dealer=dealer)
    assert first.engine_result==second.engine_result and first.meaning==second.meaning
    assert first.reason==second.reason and call(first)=='3S'
    assert first.context.seat is dealer.partner() and first.context.evaluation==evaluate_hand(HAND)
    assert conditional(classification=Strength.MINIMUM,dealer=dealer).context.seat is dealer
    with pytest.raises(FrozenInstanceError):
        first.meaning=None


def test_router_remains_45_and_does_not_adopt_new_continuations():
    before=create_standard_sayc_router().routes
    result=responder('1S','3H',Intent.ACE_ASK)
    assert call(result)=='4NT' and not result.production_adopted
    assert create_standard_sayc_router().match(result.context) is None
    after=create_standard_sayc_router().routes
    assert len(before)==len(after)==47
    assert [(r.route_id,r.priority,r.policy_dependencies) for r in before]==[
        (r.route_id,r.priority,r.policy_dependencies) for r in after]
