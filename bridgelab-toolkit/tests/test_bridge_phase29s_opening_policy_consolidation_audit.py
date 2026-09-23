"""Current partnership approvals and unknown boundaries; audit only."""
from dataclasses import replace
import json

import pytest

from bridge.auction import Auction
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.deals import generate_deal
from bridge.models import Hand, Seat, Vulnerability
from bridge.opening_policy_consolidation_audit import (
    State as S, Classification as C, Check, FAMILIES, all_negative,
    approved_playing_tricks, strong_minor_quality, assess_opening_policy,
    build_consolidation_audit,
)


def make(shape, patterns):
    """Synthetic test fixtures only, never included in the real-hand report."""
    groups = []
    for length, honors in zip(shape, patterns):
        spots = ''.join(r for r in '23456789T' if r not in honors)
        assert len(honors) <= length
        groups.append(honors + spots[:length-len(honors)] or '-')
    return Hand.parse('.'.join(groups))


def assess(shape, patterns, *, passes=0, vuln=Vulnerability.NONE):
    return assess_opening_policy(make(shape, patterns), auction=Auction(Seat.NORTH, ('P',)*passes), vulnerability=vuln)


def check(a, name):
    return next(x for x in a.checks if x.family == name)


def test_complete_negative_evidence_not_no_match():
    negative = tuple(Check(f, S.NEGATIVE, 'test exclusion', 'TEST_ONLY') for f in FAMILIES)
    assert all_negative(negative)
    assert not all_negative(()) and not all_negative(negative[:-1])
    assert not all_negative(negative+negative[:1])
    for index, item in enumerate(negative):
        assert not all_negative(negative[:index]+(replace(item, state=S.UNKNOWN),)+negative[index+1:])
    uncertain = assess((5,3,3,2), ('AKQ','Q','',''))
    assert uncertain.hcp == 11 and uncertain.rule20 == 19
    assert check(uncertain,'concentration').state is S.UNKNOWN
    assert uncertain.classification is C.UNRESOLVED


@pytest.mark.parametrize('passes', (0,1,2,3))
def test_rule20_all_seats_and_natural_priority(passes):
    a=assess((5,5,2,1), ('AK','QJ','',''), passes=passes)
    assert a.hcp == 10 and a.rule20 == 20 and a.supported_call == '1S'
    assert a.classification is C.OPENING_SUPPORTED
    assert check(a,'weak_two_suited').state is S.NEGATIVE
    b=assess((5,1,6,1), ('A','','KQ',''), passes=passes)
    assert b.hcp == 9 and b.rule20 == 20 and b.supported_call == '1S'


@pytest.mark.parametrize('shape,patterns,call', [
    ((6,6,1,0),('AKQ','K','',''),'1S'),
    ((1,2,5,5),('','', 'AKQ','K'),'1D'),
    ((1,0,6,6),('','', 'AKQ','K'),'1D'),
    ((1,5,2,5),('','AKQ','','K'),'1H'),
    ((1,5,6,1),('','AKQ','K',''),'1H'),
])
def test_exact_natural_suit_choices(shape, patterns, call):
    a=assess(shape,patterns)
    assert a.hcp == 12 and a.supported_call == call


def test_six_major_five_minor_boundary_is_not_invented():
    a=assess((6,1,5,1),('AKQ','','',''))
    assert a.hcp == 9 and a.rule20 == 20
    assert check(a,'natural_strength').state is S.POSITIVE
    assert a.classification is C.UNRESOLVED and a.supported_call is None
    assert 'natural_choice' in a.unresolved_blockers


@pytest.mark.parametrize('shape', [(5,1,5,2),(5,1,6,1),(1,2,5,5)])
def test_weak_two_suited_quality_stays_unknown(shape):
    a=assess(shape,('K','','K',''))
    assert a.hcp == 6
    assert check(a,'weak_two_suited').state is S.UNKNOWN
    assert a.classification is C.UNRESOLVED


def test_third_seat_favorable_exception_not_generalized():
    a=assess((5,1,5,2),('K','','',''),passes=2,vuln=Vulnerability.EW)
    assert a.hcp==3 and a.relative_vulnerability=='favorable'
    assert check(a,'weak_two_suited').state is S.UNKNOWN
    for passes,vuln in [(0,Vulnerability.EW),(3,Vulnerability.NS),(2,Vulnerability.NONE),(2,Vulnerability.NS)]:
        b=assess((5,1,5,2),('K','','',''),passes=passes,vuln=vuln)
        assert check(b,'weak_two_suited').state is S.NEGATIVE


@pytest.mark.parametrize('pattern,side', [('KJT','K'),('QJT','A')])
@pytest.mark.parametrize('length,expected', [(6,S.NEGATIVE),(7,S.POSITIVE),(8,S.NEGATIVE)])
def test_unfavorable_multi_examples(pattern,side,length,expected):
    a=assess((length,2,2,9-length),(pattern,side,'',''),vuln=Vulnerability.NS)
    assert a.hcp==7 and a.relative_vulnerability=='unfavorable'
    assert check(a,'multi_weak').state is expected
    assert a.classification is not C.PASS_SUPPORTED


