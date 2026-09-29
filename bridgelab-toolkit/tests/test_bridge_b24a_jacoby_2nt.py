"""Jacoby 2NT major-raise audit guards; no new convention is executable."""
from dataclasses import replace
from itertools import combinations, product

import pytest

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.first_response import assess_first_response
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.opener_rebid import assess_opener_rebid
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    PartnershipProfile, ResolvedAgreement,
)
from bridge.responder_rebid import assess_responder_rebid
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

SAYC = PartnershipProfile('jacoby-major-audit', '1', SystemProfile.SAYC, ())
# Opaque test declarations, deliberately NOT a new production family binding.
FAMILY = 'response.major.2nt'
CARDS = Hand.parse('AKQJ.KQJ.432.432')


def cards_with_support(opening, length, hcp):
    shape = (3, length, 3, 7-length) if opening == '1H' else (length, 3, 3, 7-length)
    patterns = [p for n in range(5) for p in combinations('AKQJ', n)]
    for suits in product(*[[p for p in patterns if len(p) <= n] for n in shape]):
        if sum({'A': 4, 'K': 3, 'Q': 2, 'J': 1}[r] for p in suits for r in p) == hcp:
            hand = Hand.parse('.'.join(''.join(p) + 'T98765432'[:n-len(p)] or '-'
                                       for p, n in zip(suits, shape)))
            assert evaluate_hand(hand).hcp == hcp
            return hand
    raise AssertionError('invalid fixture')


def assess(api, calls, cards=CARDS, profile=SAYC, **kwargs):
    return api(cards, auction=Auction(Seat.NORTH, calls), vulnerability=Vulnerability.NONE,
               profile=profile, **kwargs)


