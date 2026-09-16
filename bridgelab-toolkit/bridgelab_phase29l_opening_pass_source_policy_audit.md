# Phase 29L — Opening Pass source/policy acquisition audit

Read-only snapshot at `9ddf1cdde381cb13dd749504083ef5b507aa1650`. **PASS != FALLBACK_FOR_ABSTAIN**.

## A. Baseline

- Project: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit`
- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`
- Branch: `codex/phase18b`.
- Local HEAD, live remote HEAD and remote-tracking HEAD: `9ddf1cdde381cb13dd749504083ef5b507aa1650`.
- Ahead/behind: `0/0`; initial `git status --short`: no entries.
- Known `.pytest_cache` permission warnings only. Live remote checked with `git ls-remote`; no web research.
- User-supplied regression baseline: 2122 passed, 143 subtests passed; not rerun in this phase.

## B. Files inspected and search scope

Searched all 1186 tracked textual files of supported repository formats, across root knowledge, toolkit code, source metadata, tests, reports and historical text artifacts. Ripgrep discovery was followed by a deterministic full tracked-text scan. Cache directories were excluded by tracked-file enumeration. Binary ZIP bundles were not promoted to current policy; they are historical packaged artifacts, not active canonical knowledge. Search hits are discovery evidence, not endorsement of every assertion. Detailed policy evidence below records inspected relevant sections; tangential play, response, other-system and competitive hits do not define SAYC opening policy.

| Search group | Files with hits | Matching lines |
|---|---:|---:|
| opening strength / Pass | 127 | 337 |
| Rules 20 / 22 | 19 | 113 |
| strength evaluation | 98 | 415 |
| opening families / equal suits | 194 | 1309 |

The source inventory supplies paths, sections, propositions, consumers, authority and limitations. A searched-file manifest with line locations follows section V. No applicable AGENTS.md was found in the target root/subtree or inspected parent directories.

## C. Files added/modified

Added only:

- `bridge/opening_pass_source_policy_audit.py` — immutable evidence report; no hand evaluation, Deal retention or recommendations.
- `tests/test_bridge_phase29l_opening_pass_source_policy_audit.py` — evidence, serialization and semantic guards.
- `bridgelab_phase29l_opening_pass_source_policy_audit.md` — this audit and policy acquisition specification.
- `bridgelab_phase29l_opening_pass_source_policy_audit.json` — stable `to_json()` report snapshot.

Existing tracked files modified: none. No commit or push.

## D. Source inventory

No evidence record supports an authenticated, complete positive opening-Pass predicate. `positive_pass_support=false` means insufficient support for that predicate; it does not mean the source never mentions Pass. All registry authority values remain `UNKNOWN` and default coverage remains `NOT_ESTABLISHED`.

### auction: auction

- Path: `bridgelab-toolkit/bridge/auction.py`; section: module.
- Proposition: Canonical explicit Pass and passed-out representation establish legality, not hand policy.
- Current production consumers: none for this proposition.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### authority-contract: authority-contract

- Path: `bridgelab-toolkit/bridge/source_authority.py`; section: module.
- Proposition: Empty default registry; unknown authority and not-established coverage for opening sources.
- Current production consumers: none for this proposition.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### bibliography: Bibliography

- Path: `knowledge/bibliography.md`; section: Overview.
- Proposition: General references do not imply every treatment follows them exactly.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: No claim-level attribution or authenticated SAYC Pass source.

### club-choice: 1 Club

- Path: `knowledge/bidding/natural-bids/opening-bids/1-club.md`; section: Choosing 1♣ Instead of 1♦.
- Proposition: 3-3 open clubs; 4-4 usually diamonds; 5 clubs and 4 diamonds open clubs.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### diamond-choice: 1 Diamond

- Path: `knowledge/bidding/natural-bids/opening-bids/1-diamond.md`; section: Diamond Length / Better Minor Principle.
- Proposition: SAYC listed as normally 4+ diamonds; 4-4 usually diamonds.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Qualification differs from SAYC table's usually 3+; not production's cited minor source.

### four-level: Four-Level Preempts

- Path: `knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md`; section: Typical Requirements.
- Proposition: Long-suit preemptive openings exist beyond the 14 implemented families.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Eight-plus-card unsupported hands cannot become Pass just because exact six/seven predicates fail.

### hand-evaluation: Hand Evaluation

- Path: `knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md`; section: The Rule of 20 / Rule of 15.
- Proposition: Rule20 for first/second; Rule15 for fourth; honor quality and distribution supplement HCP.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### heart-length: 1 Heart

- Path: `knowledge/bidding/natural-bids/opening-bids/1-heart.md`; section: Heart Length.
- Proposition: Five-card-major systems require five hearts; typical strength 12-21.
- Current production consumers: sayc.opening.1h.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### heart-tie: 1 Heart

- Path: `knowledge/bidding/natural-bids/opening-bids/1-heart.md`; section: Common Mistakes / Opening Hearts with a Longer Spade Suit.
- Proposition: Equal five-card majors: partnership determines 1H or 1S; text says most systems open 1H.
- Current production consumers: none for this proposition.
- Audit level: `PARTNERSHIP_DEPENDENT`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Length-section citation does not adopt this separate qualified tie guidance.

### nt-shape: 1NT Opening

- Path: `knowledge/bidding/natural-bids/opening-bids/1nt-opening.md`; section: Typical Requirements / Balanced Distribution.
- Proposition: 15-17; 4333/4432/5332 balanced; 5422 partnership-dependent; five-card-major treatment requires agreement.
- Current production consumers: sayc.opening.1nt.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### nt2-reference: 2NT Opening

- Path: `knowledge/bidding/natural-bids/opening-bids/2nt-opening.md`; section: Typical Requirements / Balanced Distribution.
- Proposition: SAYC 20-21 balanced; generic partnership variants do not override the SAYC citation.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### opening-overview: Opening Bids Overview

- Path: `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`; section: Requirements for Opening / Opening Priorities.
- Proposition: Normally 12-21; major, minor, NT, strong and preempt categories; unbalanced hands may open lighter.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Prose priority list is not executable precedence; cannot override production 2C/NT gates or define Pass.

### opening-requirements: Opening Requirements

- Path: `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`; section: Traditional Opening Standard / Rules 20, 22 / Hands That Should Not Open.
- Proposition: 12+ is a starting point; distribution and controls can justify lighter openings. Generally avoid weak balanced hands and flat 10-counts. Rules 20/22 are guidelines; partners define standards.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: SAYC metadata is applicability context, not adoption. Qualified Pass guidance lacks complete domains and exceptions.

### opening-tests: opening-tests

- Path: `bridgelab-toolkit/tests/test_bridge_sayc_openings.py`; section: module.
- Proposition: Asserts canonical source citations and current opening/tie behavior; no independent authority.
- Current production consumers: none for this proposition.
- Audit level: `TEST_ONLY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### partnership-card: Cc Nily Nisim

- Path: `knowledge/bidding/convention-cards/cc-nily-nisim.md`; section: System / Opening Bids.
- Proposition: 2/1 Game Force card gives 11-21 minor openings and non-SAYC two-level treatments.
- Current production consumers: none for this proposition.
- Audit level: `PARTNERSHIP_DEPENDENT`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Not the production SAYC profile; duplicated 1C heading for diamonds; no import into SAYC.

### pass-policy: Approved SAYC opening Pass policy

- Path: `MISSING`; section: MISSING.
- Proposition: No complete approved positive predicate located.
- Current production consumers: none for this proposition.
- Audit level: `MISSING`; registry: `UNKNOWN`; source status: `MISSING`.
- Positive Pass support: NO. Limitation: Qualified reference Pass examples are not a complete adopted SAYC policy.

### pass-tests: pass-tests

- Path: `bridgelab-toolkit/tests/test_bridge_phase29k_opening_pass_policy_audit.py`; section: module.
- Proposition: Fixture Pass rule tests architecture only, not positive opening policy.
- Current production consumers: none for this proposition.
- Audit level: `TEST_ONLY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### phase25: phase25

- Path: `bridgelab-toolkit/bridgelab_phase25_source_authority_closure_record.md`; section: module.
- Proposition: Provenance and source readiness do not establish source authority.
- Current production consumers: none for this proposition.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### phase29j: phase29j

- Path: `bridgelab-toolkit/bridge/opening_abstention_root_cause_audit.py`; section: module.
- Proposition: Equal-major boundary is controlled ABSTAIN; unknown cases remain unknown.
- Current production consumers: none for this proposition.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### phase29k: phase29k

- Path: `bridgelab-toolkit/bridge/opening_pass_policy_audit.py`; section: module.
- Proposition: <=11 HCP/max length <=5 screen is source-insufficient, not Pass; four explicit passes complete auction.
- Current production consumers: none for this proposition.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### playing-tricks: Playing Tricks

- Path: `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`; section: Purpose / Estimating Playing Tricks.
- Proposition: Expected declarer tricks with little/no partner help; explicitly no universally accepted formula; examples and approximate side-suit values.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Standard`.
- Positive Pass support: NO. Limitation: Not a total deterministic evaluator proving fewer than nine tricks.

### preempt-principles: Preemptive Openings

- Path: `knowledge/bidding/principles/bidding-fundamentals/preemptive-openings.md`; section: Requirements / Partnership Agreements.
- Proposition: Suit quality, playing strength and vulnerability matter; occasional strong six-card preempts require agreement.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### preempt-reference: Three-Level Preempts

- Path: `knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md`; section: Typical Requirements / Typical Suit Quality.
- Proposition: Most partnerships: 5-10, good seven-card suit; not suitable one-level/weak two. Excellent six-card exceptions, especially third seat.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Not a deterministic 7-6 precedence contract; generic range differs from SAYC.

### preempt-tests: preempt-tests

- Path: `bridgelab-toolkit/tests/test_bridge_sayc_three_level_preempts.py`; section: module.
- Proposition: Asserts current exact-seven and weak-two overlap boundaries.
- Current production consumers: none for this proposition.
- Audit level: `TEST_ONLY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### production: production

- Path: `bridgelab-toolkit/bridge/sayc.py`; section: module.
- Proposition: Fourteen conservative opening predicates; no Pass; exact six/seven lengths and controlled ties.
- Current production consumers: sayc.opening.2c, sayc.opening.2nt, sayc.opening.1nt, sayc.opening.1h, sayc.opening.1s, sayc.opening.1d, sayc.opening.1c, sayc.opening.weak2.2s, sayc.opening.weak2.2h, sayc.opening.weak2.2d, sayc.opening.preempt3.3s, sayc.opening.preempt3.3h, sayc.opening.preempt3.3d, sayc.opening.preempt3.3c.
- Audit level: `PROJECT_POLICY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

### quick-tricks: Quick Tricks

- Path: `knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md`; section: Standard Quick Trick Values.
- Proposition: Per suit AK=2, AQ=1.5, A=1, KQ=1, K=0.5, others=0; supplement to HCP.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Standard`.
- Positive Pass support: NO. Limitation: No adopted opening evaluator; protection/short-honor cases require exact contract before use.

### rule15: Rule of 15

- Path: `knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md`; section: Formula / Exceptions.
- Proposition: Fourth seat: HCP + spade length >=15 usually open; below usually pass; exceptions remain.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### rule20: Rule of 20

