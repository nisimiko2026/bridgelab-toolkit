"""B1.3 partnership-only consolidation; no production activation."""
from dataclasses import FrozenInstanceError, replace

import pytest

from bridge.auction import Auction
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_decision_contract import NisimNilyOpeningDecisionContract
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.opening_policy_consolidation_audit import Classification, State, assess_opening_policy
from bridge.opening_policy_six_minor_integration_audit import assess_opening_policy_with_six_minor
from bridge.system_profiles import SystemProfile
from bridge.sayc_route_configuration import create_standard_sayc_router


def hand(shape, honors):
    return Hand.parse('.'.join(
        (pattern + ''.join(r for r in '23456789T' if r not in pattern)[:length-len(pattern)]) or '-'
        for length, pattern in zip(shape, honors)
    ))


def assess(cards, position=1, vulnerability=Vulnerability.NONE, **kwargs):
    return assess_opening_policy_with_six_minor(
        cards, auction=Auction(Seat.NORTH, ('P',) * (position-1)),
        vulnerability=vulnerability, **kwargs,
    )


@pytest.mark.parametrize('shape,honors', [
    ((3,3,6,1), ('AQ','A','AKQ','Q')),  # approved 8.5 PT and strong-minor Multi
    ((3,3,6,1), ('AK','A','AKQ','K')),  # 23 HCP and Rule20 minor
    ((3,3,6,1), ('AQ','A','AKQ','K')),  # 22 HCP strong suit
])
def test_strong_two_club_precedes_minor_rule20_and_multi(shape, honors):
    result = assess(hand(shape, honors))
    assert result.six_minor.preferred_call == '1D'
    assert result.supported_call == '2C'
    assert result.selected_family == 'strong_2c'
    assert result.provenance and result.unresolved_blockers == ()


@pytest.mark.parametrize('position', (1,2,3,4))
@pytest.mark.parametrize('shape,honors,expected', [
    ((1,2,6,4), ('','K','KQJ','A'), '1D'),
    ((1,2,4,6), ('','K','A','KQJ'), '1C'),
    ((5,1,6,1), ('A','','KQ',''), '1S'),
    ((6,1,5,1), ('AKQ','','',''), '1S'),
    ((5,5,2,1), ('AK','QJ','',''), '1S'),
])
def test_rule20_one_level_precedence(shape,honors,expected,position):
    cards = hand(shape,honors)
    result = assess(cards,position)
    assert result.base.rule20 == evaluate_hand(cards).rule_of_20.score >= 20
    assert result.supported_call == expected
    assert result.selected_family == 'one_level'


@pytest.mark.parametrize('minor,expected', [('7.84.KQJT96.9742','3D'), ('974.842.7.KQJT96','3C')])
def test_approved_six_minor_preempt_below_strength(minor,expected):
    result = assess(Hand.parse(minor),3,Vulnerability.EW)
    assert result.base.rule20 < 20
    assert result.supported_call == expected
    assert result.selected_family == 'six_minor_preempt'


@pytest.mark.parametrize('hcp_honors,expected', [
    (('AKQ','AK','A',''), '2D'),
    (('AKQ','AK','A','Q'), '2C'),
    (('AK','AQ','Q',''), '1NT'),
    (('AK','K','Q',''), '1S'),
])
def test_multi_notrump_and_one_level_retain_approved_meanings(hcp_honors,expected):
    assert assess(hand((5,3,3,2),hcp_honors)).supported_call == expected


@pytest.mark.parametrize('shape,honors,expected', [
    ((4,3,3,3), ('AK','K','Q',''), '1C'),
    ((4,3,3,3), ('AK','AQ','Q',''), '1NT'),
    ((4,3,3,3), ('AK','Q','Q',''), 'P'),  # 11, approved first-seat Pass
    ((4,4,4,1), ('AK','K','Q',''), '1D'),
    ((4,4,1,4), ('AK','K','','Q'), '1C'),
    ((4,4,4,1), ('AK','Q','Q',''), '1D'),  # 11, approved low singleton
])
def test_4333_and_4441_only_use_recorded_approvals(shape,honors,expected):
    result = assess(hand(shape,honors))
    assert result.supported_call == expected
    if expected is None:
        assert result.classification is Classification.UNRESOLVED
        assert result.unresolved_blockers


