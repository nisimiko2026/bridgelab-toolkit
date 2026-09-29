"""B2.3 composition preserves existing continuations and explicit gaps."""
from dataclasses import FrozenInstanceError, dataclass, replace
from itertools import combinations, product

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import KnowledgeSource, RuleDecision
from bridge.engine_router import BiddingEngineRouter, EngineRoute, auction_calls
from bridge.evaluation import evaluate_hand
from bridge.jacoby_continuation_strength_policy import (
    JacobyContinuationStrengthAssessment, JacobyContinuationStrengthClass as J,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    PartnershipProfile, ResolvedAgreement,
)
from bridge.policy_registry import PolicyRegistry
from bridge.responder_rebid import ResponderRebidDisposition as D, assess_responder_rebid
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.stayman_continuation_strength_policy import (
    StaymanContinuationStrengthAssessment, StaymanContinuationStrength as S,
)
from bridge.system_profiles import SystemProfile

SAYC = PartnershipProfile('responder-rebid-test', '1', SystemProfile.SAYC, ())
SOURCE = KnowledgeSource('test-only/b23-policy', 'Explicit test classification')
PREFIXES = (
    ('1NT', '2D', '2H'), ('1NT', '2H', '2S'),
    ('1NT', '2C', '2H'), ('1NT', '2C', '2S'),
)


def hand(shape, hcp):
    patterns = [p for n in range(5) for p in combinations('AKQJ', n)]
    for suits in product(*[[p for p in patterns if len(p) <= n] for n in shape]):
        if sum({'A': 4, 'K': 3, 'Q': 2, 'J': 1}[r] for p in suits for r in p) == hcp:
            cards = Hand.parse('.'.join(''.join(p) + 'T98765432'[:n-len(p)] or '-'
                                        for p, n in zip(suits, shape)))
            assert evaluate_hand(cards).hcp == hcp
            return cards
    raise AssertionError('invalid fixture')


def assess(prefix, cards=None, *, profile=SAYC, calls=None, dealer=Seat.NORTH, **kwargs):
    opening, response, rebid = prefix
    return assess_responder_rebid(
        hand((4, 4, 3, 2), 10) if cards is None else cards,
        auction=Auction(dealer, calls if calls is not None else (opening, 'P', response, 'P', rebid, 'P')),
        vulnerability=Vulnerability.NONE, profile=profile, **kwargs,
    )


def call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@dataclass(frozen=True)
class JacobyFixture:
    classification: J
    policy_id: str = 'fixture.b23.jacoby'

    def assess(self, context):
        assert context.evaluation == evaluate_hand(context.hand)
        return JacobyContinuationStrengthAssessment(
            self.policy_id, self.classification, 'Explicit test classification, no numeric contract.', (SOURCE,))


@dataclass(frozen=True)
class StaymanFixture:
    classification: S
    policy_id: str = 'fixture.b23.stayman'

    def assess(self, context):
        assert context.evaluation == evaluate_hand(context.hand)
        return StaymanContinuationStrengthAssessment(
            self.policy_id, self.classification, 'Explicit test classification, no numeric contract.', (SOURCE,))


def jacoby(cls):
    policy = JacobyFixture(cls)
    return dict(registry=PolicyRegistry.from_jacoby_continuation_strength_policies((policy,)),
                jacoby_continuation_strength_policy_id=policy.policy_id)


def stayman(cls):
    policy = StaymanFixture(cls)
    return dict(registry=PolicyRegistry.from_stayman_continuation_strength_policies((policy,)),
                stayman_continuation_strength_policy_id=policy.policy_id)