- Path: `knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md`; section: The Formula / When to Use / Exceptions.
- Proposition: HCP + two longest suit lengths >=20: usually open; <20: usually pass; first/second seat. No quick-trick term. 11+5+4 example opens; flat 11 example usually passes.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: May open below 20 for excellent six-card suit or controls; may pass above it for poor honors/suits or defensive hand; systems metadata empty.

### rule22: Rule of 22

- Path: `knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md`; section: Formula / Examples / Partnership Notes.
- Proposition: HCP + two longest lengths + quick tricks >=22; first/second seat; explicit Pass example and qualified borderline Pass guidance.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Standard`.
- Positive Pass support: NO. Limitation: Standard metadata is not authentication. Systems empty; style/quality/vulnerability exceptions. Example 2's printed 5+4 lengths disagree with its 5-3-2-3 hand; Example 3 prints 9 HCP for two aces (8).

### sayc-2nt: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: 2NT Opening.
- Proposition: 20-21 balanced.
- Current production consumers: sayc.opening.2nt.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-evaluation: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Hand Evaluation / Balanced Hands.
- Proposition: Approximately 12+ HCP; excellent distribution may justify lighter openings; 5422 occasionally qualifies as balanced.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-majors: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Five-Card Majors.
- Proposition: 1H and 1S promise at least five cards; no equal-major tie decision here.
- Current production consumers: sayc.opening.1h, sayc.opening.1s.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-minors: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Better Minor.
- Proposition: 3-3 minors open 1C; 4-4 open 1D; normally open longer minor; no 5-5 or 6-6 tie policy.
- Current production consumers: sayc.opening.1c, sayc.opening.1d.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-preempt: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Three-Level Openings.
- Proposition: Normally seven-card suit, weak; table supplies 6-10.
- Current production consumers: sayc.opening.preempt3.3s, sayc.opening.preempt3.3h, sayc.opening.preempt3.3d, sayc.opening.preempt3.3c.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-strong: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Strong 2♣ Opening.
- Proposition: Usually 22+ HCP OR 9+ playing tricks; artificial.
- Current production consumers: sayc.opening.2c.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-table: Standard American Yellow Card (SAYC)

- Path: `knowledge/bidding/systems/sayc.md`; section: Opening Bid Requirements.
- Proposition: 1C/1D/1H/1S 12-21; 1NT 15-17 balanced; 2C 22+ or equivalent; weak twos and three-level 6-10; 2NT 20-21 balanced.
- Current production consumers: sayc.opening.2c, sayc.opening.1nt, sayc.opening.1h, sayc.opening.1s, sayc.opening.1d, sayc.opening.1c, sayc.opening.preempt3.3s, sayc.opening.preempt3.3h, sayc.opening.preempt3.3d, sayc.opening.preempt3.3c.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### sayc-weak: SAYC

- Path: `knowledge/bidding/systems/sayc.md`; section: Weak Two Openings.
- Proposition: Six-card suit and 6-10 HCP; preemptive; no multi-suit precedence.
- Current production consumers: sayc.opening.weak2.2s, sayc.opening.weak2.2h, sayc.opening.weak2.2d.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Heading occurs twice; production cites heading text, not a unique occurrence.

### seat: Seat Position

- Path: `knowledge/bidding/principles/bidding-fundamentals/seat-position.md`; section: First Seat / Second Seat / Common Mistakes.
- Proposition: Rules 20/22 associated with first/second; third lighter; fourth Rule 15.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Standard`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### spade-length: 1 Spade

- Path: `knowledge/bidding/natural-bids/opening-bids/1-spade.md`; section: Spade Length.
- Proposition: Five-card-major systems require five spades; typical strength 12-21.
- Current production consumers: sayc.opening.1s.
- Audit level: `CANONICAL_PRODUCTION_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### spade-tie: 1 Spade

- Path: `knowledge/bidding/natural-bids/opening-bids/1-spade.md`; section: Common Mistakes / Opening 1♠ with a Longer Heart Suit.
- Proposition: Text recommends 1H with 5-5 in most five-card-major systems, to show spades later at one level.
- Current production consumers: none for this proposition.
- Audit level: `PARTNERSHIP_DEPENDENT`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Agrees with heart article's suggestion, but is not a mandatory SAYC partnership decision.

### standard-american: Standard American

- Path: `knowledge/bidding/systems/standard-american.md`; section: Fourth-Seat Openings.
- Proposition: Lists Rules 15, 20 and 22 for fourth seat.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Conflicts with dedicated 20/22 articles' seat scope; not a SAYC mandate.

### strong-reference: 2 Clubs

- Path: `knowledge/bidding/natural-bids/opening-bids/2-clubs.md`; section: Typical Requirements / Playing Tricks.
- Proposition: 22+ HCP balanced or approximately nine playing tricks; fewer than 22 can qualify.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### vulnerability: Vulnerability

- Path: `knowledge/bidding/principles/bidding-fundamentals/vulnerability.md`; section: Opening Bids.
- Proposition: Opening style and preempt risk depend on vulnerability; references Rules20/22.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Standard`.
- Positive Pass support: NO. Limitation: Internal repository reference; no authenticated claim-level external source or approved Pass policy.

### weak-reference: Weak Two Bids

- Path: `knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md`; section: Typical Requirements / Typical Suit Quality.
- Proposition: Most partnerships: 5-10 HCP, good six-card suit, outside-four-card-major agreement, unsuitable for one-level; quality and seat/vulnerability vary.
- Current production consumers: none for this proposition.
- Audit level: `SUPPORTED_REFERENCE`; registry: `UNKNOWN`; source status: `Draft`.
- Positive Pass support: NO. Limitation: Generic 5-10 differs from cited SAYC 6-10; no precise competing-long-suit resolution.

### weak-tests: weak-tests

- Path: `bridgelab-toolkit/tests/test_bridge_sayc_weak_two_openings.py`; section: module.
- Proposition: Asserts multi-six-card controlled abstention and strength/length boundaries.
- Current production consumers: none for this proposition.
- Audit level: `TEST_ONLY`; registry: `UNKNOWN`; source status: `project artifact`.
- Positive Pass support: NO. Limitation: Descriptive evidence only; not external bridge-policy authority.

## E. Authority model

The existing SourceAuthorityClassification is preserved: UNKNOWN, SUPPORTING_ONLY, PARTNERSHIP_DEPENDENT, EXISTING_AUTHENTICATED_CLASSIFICATION. The default registry is empty; an article's `status: Standard`, `systems: sayc`, official-sounding description, bibliography inclusion or current production use does not authenticate it.

Audit roles are separate from registry authority:

| Audit role | Meaning |
|---|---|
| CANONICAL_PRODUCTION_REFERENCE | Exact repository section currently cited by a production opening rule; provenance only |
| SUPPORTED_REFERENCE | Relevant repository prose, not adopted production policy |
| PARTNERSHIP_DEPENDENT | Guidance explicitly dependent on agreement or system scope |
| PROJECT_POLICY | Verified implementation, diagnostic contract or derivation from current predicates |
| TEST_ONLY | Observed behavior/fixture checks; no independent bridge authority |
| MISSING | No approved exact proposition/predicate located |

There are no authenticated opening-source claims to label AUTHORITATIVE_PRODUCTION_SOURCE. No informal material is elevated. Every finding identifies evidence and an audit role; all documentary policy remains unauthenticated in the registry.

## F. Opening-family matrix

All production rows below are PROJECT_POLICY descriptions with CANONICAL_PRODUCTION_REFERENCE citations linked through evidence IDs. Global gate: SAYC and unopened auction (all existing calls Pass). This is a matrix of existing predicates, not new decision logic. Every complement is **OTHER_OPENING_OR_UNKNOWN**, never explicitly Pass.

| Family / rule | Strength | Shape | Exclusions | Evidence | Current coverage / boundary | Complement Pass? |
|---|---|---|---|---|---|---|
| Strong 2C / `sayc.opening.2c` | 22+ HCP implemented; source also 9+ playing tricks | Any shape in HCP branch | Below 22 not evaluated for playing tricks | sayc-strong, sayc-table, production | HCP branch only; Uncomputed playing-trick domain | NO; other opening or UNKNOWN |
| 2NT / `sayc.opening.2nt` | 20-21 HCP | Canonical balanced 4333/4432/5332 | Other shapes/ranges | sayc-2nt, production | Exact balanced subset; 5422 agreement not implemented | NO; other opening or UNKNOWN |
| 1NT / `sayc.opening.1nt` | 15-17 HCP | Canonical balanced, no five-card major | Five-card major; 5422; strength upgrades/downgrades | sayc-table, nt-shape, production | Conservative subset; Other families may open excluded hands; no implication of Pass | NO; other opening or UNKNOWN |
| 1H / `sayc.opening.1h` | 12-21 HCP | 5+ hearts, strictly longer than spades | 20-21 balanced reserved for 2NT; 22+ for 2C | sayc-table, sayc-majors, heart-length, production | Strictly longer major only; Equal 5-5 and 6-6 majors excluded | NO; other opening or UNKNOWN |
| 1S / `sayc.opening.1s` | 12-21 HCP | 5+ spades, strictly longer than hearts | 20-21 balanced reserved for 2NT; 22+ for 2C | sayc-table, sayc-majors, spade-length, production | Strictly longer major only; Equal 5-5 and 6-6 majors excluded | NO; other opening or UNKNOWN |
| 1D / `sayc.opening.1d` | 12-21 HCP | D>C and D>=3, or 4-4 minors | Five-card major; clear 1NT; 20-21 balanced 2NT; 22+ 2C | sayc-table, sayc-minors, production | Clear Better-Minor cases; Equal 5-5/6-6 minors outside controlled subset | NO; other opening or UNKNOWN |
| 1C / `sayc.opening.1c` | 12-21 HCP | C>D and C>=3, or 3-3 minors | Five-card major; clear 1NT; 20-21 balanced 2NT; 22+ 2C | sayc-table, sayc-minors, production | Clear Better-Minor cases; Equal 5-5/6-6 minors outside controlled subset | NO; other opening or UNKNOWN |
| Weak 2S / `sayc.opening.weak2.2s` | 6-10 HCP | Exactly six in S | Multiple six-card D/H/S suits; any seven-card suit | sayc-weak, weak-reference, production | Unique six-card D/H/S, no seven-card suit; 6-6 D/H/S ties; 7-6 overlap; quality/seat exceptions unadopted | NO; other opening or UNKNOWN |
| Weak 2H / `sayc.opening.weak2.2h` | 6-10 HCP | Exactly six in H | Multiple six-card D/H/S suits; any seven-card suit | sayc-weak, weak-reference, production | Unique six-card D/H/S, no seven-card suit; 6-6 D/H/S ties; 7-6 overlap; quality/seat exceptions unadopted | NO; other opening or UNKNOWN |
| Weak 2D / `sayc.opening.weak2.2d` | 6-10 HCP | Exactly six in D | Multiple six-card D/H/S suits; any seven-card suit | sayc-weak, weak-reference, production | Unique six-card D/H/S, no seven-card suit; 6-6 D/H/S ties; 7-6 overlap; quality/seat exceptions unadopted | NO; other opening or UNKNOWN |
| 3S / `sayc.opening.preempt3.3s` | 6-10 HCP | Exactly seven in S | Any six-card D/H/S overlap; nonunique seven-card qualifier | sayc-table, sayc-preempt, preempt-reference, production | Unique seven-card subset; 7-6 D/H/S overlap; six/eight-card variants unimplemented; two seven-card suits impossible in 13 cards | NO; other opening or UNKNOWN |
| 3H / `sayc.opening.preempt3.3h` | 6-10 HCP | Exactly seven in H | Any six-card D/H/S overlap; nonunique seven-card qualifier | sayc-table, sayc-preempt, preempt-reference, production | Unique seven-card subset; 7-6 D/H/S overlap; six/eight-card variants unimplemented; two seven-card suits impossible in 13 cards | NO; other opening or UNKNOWN |
| 3D / `sayc.opening.preempt3.3d` | 6-10 HCP | Exactly seven in D | Any six-card D/H/S overlap; nonunique seven-card qualifier | sayc-table, sayc-preempt, preempt-reference, production | Unique seven-card subset; 7-6 D/H/S overlap; six/eight-card variants unimplemented; two seven-card suits impossible in 13 cards | NO; other opening or UNKNOWN |
| 3C / `sayc.opening.preempt3.3c` | 6-10 HCP | Exactly seven in C | Any six-card D/H/S overlap; nonunique seven-card qualifier | sayc-table, sayc-preempt, preempt-reference, production | Unique seven-card subset; 7-6 D/H/S overlap; six/eight-card variants unimplemented; two seven-card suits impossible in 13 cards | NO; other opening or UNKNOWN |
| Opening Pass / `none` | INCOMPLETE | INCOMPLETE | All unresolved domains remain protected | pass-policy, phase29k | No production rule; Missing approved positive conditions | NO; other opening or UNKNOWN |

