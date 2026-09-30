"""Card-driven Bergen first responses; opt-in, with no production route binding.

Uses the existing partnership resolver. Reference articles are never loaded.
No universal ranges, call meanings, or opener continuations live here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from itertools import combinations

from .auction import Auction, Call
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Hand, Suit, Vulnerability
from .profile_rule_support import response_system
from .partnership_profiles import (
    AgreementSourceScope, PartnershipProfile, ResolvedAgreement,
    ResolvedBiddingProfile, resolve_partnership_profile,
)

BERGEN_RAISES = 'BERGEN_RAISES'
BERGEN_FAMILY = 'response.major.raises'
JACOBY_FAMILY = 'response.major.2nt'
_SLOTS = ('simple_raise', 'three_clubs', 'three_diamonds', 'three_major')
_CALLS = frozenset(('2M', '3C', '3D', '3M'))
_FIELDS = ('call', 'enabled', 'meaning', 'min_hcp', 'max_hcp',
           'min_support', 'max_support', 'artificial', 'forcing')


class BergenConfigurationError(ValueError):
    """Contradictory, impossible or unsupported explicit card configuration."""


class BergenConfigurationIncomplete(BergenConfigurationError):
    """Enabled convention lacks required explicit card information."""


class BergenStatus(str, Enum):
    RECOMMENDED = 'RECOMMENDED'
    ABSTAIN = 'ABSTAIN'
    CONFIGURATION_INCOMPLETE = 'CONFIGURATION_INCOMPLETE'
    CONFLICT = 'CONFLICT'
    DEFER_TO_JACOBY = 'DEFER_TO_JACOBY'


@dataclass(frozen=True, slots=True)
class BergenBranch:
    call: str
    enabled: bool
    meaning: str | None = None
    hcp: tuple[int, int] | None = None
    support: tuple[int, int] | None = None
    artificial: bool | None = None
    forcing: str | None = None

    def matches(self, hcp: int, support: int) -> bool:
        return (self.enabled and self.hcp[0] <= hcp <= self.hcp[1]
                and self.support[0] <= support <= self.support[1])


@dataclass(frozen=True, slots=True)
class ResolvedBergenAgreement:
    profile: ResolvedBiddingProfile
    source: ResolvedAgreement
    branches: tuple[BergenBranch, ...]
    branch_policy: str
    jacoby_relationship: str
    jacoby_source: ResolvedAgreement | None
    jacoby_hcp: tuple[int, int] | None
    jacoby_support: tuple[int, int] | None

    @property
    def convention(self) -> str:
        return BERGEN_RAISES


def _integer(params, key):
    try:
        text = params[key]
        if not text.isascii() or not text.isdecimal():
            raise ValueError
        return int(text)
    except ValueError as exc:
        raise BergenConfigurationError(f'{key} must be a nonnegative integer') from exc


def _boolean(params, key):
    if params[key] not in ('true', 'false'):
        raise BergenConfigurationError(f'{key} must be true or false')
    return params[key] == 'true'


def _range(params, low, high, maximum):
    result = (_integer(params, low), _integer(params, high))
    if not 0 <= result[0] <= result[1] <= maximum:
        raise BergenConfigurationError(f'impossible range: {low}/{high}')
    return result


def _feasible(hcp, support):
    # Physical hand bounds, not bidding thresholds. Nine spots per suit.
    for length in range(support[0], support[1] + 1):
        minimum = sum((1, 2, 3, 4)[:max(0, length - 9)])
        maximum = sum((4, 3, 2, 1)[:length]) + sum(
            sorted((4, 3, 2, 1) * 3, reverse=True)[:13 - length])
        if max(minimum, hcp[0]) <= min(maximum, hcp[1]):
            return True
    return False


def _overlap(a_hcp, a_support, b_hcp, b_support):
    hcp = (max(a_hcp[0], b_hcp[0]), min(a_hcp[1], b_hcp[1]))
    support = (max(a_support[0], b_support[0]), min(a_support[1], b_support[1]))
    return hcp[0] <= hcp[1] and support[0] <= support[1] and _feasible(hcp, support)


def _required(params, keys):
    missing = sorted(key for key in keys if not params.get(key))
    if missing:
        raise BergenConfigurationIncomplete('Missing card parameters: ' + ', '.join(missing))


def _resolve(resolved):
    source = resolved.agreement(BERGEN_FAMILY)
    if source is None or source.treatment_id not in (BERGEN_RAISES, 'bergen'):
        return None
    # Explicit card adoption is required; an inherited system/reference default
    # must not activate a convention in another partnership.
    if source.source_scope is not AgreementSourceScope.PARTNERSHIP:
        raise BergenConfigurationIncomplete('Bergen requires explicit partnership card selection')
    if not resolved.sources:
        raise BergenConfigurationIncomplete('Bergen requires card provenance in profile.sources')
    params = dict(source.parameters)
    allowed = {'card_source', 'strength_metric', 'branch_policy', 'jacoby_relationship', 'jacoby_treatment'}
    allowed.update(f'{slot}.{field}' for slot in _SLOTS for field in _FIELDS)
    if set(params) - allowed:
        raise BergenConfigurationError('Unsupported card parameters: ' + ', '.join(sorted(set(params) - allowed)))
    _required(params, ('card_source', 'strength_metric', 'branch_policy', 'jacoby_relationship'))
    if (params['card_source'] not in resolved.sources
            or not params['card_source'].startswith('bidding/convention-cards/')):
        raise BergenConfigurationError('card_source must identify an explicit convention card in profile.sources')
    if params['strength_metric'] != 'hcp':
        raise BergenConfigurationError('Only explicit HCP ranges are supported; no point conversion')
    if params['branch_policy'] not in ('exclusive', 'conflict'):
        raise BergenConfigurationError('branch_policy must be exclusive or conflict')
    if params['jacoby_relationship'] not in ('disabled', 'disjoint', 'defer_to_jacoby'):
        raise BergenConfigurationError('Unsupported Jacoby relationship')
    branches = []
    for slot in _SLOTS:
        prefix = slot + '.'
        _required(params, (prefix + 'call', prefix + 'enabled'))
        call = params[prefix + 'call']
        if call not in _CALLS:
            raise BergenConfigurationError(f'Unsupported Bergen responder call: {call}')
        enabled = _boolean(params, prefix + 'enabled')
        if not enabled:
            if any(prefix + field in params for field in _FIELDS[2:]):
                raise BergenConfigurationError(f'Disabled branch has active meaning/ranges: {slot}')
            branches.append(BergenBranch(call, False))
            continue
        _required(params, (prefix + field for field in _FIELDS[2:]))
        hcp = _range(params, prefix + 'min_hcp', prefix + 'max_hcp', 37)
        support = _range(params, prefix + 'min_support', prefix + 'max_support', 13)
        if not _feasible(hcp, support):
            raise BergenConfigurationError(f'Impossible HCP/support combination: {slot}')
        forcing = params[prefix + 'forcing']
        if forcing not in ('nonforcing', 'invitational', 'forcing', 'game_forcing'):
            raise BergenConfigurationError(f'Unsupported forcing meaning: {forcing}')
        branches.append(BergenBranch(call, True, params[prefix + 'meaning'], hcp,
                                    support, _boolean(params, prefix + 'artificial'), forcing))
    if len({branch.call for branch in branches}) != len(branches):
        raise BergenConfigurationError('Duplicate responder calls in Bergen mapping')
    enabled = tuple(branch for branch in branches if branch.enabled)
    if params['branch_policy'] == 'exclusive':
        for a, b in combinations(enabled, 2):
            if _overlap(a.hcp, a.support, b.hcp, b.support):
                raise BergenConfigurationError(f'Overlapping exclusive branches: {a.call}/{b.call}')

    jacoby = resolved.agreement(JACOBY_FAMILY)
    relationship = params['jacoby_relationship']
    jacoby_hcp = jacoby_support = None
    if relationship == 'disabled':
        if jacoby is not None or 'jacoby_treatment' in params:
            raise BergenConfigurationError('Jacoby disabled in Bergen card but separately configured')
    else:
        _required(params, ('jacoby_treatment',))
        if jacoby is None or jacoby.treatment_id != params['jacoby_treatment']:
            raise BergenConfigurationIncomplete('Matching separate Jacoby treatment is required')
        jp = dict(jacoby.parameters)
        if set(jp) - {'min_hcp', 'min_support', 'max_hcp', 'max_support'}:
            raise BergenConfigurationError('Unsupported Jacoby eligibility parameters')
        _required(jp, ('min_hcp', 'min_support'))
        # Omitted maxima mean unbounded within a legal hand, as in min-only
        # existing Jacoby agreements. No partnership-specific minima are supplied.
        jp.setdefault('max_hcp', '37')
        jp.setdefault('max_support', '13')
        jacoby_hcp = _range(jp, 'min_hcp', 'max_hcp', 37)
        jacoby_support = _range(jp, 'min_support', 'max_support', 13)
        if not _feasible(jacoby_hcp, jacoby_support):
            raise BergenConfigurationError('Impossible separate Jacoby eligibility')
        if relationship == 'disjoint' and any(
                _overlap(b.hcp, b.support, jacoby_hcp, jacoby_support) for b in enabled):
            raise BergenConfigurationError('Bergen/Jacoby overlap contradicts disjoint card declaration')
    return ResolvedBergenAgreement(resolved, source, tuple(branches),
        params['branch_policy'], relationship, jacoby, jacoby_hcp, jacoby_support)


def resolve_bergen_agreement(
    profile: PartnershipProfile, *, base_agreements: tuple[ResolvedAgreement, ...] = (),
) -> ResolvedBergenAgreement | None:
    """Resolve card data once, then validate it; incomplete/invalid cards raise.

    None means the convention is absent/disabled. Legacy ``bergen`` identifies
    the same family but does not provide missing parameters. Overrides replace
    the whole parameter set using the existing resolver; no default merging.
    """
    return _resolve(resolve_partnership_profile(profile, base_agreements=base_agreements))


@dataclass(frozen=True, slots=True)
class BergenAssessment:
    profile: ResolvedBiddingProfile
    agreement: ResolvedBergenAgreement | None
    status: BergenStatus
    selected: RuleDecision | None
    meaning: BergenBranch | None
    reason: str

    @property
    def recommended_call(self) -> Call | None:
        return None if self.selected is None else self.selected.candidate

    @property
    def production_adopted(self) -> bool:
        return False


def assess_bergen_response(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
) -> BergenAssessment:
    """Only exact uncontested 1H/1S-P. No natural fallback or automatic Pass.

    Incomplete configuration returns an explicit abstention; contradictory
    configuration raises BergenConfigurationError before evaluating a hand.
    Jacoby deferral selects no call: its separate assessor remains authoritative.
    """
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    try:
        agreement = _resolve(resolved)
    except BergenConfigurationIncomplete as exc:
        return BergenAssessment(resolved, None, BergenStatus.CONFIGURATION_INCOMPLETE,
                                None, None, str(exc))

    def abstain(status, reason):
        return BergenAssessment(resolved, agreement, status, None, None, reason)

    if agreement is None:
        return abstain(BergenStatus.ABSTAIN, 'No active Bergen card agreement')
    calls = tuple(entry.call.serialize() for entry in auction.entries)
    if calls not in (('1H', 'P'), ('1S', 'P')):
        return abstain(BergenStatus.ABSTAIN, 'Requires exact uncontested first response after 1H/1S')
    remainder = replace(resolved, agreements=tuple(a for a in resolved.agreements
                        if a.family not in (BERGEN_FAMILY, JACOBY_FAMILY)))
    # Both families were consumed above, including an explicit Jacoby DISABLE.
    # Keep unrelated guards while avoiding a second opaque binding of our card.
    remainder_profile = replace(profile, agreements=tuple(a for a in profile.agreements
                                if a.family not in (BERGEN_FAMILY, JACOBY_FAMILY)))
    system, blockers = response_system(remainder_profile, remainder, calls[0], None)
    if blockers:
        return abstain(BergenStatus.ABSTAIN, '; '.join(blockers))
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability,
                                    system=system)
    trump = Suit.parse(calls[0][-1])
    hcp, support = context.evaluation.hcp, context.evaluation.length(trump)
    if (agreement.jacoby_relationship == 'defer_to_jacoby'
            and agreement.jacoby_hcp[0] <= hcp <= agreement.jacoby_hcp[1]
            and agreement.jacoby_support[0] <= support <= agreement.jacoby_support[1]):
        return abstain(BergenStatus.DEFER_TO_JACOBY, 'Card reserves this hand for the separate Jacoby treatment')
    candidates = [branch for branch in agreement.branches if branch.matches(hcp, support)]
    if len(candidates) > 1:
        return abstain(BergenStatus.CONFLICT, 'Multiple card branches qualify; no precedence was supplied')
    if not candidates:
        return abstain(BergenStatus.ABSTAIN, 'No enabled Bergen card branch covers this hand')
    branch = candidates[0]
    selected = RuleDecision.recommend(
        rule_id='bergen.response.' + branch.call.lower(),
        candidate=Call.parse(branch.call.replace('M', trump.letter)),
        explanation=f'{resolved.profile_id}@{resolved.version}: {branch.meaning}; {branch.forcing}',
        sources=tuple(KnowledgeSource(source, 'Explicit Bergen card parameters') for source in resolved.sources),
        priority=100)
    return BergenAssessment(resolved, agreement, BergenStatus.RECOMMENDED, selected, branch, selected.explanation)