@pytest.mark.parametrize('position', (1,2,3,4))
@pytest.mark.parametrize('honors', [('','','',''), ('AK','J','',''), ('AK','Q','','')])
def test_five_five_majors_at_most_nine_pass(position,honors):
    result = assess(hand((5,5,2,1),honors),position)
    assert result.supported_call == 'P'
    assert result.classification is Classification.PASS_SUPPORTED
    assert result.selected_family == 'five_five_major_pass'


def test_low_ordinary_pass_is_positive_evidence_and_unknown_is_not_pass():
    assert assess(hand((4,3,3,3),('','','',''))).supported_call == 'P'
    result = assess(Hand.parse('7.84.KJ9864.9742'),3,Vulnerability.EW)
    assert result.supported_call is None
    assert result.classification is Classification.UNRESOLVED


def test_unknown_strong_qualification_blocks_lower_minor_call():
    result = assess(hand((3,2,6,2),('AK','A','AKQ','')))
    assert result.six_minor.preferred_call == '1D'
    assert result.supported_call is None
    assert result.unresolved_blockers == ('strong_2c',)


def test_unapproved_weak_multi_preempt_priority_stays_visible():
    result = assess(hand((6,3,2,2),('Q','K','','')),vulnerability=Vulnerability.EW)
    assert result.supported_call is None
    assert 'multi_vs_preempt_priority' in result.unresolved_blockers


@pytest.mark.parametrize('shape', [(3,2,6,2),(2,2,4,5)])
def test_30n_approved_nt_shapes_precede_ordinary_minor(shape):
    assert assess(hand(shape,('AK','AQ','Q',''))).supported_call == '1NT'


def test_deterministic_immutable_single_outcome_and_preserved_evidence():
    cards=hand((3,3,6,1),('AQ','A','AKQ','Q'))
    a,b=assess(cards),assess(cards)
    assert a == b and a.to_json() == b.to_json()
    assert a.base == assess_opening_policy(cards,auction=Auction(Seat.NORTH),vulnerability=Vulnerability.NONE)
    assert a.base.supported_call is None  # historical unresolved precedence retained as evidence
    assert a.supported_call == '2C' and a.provenance
    with pytest.raises(FrozenInstanceError):
        a.supported_call='1D'
    with pytest.raises(ValueError,match='unresolved'):
        replace(a,classification=Classification.UNRESOLVED)


@pytest.mark.parametrize('profile', [
    replace(NISIM_NILY_PROFILE,profile_id='another-partnership'),
    replace(NISIM_NILY_PROFILE,base_system=SystemProfile.SAYC),
    replace(NISIM_NILY_PROFILE,agreements=()),
])
def test_partnership_and_system_isolation(profile):
    with pytest.raises(ValueError,match='canonical Nisim'):
        assess(hand((4,3,3,3),('','','','')),profile=profile)


def test_conflicting_contract_rejected():
    with pytest.raises(ValueError,match='precedence'):
        NisimNilyOpeningDecisionContract(strong_two_club_vs_strong_minor_precedence='2D')


@pytest.mark.parametrize('mutation', ['duplicate','state_call','family_call','six_minor_call'])
def test_contradictory_policy_evidence_rejected(monkeypatch,mutation):
    import bridge.opening_policy_six_minor_integration_audit as module
    cards=hand((3,3,6,1),('AQ','A','AKQ','Q'))
    before=assess(cards)
    if mutation=='six_minor_call':
        monkeypatch.setattr(module,'assess_six_minor_three_level_preempt',lambda *a,**k:replace(before.six_minor,preferred_call='3D'))
    else:
        checks=before.base.checks
        if mutation=='duplicate':
            checks=checks+checks[:1]
        elif mutation=='family_call':
            checks=tuple(replace(c,call='2D') if c.family=='strong_2c' else c for c in checks)
        else:
            checks=tuple(replace(c,state=State.NEGATIVE) if c.family=='strong_2c' else c for c in checks)
        monkeypatch.setattr(module,'assess_opening_policy',lambda *a,**k:replace(before.base,checks=checks))
    with pytest.raises(ValueError):
        assess(cards)


def test_production_router_unchanged():
    before=create_standard_sayc_router().routes
    assess(hand((3,3,6,1),('AQ','A','AKQ','Q')))
    after=create_standard_sayc_router().routes
    assert len(before)==len(after)==45
    assert [(r.route_id,r.priority,r.policy_dependencies) for r in before] == [(r.route_id,r.priority,r.policy_dependencies) for r in after]