## G. Rule 20 findings

- **rule20** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: rule20, opening-requirements. Present: HCP+L1+L2>=20, no quick-trick term. First/second-seat opening evaluation guidance; not production-used or authenticated. Arithmetic: 10 needs lengths sum 10, 11 needs 9, 12 needs 8; exceptions prevent deterministic OPEN/PASS. Safety exclusion: not a separate exclusion.

## H. Rule 22 findings

- **rule22** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: rule22, quick-tricks, opening-requirements. Present: HCP+L1+L2+QT>=22. First/second-seat guidance, not production-used or authenticated. At 10/11/12 HCP remaining sum must be 12/11/10. Quick tricks are explicit. Qualitative exceptions and erroneous examples require reconciliation. Safety exclusion: not a separate exclusion.

Rule22's stored definition adds quick tricks to the arithmetic total; this audit does not substitute a different remembered definition. Its Pass example prints 5+4 while the hand is 5-3-2-3; its borderline two-ace hand has 8 HCP, not the stated 9. These source defects further prevent mechanical promotion. The Rule20 Pass/open 11-HCP examples establish that an HCP cutoff alone cannot represent even the reference guidance.

## I. Borderline-hand findings

- **10-hcp-distributional** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: rule20, sayc-weak, sayc-preempt. OPEN in implemented weak/preempt subsets; 5-5 can reach Rule20 arithmetically, but adoption/quality/seat decisions are missing. Otherwise POLICY_REQUIRED. Safety exclusion: YES.
- **11-hcp** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: rule20, opening-requirements, partnership-card. No 11-HCP production opening family. Rule20 gives both open 5-4 and usually-pass flat examples; 2/1 card is not SAYC. No universal Pass. Safety exclusion: YES.
- **12-hcp** — `OPEN`; `PROJECT_POLICY`; evidence: sayc-table, production. OPEN only in covered one-level shape subsets; ties remain POLICY_REQUIRED; approximately-12 guidance is not universal Pass evidence. Safety exclusion: YES.
- **13-hcp** — `OPEN`; `PROJECT_POLICY`; evidence: sayc-table, production. OPEN only in covered one-level subsets; equal-major/minor boundary still applies. Safety exclusion: YES.
- **five-five** — `POLICY_REQUIRED`; `PARTNERSHIP_DEPENDENT`; evidence: heart-tie, spade-tie, sayc-minors, rule20. Major/minor with opening values is covered by major rule; equal majors or equal minors unresolved; lighter 5-5 needs policy. Safety exclusion: YES.
- **six-card** — `POLICY_REQUIRED`; `PROJECT_POLICY`; evidence: sayc-weak, production, rule20. OPEN for unique six-card D/H/S at 6-10 absent seven-card suit, or covered one-level strength; six clubs, 11 HCP, multiple qualifiers and exceptions unresolved. Safety exclusion: YES.
- **seven-card** — `POLICY_REQUIRED`; `PROJECT_POLICY`; evidence: sayc-preempt, preempt-reference, production. OPEN for controlled 6-10 seven-card subset without six-card D/H/S overlap, or covered one-level strength; remaining domains are not Pass. Safety exclusion: YES.
- **balanced-unbalanced** — `SOURCE_INSUFFICIENT`; `SUPPORTED_REFERENCE`; evidence: opening-requirements, sayc-evaluation, nt-shape. Balance alone proves neither OPEN nor PASS. 12/13 balanced commonly covered, 10 flat usually-pass guidance is qualified; distributional exceptions remain. Safety exclusion: YES.

OPEN labels above are conditional on current covered shape predicates, not endorsements of entire HCP classes. No audited class receives an unconditional authoritative PASS. POLICY_REQUIRED means relevant guidance needs selection/approval; SOURCE_INSUFFICIENT means no exact positive domain can be established. Shape-only classes overlap and cannot be adjudicated without strength and context.

## J. Equal-suit findings

- **equal-five-majors** — `POLICY_REQUIRED`; `PARTNERSHIP_DEPENDENT`; evidence: heart-tie, spade-tie, phase29j. Both references suggest 1H; heart article explicitly requires partnership agreement. No authenticated mandatory SAYC choice; production abstains for 12-21 equal 5-5 and 6-6. Safety exclusion: YES.
- **five-five-major-minor** — `OPEN`; `PROJECT_POLICY`; evidence: sayc-majors, production. At 12-21 the sole five-card major is strictly longer than the other major and covered; minor defers. Lower strengths need policy. Safety exclusion: not a separate exclusion.
- **equal-minors** — `POLICY_REQUIRED`; `PROJECT_POLICY`; evidence: sayc-minors, club-choice, diamond-choice, production. 3-3 ->1C and 4-4 ->1D explicitly cited and implemented subject to NT/major gates. Equal 5-5/6-6 not resolved. Equal <=2 entails a five-card major, so is not an independent minor-opening gap. Safety exclusion: YES.

## K. Strong-2C findings

- **strong-playing-tricks** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: sayc-strong, strong-reference, playing-tricks, production. Source says usually 22+ HCP OR 9+ playing tricks. Production implements HCP>=22 only. Below-22 failure cannot exclude strong opening. Future Pass needs a sourced proof of exclusion or must leave uncertain trick strength unsupported. Safety exclusion: YES.

Exact implementation: `_clear_strong_two_club(context)` is `context.evaluation.hcp >= 22`; `SaycStrongTwoClubOpeningRule.evaluate()` explicitly reports that the 9+ playing-tricks branch is not evaluated. Exact source: `knowledge/bidding/systems/sayc.md#Strong 2♣ Opening`, with corroborating `2-clubs` and `playing-tricks` articles. The risk exists below 22 even where another current rule opens; an ABSTAIN future fallback would be particularly unsafe. No heuristic maximum-suit-length or HCP screen is approved as a proof that fewer than nine playing tricks exist.

## L. Weak-two/preempt findings

- **weak-preempt-overlap** — `POLICY_REQUIRED`; `PROJECT_POLICY`; evidence: sayc-weak, sayc-preempt, weak-reference, preempt-reference, production. Two six-card D/H/S qualifiers and seven plus six D/H/S overlap abstain. No adopted precedence. Seven plus six clubs is not rejected by weak-overlap guard. Two seven-card suits cannot occur in a valid 13-card hand. Safety exclusion: YES.
- **preempt-style** — `POLICY_REQUIRED`; `PARTNERSHIP_DEPENDENT`; evidence: weak-reference, preempt-reference, four-level, production. Generic 5-10 vs production 6-10; quality, outside majors, seat/vulnerability, six-card three-level exceptions and eight-plus suits unresolved. Six clubs has no weak-two opening. None of these omissions proves Pass. Safety exclusion: YES.

A 6-6 hand with six clubs and one six-card D/H/S suit has only one weak-two qualifier and is currently covered if strength fits. A 7-6 hand with six clubs has no weak-two overlap, whereas six D/H/S triggers the overlap exclusion. Seven-plus-seven is mathematically impossible in a valid 13-card hand, although the defensive uniqueness check exists. These are implementation observations (PROJECT_POLICY), not new source rules.

Additional coverage boundaries

- **seat-scope** — `POLICY_REQUIRED`; `SUPPORTED_REFERENCE`; evidence: rule20, rule22, rule15, seat, standard-american. Dedicated 20/22 articles restrict first/second; Standard American fourth-seat section lists both. Define dealer-only versus all unopened positions, reconcile fourth-seat scope and approve third-seat/vulnerability treatment. Safety exclusion: YES.
- **nt-adjustments** — `POLICY_REQUIRED`; `PARTNERSHIP_DEPENDENT`; evidence: nt-shape, sayc-evaluation, production. Five-card-major NT choice, 5422 and strength upgrades/downgrades are unadopted; often covered by another bid, never implied Pass. Safety exclusion: YES.
- **passed-out** — `SOURCE_INSUFFICIENT`; `PROJECT_POLICY`; evidence: auction, phase29k, pass-tests. Four explicit passes can complete a legal auction; representation and test fixture do not establish which hands should pass. Safety exclusion: not a separate exclusion.
- **low-strength-screen** — `SOURCE_INSUFFICIENT`; `PROJECT_POLICY`; evidence: phase29k, rule20, opening-requirements. 29K <=11 HCP and max length <=5 screen remains SOURCE_INSUFFICIENT; distributional 5-5 and 11-HCP references defeat treating it as a positive predicate. Safety exclusion: YES.

## M. Pass-policy requirements

**Positive predicate: INCOMPLETE.** No executable hand predicate is supplied.

A future contract must affirmatively specify: (1) valid hand and nonterminal unopened auction within an approved SAYC/seat/vulnerability scope; (2) membership in an explicitly sourced, approved positive Pass domain with exact strength, distribution, control and exception conditions; (3) sufficient evidence that protected strong, constructive and preemptive domains do not apply; (4) a source identifier/section and approval/version for every condition. Unknown conditions must remain unsupported.

The predicate cannot be `all opening rules failed`, `HCP<12`, the Phase29K screen, or the negation of Rule20/22 without adopted exception handling. Excluding dangerous domains alone does not prove Pass: positive evidence is still required.

Mandatory protections: equal 5-5/6-6 majors; equal 5-5/6-6 minors; below-22 unresolved strong playing tricks; 6-6 weak-two ties; 7-6 weak-two/preempt overlap; six clubs; 5-HCP generic preempt references; eight-plus-card/four-level openings; 10/11 distributional exceptions; undefined seat/vulnerability style; optional NT shapes/adjustments. Excluded NT hands may have a covered suit opening. Resolution of every bidding family is not necessary for a narrowly scoped Pass rule if those domains can be positively and safely excluded by the approved contract.

## N. REQUIRED AUTHORITATIVE POLICY DECISIONS

### positive-domain

