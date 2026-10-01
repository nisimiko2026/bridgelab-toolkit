"""Opt-in Nisim-Nily raise continuations; sourced direction, no production route.

Qualitative suitability/strength is explicit evidence tied to the current hand
and auction. No implicit HCP classifier, hidden responder hand or DDS is used.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from .auction import Auction, Call
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .bergen_raises import resolve_bergen_agreement, BergenConfigurationError
from .models import Hand, Suit, Vulnerability
from .nisim_nily_jacoby_2nt import CueControlEvidence, _cue_check
from .nisim_nily_partnership_profile import (
    NISIM_NILY_BERGEN_PROFILE, MAJOR_RAISE_CONTINUATION_FAMILY as FAMILY,
    MAJOR_RAISE_CONTINUATION_TREATMENT as TREATMENT,
    MAJOR_RAISE_CONTINUATION_PARAMETERS as PARAMETERS,
)
from .partnership_profiles import (
    AgreementSourceScope, PartnershipProfile, ResolvedAgreement, ResolvedBiddingProfile,
    resolve_partnership_profile,
)
from .profile_rule_support import response_system

APPROVAL = KnowledgeSource('B2_4B5_MAJOR_RAISE_CONTINUATIONS', 'Approved continuations')
CARD = KnowledgeSource('bidding/convention-cards/cc-nily-nisim', 'trial bid after rise')


class RaiseIntent(str, Enum):
    SHORTNESS_TRIAL = 'SHORTNESS_TRIAL'
    HELP_SUIT_TRIAL = 'HELP_SUIT_TRIAL'
    INVITE_MAJOR = 'INVITE_MAJOR'
    NOTRUMP_GAME = 'NOTRUMP_GAME'
    GAME = 'GAME'
    MINIMUM_SIGNOFF = 'MINIMUM_SIGNOFF'
    PASS = 'PASS'
    KEYCARD_ASK = 'KEYCARD_ASK'
    CUE = 'CUE'
    ACCEPT_TRIAL = 'ACCEPT_TRIAL'


class RaiseCriterion(str, Enum):
    MINIMUM = 'MINIMUM'
    EXTRAS = 'EXTRAS'
    VERY_STRONG = 'VERY_STRONG'
    NOT_VERY_STRONG = 'NOT_VERY_STRONG'
    SLAM_SPECIAL = 'SLAM_SPECIAL'
    SUITABLE_TRIAL = 'SUITABLE_TRIAL'
    NO_SUITABLE_TRIAL = 'NO_SUITABLE_TRIAL'


@dataclass(frozen=True, slots=True)
class RaiseEvidence:
    intent: RaiseIntent
    hand: Hand
    auction: Auction
    explanation: str
    sources: tuple[KnowledgeSource, ...]
    criteria: frozenset[RaiseCriterion] = frozenset()
    call: Call | None = None
    _auction_key: tuple = field(init=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.intent, RaiseIntent) or not isinstance(self.hand, Hand) or not isinstance(self.auction, Auction):
            raise TypeError('Evidence requires typed intent, Hand and Auction')
        if not isinstance(self.explanation, str) or not self.explanation.strip():
            raise ValueError('Evidence requires an explanation')
        if not isinstance(self.sources, tuple) or not self.sources or any(not isinstance(s, KnowledgeSource) for s in self.sources):
            raise ValueError('Evidence requires source provenance')
        if not isinstance(self.criteria, frozenset) or any(not isinstance(c, RaiseCriterion) for c in self.criteria):
            raise TypeError('criteria must be a frozenset of RaiseCriterion')
        for a,b in ((RaiseCriterion.MINIMUM,RaiseCriterion.EXTRAS),
                    (RaiseCriterion.MINIMUM,RaiseCriterion.VERY_STRONG),
                    (RaiseCriterion.VERY_STRONG,RaiseCriterion.NOT_VERY_STRONG),
                    (RaiseCriterion.SUITABLE_TRIAL,RaiseCriterion.NO_SUITABLE_TRIAL)):
            if a in self.criteria and b in self.criteria:
                raise ValueError('Contradictory qualitative evidence')
        if self.intent in (RaiseIntent.HELP_SUIT_TRIAL,RaiseIntent.CUE):
            if not isinstance(self.call, Call):
                raise TypeError('Trial/cue requires an explicit Call')
        elif self.call is not None:
            raise ValueError('Only help-suit/cue intent accepts an explicit call')
        object.__setattr__(self,'_auction_key',(self.auction.dealer,self.auction.entries))


@dataclass(frozen=True, slots=True)
class RaiseMeaning:
    kind: str
    trump: Suit
    signoff: bool = False
    artificial: bool = False
    trial_suit: Suit | None = None
    control_round: int | None = None
    control_basis: str | None = None


@dataclass(frozen=True, slots=True)
class RaiseAssessment:
    profile: ResolvedBiddingProfile
    context: BiddingContext
    selected: RuleDecision | None
    meaning: RaiseMeaning | None
    blockers: tuple[str, ...]
    control_history: tuple[CueControlEvidence, ...] = ()
    production_adopted: bool = field(default=False, init=False)

    @property
    def recommended_call(self):
        return None if self.selected is None else self.selected.candidate


def _evidence(evidence, hand, auction):
    if evidence is not None:
        if not isinstance(evidence, RaiseEvidence):
            raise TypeError('Expected RaiseEvidence')
        if evidence.hand != hand or evidence._auction_key != (auction.dealer,auction.entries):
            raise ValueError('Evidence belongs to a different hand or auction')


def _context(hand, auction, vulnerability, profile, base_agreements):
    resolved=resolve_partnership_profile(profile,base_agreements=base_agreements)
    issues=[]
    if resolved.profile_id!=NISIM_NILY_BERGEN_PROFILE.profile_id or resolved.base_system is not NISIM_NILY_BERGEN_PROFILE.base_system:
        issues.append('Requires Nisim-Nily on its approved base system')
    agreement=resolved.agreement(FAMILY)
    if (agreement is None or agreement.source_scope is not AgreementSourceScope.PARTNERSHIP
            or agreement.treatment_id!=TREATMENT or agreement.parameters!=PARAMETERS):
        issues.append('Requires explicit approved B2.4B5 continuation agreement')
    try:
        bergen=resolve_bergen_agreement(profile,base_agreements=base_agreements)
    except BergenConfigurationError as exc:
        issues.append(str(exc)); bergen=None
    expected=next(a for a in NISIM_NILY_BERGEN_PROFILE.agreements if a.family=='response.major.raises')
    if bergen is None or bergen.source.parameters!=expected.parameters:
        issues.append('Requires finalized Nisim-Nily Bergen responder card')
    consumed={FAMILY,'response.major.raises','response.major.2nt'}
    rest=replace(resolved,agreements=tuple(a for a in resolved.agreements if a.family not in consumed))
    rest_profile=replace(profile,agreements=tuple(a for a in profile.agreements if a.family not in consumed))
    calls=tuple(e.call.serialize() for e in auction.entries)
    system,blockers=response_system(rest_profile,rest,calls[0] if calls else '',None,
                                   extra_families=('opener','rebid','responder.rebid'))
    issues.extend(blockers)
    context=BiddingContext.create(hand=hand,auction=auction,vulnerability=vulnerability,system=system)
    return resolved,context,tuple(issues)


def _prefix(context):
    calls=tuple(e.call.serialize() for e in context.auction.entries)
    if len(calls)<4 or len(calls)%2 or calls[0] not in ('1H','1S') or any(calls[i]!='P' for i in range(1,len(calls),2)):
        return None
    trump=Suit.parse(calls[0][-1])
    response=calls[2]
    if response not in ('2'+trump.letter,'3'+trump.letter,'3C','3D'):
        return None
    return trump,response


def _finish(profile, context, blockers=(), *, call=None, meaning=None, evidence=None, history=()):
    if blockers or call is None:
        return RaiseAssessment(profile,context,None,None,tuple(blockers) or ('No approved direction supplied',),history)
    if not context.auction.is_legal(call):
        return RaiseAssessment(profile,context,None,None,('Selected call is not legal',),history)
    sources=(APPROVAL,CARD)+(evidence.sources if evidence else ())
    why=meaning.kind+((': '+evidence.explanation) if evidence else '')
    decision=RuleDecision.recommend(rule_id='nisim_nily.major_raise.'+meaning.kind,
        candidate=call,explanation=why,sources=sources,priority=100)
    return RaiseAssessment(profile,context,decision,meaning,(),history)


def _trial(context,trump,response,evidence,agreement):
    if evidence is None or RaiseCriterion.SUITABLE_TRIAL not in evidence.criteria:
        return None
    facts=context.evaluation
    if evidence.intent is RaiseIntent.SHORTNESS_TRIAL and response=='2'+trump.letter:
        if not any(facts.length(s)<=1 for s in Suit if s is not trump):
            return None
        key='shortness_after_hearts' if trump is Suit.HEARTS else 'shortness_after_spades'
        call=Call.parse(agreement.option(key))
        return call,RaiseMeaning('shortness_trial',trump,artificial=True)
    if evidence.intent is RaiseIntent.HELP_SUIT_TRIAL and response in ('2'+trump.letter,'3C'):
        call=evidence.call
        if call.bid is None or call.bid.level!=3 or call.bid.strain.suit in (None,trump):
            return None
        special=facts.length(trump)>=6 and any(4<=facts.length(s)<=5 for s in Suit if s is not trump)
        if response=='2'+trump.letter and facts.hcp<14 and not special:
            return None
        if context.auction.is_legal(call):
            return call,RaiseMeaning('help_suit_trial',trump,trial_suit=call.bid.strain.suit)
    return None


def _cue(profile,context,trump,evidence,history):
    call=evidence.call
    if call.bid is None or call.bid.level not in (3,4):
        return _finish(profile,context,('Only three/four-level control cues are approved',),history=history)
    # Reuse the existing Nisim-Nily control policy and core exact hand facts.
    qualified=_cue_check(context,call,history,trump,'bergen')
    if qualified is None:
        return _finish(profile,context,('Cue requires an actual control and valid first/second-round history',),history=history)
    suit,round_number,basis=qualified
    shown=CueControlEvidence(suit,round_number,context.seat,len(context.auction.entries),call,basis,APPROVAL)
    return _finish(profile,context,call=call,
        meaning=RaiseMeaning('control_cue',trump,artificial=True,trial_suit=suit,control_round=round_number,control_basis=basis),
        evidence=evidence,history=history+(shown,))


def assess_major_raise_opener(hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement,...]=(),
    intent: RaiseEvidence | None=None, trials: tuple[RaiseEvidence,...]=()) -> RaiseAssessment:
    """Validate one sourced opener direction; trial preference applies before 3M.

    Missing qualitative evidence abstains. Multiple suitable trial calls abstain
    rather than inventing a suit order. No implicit default Pass is supplied.
    """
    resolved,context,issues=_context(hand,auction,vulnerability,profile,base_agreements)
    _evidence(intent,hand,auction)
    if not isinstance(trials,tuple): raise TypeError('trials must be a tuple')
    for trial in trials:
        if not isinstance(trial,RaiseEvidence): raise TypeError('trial must be RaiseEvidence')
        _evidence(trial,hand,auction)
        if trial.intent not in (RaiseIntent.SHORTNESS_TRIAL,RaiseIntent.HELP_SUIT_TRIAL):
            raise ValueError('Only trial evidence belongs in trials')
    prefix=_prefix(context)
    if prefix is None or len(auction.entries)!=4:
        issues+=('Requires opener after an exact uncontested major raise',)
    if issues: return _finish(resolved,context,issues)
    trump,response=prefix
    agreement=resolved.agreement(FAMILY)
    if response=='2'+trump.letter and (intent is None or intent.intent is RaiseIntent.INVITE_MAJOR):
        qualified=[(trial,_trial(context,trump,response,trial,agreement)) for trial in trials]
        qualified=[(trial,value) for trial,value in qualified if value is not None]
        if qualified:
            if intent is not None and RaiseCriterion.NO_SUITABLE_TRIAL in intent.criteria:
                raise ValueError('No-suitable-trial evidence contradicts supplied suitable trial')
            if len({value[0] for _,value in qualified})>1:
                return _finish(resolved,context,('Multiple suitable trials; explicit suit choice required',))
            evidence,(call,meaning)=qualified[0]
            return _finish(resolved,context,call=call,meaning=meaning,evidence=evidence)
    if intent is None: return _finish(resolved,context)
    trial=_trial(context,trump,response,intent,agreement)
    if trial:
        call,meaning=trial
        return _finish(resolved,context,call=call,meaning=meaning,evidence=intent)
    kind=intent.intent; criteria=intent.criteria; facts=context.evaluation
    major=facts.length(trump)
    call=None; meaning=None
    if response=='2'+trump.letter:
        if kind is RaiseIntent.INVITE_MAJOR and (15<=facts.hcp<=16 and major==6
                and all(facts.length(s)>=2 for s in Suit if s is not trump)
                and RaiseCriterion.NO_SUITABLE_TRIAL in criteria):
            call=Call.parse('3'+trump.letter); meaning=RaiseMeaning('major_invitation',trump)
        elif kind is RaiseIntent.NOTRUMP_GAME and facts.hcp>=18 and major==5 and facts.distribution==(5,3,3,2):
            call=Call.parse('3NT'); meaning=RaiseMeaning('notrump_game',trump,signoff=True)
        elif kind is RaiseIntent.GAME and (facts.hcp==18 or (not facts.is_balanced and facts.hcp>=16)):
            call=Call.parse('4'+trump.letter); meaning=RaiseMeaning('game_signoff',trump,signoff=True)
        elif kind is RaiseIntent.KEYCARD_ASK and RaiseCriterion.SLAM_SPECIAL in criteria:
            call=Call.parse('4NT'); meaning=RaiseMeaning('rkc_ask',trump,artificial=True)
    elif response=='3'+trump.letter:
        if kind is RaiseIntent.PASS and RaiseCriterion.NOT_VERY_STRONG in criteria:
            call=Call.pass_(); meaning=RaiseMeaning('weak_raise_pass',trump,signoff=True)
        elif kind is RaiseIntent.GAME and RaiseCriterion.VERY_STRONG in criteria:
            call=Call.parse('4'+trump.letter); meaning=RaiseMeaning('weak_raise_game',trump,signoff=True)
    elif response in ('3C','3D'):
        if kind is RaiseIntent.MINIMUM_SIGNOFF and RaiseCriterion.MINIMUM in criteria:
            call=Call.parse('3'+trump.letter); meaning=RaiseMeaning('minimum_signoff',trump,signoff=True)
        elif kind is RaiseIntent.GAME and ((response=='3C' and (facts.hcp>=16 or 6<=major<=7))
                or (response=='3D' and RaiseCriterion.EXTRAS in criteria)):
            call=Call.parse('4'+trump.letter); meaning=RaiseMeaning('game_signoff',trump,signoff=True)
        elif response=='3D' and kind is RaiseIntent.CUE:
            return _cue(resolved,context,trump,intent,())
        elif response=='3D' and kind is RaiseIntent.KEYCARD_ASK and RaiseCriterion.SLAM_SPECIAL in criteria:
            call=Call.parse('4NT'); meaning=RaiseMeaning('rkc_ask',trump,artificial=True)
    return _finish(resolved,context,() if call else ('Direction lacks approved conditions for this response',),
                   call=call,meaning=meaning,evidence=intent)


def assess_major_raise_responder(hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement,...]=(),
    intent: RaiseEvidence | None=None) -> RaiseAssessment:
    """Only help-trial acceptance or the approved 3D control-cue continuation.

    No response to a shortness trial, RKC answer scheme or trial signoff is
    invented. Prior cues are seat-specific auction claims, never hidden cards.
    """
    resolved,context,issues=_context(hand,auction,vulnerability,profile,base_agreements)
    _evidence(intent,hand,auction)
    prefix=_prefix(context)
    if prefix is None or len(auction.entries)<6 or len(auction.entries)%4!=2:
        issues+=('Requires responder after an uncontested approved opener continuation',)
    if issues: return _finish(resolved,context,issues)
    trump,response=prefix
    if response in ('2'+trump.letter,'3C') and len(auction.entries)==6:
        trial=auction.entries[4].call.bid
        if trial is not None and trial.level==3 and trial.strain.suit not in (None,trump):
            short=context.evaluation.length(trial.strain.suit)<=1
            extras=intent is not None and intent.intent is RaiseIntent.ACCEPT_TRIAL and RaiseCriterion.EXTRAS in intent.criteria
            if intent is not None and intent.intent is not RaiseIntent.ACCEPT_TRIAL:
                return _finish(resolved,context,('Only trial acceptance is defined here',))
            if short or extras:
                return _finish(resolved,context,call=Call.parse('4'+trump.letter),
                    meaning=RaiseMeaning('trial_acceptance',trump,signoff=True,trial_suit=trial.strain.suit),evidence=intent)
        return _finish(resolved,context,('No approved automatic trial fallback or shortness-trial response',))
    if response=='3D':
        history=[]
        for index in range(4,len(auction.entries),2):
            entry=auction.entries[index]; bid=entry.call.bid
            if bid is None or bid.level not in (3,4) or bid.strain.suit in (None,trump):
                return _finish(resolved,context,('Cue continuation ends at signoff, ask or unsupported call',),history=tuple(history))
            suit=bid.strain.suit
            round_number=1+sum(c.suit is suit for c in history)
            if round_number>2:
                return _finish(resolved,context,('Third control cue is not defined',),history=tuple(history))
            history.append(CueControlEvidence(suit,round_number,entry.seat,index,entry.call,'auction control claim',APPROVAL))
        if intent is not None and intent.intent is RaiseIntent.CUE:
            return _cue(resolved,context,trump,intent,tuple(history))
        return _finish(resolved,context,('Explicit responder control-cue direction required',),history=tuple(history))
    return _finish(resolved,context,('No approved responder continuation for this branch',))