@pytest.mark.parametrize('position', (1,2,3,4))
@pytest.mark.parametrize('singleton_suit', range(4))
@pytest.mark.parametrize('low_rank', ('2','T'))
def test_4441_exact_eleven_low_singleton_all_orientations(position,singleton_suit,low_rank):
    shape=[4]*4
    shape[singleton_suit]=1
    patterns=iter(('AK','Q','Q'))
    cards=hand(shape,tuple(low_rank if i==singleton_suit else next(patterns) for i in range(4)))
    assert evaluate_hand(cards).hcp == 11
    result=assess(cards,position)
    assert result.supported_call == ('1C' if singleton_suit==2 else '1D')
    assert result.selected_family == '4441_low_singleton'
    assert result.unresolved_blockers == ()
    assert 'B1.3 completion' in result.provenance[0]


@pytest.mark.parametrize('rank,others', [('J',('AK','K','')), ('Q',('AK','Q','')), ('K',('AK','J','')), ('A',('AK','',''))])
@pytest.mark.parametrize('singleton_suit', range(4))
def test_4441_singleton_jack_or_higher_does_not_qualify(rank,others,singleton_suit):
    shape=[4]*4
    shape[singleton_suit]=1
    patterns=iter(others)
    cards=hand(shape,tuple(rank if i==singleton_suit else next(patterns) for i in range(4)))
    assert evaluate_hand(cards).hcp == 11
    result=assess(cards)
    assert result.selected_family != '4441_low_singleton'
    assert result.classification is Classification.UNRESOLVED
    assert result.supported_call is None


@pytest.mark.parametrize('shape,honors', [
    ((4,4,4,1),('AK','K','','')),  # ten HCP
    ((4,4,4,1),('AK','K','Q','')), # twelve: ordinary opening takes priority
    ((4,4,3,2),('AK','Q','Q','')), # wrong shape at eleven
])
def test_4441_exception_is_not_generalized(shape,honors):
    assert assess(hand(shape,honors)).selected_family != '4441_low_singleton'


@pytest.mark.parametrize('four_card_suit', (1,2,3))
@pytest.mark.parametrize('position', (1,2,3,4))
def test_4333_nonspade_four_card_suit_passes(four_card_suit,position):
    shape=[3]*4
    shape[four_card_suit]=4
    result=assess(hand(shape,('K','Q','','')),position)
    assert result.supported_call == 'P'
    assert result.selected_family == '4333_pass'
    assert result.provenance and result.unresolved_blockers == ()


@pytest.mark.parametrize('position', (1,2))
@pytest.mark.parametrize('spades', ('K','A','QJT'))
def test_4333_four_spades_first_second_seat_passes(position,spades):
    result=assess(hand((4,3,3,3),(spades,'','','')),position)
    assert result.supported_call == 'P'
    assert result.selected_family == '4333_pass'


@pytest.mark.parametrize('position', (3,4))
@pytest.mark.parametrize('spades', ('K','A','QJT'))
def test_4333_qualified_four_spades_later_seat_opens_club(position,spades):
    result=assess(hand((4,3,3,3),(spades,'','','')),position)
    assert result.supported_call == '1C'
    assert result.selected_family == '4333_spade_exception'
    assert result.provenance and result.unresolved_blockers == ()


@pytest.mark.parametrize('position', (3,4))
@pytest.mark.parametrize('spades', ('','Q','QJ','QT','JT'))
def test_4333_insufficient_spade_quality_passes(position,spades):
    result=assess(hand((4,3,3,3),(spades,'','','')),position)
    assert result.supported_call == 'P'
    assert result.selected_family == '4333_pass'


@pytest.mark.parametrize('honors,call,family', [
    (('AK','K','Q',''), '1C','one_level'),
    (('AK','AQ','Q',''), '1NT','one_nt'),
    (('AK','AK','AQ',''), '2D','multi_nt'),
    (('AK','AK','AK','Q'), '2C','strong_2c'),
])
def test_4333_shape_exception_does_not_override_higher_priority(honors,call,family):
    result=assess(hand((3,4,3,3),honors))
    assert result.supported_call == call
    assert result.selected_family == family


@pytest.mark.parametrize('cards,position', [
    (hand((4,4,4,1),('AK','Q','Q','')),1),
    (hand((4,3,3,3),('K','','','')),3),
])
@pytest.mark.parametrize('profile', [
    replace(NISIM_NILY_PROFILE,profile_id='other-partnership'),
    replace(NISIM_NILY_PROFILE,base_system=SystemProfile.SAYC),
])
def test_shape_exceptions_are_partnership_specific(cards,position,profile):
    with pytest.raises(ValueError,match='canonical Nisim'):
        assess(cards,position,profile=profile)
