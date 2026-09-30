"""Approved Nisim-Nily Jacoby 2NT, isolated from production routing."""
from dataclasses import FrozenInstanceError, replace
from functools import lru_cache
from itertools import combinations, product

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import KnowledgeSource
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Suit, Vulnerability
from bridge.nisim_nily_jacoby_2nt import (
    APPROVAL, JacobyDisposition as D, OpenerStrength as Strength,
    OpenerStrengthEvidence, assess_jacoby_2nt_opener, assess_jacoby_2nt_response,
)
from bridge.nisim_nily_partnership_profile import (
    JACOBY_2NT_FAMILY as FAMILY, JACOBY_2NT_PARAMETERS, JACOBY_2NT_TREATMENT,
    NISIM_NILY_JACOBY_2NT_PROFILE as PROFILE, NISIM_NILY_PROFILE,
)
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    ResolvedAgreement, resolve_partnership_profile,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

SOURCE = KnowledgeSource('test-only/jacoby-opener-classification')


@lru_cache(None)
def hand(shape, hcp):
    patterns = [p for n in range(5) for p in combinations('AKQJ', n)]
    for suits in product(*[[p for p in patterns if len(p) <= n] for n in shape]):
        if sum({'A': 4, 'K': 3, 'Q': 2, 'J': 1}[r] for p in suits for r in p) == hcp:
            result = Hand.parse('.'.join(''.join(p) + 'T98765432'[:n-len(p)] or '-'
                                         for p, n in zip(suits, shape)))
            assert evaluate_hand(result).hcp == hcp
            return result
    raise AssertionError('invalid fixture')


def response(opening, cards, profile=PROFILE, **kwargs):
    return assess_jacoby_2nt_response(cards, auction=Auction(Seat.NORTH, (opening, 'P')),
        vulnerability=Vulnerability.NONE, profile=profile, **kwargs)


def opener(opening, cards, classification=None, profile=PROFILE, dealer=Seat.NORTH, **kwargs):
    auction = Auction(dealer, (opening, 'P', '2NT', 'P'))
    evidence = None if classification is None else OpenerStrengthEvidence(
        classification, cards, auction, 'Explicit test assessment; no numeric definition.', (SOURCE,))
    return assess_jacoby_2nt_opener(cards, auction=auction, vulnerability=Vulnerability.NONE,
                                  profile=profile, strength=evidence, **kwargs)


def call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('hcp', (12, 13, 14, 25))
@pytest.mark.parametrize('support', (3, 4, 5))
def test_response_hcp_and_support_boundaries(opening, hcp, support):
    shape = (3, support, 3, 7-support) if opening == '1H' else (support, 3, 3, 7-support)
    result = response(opening, hand(shape, hcp))
    expected = hcp >= 13 and support >= 4
    assert call(result) == ('2NT' if expected else None)
    if expected:
        assert result.meaning.artificial and result.meaning.game_forcing
        assert result.meaning.minimum_support == 4
        assert result.meaning.trump is Suit.parse(opening[-1])
        assert APPROVAL in result.selected.sources
        assert result.profile.agreement(FAMILY).source_scope is Scope.PARTNERSHIP


@pytest.mark.parametrize('opening,shape', [
    ('1H', (3, 4, 3, 3)), ('1H', (2, 5, 4, 2)), ('1H', (0, 4, 5, 4)),
    ('1S', (4, 3, 3, 3)), ('1S', (5, 2, 4, 2)), ('1S', (4, 0, 5, 4)),
])
def test_response_has_no_shape_or_shortness_restriction(opening, shape):
    result = response(opening, hand(shape, 13))
    assert call(result) == '2NT'
    assert result.context.evaluation == evaluate_hand(result.context.hand)


@pytest.mark.parametrize('profile', [
    NISIM_NILY_PROFILE,
    replace(PROFILE, profile_id='another-partnership'),
    replace(PROFILE, base_system=SystemProfile.SAYC),
    replace(PROFILE, profile_id='generic-2over1'),
])
@pytest.mark.parametrize('opening', ('1H', '1S'))
def test_profile_identity_base_system_and_explicit_binding_required(profile, opening):
    cards = hand((4, 4, 3, 2), 15)
    for result in (response(opening, cards, profile), opener(opening, cards, profile=profile)):
        assert result.disposition is D.ABSTAIN and call(result) is None and result.blockers