- Question: What exact hands positively qualify for opening Pass in the intended SAYC profile?
- Why production needs it: A recommendation needs affirmative grounds.
- Current evidence: pass-policy, opening-requirements, rule20, rule22.
- Missing evidence (`MISSING`): Authenticated claim-level policy or explicit approved partnership contract, including 10/11/12/13 HCP, shape, controls, exceptions and scope.
- Risk if guessed: Turning incomplete coverage into Pass.

### evaluation-choice

- Question: Adopt neither, Rule20, Rule22, or another explicitly defined borderline policy?
- Why production needs it: Resolve distributional openings and numerical/qualitative exceptions.
- Current evidence: rule20, rule22, quick-tricks.
- Missing evidence (`MISSING`): Selected method, exact quick-trick handling if used, corrected examples, exception precedence and explicit Pass domain.
- Risk if guessed: Passing valid light openings or silently changing system.

### seat-vulnerability

- Question: Which seats and vulnerabilities are covered, and what are their exceptions?
- Why production needs it: An unopened auction can already contain passes.
- Current evidence: seat, rule15, standard-american.
- Missing evidence (`MISSING`): Approved dealer-only scope or seat-specific policy; resolve fourth-seat contradiction.
- Risk if guessed: Applying first-seat standards in third/fourth seat.

### equal-suits

- Question: Resolve equal major/minor choices, or explicitly retain those domains as unsupported?
- Why production needs it: Protect controlled ABSTAIN boundaries.
- Current evidence: heart-tie, spade-tie, sayc-minors, phase29j.
- Missing evidence (`MISSING`): Approved 5-5/6-6 major and minor treatment, or documented exclusion from initial Pass scope.
- Risk if guessed: Passing opening-strength hands.

### playing-tricks

- Question: How is the below-22 strong-2C playing-trick domain safely excluded?
- Why production needs it: HCP alone does not decide strong 2C eligibility.
- Current evidence: sayc-strong, playing-tricks.
- Missing evidence (`MISSING`): Deterministic sourced evaluation or positively justified narrow-domain exclusion; uncertain cases remain unsupported.
- Risk if guessed: Passing a game-going strong hand.

### preempt-domains

- Question: Resolve or explicitly exclude competing long suits and unimplemented preempt variants?
- Why production needs it: Exact-six/seven failures are coverage gaps.
- Current evidence: sayc-weak, weak-reference, preempt-reference, four-level.
- Missing evidence (`MISSING`): Approved 6-6/7-6 precedence, range/quality/seat exceptions and six-club/eight-plus treatment, or explicit exclusions.
- Risk if guessed: Passing a legitimate preempt or constructive opening.

### nt-domains

- Question: Which optional NT shape/major/strength adjustments are adopted or excluded?
- Why production needs it: Prevent optional evaluation changes being treated as Pass.
- Current evidence: nt-shape, sayc-evaluation.
- Missing evidence (`MISSING`): Explicit scope and exclusions; no silent upgrade/downgrade policy.
- Risk if guessed: Confusing alternative opening choices with Pass.

## O. Implementation readiness

**NOT READY / INCOMPLETE.** Architecture accepts explicit Pass; source/policy acquisition is incomplete. There is no basis to implement a broad opening Pass predicate from authenticated repository sources.

## P. Exact recommended next phase

**Phase 29M — authoritative opening-policy acquisition and scope approval.** Obtain an attributable SAYC source covering a proposed narrow positive Pass domain and its exceptions. If the source intentionally leaves choices to partnership style, obtain explicit BridgeLab SAYC partnership approval for those choices, labeled as project policy. Keep unresolved domains excluded. Do not proceed directly to implementation.

Narrowest safe next step: select the intended seat scope and acquire/approve a claim-level positive Pass specification for that scope, with explicit controls/distribution/playing-trick and preempt exclusions. Do not choose 1H or 1S for equal majors or adopt Rule20/22 implicitly.

## Q. Tests/results

84 passed in 10.11s. Focused run only: Phase29L (9 tests), Phase29K, Phase29J, SAYC openings, 2NT opening, strong two club, weak-two openings, three-level preempts, source-authority contract/registry audit and route configuration. No full regression. Used bundled Python with existing local venv site-packages, PYTHONDONTWRITEBYTECODE=1 and pytest -p no:cacheprovider. No dependencies or production files changed.

## R. Route count

45 production SAYC routes; 14 opening rules within the existing opening route. Pass is a report-only fifteenth family, not a rule or route.

## S. Git status/diff

Four untracked audit deliverables only; existing tracked diff empty. `git diff --check` and `git diff --stat` clean/empty. Separate trailing-whitespace/EOF check covers all four untracked files. No commit or push. Final HEAD unchanged.

## T. Semantic guards

| Area changed? | YES/NO |
|---|---|
| Opening semantics | NO |
| Pass recommendations | NO |
| Other bidding semantics | NO |
| Routes | NO |
| Route count | NO |
| ABSTAIN | NO |
| System/treatments | NO |
| Auction | NO |
| Deal generation | NO |
| Phase29F-K | NO |
| GUI | NO |
| Contract/play/DD | NO |

## U. Stop-condition review

Expected baseline verified before edits. No production semantic change required or made. Missing authority is the audit result, not permission to invent policy. No external web research, full regression, commit or push. Repository write access was obtained through the normal sandbox escalation for the user-specified worktree. No policy approval is claimed.

## V. Required answers 1–16

1. Canonical opening citations exist in SAYC (opening table, majors, Better Minor, strong2C, 2NT, weak twos, three-level) and the 1NT/1H/1S articles. None has authenticated external authority in the empty registry. Canonical provenance is not authority.
2. Qualified opening-Pass guidance exists in Rules20/22, opening-requirements and fourth-seat Rule15, including examples. A complete approved SAYC positive Pass predicate does not exist; production has no opening Pass rule.
3. Yes: Rule20 is stored as HCP plus two longest lengths >=20, usually open; below usually pass; first/second seat; exceptions.
4. Yes: Rule22 adds quick tricks to those terms and uses >=22; first/second seat, with exceptions.
5. Neither is production-adopted or authenticated. Draft/Standard metadata and SAYC links do not establish authority.
6. 11 HCP: no current opening family. Rule20 explicitly opens a 5-4 example and usually passes a flat example. The 11-21 partnership card belongs to 2/1, not SAYC. Policy approval needed.
7. 12 HCP: one-level openings in covered shapes; generic traditional threshold is qualified by evaluation. Equal-major/minor boundaries remain; no universal Pass conclusion.
8. Equal 5-5 majors: both natural major articles suggest 1H; heart article explicitly makes choice partnership-dependent. No authenticated mandatory SAYC decision; production controlled ABSTAIN is preserved.
9. Equal minors: canonical SAYC says 3-3 clubs and 4-4 diamonds; production implements those after higher-family gates. No adopted 5-5/6-6 minor choice found.
10. Strong2C: below-22 hands with 9+ playing tricks; source gives no complete evaluator, production only checks >=22 HCP.
11. Weak/preempt: two six-card D/H/S suits, seven plus six D/H/S precedence, generic 5-10 vs SAYC 6-10, quality/seat/vulnerability exceptions, six-card three-level and eight-plus/four-level coverage.
12. Protect all controlled ties, strong playing-trick uncertainty, weak/preempt overlaps, light/distributional and long-suit gaps, the 29K low-strength screen, seat/vulnerability and optional evaluation boundaries; see M. Unknown never becomes Pass.
13. No. The positive predicate remains INCOMPLETE.
14. Missing: approved positive domain, borderline evaluation/exception method, seat/vulnerability scope, equal-suit resolution or exclusions, playing-trick proof/exclusions, preempt precedence/style/exclusions, and optional NT-domain scope. Exact acquisition questions are in N.
15. Source acquisition next, with explicit partnership-policy approval where authoritative sources leave choices. Not implementation.
16. Acquire/approve one narrowly scoped positive Pass specification with claim-level citations and explicit protected-domain exclusions, then audit readiness again.

## Search manifest and inspected-source fingerprints

This manifest is reproducible from tracked text at the baseline. Hits can be merely links or other-system material; only the interpreted inventory supports the findings. References to absent `one-level-openings.md` are links, not recovered source content.

### opening strength / Pass

