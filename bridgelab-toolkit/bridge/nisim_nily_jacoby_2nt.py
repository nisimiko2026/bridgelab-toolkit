"""Opt-in Nisim-Nily Jacoby 2NT. No standard-router registration."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from .auction import Auction, Call
from .bidding_engine import BiddingEngine, BiddingEngineResult
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Hand, Seat, Suit, Vulnerability
from .nisim_nily_partnership_profile import (
    JACOBY_2NT_APPROVAL, JACOBY_2NT_FAMILY, JACOBY_2NT_PARAMETERS,
    JACOBY_2NT_TREATMENT, NISIM_NILY_PROFILE,
)
from .partnership_profiles import (
    AgreementSourceScope, PartnershipProfile, ResolvedAgreement,
    ResolvedBiddingProfile, resolve_partnership_profile,
)
from .profile_rule_support import response_system, top_priority_conflicts
from .system_profiles import SystemProfile

APPROVAL = KnowledgeSource(JACOBY_2NT_APPROVAL, "Approved agreement")
SOURCE = KnowledgeSource("bidding/conventions/responses/jacoby-notrump", "Meaning of 2NT")


class JacobyDisposition(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    ABSTAIN = "ABSTAIN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class JacobyMeaning:
    """Only the selected approved meaning; no inferred hidden-hand facts."""
    artificial: bool
    game_forcing: bool
    trump: Suit
    minimum_support: int | None = None
    shown_shortness: Suit | None = None
    extras: bool = False
    slam_interest: bool = False
    minimum: bool = False
    balanced: bool = False
    hcp_range: tuple[int, int] | None = None
    cue_suit: Suit | None = None
    ace_ask: bool = False
    signoff: bool = False
    good_hand: bool = False
    no_suitable_cue: bool = False
    conditional_stop: bool = False
    control_round: int | None = None
    control_basis: str | None = None
    direct_slam: bool = False


@dataclass(frozen=True, slots=True)
class JacobyAssessment:
    profile: ResolvedBiddingProfile
    context: BiddingContext
    disposition: JacobyDisposition
    selected: RuleDecision | None
    meaning: JacobyMeaning | None
    engine_result: BiddingEngineResult | None
    blockers: tuple[str, ...]
    reason: str
    production_adopted: bool = False
    continuation_needed: bool = False
    continuation_sources: tuple[KnowledgeSource, ...] = ()
    control_history: tuple[CueControlEvidence, ...] = ()

    def __post_init__(self):
        if self.production_adopted:
            raise ValueError("Jacoby agreement is not production adopted")
        if self.continuation_needed and (
                self.disposition is not JacobyDisposition.ABSTAIN or not self.continuation_sources):
            raise ValueError("unresolved continuation requires abstention and provenance")
        recommended = self.disposition is JacobyDisposition.RECOMMENDED
        if recommended != (self.selected is not None) or recommended != (self.meaning is not None):
            raise ValueError("only a recommended result may select a call and meaning")
        if self.selected is not None and (not self.selected.applicable or self.blockers):
            raise ValueError("selected call requires applicable unblocked evidence")

    @property
    def recommended_call(self) -> Call | None:
        return None if self.selected is None else self.selected.candidate


def _context(hand, auction, vulnerability, profile, base_agreements):
    resolved = resolve_partnership_profile(profile, base_agreements=base_agreements)
    calls = tuple(e.call.serialize() for e in auction.entries)
    opening = calls[0] if calls else ""
    issues = []
    if (resolved.profile_id != NISIM_NILY_PROFILE.profile_id
            or resolved.base_system is not SystemProfile.TWO_OVER_ONE_GF):
        issues.append("Requires the Nisim-Nily partnership layered on TWO_OVER_ONE_GF")
    agreement = resolved.agreement(JACOBY_2NT_FAMILY)
    if (agreement is None or agreement.treatment_id != JACOBY_2NT_TREATMENT
            or agreement.source_scope is not AgreementSourceScope.PARTNERSHIP
            or agreement.parameters != JACOBY_2NT_PARAMETERS):
        issues.append("Requires the explicit approved partnership Jacoby 2NT agreement and parameters")
    # The dedicated binding consumes only the exact Jacoby family. All other
    # effective meanings still pass through the existing shared fallback guards.
    remainder = replace(resolved, agreements=tuple(a for a in resolved.agreements
                                                  if a.family != JACOBY_2NT_FAMILY))
    system, blockers = response_system(profile, remainder, opening, None,
                                       extra_families=("rebid", "opener.rebid", "responder.rebid"))
    issues.extend(blockers)
    context = BiddingContext.create(hand=hand, auction=auction, vulnerability=vulnerability, system=system)
    return resolved, context, tuple(issues)


@dataclass(frozen=True, slots=True)
class _ResponseRule:
    trump: Suit
    rule_id: str = "nisim_nily.jacoby_2nt.response"

    def evaluate(self, context):
        facts = context.evaluation
        if facts.hcp < 13 or facts.length(self.trump) < 4:
            return RuleDecision.not_applicable(self.rule_id, "Requires 13+ HCP and 4+ trump support.")
        return RuleDecision.recommend(rule_id=self.rule_id, candidate=Call.parse("2NT"),
            explanation="Nisim-Nily Jacoby 2NT: artificial game-forcing raise, 13+ HCP and 4+ support; any shape.",
            sources=(APPROVAL, SOURCE), priority=100)


def _finish(resolved, context, blockers, rules, meanings):
    if blockers:
        return JacobyAssessment(resolved, context, JacobyDisposition.ABSTAIN, None, None, None,
                                blockers, "Unresolved profile or auction meaning; no fallback.")
    evidence = BiddingEngine(rules).evaluate(context)
    tied = top_priority_conflicts(evidence)
    if tied:
        return JacobyAssessment(resolved, context, JacobyDisposition.CONFLICT, None, None, evidence,
                                tuple(d.rule_id for d in tied), "Competing approved calls; no tie-breaking agreement.")
    if evidence.recommended is None:
        return JacobyAssessment(resolved, context, JacobyDisposition.ABSTAIN, None, None, evidence,
                                ("No approved continuation qualifies",), "Approved rules abstain; no call or Pass inferred.")
    selected = evidence.recommended
    return JacobyAssessment(resolved, context, JacobyDisposition.RECOMMENDED, selected,
                            meanings[selected.rule_id], evidence, (), selected.explanation)


def assess_jacoby_2nt_response(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
) -> JacobyAssessment:
    """Assess only exact uncontested 1H/1S-P with an explicitly enabled profile."""
    resolved, context, issues = _context(hand, auction, vulnerability, profile, base_agreements)
    calls = tuple(e.call.serialize() for e in auction.entries)
    if calls not in (("1H", "P"), ("1S", "P")):
        return _finish(resolved, context, issues + ("Requires exact uncontested 1H/1S-P",), (), {})
    trump = Suit.parse(calls[0][-1])
    rule = _ResponseRule(trump)
    return _finish(resolved, context, issues, (rule,),
                   {rule.rule_id: JacobyMeaning(True, True, trump, minimum_support=4)})

class OpenerStrength(str, Enum):
    EXTRAS = "EXTRAS"
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class OpenerStrengthEvidence:
    """Caller-supplied qualitative assessment, not an HCP classifier.

    The exact hand/auction binding prevents reusing an assessment from another
    position. EXTRAS or MINIMUM require a reason and explicit source evidence.
    """
    classification: OpenerStrength
    hand: Hand
    auction: Auction
    explanation: str
    sources: tuple[KnowledgeSource, ...]

    def __post_init__(self):
        if not isinstance(self.classification, OpenerStrength):
            raise TypeError("classification must be OpenerStrength")
        if not isinstance(self.hand, Hand) or not isinstance(self.auction, Auction):
            raise TypeError("strength evidence requires exact Hand and Auction")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be str")
        if not isinstance(self.sources, tuple) or any(not isinstance(s, KnowledgeSource) for s in self.sources):
            raise TypeError("sources must be a tuple of KnowledgeSource")
        if self.classification is not OpenerStrength.UNKNOWN and (not self.explanation.strip() or not self.sources):
            raise ValueError("known opener strength requires explanation and provenance")


@dataclass(frozen=True, slots=True)
class _ShortnessRule:
    suit: Suit

    @property
    def rule_id(self):
        return "nisim_nily.jacoby_2nt.shortness." + self.suit.letter.lower()

    def evaluate(self, context):
        from .evaluation import Shortness
        shortness = context.evaluation.honor_evidence(self.suit).shortness
        if shortness not in (Shortness.SINGLETON, Shortness.VOID):
            return RuleDecision.not_applicable(self.rule_id, "Side-suit doubletons or longer are not shortness bids.")
        return RuleDecision.recommend(rule_id=self.rule_id, candidate=Call.parse("3" + self.suit.letter),
            explanation=f"Nisim-Nily Jacoby 2NT: artificial side-suit rebid shows {shortness.value} in {self.suit.name.lower()}.",
            sources=(APPROVAL,), priority=400)


@dataclass(frozen=True, slots=True)
class _StrengthRule:
    trump: Suit
    target: OpenerStrength
    evidence: OpenerStrengthEvidence | None

    @property
    def rule_id(self):
        return "nisim_nily.jacoby_2nt." + self.target.value.lower()

    def evaluate(self, context):
        if self.evidence is None or self.evidence.classification is not self.target:
            return RuleDecision.not_applicable(self.rule_id, "Requires explicit sourced opener strength; no numeric range inferred.")
        extras = self.target is OpenerStrength.EXTRAS
        return RuleDecision.recommend(rule_id=self.rule_id,
            candidate=Call.parse(("3" if extras else "4") + self.trump.letter),
            explanation=("Nisim-Nily Jacoby 2NT: 3M shows extras and slam interest. " if extras
                         else "Nisim-Nily Jacoby 2NT: 4M shows a minimum. ") + self.evidence.explanation,
            sources=(APPROVAL,) + self.evidence.sources, priority=300 if extras else 100)


@dataclass(frozen=True, slots=True)
class _BalancedRule:
    rule_id: str = "nisim_nily.jacoby_2nt.balanced"

    def evaluate(self, context):
        facts = context.evaluation
        if not facts.is_balanced or not 14 <= facts.hcp <= 15:
            return RuleDecision.not_applicable(self.rule_id, "3NT requires balanced 14-15 HCP.")
        return RuleDecision.recommend(rule_id=self.rule_id, candidate=Call.parse("3NT"),
            explanation="Nisim-Nily Jacoby 2NT: 3NT shows balanced 14-15 HCP.", sources=(APPROVAL,), priority=200)


def assess_jacoby_2nt_opener(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    strength: OpenerStrengthEvidence | None = None,
) -> JacobyAssessment:
    """Assess only opener after 1H/1S-P-2NT-P.

    Precedence: shortness > explicit extras > balanced 14-15 > explicit minimum.
    Multiple short suits yield CONFLICT (no selected call); no suit preference
    is manufactured. Later responder continuations are outside this API.
    """
    resolved, context, issues = _context(hand, auction, vulnerability, profile, base_agreements)
    if strength is not None:
        if not isinstance(strength, OpenerStrengthEvidence):
            raise TypeError("strength must be OpenerStrengthEvidence")
        if (strength.hand != hand or strength.auction.dealer is not auction.dealer
                or strength.auction.entries != auction.entries):
            raise ValueError("strength evidence belongs to a different hand or auction")
    calls = tuple(e.call.serialize() for e in auction.entries)
    if calls not in (("1H", "P", "2NT", "P"), ("1S", "P", "2NT", "P")):
        return _finish(resolved, context, issues + ("Requires exact uncontested 1H/1S-P-2NT-P",), (), {})
    trump = Suit.parse(calls[0][-1])
    short_rules = tuple(_ShortnessRule(suit) for suit in Suit if suit is not trump)
    extras = _StrengthRule(trump, OpenerStrength.EXTRAS, strength)
    minimum = _StrengthRule(trump, OpenerStrength.MINIMUM, strength)
    balanced = _BalancedRule()
    meanings = {r.rule_id: JacobyMeaning(True, True, trump, shown_shortness=r.suit) for r in short_rules}
    meanings.update({
        extras.rule_id: JacobyMeaning(False, True, trump, extras=True, slam_interest=True),
        balanced.rule_id: JacobyMeaning(False, True, trump, balanced=True, hcp_range=(14, 15)),
        minimum.rule_id: JacobyMeaning(False, True, trump, minimum=True),
    })
    return _finish(resolved, context, issues, (*short_rules, extras, balanced, minimum), meanings)


CONTINUATION_APPROVAL = KnowledgeSource("B2_4A3_JACOBY_CONTINUATIONS", "Approved continuations")


class ResponderIntent(str, Enum):
    CUE_BID = "CUE_BID"
    ACE_ASK = "ACE_ASK"
    SIGNOFF = "SIGNOFF"
    GOOD_NO_CUE = "GOOD_NO_CUE"
    CONDITIONAL_STOP = "CONDITIONAL_STOP"
    DIRECT_SLAM = "DIRECT_SLAM"


@dataclass(frozen=True, slots=True)
class ResponderContinuationEvidence:
    """Sourced direction, not a numeric hand-strength or control classifier.

    CUE_BID includes the caller's specific legal new-suit call. GOOD_NO_CUE
    attests a good hand, slam interest and no suitable/available cue. The
    conditional-stop intent attests insufficient strength for direct cue/ask.
    """
    intent: ResponderIntent
    hand: Hand
    auction: Auction
    explanation: str
    sources: tuple[KnowledgeSource, ...]
    cue_call: Call | None = None
    cue_round: int | None = None
    slam_call: Call | None = None
    _auction_key: tuple = field(init=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.intent, ResponderIntent):
            raise TypeError("intent must be ResponderIntent")
        if not isinstance(self.hand, Hand) or not isinstance(self.auction, Auction):
            raise TypeError("continuation evidence requires Hand and Auction")
        if not isinstance(self.explanation, str) or not self.explanation.strip():
            raise ValueError("continuation intent requires an explanation")
        if not isinstance(self.sources, tuple) or not self.sources:
            raise ValueError("continuation intent requires source provenance")
        if any(not isinstance(s, KnowledgeSource) for s in self.sources):
            raise TypeError("sources must contain KnowledgeSource")
        if self.intent is ResponderIntent.CUE_BID:
            if not isinstance(self.cue_call, Call):
                raise TypeError("cue intent requires an explicit Call")
        elif self.cue_call is not None:
            raise ValueError("only cue intent may specify cue_call")
        if self.cue_round is not None and (self.intent is not ResponderIntent.CUE_BID
                or type(self.cue_round) is not int or self.cue_round not in (1, 2)):
            raise ValueError("cue_round requires cue intent and round 1 or 2")
        if self.intent is ResponderIntent.DIRECT_SLAM:
            if not isinstance(self.slam_call, Call):
                raise TypeError("direct slam requires an explicit slam_call")
        elif self.slam_call is not None:
            raise ValueError("only direct-slam intent may specify slam_call")
        object.__setattr__(self, "_auction_key", (self.auction.dealer, self.auction.entries))


def _continuation_prefix(auction: Auction):
    """Identify the approved six-call prefix without inferring hidden cards."""
    calls = tuple(e.call.serialize() for e in auction.entries)
    if (len(calls) < 6 or calls[0] not in ("1H", "1S") or calls[2] != "2NT"
            or any(calls[i] != "P" for i in (1, 3, 5))):
        return None
    trump = Suit.parse(calls[0][-1])
    rebid = calls[4]
    if rebid == "3" + trump.letter:
        return trump, "extras"
    if rebid == "3NT":
        return trump, "balanced"
    if rebid in tuple("3" + s.letter for s in Suit if s is not trump):
        return trump, "shortness"
    return None


@dataclass(frozen=True, slots=True)
class _ContinuationRule:
    rule_id: str
    candidate: Call
    explanation: str
    sources: tuple[KnowledgeSource, ...]

    def evaluate(self, context):
        if not context.auction.is_legal(self.candidate):
            return RuleDecision.not_applicable(self.rule_id, "Approved call is not available in this auction.")
        return RuleDecision.recommend(rule_id=self.rule_id, candidate=self.candidate,
            explanation=self.explanation, sources=self.sources, priority=100)


def assess_jacoby_2nt_responder(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    intent: ResponderContinuationEvidence | None = None,
) -> JacobyAssessment:
    """Apply approved meanings to explicit responder intent; never infer ranges.

    A4 checks first/second controls; no cue order, ace-ask variant, or strength
    threshold is implied. Missing intent or an unsupported path abstains.
    """
    resolved, context, issues = _context(hand, auction, vulnerability, profile, base_agreements)
    if intent is not None:
        if not isinstance(intent, ResponderContinuationEvidence):
            raise TypeError("intent must be ResponderContinuationEvidence")
        if intent.hand != hand or intent._auction_key != (auction.dealer, auction.entries):
            raise ValueError("intent evidence belongs to a different hand or auction")
    prefix = _continuation_prefix(auction)
    if len(auction.entries) != 6 or prefix is None:
        issues += ("Requires responder after an approved uncontested Jacoby opener rebid",)
    if intent is None:
        issues += ("Responder direction is not supplied; no hand thresholds inferred",)
    if issues:
        return _finish(resolved, context, issues, (), {})
    trump, branch = prefix
    kind = intent.intent
    meaning = JacobyMeaning(False, True, trump)
    candidate = None
    why = ""
    if kind is ResponderIntent.ACE_ASK:
        candidate = Call.parse("4NT")
        meaning = replace(meaning, artificial=True, ace_ask=True, slam_interest=True)
        why = "4NT asks for aces; no response scheme or keycard variant is inferred."
    elif kind is ResponderIntent.CUE_BID:
        return _assess_cue(resolved, context, intent, (), trump, branch)
    elif kind is ResponderIntent.SIGNOFF and branch == "balanced":
        candidate = Call.parse("4" + trump.letter)
        meaning = replace(meaning, signoff=True)
        why = "After balanced 14-15 3NT, responder's 4M is signoff."
    elif kind is ResponderIntent.GOOD_NO_CUE and branch == "shortness":
        if _available_cues(context, (), trump, branch):
            return _finish(resolved, context, ("An actual control cue is available; no-cue fallback is unsupported",), (), {})
        candidate = Call.parse("3" + trump.letter)
        meaning = replace(meaning, good_hand=True, slam_interest=True, no_suitable_cue=True)
        why = "Available 3M shows a good hand and slam interest with no suitable/available cue-bid."
    elif kind is ResponderIntent.CONDITIONAL_STOP and branch == "shortness":
        candidate = Call.parse("4" + trump.letter)
        meaning = replace(meaning, conditional_stop=True)
        why = ("After shortness, 4M shows insufficient strength for direct cue/ace ask and returns the "
               "decision to opener: minimum passes, maximum must continue; not a hard signoff.")
    if candidate is None:
        return _finish(resolved, context, ("Intent/call has no approved meaning for this opener rebid",), (), {})
    rule = _ContinuationRule("nisim_nily.jacoby_2nt.responder." + kind.value.lower(), candidate,
        why + " " + intent.explanation, (APPROVAL, CONTINUATION_APPROVAL) + intent.sources)
    return _finish(resolved, context, (), (rule,), {rule.rule_id: meaning})


def assess_jacoby_2nt_conditional_stop(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    strength: OpenerStrengthEvidence | None = None,
    intent: ResponderContinuationEvidence | None = None,
) -> JacobyAssessment:
    """Opener after shortness-4M: minimum Pass, maximum continuation required.

    MAXIMUM is explicit evidence; EXTRAS is not silently equated with it.
    A4 permits explicit ace-ask, legal heart-trump 4S cue, or direct-slam intent.
    """
    resolved, context, issues = _context(hand, auction, vulnerability, profile, base_agreements)
    if strength is not None:
        if not isinstance(strength, OpenerStrengthEvidence):
            raise TypeError("strength must be OpenerStrengthEvidence")
        if (strength.hand != hand or strength.auction.dealer is not auction.dealer
                or strength.auction.entries != auction.entries):
            raise ValueError("strength evidence belongs to a different hand or auction")
    prefix = _continuation_prefix(auction)
    calls = tuple(e.call.serialize() for e in auction.entries)
    if (len(calls) != 8 or prefix is None or prefix[1] != "shortness"
            or calls[6] != "4" + prefix[0].letter or calls[7] != "P"):
        issues += ("Requires opener after uncontested Jacoby shortness and responder's conditional 4M",)
    if issues:
        return _finish(resolved, context, issues, (), {})
    trump = prefix[0]
    if strength is not None and strength.classification is OpenerStrength.MINIMUM:
        rule = _ContinuationRule("nisim_nily.jacoby_2nt.conditional_stop.minimum", Call.pass_(),
            "Minimum opener passes responder's conditional 4M. " + strength.explanation,
            (APPROVAL, CONTINUATION_APPROVAL) + strength.sources)
        return _finish(resolved, context, (), (rule,),
                       {rule.rule_id: JacobyMeaning(False, True, trump, minimum=True, signoff=True)})
    if intent is not None:
        _validate_intent(intent, hand, auction)
    result = _finish(resolved, context, (), (), {})
    if strength is not None and strength.classification is OpenerStrength.MAXIMUM:
        if intent is not None:
            return _maximum_continuation(resolved, context, strength, intent, trump)
        return replace(result, continuation_needed=True,
            continuation_sources=(APPROVAL, CONTINUATION_APPROVAL) + strength.sources,
            blockers=("Maximum opener must continue; an approved direction must be supplied",),
            reason="Maximum opener must continue after conditional 4M; abstain until an approved direction is supplied. " + strength.explanation)
    return replace(result, blockers=("Minimum/maximum classification is unresolved",),
                   reason="No automatic strength classification or default Pass is permitted.")


SLAM_APPROVAL = KnowledgeSource("B2_4A4_JACOBY_SLAM_CONTINUATIONS", "Approved cue and maximum-opener rules")
# The same sourced direction contract is shared by opener and responder.
JacobyContinuationIntent = ResponderIntent
JacobyContinuationEvidence = ResponderContinuationEvidence


@dataclass(frozen=True, slots=True)
class CueControlEvidence:
    suit: Suit
    round: int
    seat: Seat
    auction_index: int
    call: Call
    basis: str  # prior auction claim, or current hand's exact control basis
    source: KnowledgeSource = SLAM_APPROVAL


def _validate_intent(intent, hand, auction):
    if not isinstance(intent, ResponderContinuationEvidence):
        raise TypeError("intent must be JacobyContinuationEvidence")
    if intent.hand != hand or intent._auction_key != (auction.dealer, auction.entries):
        raise ValueError("intent evidence belongs to a different hand or auction")


def _cue_check(context, candidate, history, trump, branch, requested_round=None, allow_short_suit=False):
    if not context.auction.is_legal(candidate) or candidate.bid is None:
        return None
    suit = candidate.bid.strain.suit
    if suit is None or suit is trump:
        return None
    prior = tuple(c for c in history if c.suit is suit)
    # Initial shortness is not an Ace cue and cannot authorize a King cue.
    short_suit = context.auction.entries[4].call.bid.strain.suit if branch == "shortness" else None
    if suit is short_suit and not prior and not allow_short_suit:
        return None
    next_round = len(prior) + 1
    if next_round > 2 or (requested_round is not None and requested_round != next_round):
        return None
    facts = context.evaluation.honor_evidence(suit)
    if next_round == 1 and facts.first_round_control:
        return suit, 1, "ace" if facts.has_ace else "void"
    if next_round == 2 and prior[0].round == 1 and facts.second_round_control:
        return suit, 2, "guarded king" if facts.has_guarded_king else "singleton"
    return None


def _available_cues(context, history, trump, branch):
    return tuple(c for c in context.auction.legal_calls()
                 if _cue_check(context, c, history, trump, branch) is not None)


def _assess_cue(resolved, context, intent, history, trump, branch, allow_short_suit=False):
    qualified = _cue_check(context, intent.cue_call, history, trump, branch,
                           intent.cue_round, allow_short_suit)
    if qualified is None:
        result = _finish(resolved, context,
            ("Cue requires a legal side-suit call, matching control round/history, and actual hand control",), (), {})
        return replace(result, control_history=history)
    suit, round_number, basis = qualified
    rule = _ContinuationRule("nisim_nily.jacoby_2nt.cue",
        intent.cue_call, f"Round {round_number} {suit.name.lower()} control cue ({basis}); slam interest. " + intent.explanation,
        (APPROVAL, CONTINUATION_APPROVAL, SLAM_APPROVAL) + intent.sources)
    meaning = JacobyMeaning(True, True, trump, cue_suit=suit, slam_interest=True,
                            control_round=round_number, control_basis=basis)
    result = _finish(resolved, context, (), (rule,), {rule.rule_id: meaning})
    shown = CueControlEvidence(suit, round_number, context.seat, len(context.auction.entries),
                               intent.cue_call, basis)
    return replace(result, control_history=history + (shown,))


def _read_control_history(auction, trump, branch):
    """Replay only approved partnership calls; never turn shortness into an Ace.

    Prior control claims belong to their bidding seats. No hidden card holding
    is reconstructed or verified. Stop at unimplemented/terminal meanings.
    """
    history = []
    mode = "active"
    entries = auction.entries
    if len(entries) % 2 or any(entries[i].call.serialize() != "P" for i in range(1, len(entries), 2)):
        return (), "unsupported", "Requires an uncontested partnership turn"
    short_suit = entries[4].call.bid.strain.suit if branch == "shortness" else None
    for index in range(6, len(entries), 2):
        entry = entries[index]
        call = entry.call.serialize()
        if mode == "terminal":
            return tuple(history), mode, "Continuation after an ace ask, signoff, or direct slam is not defined"
        if call == "4NT":
            mode = "terminal"
            continue
        if index == 6 and call == "4" + trump.letter and branch in ("balanced", "shortness"):
            mode = "terminal" if branch == "balanced" else "conditional"
            continue
        if index == 6 and branch == "shortness" and call == "3" + trump.letter:
            continue  # approved no-cue fallback; not a control claim
        conditional = mode == "conditional"
        if conditional:
            if call == "P" or call in ("6" + trump.letter, "7" + trump.letter):
                mode = "terminal"
                continue
            if trump is not Suit.HEARTS or call != "4S":
                return tuple(history), mode, "Unsupported maximum-opener continuation"
        bid = entry.call.bid
        if bid is None or bid.strain.suit is None or bid.strain.suit is trump:
            return tuple(history), mode, "Unapproved call in cue history"
        suit = bid.strain.suit
        prior = tuple(c for c in history if c.suit is suit)
        if suit is short_suit and not prior and not conditional:
            return tuple(history), mode, "Shortness repeat has no established cue meaning"
        next_round = len(prior) + 1
        if next_round > 2:
            return tuple(history), mode, "Third control cue in a suit is not defined"
        history.append(CueControlEvidence(suit, next_round, entry.seat, index, entry.call, "auction control claim"))
        mode = "active"
    if mode == "terminal":
        return tuple(history), mode, "Continuation after an ace ask, signoff, or direct slam is not defined"
    return tuple(history), mode, None


def _maximum_continuation(resolved, context, strength, intent, trump):
    sources = (APPROVAL, CONTINUATION_APPROVAL, SLAM_APPROVAL) + strength.sources + intent.sources
    if intent.intent is ResponderIntent.CUE_BID and trump is Suit.HEARTS and intent.cue_call == Call.parse("4S"):
        result = _assess_cue(resolved, context, intent, (), trump, "shortness", allow_short_suit=True)
        if result.selected is not None:
            selected = replace(result.selected, sources=sources)
            evidence = replace(result.engine_result, recommended=selected, decisions=(selected,))
            return replace(result, selected=selected, engine_result=evidence)
    elif intent.intent is ResponderIntent.ACE_ASK:
        rule = _ContinuationRule("nisim_nily.jacoby_2nt.maximum.ace_ask", Call.parse("4NT"),
            "Maximum opener asks for aces. " + strength.explanation + " " + intent.explanation, sources)
        return _finish(resolved, context, (), (rule,),
            {rule.rule_id: JacobyMeaning(True, True, trump, ace_ask=True, slam_interest=True)})
    elif intent.intent is ResponderIntent.DIRECT_SLAM:
        if intent.slam_call.serialize() in ("6" + trump.letter, "7" + trump.letter):
            rule = _ContinuationRule("nisim_nily.jacoby_2nt.maximum.direct_slam", intent.slam_call,
                "Sourced maximum and sufficient strength for the specified direct trump slam. "
                + strength.explanation + " " + intent.explanation, sources)
            return _finish(resolved, context, (), (rule,),
                {rule.rule_id: JacobyMeaning(False, True, trump, direct_slam=True, slam_interest=True)})
    result = _finish(resolved, context, (), (), {})
    return replace(result, continuation_needed=True, continuation_sources=sources,
        blockers=("Maximum opener must continue; supplied direction/control is not approved or available",),
        reason="No fallback call inferred for maximum opener.")


def assess_jacoby_2nt_slam_continuation(
    hand: Hand, *, auction: Auction, vulnerability: Vulnerability,
    profile: PartnershipProfile, base_agreements: tuple[ResolvedAgreement, ...] = (),
    intent: JacobyContinuationEvidence | None = None,
    strength: OpenerStrengthEvidence | None = None,
) -> JacobyAssessment:
    """Both partners' approved cue/ace-ask paths, including maximum after 4M.

    Cue suit/ace ask/direct slam choice remains explicit; no new strength
    thresholds or precedence among available slam directions is invented.
    """
    if len(auction.entries) == 6:
        return assess_jacoby_2nt_responder(hand, auction=auction, vulnerability=vulnerability,
            profile=profile, base_agreements=base_agreements, intent=intent)
    resolved, context, issues = _context(hand, auction, vulnerability, profile, base_agreements)
    if intent is not None:
        _validate_intent(intent, hand, auction)
    prefix = _continuation_prefix(auction)
    if prefix is None or len(auction.entries) < 8:
        issues += ("Requires an established approved Jacoby continuation",)
    if issues:
        return _finish(resolved, context, issues, (), {})
    trump, branch = prefix
    history, mode, error = _read_control_history(auction, trump, branch)
    if error:
        return replace(_finish(resolved, context, (error,), (), {}), control_history=history)
    if mode == "conditional":
        return assess_jacoby_2nt_conditional_stop(hand, auction=auction, vulnerability=vulnerability,
            profile=profile, base_agreements=base_agreements, strength=strength, intent=intent)
    if intent is None:
        return replace(_finish(resolved, context, ("No sourced slam direction supplied",), (), {}), control_history=history)
    if intent.intent is ResponderIntent.CUE_BID:
        return _assess_cue(resolved, context, intent, history, trump, branch)
    if intent.intent is ResponderIntent.ACE_ASK:
        rule = _ContinuationRule("nisim_nily.jacoby_2nt.slam.ace_ask", Call.parse("4NT"),
            "4NT asks for aces; no answer scheme inferred. " + intent.explanation,
            (APPROVAL, CONTINUATION_APPROVAL, SLAM_APPROVAL) + intent.sources)
        result = _finish(resolved, context, (), (rule,),
            {rule.rule_id: JacobyMeaning(True, True, trump, ace_ask=True, slam_interest=True)})
        return replace(result, control_history=history)
    return replace(_finish(resolved, context, ("No approved fallback at this later cue position",), (), {}),
                   control_history=history)