@pytest.mark.parametrize('selection', [
    AgreementSelection(FAMILY, R.DISABLE),
    AgreementSelection(FAMILY, R.REPLACE, 'natural'),
    AgreementSelection(FAMILY, R.REPLACE, JACOBY_2NT_TREATMENT, (('min_hcp', '12'),)),
])
def test_override_disable_and_unsupported_parameters_block_fallback(selection):
    profile = replace(PROFILE, agreements=tuple(a for a in PROFILE.agreements if a.family != FAMILY)+(selection,))
    for result in (response('1H', hand((4, 4, 3, 2), 15), profile),
                   opener('1H', hand((3, 5, 3, 2), 15), profile=profile)):
        assert call(result) is None and result.engine_result is None


def test_resolver_override_and_provenance():
    base = ResolvedAgreement(FAMILY, 'natural', R.INHERIT, Scope.SYSTEM)
    result = response('1H', hand((4, 4, 3, 2), 13), base_agreements=(base,))
    assert call(result) == '2NT'
    assert result.profile.agreement(FAMILY).source_scope is Scope.PARTNERSHIP
    assert result.profile.agreement(FAMILY).parameters == JACOBY_2NT_PARAMETERS
    assert APPROVAL.article_id in result.profile.sources
    # Inheriting the same text from the system does not enable a partnership rule.
    base = replace(base, treatment_id=JACOBY_2NT_TREATMENT, parameters=JACOBY_2NT_PARAMETERS)
    result = response('1H', hand((4, 4, 3, 2), 13), NISIM_NILY_PROFILE, base_agreements=(base,))
    assert call(result) is None


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('length', (0, 1, 2))
@pytest.mark.parametrize('suit', tuple(Suit))
def test_side_suit_void_singleton_and_doubleton(opening, length, suit):
    trump = Suit.parse(opening[-1])
    if suit is trump:
        # A short trump suit is never described by a new side-suit bid.
        lengths = {s: 3 for s in Suit}
        lengths[trump] = length
        lengths[Suit.CLUBS] += 4-length
    else:
        lengths = {s: 3 for s in Suit}
        lengths[trump] = 7-length
        lengths[suit] = length
    cards = hand(tuple(lengths[s] for s in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)), 13)
    result = opener(opening, cards)
    if suit is not trump and length <= 1:
        assert call(result) == '3' + suit.letter
        assert result.meaning.shown_shortness is suit and result.meaning.artificial
        assert result.meaning.game_forcing and APPROVAL in result.selected.sources
        assert ('void' if length == 0 else 'singleton') in result.reason
    else:
        assert call(result) is None


@pytest.mark.parametrize('opening,shape', [('1H', (3, 5, 3, 2)), ('1S', (5, 3, 3, 2))])
@pytest.mark.parametrize('hcp,expected', [(13, None), (14, '3NT'), (15, '3NT'), (16, None)])
def test_balanced_14_15_only(opening, shape, hcp, expected):
    result = opener(opening, hand(shape, hcp))
    assert call(result) == expected
    if expected:
        assert result.meaning.balanced and result.meaning.hcp_range == (14, 15)


@pytest.mark.parametrize('shape', ((2, 5, 4, 2), (2, 6, 3, 2)))
@pytest.mark.parametrize('hcp', (14, 15))
def test_semi_balanced_is_not_balanced_3nt(shape, hcp):
    assert call(opener('1H', hand(shape, hcp))) is None


@pytest.mark.parametrize('opening,shape', [('1H', (2, 5, 4, 2)), ('1S', (5, 2, 4, 2))])
@pytest.mark.parametrize('classification,level', [(Strength.EXTRAS, '3'), (Strength.MINIMUM, '4')])
def test_qualitative_opener_meanings_require_explicit_sourced_evidence(opening, shape, classification, level):
    cards = hand(shape, 13)
    result = opener(opening, cards, classification)
    assert call(result) == level + opening[-1]
    assert SOURCE in result.selected.sources and APPROVAL in result.selected.sources
    assert result.meaning.extras == (classification is Strength.EXTRAS)
    assert result.meaning.slam_interest == (classification is Strength.EXTRAS)
    assert result.meaning.minimum == (classification is Strength.MINIMUM)
    assert call(opener(opening, cards)) is None
    assert call(opener(opening, cards, Strength.UNKNOWN)) is None


@pytest.mark.parametrize('classification', (Strength.EXTRAS, Strength.MINIMUM))
def test_shortness_has_precedence_over_qualitative_strength(classification):
    result = opener('1H', hand((1, 5, 4, 3), 15), classification)
    assert call(result) == '3S'
    assert len(result.engine_result.candidates) == 2


def test_explicit_extras_then_balanced_then_explicit_minimum_precedence():
    cards = hand((3, 5, 3, 2), 14)
    assert call(opener('1H', cards, Strength.EXTRAS)) == '3H'
    assert call(opener('1H', cards, Strength.MINIMUM)) == '3NT'