- `bridgelab-toolkit/benchmarks/next_family_source_readiness_audit.py`: 94
- `bridgelab-toolkit/bridge/auction.py`: 277,357
- `bridgelab-toolkit/bridge/opening_pass_policy_audit.py`: 1,15,21,29,45,51,56,64,65,75,81,93,98,100,101,115,116,117,120,121 (+2 more)
- `bridgelab-toolkit/bridge/sayc.py`: 33,35,141,185,229,283,336,371,498
- `bridgelab-toolkit/bridge/sayc_1d_notrump.py`: 7,71,79
- `bridgelab-toolkit/bridge/sayc_1h_responses.py`: 11,143,154
- `bridgelab-toolkit/bridge/sayc_1s_responses.py`: 11,140,151
- `bridgelab-toolkit/bridge/sayc_coverage_benchmark.py`: 23,100
- `bridgelab-toolkit/bridge/sayc_major_raise_opener_rebids.py`: 5,54
- `bridgelab-toolkit/bridge/sayc_takeout_advancer.py`: 35
- `bridgelab-toolkit/bridge/two_over_one.py`: 89
- `bridgelab-toolkit/bridgelab_phase12m_next_family_source_readiness_audit.json`: 72
- `bridgelab-toolkit/bridgelab_phase12m_next_family_source_readiness_audit.md`: 18
- `bridgelab-toolkit/metadata/category_normalization_batch3_3i.py`: 169
- `bridgelab-toolkit/tests/test_bridge_auction.py`: 84,87,95
- `bridgelab-toolkit/tests/test_bridge_auction_simulation.py`: 11
- `bridgelab-toolkit/tests/test_bridge_batch_simulation.py`: 8,40
- `bridgelab-toolkit/tests/test_bridge_end_to_end_sayc_simulation.py`: 17
- `bridgelab-toolkit/tests/test_bridge_engine_router.py`: 12
- `bridgelab-toolkit/tests/test_bridge_engine_router_simulation.py`: 10
- `bridgelab-toolkit/tests/test_bridge_phase29g_full_auction_simulation.py`: 65,73
- `bridgelab-toolkit/tests/test_bridge_phase29k_opening_pass_policy_audit.py`: 8,9,21,36,37,41,46,51,53,57
- `bridgelab-toolkit/tests/test_bridge_sayc_natural_overcalls.py`: 29
- `bridgelab-toolkit/tests/test_bridge_sayc_openings.py`: 71,72
- `knowledge/bidding/conventions/competitive/balancing-double.md`: 137,161
- `knowledge/bidding/conventions/competitive/balancing-notrump.md`: 100
- `knowledge/bidding/conventions/competitive/equal-level-conversion-doubles.md`: 162
- `knowledge/bidding/conventions/competitive/equal-level-conversion.md`: 210
- `knowledge/bidding/conventions/competitive/michaels-cue-bid.md`: 155
- `knowledge/bidding/conventions/competitive/multi-landy.md`: 47
- `knowledge/bidding/conventions/competitive/negative-free-bid.md`: 129,198,639,659
- `knowledge/bidding/conventions/competitive/responsive-cue-bid.md`: 182,195
- `knowledge/bidding/conventions/competitive/unusual-2nt.md`: 188
- `knowledge/bidding/conventions/doubles/optional-double.md`: 261
- `knowledge/bidding/conventions/doubles/re-opening-double.md`: 124,248
- `knowledge/bidding/conventions/doubles/responsive-double.md`: 204,253
- `knowledge/bidding/conventions/doubles/support-double.md`: 121
- `knowledge/bidding/conventions/doubles/support-redouble.md`: 118,194
- `knowledge/bidding/conventions/doubles/take-out-double.md`: 53,73,654
- `knowledge/bidding/conventions/game-invitations/2nt-game-try.md`: 329
- `knowledge/bidding/conventions/game-invitations/artificial-game-tries.md`: 349
- `knowledge/bidding/conventions/game-invitations/game-invitations.md`: 66,86
- `knowledge/bidding/conventions/game-invitations/guides/common-mistakes.md`: 65,69
- `knowledge/bidding/conventions/game-invitations/help-suit-game-try.md`: 579,2634
- `knowledge/bidding/conventions/game-invitations/long-suit-game-try.md`: 349,2532
- `knowledge/bidding/conventions/game-invitations/maximal-game-try.md`: 408,2115
- `knowledge/bidding/conventions/game-invitations/short-suit-game-try.md`: 237
- `knowledge/bidding/conventions/game-invitations/two-way-game-try.md`: 381
- `knowledge/bidding/conventions/opening-bids/ekren.md`: 106,112
- `knowledge/bidding/conventions/opening-bids/flannery.md`: 57
- `knowledge/bidding/conventions/opening-bids/index-opening-bids.md`: 32,248,384
- `knowledge/bidding/conventions/opening-bids/namyats.md`: 127,485
- `knowledge/bidding/conventions/opening-bids/roman-2-diamonds.md`: 289
- `knowledge/bidding/conventions/opening-bids/two-diamond-multi.md`: 117
- `knowledge/bidding/conventions/responses/bergen-raises.md`: 167
- `knowledge/bidding/conventions/responses/drury.md`: 57,80,172,227,256,530
- `knowledge/bidding/conventions/responses/inverted-minors.md`: 193,590
- `knowledge/bidding/conventions/responses/jacoby-notrump.md`: 160,342
- `knowledge/bidding/conventions/responses/new-minor-forcing.md`: 235
- `knowledge/bidding/conventions/responses/passed-hand-bergen.md`: 72,247,255
- `knowledge/bidding/conventions/responses/passed-hand-jacoby.md`: 264
- `knowledge/bidding/conventions/responses/passed-hand-splinter.md`: 101
- `knowledge/bidding/conventions/responses/response-to-gambling-3nt.md`: 41,300
- `knowledge/bidding/conventions/responses/reverse-drury.md`: 62,509
- `knowledge/bidding/conventions/responses/swiss-raise.md`: 103
- `knowledge/bidding/conventions/responses/two-way-checkback.md`: 184
- `knowledge/bidding/conventions/responses/two-way-new-minor-forcing.md`: 162
- `knowledge/bidding/natural-bids/opening-bids/1-club.md`: 76,110,234,341,580,674
- `knowledge/bidding/natural-bids/opening-bids/1-diamond.md`: 3,56,122,241,348,390,616,720
- `knowledge/bidding/natural-bids/opening-bids/1-heart.md`: 3,42,68,132,170,174,228,310
- `knowledge/bidding/natural-bids/opening-bids/1-spade.md`: 3,41,127,165,221,302,697
- `knowledge/bidding/natural-bids/opening-bids/1nt-opening.md`: 3,51,611
- `knowledge/bidding/natural-bids/opening-bids/2-clubs.md`: 3
- `knowledge/bidding/natural-bids/opening-bids/2nt-opening.md`: 3,53,451,685
- `knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md`: 3,37,231,538
- `knowledge/bidding/natural-bids/opening-bids/natural-opening-bids-index.md`: 23,44,51
- `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`: 3,33,241,325,351,436,531,546
- `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`: 2,49,124,182,236,294,358,459,493,523,644,663,669
- `knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md`: 3,36,526
- `knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md`: 3,38,125,511,572,588
- `knowledge/bidding/natural-bids/rebids/jump-rebids.md`: 81,582
- `knowledge/bidding/natural-bids/rebids/natural-rebids-index.md`: 66
- `knowledge/bidding/natural-bids/rebids/opener-after-2nt.md`: 552
- `knowledge/bidding/natural-bids/rebids/opener-after-minor.md`: 557
- `knowledge/bidding/natural-bids/rebids/opening-rebids.md`: 348
- `knowledge/bidding/natural-bids/rebids/responder-rebids.md`: 147
- `knowledge/bidding/natural-bids/rebids/reverse-bid.md`: 60
- `knowledge/bidding/natural-bids/responses/limit-raise.md`: 84,88,150,197,244,300,521,587
- `knowledge/bidding/natural-bids/responses/natural-responses-index.md`: 90
- `knowledge/bidding/natural-bids/responses/raising-partners-major.md`: 170,234
- `knowledge/bidding/natural-bids/responses/raising-partners-minor.md`: 147,571
- `knowledge/bidding/natural-bids/responses/respond-preemptive-opening-in-3-level.md`: 102,165
- `knowledge/bidding/natural-bids/responses/responding-to-opening-bids.md`: 150,248
- `knowledge/bidding/natural-bids/responses/responding-with-balanced-hands.md`: 161,228
- `knowledge/bidding/natural-bids/responses/response-to-1-club.md`: 126,245,328
- `knowledge/bidding/natural-bids/responses/response-to-1-diamond.md`: 121,222,304
- `knowledge/bidding/natural-bids/responses/response-to-2nt.md`: 362
- `knowledge/bidding/natural-bids/responses/response-to-four-level-preempt.md`: 124,470
- `knowledge/bidding/natural-bids/responses/response-to-major-opening.md`: 152,194,335,684
- `knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md`: 127,465
- `knowledge/bidding/natural-bids/responses/response-to-weak-two.md`: 561
- `knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md`: 275,364
- `knowledge/bidding/principles/bidding-fundamentals/index-fundamental-bids.md`: 36,121,240
- `knowledge/bidding/principles/bidding-fundamentals/offensive-vs-defensive-values.md`: 165,182,264
- `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`: 169
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md`: 118,157,196
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md`: 117,157,198,214
- `knowledge/bidding/principles/bidding-fundamentals/seat-position.md`: 4,26,47,79,107,189,238
- `knowledge/bidding/principles/partnership/disclosure.md`: 78
- `knowledge/bidding/principles/partnership/partnership-agreements.md`: 149
- `knowledge/bidding/systems/2-over-1.md`: 62,426,466,1268,1751,2140
- `knowledge/bidding/systems/acol.md`: 79,656,3111
- `knowledge/bidding/systems/culbertson.md`: 121,133
- `knowledge/bidding/systems/ehaa.md`: 53,69,110,117
- `knowledge/bidding/systems/neapolitan-club.md`: 58,299
- `knowledge/bidding/systems/polish-club.md`: 292,666,983,3155
- `knowledge/bidding/systems/precision.md`: 708,735,1430,1776,2246
- `knowledge/bidding/systems/roman-club.md`: 308
- `knowledge/bidding/systems/roman-precision.md`: 114
- `knowledge/bidding/systems/roth-stone.md`: 44,80
- `knowledge/bidding/systems/sayc.md`: 166,577,727,877,1011,2931
- `knowledge/bidding/systems/standard-american.md`: 64,166,432,661
- `knowledge/play/counting/counting-defenders.md`: 92
- `knowledge/play/counting/counting-points.md`: 107,118
- `knowledge/play/declarer-play/general-techniques/finesses/intra-finesse.md`: 223
- `knowledge/references/bridge-glossary.md`: 142
- `knowledge/references/bridge-terminology.md`: 160
### Rules 20 / 22