def serialized(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('length', (3, 4, 5))
@pytest.mark.parametrize('hcp', (12, 13, 14))
def test_support_and_source_hcp_examples_do_not_activate_unimplemented_jacoby(opening, length, hcp):
    result = assess(assess_first_response, (opening, 'P'), cards_with_support(opening, length, hcp))
    assert serialized(result) != '2NT'
    # A traditional limit raise at 12 is existing behavior, not Jacoby.
    if hcp == 12 and length >= 4:
        assert serialized(result) == '3' + opening[-1]
        assert 'invitational' in result.reason
    else:
        assert serialized(result) is None


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('profile', (SAYC, NISIM_NILY_PROFILE))
def test_no_opener_jacoby_major_raise_continuation_route(opening, profile):
    result = assess(assess_opener_rebid, (opening, 'P', '2NT', 'P'), profile=profile)
    assert result.route_id is None and result.engine_result is None
    assert serialized(result) is None and result.blockers
    assert result.context.system.system == profile.base_system.value


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('rebid', ('3C', '3D', '3H', '3S', '3NT', '4H', '4S'))
def test_no_responder_jacoby_continuation_is_inferred_from_source_examples(opening, rebid):
    result = assess(assess_responder_rebid, (opening, 'P', '2NT', 'P', rebid, 'P'))
    assert result.route_id is None and result.engine_result is None
    assert serialized(result) is None  # including no automatic Pass at game


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('treatment', ('jacoby_2nt', 'natural'))
def test_explicit_but_unbound_2nt_meaning_cannot_fall_back_to_another_raise(opening, treatment):
    profile = replace(SAYC, agreements=(AgreementSelection(FAMILY, R.ENABLE, treatment),))
    result = assess(assess_first_response, (opening, 'P'), cards_with_support(opening, 4, 12), profile)
    assert serialized(result) is None and result.engine_result is None
    assert FAMILY in ' '.join(result.blockers)
    assert result.profile.agreement(FAMILY).treatment_id == treatment
    assert result.profile.agreement(FAMILY).source_scope is Scope.PARTNERSHIP
    # The explicit but unbound choice never changes another partnership.
    assert serialized(assess(assess_first_response, (opening, 'P'),
                             cards_with_support(opening, 4, 12))) == '3' + opening[-1]


@pytest.mark.parametrize('opening', ('1H', '1S'))
def test_profile_override_preserves_opaque_forcing_fit_parameters_and_provenance(opening):
    base = ResolvedAgreement(FAMILY, 'natural', R.INHERIT, Scope.SYSTEM)
    params = (('forcing', 'game_force'), ('min_support', '4'))
    profile = replace(SAYC, sources=('bidding/conventions/responses/jacoby-notrump',),
        agreements=(AgreementSelection(FAMILY, R.REPLACE, 'jacoby_2nt', params),))
    result = assess(assess_first_response, (opening, 'P'), profile=profile, base_agreements=(base,))
    effective = result.profile.agreement(FAMILY)
    assert effective.parameters == params and effective.source_scope is Scope.PARTNERSHIP
    assert effective.treatment_id == 'jacoby_2nt' and result.profile.sources == profile.sources
    assert serialized(result) is None  # metadata does not implement a GF raise
    inherited = assess(assess_first_response, (opening, 'P'), base_agreements=(base,))
    assert inherited.profile.agreement(FAMILY).source_scope is Scope.SYSTEM
    assert serialized(inherited) is None


def test_conflicting_natural_and_jacoby_family_declarations_are_rejected():
    with pytest.raises(ValueError, match='duplicate agreement family'):
        replace(SAYC, agreements=(AgreementSelection(FAMILY, R.ENABLE, 'natural'),
                                 AgreementSelection(FAMILY.upper(), R.ENABLE, 'jacoby_2nt')))


@pytest.mark.parametrize('opening', ('1H', '1S'))
def test_disabled_jacoby_declaration_is_not_resurrected(opening):
    profile = replace(SAYC, agreements=(AgreementSelection(FAMILY, R.DISABLE),))
    result = assess(assess_first_response, (opening, 'P'), profile=profile)
    assert serialized(result) is None and result.blockers


@pytest.mark.parametrize('opening', ('1H', '1S'))
def test_nisim_nily_does_not_gain_a_binding_from_convention_card_listing(opening):
    result = assess(assess_first_response, (opening, 'P'),
                    cards_with_support(opening, 4, 14), NISIM_NILY_PROFILE)
    assert result.context.system.system == 'TWO_OVER_ONE_GF'
    assert serialized(result) is None
    assert result.profile.agreement(FAMILY) is None


@pytest.mark.parametrize('opening', ('1H', '1S'))
def test_deterministic_abstention_keeps_original_rule_trace(opening):
    first = assess(assess_first_response, (opening, 'P'))
    second = assess(assess_first_response, (opening, 'P'))
    assert first.engine_result == second.engine_result and first.reason == second.reason
    assert serialized(first) is None
    original = create_standard_sayc_router().evaluate(first.context)
    assert first.engine_result == original


def test_existing_jacoby_routes_are_transfers_not_major_raises():
    routes = create_standard_sayc_router().routes
    assert len(routes) == 45
    jacoby = {r.route_id for r in routes if 'jacoby' in r.route_id}
    assert jacoby == {
        'sayc.response.1nt.jacoby', 'sayc.opener.1nt.jacoby.2d', 'sayc.opener.1nt.jacoby.2h',
        'sayc.responder.1nt.jacoby.hearts.continuation',
        'sayc.responder.1nt.jacoby.spades.continuation',
        'sayc.response.2nt.jacoby', 'sayc.opener.2nt.jacoby.3d', 'sayc.opener.2nt.jacoby.3h',
    }
    # Running every existing transfer engine on a major-raise prefix cannot
    # reinterpret 2NT as a natural NT opening/accepted transfer.
    for calls in [('1H', 'P'), ('1S', 'P'), ('1H', 'P', '2NT', 'P'),
                  ('1S', 'P', '2NT', 'P'), ('1H', 'P', '2NT', 'P', '3C', 'P')]:
        context = BiddingContext.create(hand=CARDS, auction=Auction(Seat.NORTH, calls),
                                        vulnerability=Vulnerability.NONE, system=SystemContext('SAYC'))
        for route in routes:
            if route.route_id in jacoby:
                assert route.engine.evaluate(context).recommended_call is None
    assert len(create_standard_sayc_router().routes) == 45
