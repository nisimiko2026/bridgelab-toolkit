"""Opt-in Nisim-Nily Jacoby 2NT. No standard-router registration."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .auction import Auction, Call
from .bidding_engine import BiddingEngine, BiddingEngineResult
from .bidding_rules import BiddingContext, KnowledgeSource, RuleDecision
from .models import Hand, Suit, Vulnerability
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

    def __post_init__(self):
        if self.production_adopted:
            raise ValueError("Jacoby agreement is not production adopted")
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