- `bridgelab-toolkit/metadata/category_normalization_batch3_3z.py`: 13
- `bridgelab-toolkit/metadata/title_h1_case_normalization_batch1.py`: 17,43
- `bridgelab-toolkit/tests/test_category_normalization_batch3_3z.py`: 27,32
- `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`: 557,559
- `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`: 36,37,218,220,249,251,495,509,614,615,627,628,663
- `knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md`: 29,258,405,447
- `knowledge/bidding/principles/bidding-fundamentals/kaplan-rubens-hand-evaluation.md`: 31,331,388
- `knowledge/bidding/principles/bidding-fundamentals/losing-trick-count.md`: 29,319,396,435
- `knowledge/bidding/principles/bidding-fundamentals/offensive-vs-defensive-values.md`: 33,34,301,302,343,344
- `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`: 31,32,322,323
- `knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md`: 27,28,46,176,178,268,269,277,278,290
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md`: 24,25,279,280,315,316
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md`: 2,3,26,37,41,43,53,65,220,261,288,294,328,364,366,398,402,408
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md`: 2,3,5,16,17,27,37,41,139,151,162,163,168,175,184
- `knowledge/bidding/principles/bidding-fundamentals/seat-position.md`: 32,33,83,84,115,116,310,318,319
- `knowledge/bidding/principles/bidding-fundamentals/vulnerability.md`: 33,34,364,365
- `knowledge/bidding/principles/principles-index.md`: 31,32,127,128
- `knowledge/bidding/systems/standard-american.md`: 70,71,423,424
- `knowledge/references/bridge-terminology.md`: 55,255
### strength evaluation

- `bridgelab-toolkit/bridge/sayc.py`: 361,368
- `bridgelab-toolkit/metadata/category_normalization_batch3_3aa.py`: 18,21
- `knowledge/bidding/conventions/competitive/brozel.md`: 31,253
- `knowledge/bidding/conventions/competitive/cappelletti.md`: 43,443
- `knowledge/bidding/conventions/competitive/dont.md`: 41,472
- `knowledge/bidding/conventions/competitive/fit-jump-shift.md`: 43,155,271,768
- `knowledge/bidding/conventions/competitive/fit-jump.md`: 43,303
- `knowledge/bidding/conventions/competitive/ghestem.md`: 38,357
- `knowledge/bidding/conventions/competitive/hamilton.md`: 33,256,474
- `knowledge/bidding/conventions/competitive/landy.md`: 35,469
- `knowledge/bidding/conventions/competitive/michaels-cue-bid.md`: 45,382
- `knowledge/bidding/conventions/competitive/multi-landy.md`: 33,239,380
- `knowledge/bidding/conventions/competitive/negative-free-bid.md`: 48,236
- `knowledge/bidding/conventions/competitive/top-and-bottom-cue-bid.md`: 42,279
- `knowledge/bidding/conventions/competitive/unusual-2nt.md`: 3,42,201,269,419
- `knowledge/bidding/conventions/competitive/unusual-vs-unusual.md`: 49,332
- `knowledge/bidding/conventions/competitive/weak-jump-overcall.md`: 45,134,254,449,624,649
- `knowledge/bidding/conventions/competitive/western-cue-bid.md`: 42,200
- `knowledge/bidding/conventions/defensive-methods/twerb.md`: 49,349
- `knowledge/bidding/conventions/doubles/action-double.md`: 35,427
- `knowledge/bidding/conventions/doubles/dsi.md`: 33,34,178,268
- `knowledge/bidding/conventions/doubles/maximal-double.md`: 34,185
- `knowledge/bidding/conventions/doubles/optional-double.md`: 33,221
- `knowledge/bidding/conventions/doubles/re-opening-double.md`: 35,390,530
- `knowledge/bidding/conventions/doubles/responsive-double.md`: 38,399
- `knowledge/bidding/conventions/doubles/support-double.md`: 38,366
- `knowledge/bidding/conventions/doubles/take-out-double.md`: 37,172,468,645
- `knowledge/bidding/conventions/game-invitations/game-invitations.md`: 30,129
- `knowledge/bidding/conventions/game-invitations/help-suit-game-try.md`: 2889,2890
- `knowledge/bidding/conventions/game-invitations/invitations-index.md`: 37,188
- `knowledge/bidding/conventions/game-invitations/long-suit-game-try.md`: 46,1905,2840,2841
- `knowledge/bidding/conventions/game-invitations/two-way-game-try.md`: 47,862
- `knowledge/bidding/conventions/opening-bids/benjamin-two-bids.md`: 30,125
- `knowledge/bidding/conventions/opening-bids/ekren.md`: 38,488,560
- `knowledge/bidding/conventions/opening-bids/gambling-3nt.md`: 46,47,214,218,222,223,242,715,782
- `knowledge/bidding/conventions/opening-bids/muiderberg-two.md`: 39
- `knowledge/bidding/conventions/opening-bids/namyats.md`: 43,128,132,529
- `knowledge/bidding/conventions/opening-bids/roman-2-diamonds.md`: 38,103,281
- `knowledge/bidding/conventions/opening-bids/two-diamond-multi.md`: 35,119,282,475,506,569
- `knowledge/bidding/conventions/relay/relay-bidding.md`: 52,242
- `knowledge/bidding/conventions/responses/2nt-inquiry-over-weak-2.md`: 443
- `knowledge/bidding/conventions/responses/minor-suit-stayman.md`: 40,272
- `knowledge/bidding/conventions/responses/ogust.md`: 34,202
- `knowledge/bidding/conventions/responses/response-to-gambling-3nt.md`: 452
- `knowledge/bidding/conventions/responses/reverse-drury.md`: 358
- `knowledge/bidding/conventions/responses/soloway.md`: 45,158
- `knowledge/bidding/conventions/slam-conventions/asking-bid.md`: 47,201
- `knowledge/bidding/conventions/slam-conventions/control-bidding.md`: 29,301
- `knowledge/bidding/conventions/slam-conventions/cue-bidding.md`: 42,76
- `knowledge/bidding/conventions/slam-conventions/slam-bid-index.md`: 38,116,214
- `knowledge/bidding/natural-bids/opening-bids/1-club.md`: 44,82,567
- `knowledge/bidding/natural-bids/opening-bids/1-diamond.md`: 41,603
- `knowledge/bidding/natural-bids/opening-bids/1-heart.md`: 48,214,713
- `knowledge/bidding/natural-bids/opening-bids/1-spade.md`: 47,207,686
- `knowledge/bidding/natural-bids/opening-bids/2-clubs.md`: 49,50,103,211,214,218,222,226,568,601,602,628,645,729
- `knowledge/bidding/natural-bids/opening-bids/2nt-opening.md`: 55,148
- `knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md`: 39,134,497,511,558,624
- `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`: 39,99,119,321
- `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`: 33,34,66,146,186,188,200,202,206,214,262,320,476,477,579,580,613,630,631,665
- `knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md`: 38,133,499,546
- `knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md`: 40,130,545,594
- `knowledge/bidding/natural-bids/rebids/jump-rebids.md`: 34,76,260,287,291,324,381,473,518
- `knowledge/bidding/natural-bids/rebids/natural-rebids-index.md`: 70
- `knowledge/bidding/natural-bids/rebids/rebids-after-preempts.md`: 43,398,495,552
- `knowledge/bidding/natural-bids/rebids/reverse-bid.md`: 34,223,644
- `knowledge/bidding/natural-bids/responses/limit-raise.md`: 36,37,240,598
- `knowledge/bidding/natural-bids/responses/raising-partners-major.md`: 42,480
- `knowledge/bidding/natural-bids/responses/respond-preemptive-opening-in-3-level.md`: 41,43,123,137,509
- `knowledge/bidding/natural-bids/responses/responding-to-opening-bids.md`: 45,472
- `knowledge/bidding/natural-bids/responses/responding-with-unbalanced-hands.md`: 35,36,62,116,556
- `knowledge/bidding/natural-bids/responses/response-to-1-diamond.md`: 46,519
- `knowledge/bidding/natural-bids/responses/response-to-2-clubs.md`: 47,48,72,94,569,570
- `knowledge/bidding/natural-bids/responses/response-to-2nt.md`: 50,604
- `knowledge/bidding/natural-bids/responses/response-to-four-level-preempt.md`: 37,111,425,472,548
- `knowledge/bidding/natural-bids/responses/response-to-major-opening.md`: 56,626
- `knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md`: 39,115,420,467
- `knowledge/bidding/natural-bids/responses/response-to-weak-two.md`: 39,524,564
- `knowledge/bidding/principles/bidding-fundamentals/competitive-bidding-philosophy.md`: 27,199
- `knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md`: 27,198
- `knowledge/bidding/principles/bidding-fundamentals/kaplan-rubens-hand-evaluation.md`: 29,272
- `knowledge/bidding/principles/bidding-fundamentals/offensive-vs-defensive-values.md`: 30,31,116,134,203,218,228,276,289,298,299,312,320,340,341
- `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`: 2,3,30,41,45,47,54,75,79,91,101,111,121,131,162,167,182,187,202,208 (+15 more)
- `knowledge/bidding/principles/bidding-fundamentals/preemptive-openings.md`: 40,173,186,346,358,443,530
- `knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md`: 2,3,4,37,41,43,51,59,92,99,112,118,131,136,140,144,178,185,195,205 (+5 more)
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md`: 23,280
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md`: 24,328
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md`: 6,25,41,47,53,55,57,59,89,112,131,146,163,184
- `knowledge/bidding/principles/bidding-fundamentals/seat-position.md`: 29,30,253,322,323
- `knowledge/bidding/principles/bidding-fundamentals/vulnerability.md`: 31,32,211,361,362
- `knowledge/bidding/principles/principles-index.md`: 28,29,125,126
- `knowledge/bidding/systems/acol.md`: 85,229,369,3013,3774
- `knowledge/bidding/systems/benjamin-acol.md`: 40,56,82,95,150,211,213,217,243,291,302,332
- `knowledge/bidding/systems/culbertson.md`: 39,40,58,75,76,104,210,307,345,351
- `knowledge/bidding/systems/polish-club.md`: 80,3082,3873
- `knowledge/bidding/systems/sayc.md`: 89,219,226,1140
- `knowledge/bidding/systems/standard-american.md`: 68,151,173
- `knowledge/play/defence/opening-leads/leads-against-suit.md`: 25,188
- `knowledge/references/common-bridge-abbreviations.md`: 58,161
### opening families / equal suits