def test_multiple_short_suits_never_use_registration_order_or_minimum_fallback():
    result = opener('1S', hand((7, 1, 1, 4), 13), Strength.MINIMUM)
    assert result.disposition is D.CONFLICT and result.meaning is None and call(result) is None
    assert {d.candidate.serialize() for d in result.engine_result.candidates} == {'3H', '3D', '4S'}
    assert len(result.blockers) == 2


@pytest.mark.parametrize('kwargs', [dict(explanation=''), dict(sources=())])
def test_known_strength_requires_provenance(kwargs):
    values = dict(classification=Strength.EXTRAS, hand=hand((3, 5, 3, 2), 16),
                  auction=Auction(Seat.NORTH, ('1H', 'P', '2NT', 'P')),
                  explanation='Explicit assessment', sources=(SOURCE,))
    values.update(kwargs)
    with pytest.raises(ValueError):
        OpenerStrengthEvidence(**values)


def test_strength_evidence_is_bound_to_hand_and_auction():
    cards = hand((3, 5, 3, 2), 16)
    auction = Auction(Seat.NORTH, ('1H', 'P', '2NT', 'P'))
    evidence = OpenerStrengthEvidence(Strength.EXTRAS, cards, auction, 'Explicit', (SOURCE,))
    for other_hand, other_auction in ((hand((3, 5, 3, 2), 17), auction),
            (cards, Auction(Seat.EAST, ('1H', 'P', '2NT', 'P')))):
        with pytest.raises(ValueError, match='different hand or auction'):
            assess_jacoby_2nt_opener(other_hand, auction=other_auction,
                vulnerability=Vulnerability.NONE, profile=PROFILE, strength=evidence)


@pytest.mark.parametrize('calls', [
    ('1H', 'X'), ('1S', '2C'), ('P', '1H', 'P'), ('1C', 'P'), ('1NT', 'P'),
    ('1H', 'P', '2NT', 'P'), ('1H', 'P', '2NT', 'P', '3C', 'P'),
])
def test_response_scope_excludes_interference_other_openings_and_later_calls(calls):
    result = assess_jacoby_2nt_response(hand((4, 4, 3, 2), 15), auction=Auction(Seat.NORTH, calls),
                                      vulnerability=Vulnerability.NONE, profile=PROFILE)
    assert call(result) is None


@pytest.mark.parametrize('calls', [
    ('1H', 'X', '2NT', 'P'), ('1S', 'P', '2NT', 'X'), ('1S', 'P', '2NT', '3C'),
    ('1S', 'P', '2C', 'P'), ('2NT', 'P', '3D', 'P'),
    ('1H', 'P', '2NT', 'P', '3S', 'P'),
])
def test_no_interference_other_conventions_or_later_slam_continuations(calls):
    result = assess_jacoby_2nt_opener(hand((3, 5, 3, 2), 15), auction=Auction(Seat.NORTH, calls),
                                    vulnerability=Vulnerability.NONE, profile=PROFILE)
    assert call(result) is None


@pytest.mark.parametrize('dealer', tuple(Seat))
def test_deterministic_single_immutable_outcome_and_core_evaluation(dealer):
    cards = hand((3, 5, 3, 2), 15)
    first = opener('1H', cards, dealer=dealer)
    second = opener('1H', cards, dealer=dealer)
    assert first.engine_result == second.engine_result and first.meaning == second.meaning
    assert first.context.seat is dealer and first.context.evaluation == evaluate_hand(cards)
    assert call(first) == '3NT' and not first.production_adopted
    with pytest.raises(FrozenInstanceError):
        first.selected = None


def test_opt_in_revision_preserves_old_profile_and_45_production_routes():
    old = NISIM_NILY_PROFILE.to_json()
    before = create_standard_sayc_router().routes
    result = response('1H', hand((3, 4, 3, 3), 13))
    assert call(result) == '2NT'
    assert resolve_partnership_profile(NISIM_NILY_PROFILE).agreement(FAMILY) is None
    assert PROFILE.version == 'B2.4A2' and PROFILE.profile_id == NISIM_NILY_PROFILE.profile_id
    assert NISIM_NILY_PROFILE.to_json() == old
    assert create_standard_sayc_router().evaluate(result.context).recommended_call is None
    after = create_standard_sayc_router().routes
    assert len(before) == len(after) == 45
    assert [(r.route_id, r.priority, r.policy_dependencies) for r in before] == [
        (r.route_id, r.priority, r.policy_dependencies) for r in after]