@pytest.mark.parametrize('prefix', PREFIXES[:2])
@pytest.mark.parametrize('classification,expected', [
    (J.WEAK, 'P'), (J.INVITATIONAL, '2NT'), (J.GAME_GOING, 'game'),
    (J.SLAM_INTEREST, None), (J.UNKNOWN, None),
])
def test_transfer_signoff_invitation_and_game_mapping(prefix, classification, expected):
    result = assess(prefix, **jacoby(classification))
    expected = '4' + prefix[2][-1] if expected == 'game' else expected
    assert call(result) == expected
    assert result.disposition is (D.RECOMMENDED if expected else D.ABSTAIN)
    if expected:
        assert SOURCE in result.selected.sources
        assert classification.name in result.reason
        assert result.reason == result.selected.explanation


@pytest.mark.parametrize('prefix', PREFIXES[2:])
@pytest.mark.parametrize('length', (3, 4, 5))
@pytest.mark.parametrize('classification', tuple(S))
def test_stayman_raise_support_boundary_and_class(prefix, length, classification):
    shape = (3, length, 3, 7-length) if prefix[2] == '2H' else (length, 3, 3, 7-length)
    result = assess(prefix, hand(shape, 10), **stayman(classification))
    expected = '4' + prefix[2][-1] if length >= 4 and classification is S.GAME_GOING else None
    assert call(result) == expected
    if expected:
        assert 'GAME_GOING' in result.reason and SOURCE in result.selected.sources


@pytest.mark.parametrize('prefix', PREFIXES)
@pytest.mark.parametrize('hcp', (0, 7, 8, 9, 10, 15, 16, 25))
def test_no_invented_hcp_threshold_or_default_classifier(prefix, hcp):
    result = assess(prefix, hand((4, 4, 3, 2), hcp))
    assert result.disposition is D.ABSTAIN and result.engine_result is not None
    assert 'policy' in result.engine_result.decisions[0].explanation.lower()


@pytest.mark.parametrize('hcp', (7, 8, 9, 10))
def test_explicit_class_is_not_reclassified_by_consolidation(hcp):
    # Fixed fixtures are API probes, not proposed partnership HCP thresholds.
    cards = hand((3, 5, 3, 2), hcp)
    assert call(assess(PREFIXES[0], cards, **jacoby(J.WEAK))) == 'P'
    assert call(assess(PREFIXES[0], cards, **jacoby(J.INVITATIONAL))) == '2NT'
    assert call(assess(PREFIXES[0], cards, **jacoby(J.GAME_GOING))) == '4H'


@pytest.mark.parametrize('length', (4, 5, 6))
def test_accepted_transfer_remains_auction_evidence(length):
    # The legacy rule maps a supplied class; it does not revalidate the first bid
    # or invent a six-card own-suit invitational rebid.
    cards = hand((3, length, 2, 8-length), 8)
    assert call(assess(PREFIXES[0], cards, **jacoby(J.INVITATIONAL))) == '2NT'


@pytest.mark.parametrize('prefix', [
    ('1C', '1H', '1S'),  # own-suit rebid / preference / fourth suit unresolved
    ('1C', '1S', '2D'), ('1D', '1S', '2C'),
    ('1D', '1H', '1NT'), ('1C', '1H', '2H'),  # NT / raise / invite / signoff unresolved
    ('1H', '1S', '2H'), ('1S', '1NT', '2C'),
    ('2C', '2D', '2NT'), ('2NT', '3D', '3H'),
    ('2NT', '3H', '3S'), ('2NT', '3C', '3H'),
    ('1NT', '2C', '2D'), ('1NT', '2D', '3H'),
    ('2D', '2H', '2S'), ('3C', '3H', '4C'),
])
def test_missing_families_never_manufacture_a_rebid(prefix):
    result = assess(prefix, **jacoby(J.GAME_GOING))
    assert result.disposition is D.ABSTAIN
    assert result.route_id is None and result.engine_result is None and call(result) is None


@pytest.mark.parametrize('prefix', [('1S', '2C', '2D'), ('1H', '2D', '2S')])
def test_game_forcing_context_is_preserved_without_inventing_continuation(prefix):
    result = assess(prefix, profile=NISIM_NILY_PROFILE)
    assert result.disposition is D.ABSTAIN and call(result) is None  # never Pass in GF by fallback
    assert result.context.system.system == 'TWO_OVER_ONE_GF'
    agreement = result.profile.agreement('response.major.two_over_one')
    assert agreement.treatment_id == 'game_force' and agreement.source_scope is Scope.PARTNERSHIP