- `bridgelab-toolkit/archive/phase17/bridgelab_phase17a_bridge_intelligence_source_readiness_audit.json`: 593,603,610,620,644
- `bridgelab-toolkit/archive/phase17/bridgelab_phase17a_bridge_intelligence_source_readiness_audit.md`: 67,68,70
- `bridgelab-toolkit/benchmarks/declarer_play_adapter_integration.py`: 42
- `bridgelab-toolkit/benchmarks/end_to_end_analysis_architecture.py`: 58
- `bridgelab-toolkit/benchmarks/next_family_source_readiness_audit.py`: 78,80,96,97,195,196,210,281
- `bridgelab-toolkit/benchmarks/phase12_coverage_closure_audit.py`: 7,13,16
- `bridgelab-toolkit/benchmarks/phase13_coverage_closure_audit.py`: 77
- `bridgelab-toolkit/benchmarks/phase17_bridge_intelligence_source_readiness_audit.py`: 407,408,417,418,435
- `bridgelab-toolkit/benchmarks/phase28a_current_bidding_inventory.py`: 49,52,53
- `bridgelab-toolkit/benchmarks/responder_rebid_source_readiness_audit.py`: 212
- `bridgelab-toolkit/benchmarks/stayman_gamegoing_audit.py`: 264
- `bridgelab-toolkit/benchmarks/strong_two_club_balanced_rebid.py`: 1,110,111,117,134,155
- `bridgelab-toolkit/benchmarks/strong_two_club_rebid_residual_audit.py`: 1,120,222,252,253,269
- `bridgelab-toolkit/benchmarks/three_level_preempt_response_source_readiness_audit.py`: 1,118,135,234,235,236,237,238,259,261,262,288,289,300,351
- `bridgelab-toolkit/benchmarks/weak_two_response_source_readiness_audit.py`: 1,37,57,58,59,62,64,106
- `bridgelab-toolkit/bridge/abstention_analysis.py`: 39,40
- `bridgelab-toolkit/bridge/opening_abstention_root_cause_audit.py`: 20,112,119,120,123,124,125
- `bridgelab-toolkit/bridge/sayc.py`: 10,14,15,37,39,41,43,83,91,105,120,128,136,162,181,186,206,225,230,250 (+29 more)
- `bridgelab-toolkit/bridge/sayc_1d1s_opener_rebids.py`: 16
- `bridgelab-toolkit/bridge/sayc_responses.py`: 21
- `bridgelab-toolkit/bridge/sayc_strong_two_club.py`: 1,56,64
- `bridgelab-toolkit/bridge/two_over_one_balanced_rebids.py`: 1
- `bridgelab-toolkit/bridge/two_over_one_responses.py`: 21
- `bridgelab-toolkit/bridgelab_phase12e_1nt_stayman_gamegoing_audit.md`: 26
- `bridgelab-toolkit/bridgelab_phase12l_dual_major_downstream_coverage_audit.json`: 476,718,872
- `bridgelab-toolkit/bridgelab_phase12l_dual_major_downstream_coverage_audit.md`: 101,112
- `bridgelab-toolkit/bridgelab_phase12m_next_family_source_readiness_audit.json`: 185,189,223,227,289,446,484
- `bridgelab-toolkit/bridgelab_phase12m_next_family_source_readiness_audit.md`: 22,24,33,34,100,120,142,146
- `bridgelab-toolkit/bridgelab_phase12n_strong_2c_balanced_rebid.md`: 1,18,39
- `bridgelab-toolkit/bridgelab_phase12o_strong_2c_rebid_residual_audit.json`: 3,656
- `bridgelab-toolkit/bridgelab_phase12o_strong_2c_rebid_residual_audit.md`: 1,71
- `bridgelab-toolkit/bridgelab_phase12p_natural_1nt_response_source_readiness_audit.json`: 202,1502,2204
- `bridgelab-toolkit/bridgelab_phase12p_natural_1nt_response_source_readiness_audit.md`: 105,144
- `bridgelab-toolkit/bridgelab_phase12q_responder_rebid_source_readiness_audit.json`: 386,488,570,578,657,663,1306,1394,1416,1517,1518,1619,1722,2715,2871,2987,3061,6571,7143,8521 (+17 more)
- `bridgelab-toolkit/bridgelab_phase12q_responder_rebid_source_readiness_audit.md`: 161
- `bridgelab-toolkit/bridgelab_phase12r_three_level_preempt_response_source_readiness_audit.json`: 3,78,79,168,323,325,333,433,435,491,1555,2771,4329,5355,5735,6777,6802,6831,6871,6896 (+31 more)
- `bridgelab-toolkit/bridgelab_phase12r_three_level_preempt_response_source_readiness_audit.md`: 1,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46 (+8 more)
- `bridgelab-toolkit/bridgelab_phase12s_weak_two_response_source_readiness_audit.json`: 3,36,104,105,278,283,286,300,796,7192,10156,11599,14719,15148,15382,16552,17215,21519,21541,21563 (+21 more)
- `bridgelab-toolkit/bridgelab_phase12s_weak_two_response_source_readiness_audit.md`: 1,10,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43 (+1 more)
- `bridgelab-toolkit/bridgelab_phase12u_phase12_coverage_closure_audit.json`: 22,40,46,113,131
- `bridgelab-toolkit/bridgelab_phase12u_phase12_coverage_closure_audit.md`: 60,78,173,191,197
- `bridgelab-toolkit/bridgelab_phase13a_end_to_end_analysis_architecture.json`: 46
- `bridgelab-toolkit/bridgelab_phase13b_declarer_play_adapter_integration.json`: 71
- `bridgelab-toolkit/bridgelab_phase13l_phase13_coverage_closure_audit.json`: 75
- `bridgelab-toolkit/bridgelab_phase26b_system_profile_contract_design.md`: 116
- `bridgelab-toolkit/bridgelab_phase28a_current_bidding_inventory.json`: 299,314,319
- `bridgelab-toolkit/bridgelab_phase28a_current_bidding_inventory.md`: 56,59,60
- `bridgelab-toolkit/bridgelab_phase28b_final_bidding_coverage_closure_audit.json`: 34,58,66
- `bridgelab-toolkit/bridgelab_phase28b_final_bidding_coverage_closure_audit.md`: 27,30,31
- `bridgelab-toolkit/data/conventions.yaml`: 53
- `bridgelab-toolkit/metadata/category_normalization_batch3_3i.py`: 183,200
- `bridgelab-toolkit/metadata/category_normalization_batch3_3j.py`: 263,281
- `bridgelab-toolkit/metadata/category_normalization_batch3_3o.py`: 303,315,321,332
- `bridgelab-toolkit/tests/test_bridge_core_models.py`: 12,20
- `bridgelab-toolkit/tests/test_bridge_hand_evaluation.py`: 28,61,73,79,84,85
- `bridgelab-toolkit/tests/test_bridge_phase12m_next_family_source_readiness_audit.py`: 33,34
- `bridgelab-toolkit/tests/test_bridge_phase12o_strong_two_club_rebid_residual_audit.py`: 57
- `bridgelab-toolkit/tests/test_bridge_phase12r_three_level_preempt_response_source_readiness_audit.py`: 3,4,10,44,49,50,51,52,53,55,69,89
- `bridgelab-toolkit/tests/test_bridge_phase12s_weak_two_response_source_readiness_audit.py`: 2,3,8,37,51,63,74
- `bridgelab-toolkit/tests/test_bridge_phase13a_end_to_end_analysis_architecture.py`: 44,45
- `bridgelab-toolkit/tests/test_bridge_phase13b_declarer_play_adapter_integration.py`: 81,133
- `bridgelab-toolkit/tests/test_bridge_phase13l_phase13_coverage_closure_audit.py`: 27
- `bridgelab-toolkit/tests/test_bridge_phase29j_opening_abstention_root_cause.py`: 31,56,74,79
- `bridgelab-toolkit/tests/test_bridge_sayc_1c_responses.py`: 75
- `bridgelab-toolkit/tests/test_bridge_sayc_2nt_jacoby.py`: 27
- `bridgelab-toolkit/tests/test_bridge_sayc_openings.py`: 57,89,122,142,192
- `bridgelab-toolkit/tests/test_bridge_sayc_strong_two_club.py`: 13,17
- `bridgelab-toolkit/tests/test_bridge_sayc_weak_two_openings.py`: 6,7,8,10,11,12
- `bridgelab-toolkit/tests/test_bridge_stopper_evidence.py`: 23
- `bridgelab-toolkit/tests/test_bridge_two_over_one_responses.py`: 130
- `bridgelab-toolkit/tests/test_phase28b_final_bidding_coverage_closure_audit.py`: 44,48,52,55
- `knowledge/bidding/conventions/competitive/aspro.md`: 143,198,266,291
- `knowledge/bidding/conventions/competitive/balancing-double.md`: 742
- `knowledge/bidding/conventions/competitive/balancing-notrump.md`: 432
- `knowledge/bidding/conventions/competitive/brozel.md`: 155,183,201,219,237
- `knowledge/bidding/conventions/competitive/cappelletti.md`: 184,205,223,241
- `knowledge/bidding/conventions/competitive/dont.md`: 173,218,254
- `knowledge/bidding/conventions/competitive/equal-level-conversion-doubles.md`: 3
- `knowledge/bidding/conventions/competitive/fit-jump-shift.md`: 204
- `knowledge/bidding/conventions/competitive/ghestem.md`: 55,188,194,494
- `knowledge/bidding/conventions/competitive/hamilton.md`: 173,194,219,235
- `knowledge/bidding/conventions/competitive/landy.md`: 124,177,206,534
- `knowledge/bidding/conventions/competitive/leaping-michaels.md`: 4,43,49,51,55,56,57,75,97,214,258,268,285,297,307,316,333,350,354,367 (+3 more)
- `knowledge/bidding/conventions/competitive/meckwell.md`: 193,211,224,248
- `knowledge/bidding/conventions/competitive/michaels-cue-bid.md`: 59,107,134,177,183,476,501,543
- `knowledge/bidding/conventions/competitive/multi-landy.md`: 134,183,205,223
- `knowledge/bidding/conventions/competitive/responsive-cue-bid.md`: 217
- `knowledge/bidding/conventions/competitive/sandwich-nt.md`: 127,331,409
- `knowledge/bidding/conventions/competitive/scrambling-2nt.md`: 201
- `knowledge/bidding/conventions/competitive/top-and-bottom-cue-bid.md`: 244,421,480,548,670
- `knowledge/bidding/conventions/competitive/unusual-2nt.md`: 211,217,556,585
- `knowledge/bidding/conventions/competitive/unusual-vs-unusual.md`: 566
- `knowledge/bidding/conventions/competitive/weak-jump-overcall.md`: 522,524,627
- `knowledge/bidding/conventions/conventions-index.md`: 166,167
- `knowledge/bidding/conventions/defensive-methods/crash.md`: 398,548
- `knowledge/bidding/conventions/defensive-methods/defense-against-multi-2d.md`: 47,51,58,93,105,361,363,588,605,659,678
- `knowledge/bidding/conventions/defensive-methods/suction.md`: 203,399
- `knowledge/bidding/conventions/defensive-methods/twerb.md`: 76,263
- `knowledge/bidding/conventions/defensive-methods/woolsey-defense-to-multi.md`: 79,80,101,198,225,368,486,610,625,673
- `knowledge/bidding/conventions/doubles/negative-double.md`: 360,819
- `knowledge/bidding/conventions/game-invitations/help-suit-game-try.md`: 589
- `knowledge/bidding/conventions/game-invitations/long-suit-game-try.md`: 249
- `knowledge/bidding/conventions/game-invitations/short-suit-game-try.md`: 258
- `knowledge/bidding/conventions/opening-bids/benjamin-two-bids.md`: 56,68,96,102,133,149,150,186,212,258,281,284,324,334,381,389,398,404,405,431
- `knowledge/bidding/conventions/opening-bids/ekren.md`: 34,67,137,187,312,326,339,591
- `knowledge/bidding/conventions/opening-bids/flannery.md`: 37,63,294,510,544,550
- `knowledge/bidding/conventions/opening-bids/gambling-3nt.md`: 95
- `knowledge/bidding/conventions/opening-bids/index-opening-bids.md`: 33,127,133,149,250,274,275,276,371,372
- `knowledge/bidding/conventions/opening-bids/muiderberg-two.md`: 5,39,45,47,51,59,63,106,108,242,257,278,289,301,327,338,350,400,444
- `knowledge/bidding/conventions/opening-bids/namyats.md`: 39,546
- `knowledge/bidding/conventions/opening-bids/roman-2-diamonds.md`: 270,307,317
- `knowledge/bidding/conventions/opening-bids/two-diamond-multi.md`: 3,31,50,52,56,57,80,86,173,186,359,372,404,577,585
- `knowledge/bidding/conventions/relay/kokish-relay.md`: 3,61,71,657,673,679,700,706
- `knowledge/bidding/conventions/responses/2nt-inquiry-after-multi-two-diamond.md`: 53,80,81,131,132,133,134,243,255,360,441,450,452
- `knowledge/bidding/conventions/responses/2nt-inquiry-over-weak-2.md`: 2,3,44,49,53,67,376,410,426,427,437,438,459
- `knowledge/bidding/conventions/responses/checkback-stayman.md`: 124
- `knowledge/bidding/conventions/responses/feature-ask.md`: 3,5,18,33,50,103,581,588
- `knowledge/bidding/conventions/responses/five-card-stayman.md`: 4,49,55,57,60,102,130,132,204,216,218,265,273,295,326,354,376,384,395
- `knowledge/bidding/conventions/responses/inverted-minors.md`: 359,383,405
- `knowledge/bidding/conventions/responses/minor-suit-stayman.md`: 122
- `knowledge/bidding/conventions/responses/ogust.md`: 3,5,17,30,48,52,76,120,359,525,531
- `knowledge/bidding/conventions/responses/preemptive-raise.md`: 201
- `knowledge/bidding/conventions/responses/puppet-stayman.md`: 52,116,131,146,166,195,274,286,482
- `knowledge/bidding/conventions/responses/responding-to-multi-2diamond.md`: 58,59,386,397
- `knowledge/bidding/conventions/responses/response-to-gambling-3nt.md`: 449
- `knowledge/bidding/conventions/responses/responses-index.md`: 234,412
- `knowledge/bidding/conventions/responses/smolen.md`: 3,192,267,277,488,512,530,541
- `knowledge/bidding/conventions/responses/soloway.md`: 352
- `knowledge/bidding/conventions/responses/stayman.md`: 307
- `knowledge/bidding/conventions/responses/two-way-stayman.md`: 232
- `knowledge/bidding/conventions/responses/walsh.md`: 241
- `knowledge/bidding/conventions/slam-conventions/asking-bid.md`: 176
- `knowledge/bidding/conventions/transfers/jacoby-transfers.md`: 117,331,598
- `knowledge/bidding/conventions/transfers/texas-transfers.md`: 125,273
- `knowledge/bidding/natural-bids/opening-bids/1-club.md`: 150,457,473,525,531,592,593,594,611,679
- `knowledge/bidding/natural-bids/opening-bids/1-diamond.md`: 160,163,211,215,491,507,509,557,559,563,628,629,630,647,725
- `knowledge/bidding/natural-bids/opening-bids/1-heart.md`: 120,180,187,597,630,667,671,736,831
- `knowledge/bidding/natural-bids/opening-bids/1-spade.md`: 115,175,182,573,606,643,709,803
- `knowledge/bidding/natural-bids/opening-bids/1nt-opening.md`: 223,227,231,262,455,555,557
- `knowledge/bidding/natural-bids/opening-bids/2nt-opening.md`: 247,251,286,396,531,623,625
- `knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md`: 553,554,556,605
- `knowledge/bidding/natural-bids/opening-bids/natural-opening-bids-index.md`: 63,68,69,81,82
- `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`: 34,35,161,173,199,267,269,278,303,403,468,469,534,535,536,553,573,574,575
- `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`: 460,461,463,636,637
- `knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md`: 2,3,53,57,77,96,147,248,348,361,423,512,541,543,544,600,602,615,620
- `knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md`: 2,3,54,58,59,63,73,79,125,140,197,239,396,465,481,489,505,513,537,558 (+5 more)
- `knowledge/bidding/natural-bids/rebids/natural-rebids-index.md`: 55
- `knowledge/bidding/natural-bids/rebids/opener-after-1nt.md`: 216
- `knowledge/bidding/natural-bids/rebids/opener-after-2nt.md`: 236
- `knowledge/bidding/natural-bids/rebids/opener-after-major.md`: 375
- `knowledge/bidding/natural-bids/rebids/opener-after-minor.md`: 589
- `knowledge/bidding/natural-bids/rebids/opening-rebids.md`: 475
- `knowledge/bidding/natural-bids/rebids/rebids-after-preempts.md`: 3,40,65,66,109,111,225,227,427,531,543,544,546,547,579,612,624
- `knowledge/bidding/natural-bids/rebids/reverse-bid.md`: 127
- `knowledge/bidding/natural-bids/responses/natural-responses-index.md`: 40,41,83,84
- `knowledge/bidding/natural-bids/responses/raising-partners-minor.md`: 62
- `knowledge/bidding/natural-bids/responses/respond-preemptive-opening-in-3-level.md`: 3,39,58,365,561,582,583,594,597,620
- `knowledge/bidding/natural-bids/responses/responding-with-unbalanced-hands.md`: 99
- `knowledge/bidding/natural-bids/responses/response-to-1-diamond.md`: 87
- `knowledge/bidding/natural-bids/responses/response-to-2nt.md`: 324
- `knowledge/bidding/natural-bids/responses/response-to-four-level-preempt.md`: 466,467,468,469,529
- `knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md`: 2,3,37,50,54,78,85,271,406,447,460,461,463,520,522,535,542
- `knowledge/bidding/natural-bids/responses/response-to-weak-two.md`: 2,3,50,54,57,76,78,474,512,547,560,568,623,630
- `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`: 26,57,210,233,235,245,329,336
- `knowledge/bidding/principles/bidding-fundamentals/preemptive-openings.md`: 35,508,527
- `knowledge/bidding/principles/partnership/convention-cards.md`: 129
- `knowledge/bidding/principles/partnership/partnership-agreements.md`: 150
- `knowledge/bidding/systems/2-over-1.md`: 332,2718,2828,2956,3089,3141
- `knowledge/bidding/systems/acol.md`: 114,116,178,315,316,442,459,501,513,525,537,560,587,601,648,649,650,693,1150,1162 (+25 more)
- `knowledge/bidding/systems/benjamin-acol.md`: 5,39,52,58,60,69,84,85,171,179,187,219,283,293,339,345
- `knowledge/bidding/systems/blue-club.md`: 133
- `knowledge/bidding/systems/carrot-club.md`: 71,92,93,94,177,181,190,302,323,324,325,326,332,335,350
- `knowledge/bidding/systems/chinese-precision.md`: 76,96,97,98,221,338,339,340,341,349,352,365
- `knowledge/bidding/systems/culbertson.md`: 182,296,325,326
- `knowledge/bidding/systems/ehaa.md`: 82,102,103,104,206,310,312,313,314,326,330,344
- `knowledge/bidding/systems/kaplan-sheinwold.md`: 6,65,100,113,161,289,313,314,315,342
- `knowledge/bidding/systems/magic-diamond.md`: 5,59,70,90,91,92,180,294,295,296,297,298,310,315,327
- `knowledge/bidding/systems/moscito.md`: 6,60,69,89,90,91,225,359,361,362,363,376,379,392
- `knowledge/bidding/systems/neapolitan-club.md`: 309,310,311
- `knowledge/bidding/systems/polish-club.md`: 181,292,323,368,369,370,398,651,652,653,666,712,1065,1069,2865,2881,2945,2949,2972,2976 (+7 more)
- `knowledge/bidding/systems/precision.md`: 298,299,300,467,757,758,759,1240,2874,3336
- `knowledge/bidding/systems/roman-club.md`: 319,320
- `knowledge/bidding/systems/roman-precision.md`: 72,92,93,94,237,241,242,243,349,350,351,352,353,366,369
- `knowledge/bidding/systems/roth-stone.md`: 5,58,60,68,70,77,158,200,299,318,326,328,329,330,336,342,355
- `knowledge/bidding/systems/sayc.md`: 3,184,186,203,204,205,267,287,289,291,369,541,549,550,587,1130,1164,1873,2454,2596 (+13 more)
- `knowledge/bidding/systems/sef.md`: 66,73,94,95,156,187,315,316,317,318,319,331,348
- `knowledge/bidding/systems/standard-american.md`: 127,231,239,268,434,668,669,696
- `knowledge/bidding/systems/super-precision.md`: 75,95,96,97,244,248,249,250,359,360,361,362,376,379
- `knowledge/bidding/systems/ultimate-club.md`: 6,61,72,92,93,94,229,233,234,235,339,340,341,342,356,359,372
- `knowledge/bidding/systems/wspolny-jezyk.md`: 70,77,97,98,99,193,327,328,329,330,331,343,347,360
- `knowledge/play/counting/counting-declarer.md`: 112
- `knowledge/play/counting/counting-distribution.md`: 126
- `knowledge/play/counting/counting-points.md`: 67
- `knowledge/references/bridge-glossary.md`: 545