def test_multi_favorable_example_and_second_suit_exclusion():
    a=assess((6,3,2,2),('Q','K','',''),vuln=Vulnerability.EW)
    assert a.hcp==5 and check(a,'multi_weak').state is S.POSITIVE
    assert a.classification is C.UNRESOLVED  # preempt level/priority not guessed
    b=assess((6,5,1,1),('Q','K','',''),vuln=Vulnerability.EW)
    assert check(b,'multi_weak').state is S.NEGATIVE
    c=assess((6,3,2,2),('J','A','',''),vuln=Vulnerability.EW)
    assert check(c,'multi_weak').state is S.UNKNOWN


@pytest.mark.parametrize('holding', ['KJT2345','QJT2345','KJ92345','QJ92345','AT23456','KT23456','KJT9234'])
def test_strong_minor_seven_patterns(holding):
    assert len(holding)==7 and strong_minor_quality(holding) is S.POSITIVE


def test_strong_minor_shape_and_side_suit_exclusion():
    a=assess((3,2,7,1),('AK','AQ','KJT','K'))
    assert a.hcp==20 and check(a,'multi_minor').state is S.POSITIVE
    assert a.supported_call=='2D'
    b=assess((4,2,6,1),('AK','AQ','KJT','K'))
    assert b.hcp==20 and check(b,'multi_minor').state is S.NEGATIVE
    c=assess((3,2,6,2),('AK','AQ','KJT','K'))
    assert c.shape=='semi-balanced' and check(c,'multi_minor').state is S.UNKNOWN
    assert strong_minor_quality('J923456') is S.UNKNOWN


@pytest.mark.parametrize('last,hcp,call', [('',20,'2D'),('J',21,'2D'),('Q',22,'2C'),('K',23,'2C')])
def test_multi_nt_and_strong_priority(last,hcp,call):
    a=assess((5,3,3,2),('AKQ','AK','A',last))
    assert a.hcp==hcp and a.supported_call==call


def test_balanced22_without_strong_suit_and_5422():
    a=assess((4,3,3,3),('AKQ','AK','AQ',''))
    assert a.hcp==22 and a.supported_call=='2D'
    b=assess((5,3,3,2),('T','AKQ','AKQ','A'))
    assert b.hcp==22 and check(b,'strong_2c').state is S.NEGATIVE and b.supported_call=='2D'
    c=assess((5,4,2,2),('AKQ','AK','A',''))
    assert c.hcp==20 and check(c,'multi_nt').state is S.UNKNOWN
    assert c.supported_call is None


def test_one_nt_extended_range_and_shape_ambiguity():
    a=assess((5,3,3,2),('AK','AQ','J',''),passes=2)
    assert a.hcp==14 and check(a,'one_nt').state is S.POSITIVE
    first=assess((5,3,3,2),('AK','AQ','J',''))
    assert check(first,'one_nt').state is S.NEGATIVE
    b=assess((5,4,2,2),('AK','AQ','Q',''))
    assert b.hcp==15 and check(b,'one_nt').state is S.NEGATIVE  # nine major cards
    c=assess((3,2,6,2),('AK','AQ','Q',''))
    assert check(c,'one_nt').state is S.UNKNOWN


def test_approved_pt_values_and_missing_values():
    assert approved_playing_tricks('QJ2')==.25
    assert approved_playing_tricks('K2')==0
    assert approved_playing_tricks('AKQ234')==6
    assert approved_playing_tricks('AJT')==1.5
    assert approved_playing_tricks('KQT')==1.5
    assert approved_playing_tricks('32') is None
    assert approved_playing_tricks('AKQJ234') is None
    a=assess((6,3,3,1),('AKQ','AQ','A','Q'))
    assert a.hcp==21 and sum(a.playing_trick_components)==8.5
    assert check(a,'strong_2c').state is S.POSITIVE and a.supported_call=='2C'
    b=assess((6,3,3,1),('AKQ','AK','QJ','Q'))
    assert b.hcp==21 and sum(b.playing_trick_components)==8.25
    assert check(b,'strong_2c').state is S.NEGATIVE


@pytest.fixture(scope='module')
def sample():
    batch=run_full_auction_simulation(SimulationConfig(100,1000))
    return batch,build_consolidation_audit(batch)


def test_real_population_and_no_unknown_pass(sample):
    batch,r=sample
    assert r.population==616 and r.simulation_errors==0 and r.route_count==45
    assert dict(r.counts)=={'OPENING_SUPPORTED':48,'PARTNERSHIP_TREATMENT_SUPPORTED':0,'PASS_SUPPORTED':440,'UNRESOLVED':128}
    for row in r.cases:
        a=row.assessment
        assert a.hand==generate_deal(100+row.deal_index).hand(Seat(a.dealer)).serialize()
        assert a.opening_position==1 and row.production_decision=='abstain'
        assert len(a.checks)==len(FAMILIES)
        if a.classification is C.PASS_SUPPORTED:
            assert all_negative(a.checks) and not a.unresolved_blockers
        if a.classification is C.UNRESOLVED:
            assert a.supported_call is None
    assert r.to_json()==build_consolidation_audit(batch).to_json()
    assert json.loads(r.to_json())==r.to_dict()
    assert not r.production_changed


def test_review_queues_exact_and_population_bound(sample):
    r=sample[1]
    assert [len(ids) for _,ids in r.queues]==[59,19,36,13,23,51,0,0]
    real={row.deal_index for row in r.cases}
    assert all(set(ids)<=real for _,ids in r.queues)
