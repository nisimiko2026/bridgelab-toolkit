"""Phase 29L repository-evidence snapshot; never evaluates a hand or recommends a call.

Canonical production citations are provenance, not authenticated authority.
This audit deliberately preserves the existing source-authority registry values.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum

from .source_authority import DEFAULT_SOURCE_AUTHORITY_REGISTRY, SourceAuthorityClassification


class SourceAuthority(str, Enum):
    CANONICAL_PRODUCTION_REFERENCE = "CANONICAL_PRODUCTION_REFERENCE"
    SUPPORTED_REFERENCE = "SUPPORTED_REFERENCE"
    PARTNERSHIP_DEPENDENT = "PARTNERSHIP_DEPENDENT"
    PROJECT_POLICY = "PROJECT_POLICY"
    TEST_ONLY = "TEST_ONLY"
    MISSING = "MISSING"


class PolicySupport(str, Enum):
    OPEN = "OPEN"
    PASS = "PASS"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    SOURCE_INSUFFICIENT = "SOURCE_INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class OpeningPolicyEvidence:
    evidence_id: str
    path: str
    title: str
    section: str
    proposition: str
    production_rules: tuple[str, ...]
    authority: SourceAuthority
    registry_authority: SourceAuthorityClassification
    source_status: str
    positive_pass_support: bool
    limitations: str


@dataclass(frozen=True, slots=True)
class OpeningFamilyPolicy:
    family: str
    rule_id: str | None
    strength: str
    shape: str
    exclusions: str
    evidence_ids: tuple[str, ...]
    current_coverage: str
    controlled_boundary: str
    complement_explicitly_pass: bool = False
    complement_status: str = "OTHER_OPENING_OR_UNKNOWN; never infer Pass"
    authority: SourceAuthority = SourceAuthority.PROJECT_POLICY


@dataclass(frozen=True, slots=True)
class PolicyFinding:
    finding_id: str
    support: PolicySupport
    evidence_ids: tuple[str, ...]
    authority: SourceAuthority
    finding: str
    safety_exclusion: bool = False


@dataclass(frozen=True, slots=True)
class PolicyRequirement:
    requirement_id: str
    question: str
    why_needed: str
    evidence_ids: tuple[str, ...]
    missing_evidence: str
    risk_if_guessed: str
    authority: SourceAuthority = SourceAuthority.MISSING


@dataclass(frozen=True, slots=True)
class OpeningPassSourceReport:
    baseline_head: str
    source_inventory: tuple[OpeningPolicyEvidence, ...]
    family_policy_matrix: tuple[OpeningFamilyPolicy, ...]
    rule_20_22_findings: tuple[PolicyFinding, ...]
    borderline_hand_findings: tuple[PolicyFinding, ...]
    equal_suit_findings: tuple[PolicyFinding, ...]
    strong_2c_safety_findings: tuple[PolicyFinding, ...]
    weak_two_preempt_safety_findings: tuple[PolicyFinding, ...]
    other_safety_findings: tuple[PolicyFinding, ...]
    missing_policy_requirements: tuple[PolicyRequirement, ...]
    implementation_readiness: str = "INCOMPLETE"
    positive_pass_predicate: str = "INCOMPLETE: no approved positive domain"
    invariant: str = "PASS != FALLBACK_FOR_ABSTAIN"
    pass_recommendations_created: int = 0

    def to_dict(self) -> dict:
        # JSON-normalization makes tuples lists and string enums plain strings.
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


_OPENING = "bidding/natural-bids/opening-bids/"
_FUNDAMENTALS = "bidding/principles/bidding-fundamentals/"
_SAYC = "bidding/systems/sayc"
_ONE = tuple("sayc.opening." + bid for bid in ("1nt", "1h", "1s", "1d", "1c"))
_WEAK = tuple("sayc.opening.weak2.2" + suit for suit in "shd")
_PREEMPT = tuple("sayc.opening.preempt3.3" + suit for suit in "shdc")
_ALL = ("sayc.opening.2c", "sayc.opening.2nt") + _ONE + _WEAK + _PREEMPT


def _evidence(key, article, title, section, proposition, rules=(), *,
              authority=SourceAuthority.SUPPORTED_REFERENCE, status="Draft", limitations=""):
    registry = DEFAULT_SOURCE_AUTHORITY_REGISTRY.record_for(article)
    return OpeningPolicyEvidence(
        key, "knowledge/" + article + ".md", title, section, proposition, rules,
        authority, registry.authority, status, False, limitations or
        "Internal repository reference; no authenticated claim-level external source or approved Pass policy.",
    )


def _inventory() -> tuple[OpeningPolicyEvidence, ...]:
    canonical = SourceAuthority.CANONICAL_PRODUCTION_REFERENCE
    partner = SourceAuthority.PARTNERSHIP_DEPENDENT
    rows = [
        _evidence("sayc-table", _SAYC, "Standard American Yellow Card (SAYC)", "Opening Bid Requirements",
                  "1C/1D/1H/1S 12-21; 1NT 15-17 balanced; 2C 22+ or equivalent; weak twos and three-level 6-10; 2NT 20-21 balanced.",
                  ("sayc.opening.2c",) + _ONE + _PREEMPT, authority=canonical),
        _evidence("sayc-evaluation", _SAYC, "SAYC", "Hand Evaluation / Balanced Hands",
                  "Approximately 12+ HCP; excellent distribution may justify lighter openings; 5422 occasionally qualifies as balanced."),
        _evidence("sayc-majors", _SAYC, "SAYC", "Five-Card Majors",
                  "1H and 1S promise at least five cards; no equal-major tie decision here.",
                  ("sayc.opening.1h", "sayc.opening.1s"), authority=canonical),
        _evidence("sayc-minors", _SAYC, "SAYC", "Better Minor",
                  "3-3 minors open 1C; 4-4 open 1D; normally open longer minor; no 5-5 or 6-6 tie policy.",
                  ("sayc.opening.1c", "sayc.opening.1d"), authority=canonical),
        _evidence("sayc-strong", _SAYC, "SAYC", "Strong 2♣ Opening",
                  "Usually 22+ HCP OR 9+ playing tricks; artificial.", ("sayc.opening.2c",), authority=canonical),
        _evidence("sayc-2nt", _SAYC, "SAYC", "2NT Opening",
                  "20-21 balanced.", ("sayc.opening.2nt",), authority=canonical),
        _evidence("sayc-weak", _SAYC, "SAYC", "Weak Two Openings",
                  "Six-card suit and 6-10 HCP; preemptive; no multi-suit precedence.", _WEAK, authority=canonical,
                  limitations="Heading occurs twice; production cites heading text, not a unique occurrence."),
        _evidence("sayc-preempt", _SAYC, "SAYC", "Three-Level Openings",
                  "Normally seven-card suit, weak; table supplies 6-10.", _PREEMPT, authority=canonical),
        _evidence("nt-shape", _OPENING + "1nt-opening", "1NT Opening", "Typical Requirements / Balanced Distribution",
                  "15-17; 4333/4432/5332 balanced; 5422 partnership-dependent; five-card-major treatment requires agreement.",
                  ("sayc.opening.1nt",), authority=canonical),
        _evidence("heart-length", _OPENING + "1-heart", "1 Heart", "Heart Length",
                  "Five-card-major systems require five hearts; typical strength 12-21.", ("sayc.opening.1h",), authority=canonical),
        _evidence("spade-length", _OPENING + "1-spade", "1 Spade", "Spade Length",
                  "Five-card-major systems require five spades; typical strength 12-21.", ("sayc.opening.1s",), authority=canonical),
        _evidence("heart-tie", _OPENING + "1-heart", "1 Heart", "Common Mistakes / Opening Hearts with a Longer Spade Suit",
                  "Equal five-card majors: partnership determines 1H or 1S; text says most systems open 1H.", authority=partner,
                  limitations="Length-section citation does not adopt this separate qualified tie guidance."),
        _evidence("spade-tie", _OPENING + "1-spade", "1 Spade", "Common Mistakes / Opening 1♠ with a Longer Heart Suit",
                  "Text recommends 1H with 5-5 in most five-card-major systems, to show spades later at one level.", authority=partner,
                  limitations="Agrees with heart article's suggestion, but is not a mandatory SAYC partnership decision."),
        _evidence("club-choice", _OPENING + "1-club", "1 Club", "Choosing 1♣ Instead of 1♦",
                  "3-3 open clubs; 4-4 usually diamonds; 5 clubs and 4 diamonds open clubs."),
        _evidence("diamond-choice", _OPENING + "1-diamond", "1 Diamond", "Diamond Length / Better Minor Principle",
                  "SAYC listed as normally 4+ diamonds; 4-4 usually diamonds.",
                  limitations="Qualification differs from SAYC table's usually 3+; not production's cited minor source."),
        _evidence("opening-requirements", _OPENING + "opening-requirements", "Opening Requirements", "Traditional Opening Standard / Rules 20, 22 / Hands That Should Not Open",
                  "12+ is a starting point; distribution and controls can justify lighter openings. Generally avoid weak balanced hands and flat 10-counts. Rules 20/22 are guidelines; partners define standards.",
                  limitations="SAYC metadata is applicability context, not adoption. Qualified Pass guidance lacks complete domains and exceptions."),
        _evidence("rule20", _FUNDAMENTALS + "rule-of-20", "Rule of 20", "The Formula / When to Use / Exceptions",
                  "HCP + two longest suit lengths >=20: usually open; <20: usually pass; first/second seat. No quick-trick term. 11+5+4 example opens; flat 11 example usually passes.",
                  limitations="May open below 20 for excellent six-card suit or controls; may pass above it for poor honors/suits or defensive hand; systems metadata empty."),
        _evidence("rule22", _FUNDAMENTALS + "rule-of-22", "Rule of 22", "Formula / Examples / Partnership Notes",
                  "HCP + two longest lengths + quick tricks >=22; first/second seat; explicit Pass example and qualified borderline Pass guidance.", status="Standard",
                  limitations="Standard metadata is not authentication. Systems empty; style/quality/vulnerability exceptions. Example 2's printed 5+4 lengths disagree with its 5-3-2-3 hand; Example 3 prints 9 HCP for two aces (8)."),
        _evidence("quick-tricks", _FUNDAMENTALS + "quick-tricks", "Quick Tricks", "Standard Quick Trick Values",
                  "Per suit AK=2, AQ=1.5, A=1, KQ=1, K=0.5, others=0; supplement to HCP.", status="Standard",
                  limitations="No adopted opening evaluator; protection/short-honor cases require exact contract before use."),
        _evidence("playing-tricks", _FUNDAMENTALS + "playing-tricks", "Playing Tricks", "Purpose / Estimating Playing Tricks",
                  "Expected declarer tricks with little/no partner help; explicitly no universally accepted formula; examples and approximate side-suit values.", status="Standard",
                  limitations="Not a total deterministic evaluator proving fewer than nine tricks."),
        _evidence("strong-reference", _OPENING + "2-clubs", "2 Clubs", "Typical Requirements / Playing Tricks",
                  "22+ HCP balanced or approximately nine playing tricks; fewer than 22 can qualify."),
        _evidence("weak-reference", _OPENING + "weak-two-bids", "Weak Two Bids", "Typical Requirements / Typical Suit Quality",
                  "Most partnerships: 5-10 HCP, good six-card suit, outside-four-card-major agreement, unsuitable for one-level; quality and seat/vulnerability vary.",
                  limitations="Generic 5-10 differs from cited SAYC 6-10; no precise competing-long-suit resolution."),
        _evidence("preempt-reference", _OPENING + "three-level-preempts", "Three-Level Preempts", "Typical Requirements / Typical Suit Quality",
                  "Most partnerships: 5-10, good seven-card suit; not suitable one-level/weak two. Excellent six-card exceptions, especially third seat.",
                  limitations="Not a deterministic 7-6 precedence contract; generic range differs from SAYC."),
        _evidence("four-level", _OPENING + "four-level-preempts", "Four-Level Preempts", "Typical Requirements",
                  "Long-suit preemptive openings exist beyond the 14 implemented families.",
                  limitations="Eight-plus-card unsupported hands cannot become Pass just because exact six/seven predicates fail."),
        _evidence("rule15", _FUNDAMENTALS + "rule-of-15", "Rule of 15", "Formula / Exceptions",
                  "Fourth seat: HCP + spade length >=15 usually open; below usually pass; exceptions remain."),
        _evidence("seat", _FUNDAMENTALS + "seat-position", "Seat Position", "First Seat / Second Seat / Common Mistakes",
                  "Rules 20/22 associated with first/second; third lighter; fourth Rule 15.", status="Standard"),
        _evidence("standard-american", "bidding/systems/standard-american", "Standard American", "Fourth-Seat Openings",
                  "Lists Rules 15, 20 and 22 for fourth seat.",
                  limitations="Conflicts with dedicated 20/22 articles' seat scope; not a SAYC mandate."),
        _evidence("partnership-card", "bidding/convention-cards/cc-nily-nisim", "Cc Nily Nisim", "System / Opening Bids",
                  "2/1 Game Force card gives 11-21 minor openings and non-SAYC two-level treatments.", authority=partner,
                  limitations="Not the production SAYC profile; duplicated 1C heading for diamonds; no import into SAYC."),
        _evidence("bibliography", "bibliography", "Bibliography", "Overview",
                  "General references do not imply every treatment follows them exactly.",
                  limitations="No claim-level attribution or authenticated SAYC Pass source."),
        _evidence("nt2-reference", _OPENING + "2nt-opening", "2NT Opening", "Typical Requirements / Balanced Distribution",
                  "SAYC 20-21 balanced; generic partnership variants do not override the SAYC citation."),
        _evidence("opening-overview", _OPENING + "opening-bids-overview", "Opening Bids Overview", "Requirements for Opening / Opening Priorities",
                  "Normally 12-21; major, minor, NT, strong and preempt categories; unbalanced hands may open lighter.",
                  limitations="Prose priority list is not executable precedence; cannot override production 2C/NT gates or define Pass."),
        _evidence("hand-evaluation", _FUNDAMENTALS + "hand-evaluation", "Hand Evaluation", "The Rule of 20 / Rule of 15",
                  "Rule20 for first/second; Rule15 for fourth; honor quality and distribution supplement HCP."),
        _evidence("preempt-principles", _FUNDAMENTALS + "preemptive-openings", "Preemptive Openings", "Requirements / Partnership Agreements",
                  "Suit quality, playing strength and vulnerability matter; occasional strong six-card preempts require agreement."),
        _evidence("vulnerability", _FUNDAMENTALS + "vulnerability", "Vulnerability", "Opening Bids",
                  "Opening style and preempt risk depend on vulnerability; references Rules20/22.", status="Standard"),
    ]
    for key, path, proposition, authority in (
        ("production", "bridge/sayc.py", "Fourteen conservative opening predicates; no Pass; exact six/seven lengths and controlled ties.", SourceAuthority.PROJECT_POLICY),
        ("authority-contract", "bridge/source_authority.py", "Empty default registry; unknown authority and not-established coverage for opening sources.", SourceAuthority.PROJECT_POLICY),
        ("phase25", "bridgelab_phase25_source_authority_closure_record.md", "Provenance and source readiness do not establish source authority.", SourceAuthority.PROJECT_POLICY),
        ("phase29j", "bridge/opening_abstention_root_cause_audit.py", "Equal-major boundary is controlled ABSTAIN; unknown cases remain unknown.", SourceAuthority.PROJECT_POLICY),
        ("phase29k", "bridge/opening_pass_policy_audit.py", "<=11 HCP/max length <=5 screen is source-insufficient, not Pass; four explicit passes complete auction.", SourceAuthority.PROJECT_POLICY),
        ("auction", "bridge/auction.py", "Canonical explicit Pass and passed-out representation establish legality, not hand policy.", SourceAuthority.PROJECT_POLICY),
        ("opening-tests", "tests/test_bridge_sayc_openings.py", "Asserts canonical source citations and current opening/tie behavior; no independent authority.", SourceAuthority.TEST_ONLY),
        ("weak-tests", "tests/test_bridge_sayc_weak_two_openings.py", "Asserts multi-six-card controlled abstention and strength/length boundaries.", SourceAuthority.TEST_ONLY),
        ("preempt-tests", "tests/test_bridge_sayc_three_level_preempts.py", "Asserts current exact-seven and weak-two overlap boundaries.", SourceAuthority.TEST_ONLY),
        ("pass-tests", "tests/test_bridge_phase29k_opening_pass_policy_audit.py", "Fixture Pass rule tests architecture only, not positive opening policy.", SourceAuthority.TEST_ONLY),
    ):
        rows.append(OpeningPolicyEvidence(key, "bridgelab-toolkit/" + path, key, "module",
                    proposition, _ALL if key == "production" else (), authority,
                    SourceAuthorityClassification.UNKNOWN, "project artifact", False,
                    "Descriptive evidence only; not external bridge-policy authority."))
    rows.append(OpeningPolicyEvidence("pass-policy", "", "Approved SAYC opening Pass policy", "",
                "No complete approved positive predicate located.", (), SourceAuthority.MISSING,
                SourceAuthorityClassification.UNKNOWN, "MISSING", False,
                "Qualified reference Pass examples are not a complete adopted SAYC policy."))
    return tuple(sorted(rows, key=lambda row: row.evidence_id))


def _families() -> tuple[OpeningFamilyPolicy, ...]:
    rows = [
        OpeningFamilyPolicy("Strong 2C", "sayc.opening.2c", "22+ HCP implemented; source also 9+ playing tricks",
                            "Any shape in HCP branch", "Below 22 not evaluated for playing tricks", ("sayc-strong", "sayc-table", "production"),
                            "HCP branch only", "Uncomputed playing-trick domain"),
        OpeningFamilyPolicy("2NT", "sayc.opening.2nt", "20-21 HCP", "Canonical balanced 4333/4432/5332",
                            "Other shapes/ranges", ("sayc-2nt", "production"), "Exact balanced subset", "5422 agreement not implemented"),
        OpeningFamilyPolicy("1NT", "sayc.opening.1nt", "15-17 HCP", "Canonical balanced, no five-card major",
                            "Five-card major; 5422; strength upgrades/downgrades", ("sayc-table", "nt-shape", "production"),
                            "Conservative subset", "Other families may open excluded hands; no implication of Pass"),
    ]
    for bid, suit, other in (("1H", "hearts", "spades"), ("1S", "spades", "hearts")):
        rows.append(OpeningFamilyPolicy(bid, "sayc.opening." + bid.lower(), "12-21 HCP",
                    f"5+ {suit}, strictly longer than {other}", "20-21 balanced reserved for 2NT; 22+ for 2C",
                    ("sayc-table", "sayc-majors", "heart-length" if bid == "1H" else "spade-length", "production"),
                    "Strictly longer major only", "Equal 5-5 and 6-6 majors excluded"))
    for bid, shape in (("1D", "D>C and D>=3, or 4-4 minors"), ("1C", "C>D and C>=3, or 3-3 minors")):
        rows.append(OpeningFamilyPolicy(bid, "sayc.opening." + bid.lower(), "12-21 HCP", shape,
                    "Five-card major; clear 1NT; 20-21 balanced 2NT; 22+ 2C", ("sayc-table", "sayc-minors", "production"),
                    "Clear Better-Minor cases", "Equal 5-5/6-6 minors outside controlled subset"))
    for suit in "SHD":
        rows.append(OpeningFamilyPolicy("Weak 2" + suit, "sayc.opening.weak2.2" + suit.lower(), "6-10 HCP",
                    "Exactly six in " + suit, "Multiple six-card D/H/S suits; any seven-card suit",
                    ("sayc-weak", "weak-reference", "production"), "Unique six-card D/H/S, no seven-card suit",
                    "6-6 D/H/S ties; 7-6 overlap; quality/seat exceptions unadopted"))
    for suit in "SHDC":
        rows.append(OpeningFamilyPolicy("3" + suit, "sayc.opening.preempt3.3" + suit.lower(), "6-10 HCP",
                    "Exactly seven in " + suit, "Any six-card D/H/S overlap; nonunique seven-card qualifier",
                    ("sayc-table", "sayc-preempt", "preempt-reference", "production"), "Unique seven-card subset",
                    "7-6 D/H/S overlap; six/eight-card variants unimplemented; two seven-card suits impossible in 13 cards"))
    rows.append(OpeningFamilyPolicy("Opening Pass", None, "INCOMPLETE", "INCOMPLETE",
                "All unresolved domains remain protected", ("pass-policy", "phase29k"), "No production rule",
                "Missing approved positive conditions", authority=SourceAuthority.MISSING))
    return tuple(rows)


def build_opening_pass_source_report() -> OpeningPassSourceReport:
    """Return immutable snapshot facts without reading deals or running bidding logic."""
    required = PolicySupport.POLICY_REQUIRED
    insufficient = PolicySupport.SOURCE_INSUFFICIENT
    reference = SourceAuthority.SUPPORTED_REFERENCE
    project = SourceAuthority.PROJECT_POLICY
    partner = SourceAuthority.PARTNERSHIP_DEPENDENT
    def f(key, support, ids, authority, text, protect=False):
        return PolicyFinding(key, support, ids, authority, text, protect)
    rules = (
        f("rule20", required, ("rule20", "opening-requirements"), reference,
          "Present: HCP+L1+L2>=20, no quick-trick term. First/second-seat opening evaluation guidance; not production-used or authenticated. Arithmetic: 10 needs lengths sum 10, 11 needs 9, 12 needs 8; exceptions prevent deterministic OPEN/PASS."),
        f("rule22", required, ("rule22", "quick-tricks", "opening-requirements"), reference,
          "Present: HCP+L1+L2+QT>=22. First/second-seat guidance, not production-used or authenticated. At 10/11/12 HCP remaining sum must be 12/11/10. Quick tricks are explicit. Qualitative exceptions and erroneous examples require reconciliation."),
    )
    borderline = (
        f("10-hcp-distributional", required, ("rule20", "sayc-weak", "sayc-preempt"), reference,
          "OPEN in implemented weak/preempt subsets; 5-5 can reach Rule20 arithmetically, but adoption/quality/seat decisions are missing. Otherwise POLICY_REQUIRED.", True),
        f("11-hcp", required, ("rule20", "opening-requirements", "partnership-card"), reference,
          "No 11-HCP production opening family. Rule20 gives both open 5-4 and usually-pass flat examples; 2/1 card is not SAYC. No universal Pass.", True),
        f("12-hcp", PolicySupport.OPEN, ("sayc-table", "production"), project,
          "OPEN only in covered one-level shape subsets; ties remain POLICY_REQUIRED; approximately-12 guidance is not universal Pass evidence.", True),
        f("13-hcp", PolicySupport.OPEN, ("sayc-table", "production"), project,
          "OPEN only in covered one-level subsets; equal-major/minor boundary still applies.", True),
        f("five-five", required, ("heart-tie", "spade-tie", "sayc-minors", "rule20"), partner,
          "Major/minor with opening values is covered by major rule; equal majors or equal minors unresolved; lighter 5-5 needs policy.", True),
        f("six-card", required, ("sayc-weak", "production", "rule20"), project,
          "OPEN for unique six-card D/H/S at 6-10 absent seven-card suit, or covered one-level strength; six clubs, 11 HCP, multiple qualifiers and exceptions unresolved.", True),
        f("seven-card", required, ("sayc-preempt", "preempt-reference", "production"), project,
          "OPEN for controlled 6-10 seven-card subset without six-card D/H/S overlap, or covered one-level strength; remaining domains are not Pass.", True),
        f("balanced-unbalanced", insufficient, ("opening-requirements", "sayc-evaluation", "nt-shape"), reference,
          "Balance alone proves neither OPEN nor PASS. 12/13 balanced commonly covered, 10 flat usually-pass guidance is qualified; distributional exceptions remain.", True),
    )
    equal = (
        f("equal-five-majors", required, ("heart-tie", "spade-tie", "phase29j"), partner,
          "Both references suggest 1H; heart article explicitly requires partnership agreement. No authenticated mandatory SAYC choice; production abstains for 12-21 equal 5-5 and 6-6.", True),
        f("five-five-major-minor", PolicySupport.OPEN, ("sayc-majors", "production"), project,
          "At 12-21 the sole five-card major is strictly longer than the other major and covered; minor defers. Lower strengths need policy."),
        f("equal-minors", required, ("sayc-minors", "club-choice", "diamond-choice", "production"), project,
          "3-3 ->1C and 4-4 ->1D explicitly cited and implemented subject to NT/major gates. Equal 5-5/6-6 not resolved. Equal <=2 entails a five-card major, so is not an independent minor-opening gap.", True),
    )
    strong = (f("strong-playing-tricks", required, ("sayc-strong", "strong-reference", "playing-tricks", "production"), reference,
              "Source says usually 22+ HCP OR 9+ playing tricks. Production implements HCP>=22 only. Below-22 failure cannot exclude strong opening. Future Pass needs a sourced proof of exclusion or must leave uncertain trick strength unsupported.", True),)
    weak = (
        f("weak-preempt-overlap", required, ("sayc-weak", "sayc-preempt", "weak-reference", "preempt-reference", "production"), project,
          "Two six-card D/H/S qualifiers and seven plus six D/H/S overlap abstain. No adopted precedence. Seven plus six clubs is not rejected by weak-overlap guard. Two seven-card suits cannot occur in a valid 13-card hand.", True),
        f("preempt-style", required, ("weak-reference", "preempt-reference", "four-level", "production"), partner,
          "Generic 5-10 vs production 6-10; quality, outside majors, seat/vulnerability, six-card three-level exceptions and eight-plus suits unresolved. Six clubs has no weak-two opening. None of these omissions proves Pass.", True),
    )
    other = (
        f("seat-scope", required, ("rule20", "rule22", "rule15", "seat", "standard-american"), reference,
          "Dedicated 20/22 articles restrict first/second; Standard American fourth-seat section lists both. Define dealer-only versus all unopened positions, reconcile fourth-seat scope and approve third-seat/vulnerability treatment.", True),
        f("nt-adjustments", required, ("nt-shape", "sayc-evaluation", "production"), partner,
          "Five-card-major NT choice, 5422 and strength upgrades/downgrades are unadopted; often covered by another bid, never implied Pass.", True),
        f("passed-out", insufficient, ("auction", "phase29k", "pass-tests"), project,
          "Four explicit passes can complete a legal auction; representation and test fixture do not establish which hands should pass."),
        f("low-strength-screen", insufficient, ("phase29k", "rule20", "opening-requirements"), project,
          "29K <=11 HCP and max length <=5 screen remains SOURCE_INSUFFICIENT; distributional 5-5 and 11-HCP references defeat treating it as a positive predicate.", True),
    )
    missing = (
        PolicyRequirement("positive-domain", "What exact hands positively qualify for opening Pass in the intended SAYC profile?",
                          "A recommendation needs affirmative grounds.", ("pass-policy", "opening-requirements", "rule20", "rule22"),
                          "Authenticated claim-level policy or explicit approved partnership contract, including 10/11/12/13 HCP, shape, controls, exceptions and scope.", "Turning incomplete coverage into Pass."),
        PolicyRequirement("evaluation-choice", "Adopt neither, Rule20, Rule22, or another explicitly defined borderline policy?",
                          "Resolve distributional openings and numerical/qualitative exceptions.", ("rule20", "rule22", "quick-tricks"),
                          "Selected method, exact quick-trick handling if used, corrected examples, exception precedence and explicit Pass domain.", "Passing valid light openings or silently changing system."),
        PolicyRequirement("seat-vulnerability", "Which seats and vulnerabilities are covered, and what are their exceptions?",
                          "An unopened auction can already contain passes.", ("seat", "rule15", "standard-american"),
                          "Approved dealer-only scope or seat-specific policy; resolve fourth-seat contradiction.", "Applying first-seat standards in third/fourth seat."),
        PolicyRequirement("equal-suits", "Resolve equal major/minor choices, or explicitly retain those domains as unsupported?",
                          "Protect controlled ABSTAIN boundaries.", ("heart-tie", "spade-tie", "sayc-minors", "phase29j"),
                          "Approved 5-5/6-6 major and minor treatment, or documented exclusion from initial Pass scope.", "Passing opening-strength hands."),
        PolicyRequirement("playing-tricks", "How is the below-22 strong-2C playing-trick domain safely excluded?",
                          "HCP alone does not decide strong 2C eligibility.", ("sayc-strong", "playing-tricks"),
                          "Deterministic sourced evaluation or positively justified narrow-domain exclusion; uncertain cases remain unsupported.", "Passing a game-going strong hand."),
        PolicyRequirement("preempt-domains", "Resolve or explicitly exclude competing long suits and unimplemented preempt variants?",
                          "Exact-six/seven failures are coverage gaps.", ("sayc-weak", "weak-reference", "preempt-reference", "four-level"),
                          "Approved 6-6/7-6 precedence, range/quality/seat exceptions and six-club/eight-plus treatment, or explicit exclusions.", "Passing a legitimate preempt or constructive opening."),
        PolicyRequirement("nt-domains", "Which optional NT shape/major/strength adjustments are adopted or excluded?",
                          "Prevent optional evaluation changes being treated as Pass.", ("nt-shape", "sayc-evaluation"),
                          "Explicit scope and exclusions; no silent upgrade/downgrade policy.", "Confusing alternative opening choices with Pass."),
    )
    return OpeningPassSourceReport("9ddf1cdde381cb13dd749504083ef5b507aa1650", _inventory(), _families(),
                                   rules, borderline, equal, strong, weak, other, missing)