@pytest.mark.parametrize('prefix', PREFIXES)
def test_nisim_nily_isolation_even_with_explicit_classifier(prefix):
    config = jacoby(J.GAME_GOING) if prefix[1] != '2C' else stayman(S.GAME_GOING)
    assert call(assess(prefix, profile=NISIM_NILY_PROFILE, **config)) is None
    assert call(assess(prefix, **config)) == '4' + prefix[2][-1]


@pytest.mark.parametrize('family', ('opening.1nt', 'response.1nt', 'rebid', 'opener.rebid', 'responder.rebid.1nt'))
@pytest.mark.parametrize('resolution', (R.ENABLE, R.DISABLE))
def test_unbound_or_disabled_meanings_block_policy_fallback(family, resolution):
    selection = AgreementSelection(family, resolution, 'unbound' if resolution is R.ENABLE else None)
    profile = replace(SAYC, agreements=(selection,))
    result = assess(PREFIXES[0], profile=profile, **jacoby(J.GAME_GOING))
    assert result.disposition is D.ABSTAIN and result.blockers and result.engine_result is None
    assert call(assess(PREFIXES[0], **jacoby(J.GAME_GOING))) == '4H'


def test_resolver_precedence_parameters_and_source_scope_are_preserved():
    base = ResolvedAgreement('responder.rebid.1nt', 'base-contract', R.INHERIT, Scope.SYSTEM,
                             (('min_hcp', '9'),))
    inherited = assess(PREFIXES[0], base_agreements=(base,))
    assert inherited.profile.agreement(base.family).source_scope is Scope.SYSTEM
    profile = replace(SAYC, sources=('test-profile-source',), agreements=(
        AgreementSelection(base.family, R.REPLACE, 'partnership-contract', (('min_hcp', '10'),)),))
    result = assess(PREFIXES[0], profile=profile, base_agreements=(base,), **jacoby(J.GAME_GOING))
    effective = result.profile.agreement(base.family)
    assert effective.source_scope is Scope.PARTNERSHIP and effective.parameters == (('min_hcp', '10'),)
    assert effective.treatment_id == 'partnership-contract'
    assert result.profile.sources == ('test-profile-source',) and call(result) is None


def test_unrelated_opening_family_does_not_leak():
    profile = replace(SAYC, agreements=(AgreementSelection('response.1d', R.ENABLE, 'unbound'),))
    assert call(assess(PREFIXES[0], profile=profile, **jacoby(J.WEAK))) == 'P'


@pytest.mark.parametrize('prefix', PREFIXES)
def test_unregistered_policy_abstains_and_wrong_policy_family_does_not_substitute(prefix):
    option = ('jacoby_continuation_strength_policy_id' if prefix[1] != '2C'
              else 'stayman_continuation_strength_policy_id')
    assert call(assess(prefix, **{option: 'missing'})) is None
    wrong = stayman(S.GAME_GOING) if prefix[1] != '2C' else jacoby(J.GAME_GOING)
    assert call(assess(prefix, **wrong)) is None


@pytest.mark.parametrize('option', ('jacoby_continuation_strength_policy_id', 'stayman_continuation_strength_policy_id'))
@pytest.mark.parametrize('bad', ('', '  ', 12))
def test_invalid_policy_ids(option, bad):
    with pytest.raises(ValueError):
        assess(PREFIXES[0], **{option: bad})