### Inspected evidence paths (SHA-256)

- `bridgelab-toolkit/bridge/auction.py`: `586783b201e02cbf79a563fcf3569a3d816522204d742946f4a552eac706b3fe`
- `bridgelab-toolkit/bridge/opening_abstention_root_cause_audit.py`: `a7e4d249355e4557505250667a5486168352c9b74576dc5e90c27dee2ba64fde`
- `bridgelab-toolkit/bridge/opening_pass_policy_audit.py`: `3e682796a5e2ef8ddc8d3cdc9259aeba848a03d288c1b076c9bcb0aa63f19a8e`
- `bridgelab-toolkit/bridge/sayc.py`: `60c3fa00ea1657def24bc682abc4668b1501496107401dee46393eae4f17ce91`
- `bridgelab-toolkit/bridge/source_authority.py`: `e47b09319a9aff65f538bec09c112a6d43544c6bc7043c4d19d9cef9a3be42b3`
- `bridgelab-toolkit/bridgelab_phase25_source_authority_closure_record.md`: `a673bfbf48bb610fffee708ba1e9671d02a5398a0145692c7f284e355a89e523`
- `bridgelab-toolkit/tests/test_bridge_phase29k_opening_pass_policy_audit.py`: `2c59172f973e0ca36ec9b4cb297d40d869646aa9d4842918afcddd91d58694ef`
- `bridgelab-toolkit/tests/test_bridge_sayc_openings.py`: `0d8b2cab93ea777a5400cb9cc381f56df9305bd788e124d0cf3b09f7840b3608`
- `bridgelab-toolkit/tests/test_bridge_sayc_three_level_preempts.py`: `2ec8d34be66e8302873438c05376a78634089ce27ecfa2e6ba9a923c635bdfd7`
- `bridgelab-toolkit/tests/test_bridge_sayc_weak_two_openings.py`: `6e27b8fb0db26b10ceeda3d6cd4bb220bc00290458a8c505e722ccbf51f27ea7`
- `knowledge/bibliography.md`: `2ab618a4f289b373da62a160b8a6e44a20c374122884add84e91c66334633882`
- `knowledge/bidding/convention-cards/cc-nily-nisim.md`: `3cb42ddaea04706365637a05e3217be6682971f27fafc6aa96c5ca8381d4ebca`
- `knowledge/bidding/natural-bids/opening-bids/1-club.md`: `d104424bb70cd9a7ab19764dfd28185a86211ac99ec94037b9ea7a5de5ae3bf6`
- `knowledge/bidding/natural-bids/opening-bids/1-diamond.md`: `7643ae1859216d594447055a0ac618dff420471b9c54f3a8ea884e1b3d14b7c3`
- `knowledge/bidding/natural-bids/opening-bids/1-heart.md`: `902b4306ee8c53d5b05d8caa9960f33555cbfd12b5f38dc815589ea3874398c0`
- `knowledge/bidding/natural-bids/opening-bids/1-spade.md`: `586b230df54fdcf481f3b8bc2278c4fefee3000d7c145e47f8b8b665c08b955d`
- `knowledge/bidding/natural-bids/opening-bids/1nt-opening.md`: `c21566ca6232648beee09b019596498c48fb5cbe80ae93a9971586eb7cb81ede`
- `knowledge/bidding/natural-bids/opening-bids/2-clubs.md`: `7f2fb2c10310997e307b386e99d3b15e55dee5d71b6e23b6a5af24a5a99ff39b`
- `knowledge/bidding/natural-bids/opening-bids/2nt-opening.md`: `9362055bec96b13c94f13cf5131029ab95a0d38ac2dde9d5092586a162f801fd`
- `knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md`: `c59b0e917ae62768a05f2c7e4d0732980451423e66ff5ee97e751715ca04c578`
- `knowledge/bidding/natural-bids/opening-bids/opening-bids-overview.md`: `8b1cad250cd2e5a8763620faf91dd4e9a834a40fbe1066d1d01d59c7d539b08e`
- `knowledge/bidding/natural-bids/opening-bids/opening-requirements.md`: `7ef4a85b612129102d0b728a65202ce998b938d0c7668d9f6ae0a16dfe1dc196`
- `knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md`: `1734b40a47d9444131c842586e3e11744b49412a82d56708df21c7bfb47002a9`
- `knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md`: `e3c55c09e66aa791cefc982e39b3bb990313d3442127792d7d8321a6bf3b6fdc`
- `knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md`: `5589de93969874f2cd71a48fc736d10348188925a6f8e90b4668024296c069fc`
- `knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`: `d1644dc9e0307c4fe34e7c1c448a73fbc20b1caae2abd197ca04d374bba75af5`
- `knowledge/bidding/principles/bidding-fundamentals/preemptive-openings.md`: `59395458d8abaec9d7db071858ba60c9e360d9b327c99862bde317c5d2c6402c`
- `knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md`: `9b743c2c92fb09d1b7c9afdb687d26885e2d9544b94d23ee3541b9f28d50add5`
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md`: `69612bfe28ffffd133c4f803bd0a5c0c75da6bef74838fe5374534fd5efbd667`
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md`: `8ab42b0e2b89d0ee6d62109d4b4319039190601ad53afb4165a6f2ef7c630bf4`
- `knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md`: `a757ba5e13bad5d4e2fa961c5e747054b8a0eb8bcf95accc665cf908ed4dd779`
- `knowledge/bidding/principles/bidding-fundamentals/seat-position.md`: `6fce3a3a6b1448efa37ecde71074896b39fa2bf22b1eb39a231e8deb03cea3e9`
- `knowledge/bidding/principles/bidding-fundamentals/vulnerability.md`: `8a21cce0a37cf1ce5bb1564500b2d0f691d70d8dafc052d2e989b1bb42f68412`
- `knowledge/bidding/systems/sayc.md`: `99ed2523aa725470e2f5c02d64a381cc65cfb41e6bed9e29051d61709316474c`
- `knowledge/bidding/systems/standard-american.md`: `c6cd6ca5bbe6df19db7a266675b1b98f8edb85857f3c68a16aa97a933ba37740`