@pytest.mark.parametrize('calls', [
    (), ('P', 'P', 'P', 'P'), ('1NT', 'P'), ('1NT', 'P', '2D', 'P'),
    ('1NT', 'P', '2D', 'P', '2H'), ('1NT', 'P', '2D', 'P', '2H', 'P', '2NT', 'P'),
    ('1C', '1D', '1H', 'P', '1S', 'P'), ('1C', 'P', '1H', '1S', '2C', 'P'),
    ('1NT', 'P', '2D', 'P', '2H', '2S'), ('1NT', 'X', '2D', 'P', '2H', 'P'),
    ('1NT', 'P', '2D', 'X', '2H', 'P'), ('1NT', 'P', '2D', 'P', '2H', 'X'),
])
def test_scope_rejects_wrong_turn_completed_and_competitive_auctions(calls):
    with pytest.raises(ValueError):
        assess(PREFIXES[0], calls=calls)


@pytest.mark.parametrize('passes', (1, 2, 3))
def test_leading_passes_are_not_removed_to_manufacture_a_route(passes):
    result = assess(PREFIXES[0], calls=('P',)*passes + ('1NT', 'P', '2D', 'P', '2H', 'P'),
                    **jacoby(J.WEAK))
    assert result.disposition is D.ABSTAIN and result.route_id is None


@pytest.mark.parametrize('dealer', tuple(Seat))
def test_deterministic_immutable_core_facts_and_responder_orientation(dealer):
    first = assess(PREFIXES[0], dealer=dealer, **jacoby(J.WEAK))
    second = assess(PREFIXES[0], dealer=dealer, **jacoby(J.WEAK))
    assert first.selected == second.selected and first.reason == second.reason
    assert first.engine_result == second.engine_result and call(first) == 'P'
    assert first.context.seat is dealer.partner()
    assert first.context.evaluation == evaluate_hand(first.context.hand)
    assert (first.opening, first.response, first.opener_rebid) == PREFIXES[0]
    with pytest.raises(FrozenInstanceError):
        first.selected = None
    with pytest.raises(ValueError):
        replace(first, production_adopted=True)


@dataclass(frozen=True)
class FixtureRule:
    rule_id: str
    bid: str
    priority: int

    def evaluate(self, context):
        return RuleDecision.recommend(rule_id=self.rule_id, candidate=Call.parse(self.bid),
            explanation='Test conflict evidence.', sources=(SOURCE,), priority=self.priority)


@pytest.mark.parametrize('bid,priority,expected', [('2NT', 100, None), ('2NT', 90, 'P'), ('P', 100, 'P')])
def test_shared_conflict_precedence_and_same_call_deduplication(monkeypatch, bid, priority, expected):
    import bridge.responder_rebid as module
    engine = BiddingEngine((FixtureRule('a', 'P', 100), FixtureRule('b', bid, priority)))
    router = BiddingEngineRouter((EngineRoute('sayc.responder.fixture',
        auction_calls('1NT', 'P', '2D', 'P', '2H', 'P'), engine),))
    monkeypatch.setattr(module, 'create_standard_sayc_router', lambda registry: router)
    result = assess(PREFIXES[0])
    assert call(result) == expected and len(result.engine_result.decisions) == 2
    assert result.disposition is (D.CONFLICT if expected is None else D.RECOMMENDED)


def test_all_responder_routes_match_original_evidence_and_keep_45_routes():
    before = create_standard_sayc_router().routes
    covered = set()
    for prefix in PREFIXES:
        configs = [dict()] + ([jacoby(c) for c in J] if prefix[1] != '2C' else [stayman(c) for c in S])
        for config in configs:
            result = assess(prefix, **config)
            original = create_standard_sayc_router(config.get('registry')).evaluate(result.context)
            assert result.engine_result == original
            assert result.recommended_call == original.recommended_call
            covered.add(result.route_id)
    assert covered == {r.route_id for r in before if r.route_id.startswith('sayc.responder.')}
    after = create_standard_sayc_router().routes
    assert len(before) == len(after) == 45
    assert [(r.route_id, r.priority, r.policy_dependencies) for r in before] == [
        (r.route_id, r.priority, r.policy_dependencies) for r in after]
