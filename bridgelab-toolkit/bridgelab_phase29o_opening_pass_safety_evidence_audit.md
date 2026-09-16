# Phase 29O — Opening Pass safety evidence resolution

**447 candidates: SAFE 0; UNSAFE 0; UNKNOWN 447. Production Pass readiness: NO.**

PASS != FALLBACK_FOR_ABSTAIN. This audit resolves what the missing evidence consists of; it does not invent the missing bridge policy. No web research, production implementation, full regression, commit or push.

## A. Baseline verification

- Project: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit`
- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`
- Branch `codex/phase18b`.
- Local HEAD, live remote HEAD and remote-tracking HEAD: `dadc425bfac59bf5e217c756a73373abac9a2097`.
- Ahead/behind `0/0`; initial working tree clean. Known `.pytest_cache` permission warnings only.
- Supplied regression baseline 2162 passed, 143 subtests passed; not rerun.

## B. Files inspected and methodology

Reused the Phase29N report builder, which already invokes canonical Phase29I/J/K/H audit/reproduction checks. Each of the 616 depth-0 cases is evaluated from its recorded canonical Hand with its actual dealer, vulnerability and the simulator's explicit SAYC system. The new report retains full evidence records for all 447 insufficient cases, plus bounded representatives of other groups. No Deal objects are retained. Canonical HCP, lengths, shapes, Rule20, Auction and vulnerability methods are reused.

Required inputs inspected/reused: `bridge/opening_pass_positive_predicate_audit.py`, `nisim_nily_opening_policy.py`, `opening_pass_source_policy_audit.py`, `opening_pass_policy_audit.py`, `opening_abstention_root_cause_audit.py`, `full_auction_abstention_audit.py`, `full_auction_coverage.py`, `deal_simulator.py`, and the Phase29L/M/N Markdown reports. Also inspected `bridge/sayc.py`, `evaluation.py`, `models.py`, `bidding_rules.py`, `system_profiles.py` and route configuration. Existing Phase29J–N tests were run.

Repository search: `rg -n -i 'playing.?trick|quick.?trick'` across toolkit Python files, followed by opening/evaluation inspections. Matches were notes/audits, metadata maintenance, tests and the explicit unevaluated strong2C message; no usable canonical PT/QT evaluator was found. Controls (A=2, K=1), suit-quality facts, double-dummy/declarer analysis and HCP are not substituted for a partnership opening playing-trick metric.

Knowledge reviewed: SAYC; opening-requirements; 1NT; strong 2C; weak-two/three-level/four-level preempt articles; Rule20; Rule22; playing-tricks; quick-tricks; seat-position; vulnerability; and the nily–nisim convention card. Evidence identifiers appear in the exception and gap matrices. The convention card is 2/1, not the production SAYC profile; it does not silently supply this Pass policy. No applicable AGENTS.md found in the inspected target paths.

## C. Files added

- `bridge/opening_pass_safety_evidence_audit.py`
- `tests/test_bridge_phase29o_opening_pass_safety_evidence_audit.py`
- `bridgelab_phase29o_opening_pass_safety_evidence_audit.md`
- `bridgelab_phase29o_opening_pass_safety_evidence_audit.json`

## D. Files modified

None. Existing production, profile, source and Phase29J–N files unchanged.

## E. Safety evidence model

Immutable typed SAFE / UNSAFE / UNKNOWN evidence carries authority, source identifiers and an explanation for each dimension. SAFE means the required affirmative safety contract is satisfied, UNSAFE means a known positive opening/approved strength predicate applies, UNKNOWN means exclusion cannot be proved. UNKNOWN is not UNSAFE. Overall UNSAFE takes precedence if a known hazard applies; otherwise every required dimension must be SAFE. Missing/duplicate/incomplete evidence cannot satisfy the all-safe conjunction.

Known existing opening recommendations are observed by reusing the unchanged SAYC opening engine, not duplicating its rules. Failed rules supply no SAFE evidence. Approved 12+ strength and 11-HCP Rule20 strength are separately explicit barriers to this ordinary <=10 Pass design; they do not select an arbitrary call. A <=10 Rule20 score>=20 is a protected potential opening, not an approved positive OPEN verdict. The module creates no Pass RuleDecision or router.

Authority distinction: CANONICAL_PRODUCTION_REFERENCE describes existing repository provenance; it does not authenticate external bridge correctness. Explicit Phase29M partnership choices remain NISIM_NILY_PARTNERSHIP_POLICY. Qualified notes remain supported references. The source-authority registry is not modified.

## F. Playing-trick findings

No canonical playing-trick evaluator and no canonical quick-trick evaluator were located. Neither is used by production openings. The current evaluator supplies HCP, controls, shape and honor/quality facts only. `sayc.py` implements strong2C at HCP>=22 and explicitly says the 9+ playing-trick alternative is not evaluated.

`knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md` defines expected declarer tricks with little/no partner help under suitable fit/contract assumptions, explicitly says there is no universally accepted formula, and supplies approximate examples. That is not a complete deterministic estimator or upper-bound theorem. `quick-tricks.md` supplies AK=2, AQ=1.5, A=1, KQ=1, K=0.5 tables; quick tricks are not playing tricks. Rule22 incorporates QT but is explicitly unadopted. None proves an ordinary low-HCP hand lies outside every protected strong-opening domain.

The strong2C mapping '22+ OR 9+ playing tricks' is conceptually present in the repository, but the alternative's measurement/assumptions/exclusion predicate lack authenticated complete support. This is a source gap plus a partnership treatment gap, not merely an engine-helper task. Do not write a formula to make UNKNOWN disappear. Below-22 HCP excludes only the HCP branch, not the alternative.

## G. Exception-policy findings

For the 447, existing evidence affirmatively establishes the bounded HCP/length/Rule20/equal-suit exclusions recorded per case. Thus normal >=12 strength, the approved 11-HCP screen, the current >=22 branch, ordinary six/seven/eight-plus domains, 6-6/7-6 overlaps and equal>=5 selectors can be excluded within their stated scopes. These are scoped exclusions, not proof that all possible exceptions are covered.

Residual exception UNKNOWN is concrete: control-rich light openings; excellent suit/honor texture; unusual distribution upgrades; unresolved optional opening/NT adjustment rules; and lack of an adopted closed exception set. `opening-requirements#Controls` allows lighter openings qualitatively. `rule-of-20#Exceptions` allows opening below20 for controls/excellent six-card suits and passing above20 for poor placement/suits. Six-card shapes are absent from the 447, but controls/quality guidance has no threshold or approved exclusion. Strong playing tricks and context are separated into their own dimensions rather than counted as extra primary populations.

### Audit exception registry

YES/NO predicate availability is limited to the scope column. A known shape-exclusion predicate does not mean the bid selector inside that shape is resolved. This registry inventories located material; it is not declared exhaustive partnership policy.

| ID / name | Authority | Positive predicate? | Exclusion? | Production? | Pass relevant? | Scope and evidence |
|---|---|---|---|---|---|---|
| normal-strength: 12+ normal strength | NISIM_NILY_PARTNERSHIP_POLICY | YES | YES | YES | YES | Strength only; production covers family subsets, not arbitrary calls. Sources: bridge/nisim_nily_opening_policy.py#strength-12, bridge/nisim_nily_opening_policy.py#strength-13-plus. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| rule20-11: 11-HCP Rule20 screen | NISIM_NILY_PARTNERSHIP_POLICY | YES | YES | NO | YES | 11 HCP and score>=20; helper exists, call-family integration absent. Sources: bridge/nisim_nily_opening_policy.py#strength-11, knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| rule20-low: Low-HCP Rule20 qualification | SUPPORTED_REFERENCE | YES | YES | NO | YES | Arithmetic exists; <=10 opening entitlement NOT approved. Sources: bridge/nisim_nily_opening_policy.py#strength-10-or-less, knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md#Exceptions. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| strong-hcp: Strong 2C HCP branch | CANONICAL_PRODUCTION_REFERENCE | YES | YES | YES | YES | HCP>=22 only; does not exclude playing-trick alternative. Sources: knowledge/bidding/systems/sayc.md#Strong 2♣ Opening, bridge/sayc.py. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| strong-playing: Strong 2C playing-trick alternative | SOURCE_INSUFFICIENT | NO | NO | NO | YES | 9+ playing-trick concept; no complete evaluator or safe upper bound. Sources: knowledge/bidding/systems/sayc.md#Strong 2♣ Opening, knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| weak-two: Controlled weak twos | CANONICAL_PRODUCTION_REFERENCE | YES | YES | YES | YES | Current exact-six 6-10 subset only; <=5 excludes this length domain. Sources: knowledge/bidding/systems/sayc.md#Weak Two Openings, bridge/sayc.py. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| preempt-three: Controlled three-level preempts | CANONICAL_PRODUCTION_REFERENCE | YES | YES | YES | YES | Current exact-seven 6-10 subset only; <=5 excludes ordinary length domain. Sources: knowledge/bidding/systems/sayc.md#Three-Level Openings, bridge/sayc.py. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| preempt-variants: Long-suit and competing-suit variants | SUPPORTED_REFERENCE | NO | YES | NO | YES | <=5 excludes six/seven/eight-plus shapes and 6-6/7-6 overlap only; does not decide bids within them. Sources: knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md, knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md, knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| equal-majors: Exactly 5S-5H preference 1S | NISIM_NILY_PARTNERSHIP_POLICY | YES | YES | NO | YES | Preference conditional on opening eligibility; no extension to 6-6. Sources: bridge/nisim_nily_opening_policy.py#equal-five-card-majors. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| equal-minors: Unresolved equal 5-5/6-6 minors | UNRESOLVED | NO | YES | NO | YES | Shape membership/exclusion known; selector missing; 3-3/4-4 already defined. Sources: bridge/nisim_nily_opening_policy.py#equal-minors-5-5, knowledge/bidding/systems/sayc.md#Better Minor. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| controls-distribution: Controls, suit quality, distribution upgrades | SUPPORTED_REFERENCE | NO | NO | NO | YES | Qualitative lighter-opening exceptions; no closed exclusion contract. Sources: knowledge/bidding/natural-bids/opening-bids/opening-requirements.md#Controls, knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md#Exceptions. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| nt-adjustments: Optional NT shapes and strength adjustments | SUPPORTED_REFERENCE | NO | NO | NO | YES | Canonical NT subset exists; optional 5422/upgrades/five-card-major choices unadopted. Sources: knowledge/bidding/natural-bids/opening-bids/1nt-opening.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| seat-style: Seat/passed-hand opening style | SUPPORTED_REFERENCE | NO | NO | NO | YES | First/second sound; third light; fourth Rule15; no approved partnership application. Sources: knowledge/bidding/principles/bidding-fundamentals/seat-position.md, knowledge/bidding/principles/bidding-fundamentals/rule-of-15.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| vulnerability-style: Vulnerability opening/preempt style | SUPPORTED_REFERENCE | NO | NO | NO | YES | Aggressiveness differs by vulnerability; no exact adopted thresholds. Sources: knowledge/bidding/principles/bidding-fundamentals/vulnerability.md. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| system-options: Partnership activation and optional treatments | PROJECT_CONTRACT | NO | NO | NO | YES | SystemContext facts exist; generic SAYC does not imply nisim-nily activation. Sources: bridge/system_profiles.py, bridge/bidding_rules.py, bridge/nisim_nily_opening_policy.py. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |
| rule22: Rule22 / quick-trick guidance | SUPPORTED_REFERENCE | NO | NO | NO | YES | Not adopted; not an independent required Pass gate or substitute for playing tricks. Sources: knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md, knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md, bridge/nisim_nily_opening_policy.py#rule22. Unproved relevant exclusion remains UNKNOWN; no fallback Pass. |

## H. Context findings

The source distinguishes opening position (first/second/third/fourth) from compass seat (N/E/S/W). The entire 447-case subset is dealer-first-seat, empty auction, actor not previously passed, explicit simulator SystemContext('SAYC') with empty options. These facts can be established; they were not missing data in Phase29N. Later-seat and passed-hand questions are out of this particular population, but matter if a future rule's scope expands.

The seat-position source describes disciplined first/second openings, lighter tactical third-seat openings and fourth-seat Rule15. The vulnerability source describes more aggressive favorable and more disciplined unfavorable style. Dedicated Rule20/22 sources restrict first/second seat, whereas the generic Standard American fourth-seat discussion lists them too (Phase29L discrepancy). No complete approved nisim–nily seat/vulnerability Pass contract resolves these choices.

Production SAYC opening gates use system identity and an unopened auction; the current opening predicates do not vary their thresholds by seat or vulnerability. That implementation omission is not partnership approval that context is irrelevant. SystemContext options are explicit opaque facts, system profiles separate SAYC from 2/1, and no nisim–nily activation option exists. Empty options mean no selected options, not an approved assertion that every contextual exception is absent.

Relative vulnerability is computed with canonical `Vulnerability.is_vulnerable` for actor and opponent, not inferred from labels alone:

- equal-nonvulnerable: 102
- equal-vulnerable: 111
- favorable: 234

The deterministic dealer/vulnerability cycles may correlate these contexts; this sample does not independently validate all seat/vulnerability combinations. Known context facts therefore refine the diagnosis without changing CONTEXT_SAFETY from UNKNOWN.

## I. Additional independent dimension

POSITIVE_PASS_POLICY: even complete exclusions would still require an affirmative approved Pass domain. Phase29M explicitly records positive-pass INCOMPLETE; Phase29N G is a proposal to audit, not production approval. This approval gap is distinct from the substance of exception or context predicates. All 447 remain UNKNOWN on it. Quick-trick policy is not added as a mandatory independent gate because Rule22 is unadopted. No extra speculative safety dimensions are introduced.

## J. 447-case decomposition

Each of the 447 JSON records contains canonical HCP/SHDC lengths/shape/Rule20, previous classification, actual context, all evidence dimensions, positive hazard list, scoped exclusions and overall result. All 447 have no positive hazard located; that absence is not used to infer SAFE.

| Dimension | SAFE | UNSAFE | UNKNOWN |
|---|---:|---:|---:|
| PLAYING_TRICK_SAFETY | 0 | 0 | 447 |
| EXCEPTION_POLICY_SAFETY | 0 | 0 | 447 |
| CONTEXT_SAFETY | 0 | 0 | 447 |
| POSITIVE_PASS_POLICY | 0 | 0 | 447 |

Intersections of the original three dimensions (mutually exclusive; fourth dimension also UNKNOWN for every case):

| UNKNOWN dimensions | Count |
|---|---:|
| NONE_UNKNOWN | 0 |
| PLAYING_TRICK_SAFETY | 0 |
| EXCEPTION_POLICY_SAFETY | 0 |
| PLAYING_TRICK_SAFETY+EXCEPTION_POLICY_SAFETY | 0 |
| CONTEXT_SAFETY | 0 |
| PLAYING_TRICK_SAFETY+CONTEXT_SAFETY | 0 |
| EXCEPTION_POLICY_SAFETY+CONTEXT_SAFETY | 0 |
| PLAYING_TRICK_SAFETY+EXCEPTION_POLICY_SAFETY+CONTEXT_SAFETY | 447 |

Only playing-trick unknown=0; only exception unknown=0; only context unknown=0; exactly two unknown=0; all three unknown=447; all required dimensions safe=0. All three original dimensions tie as blockers of 447 cases. No single decision alone unlocks any safe candidate because the other independent gaps remain.

## K. 616-case reconciliation

1000 deals; 616 depth-0 opening abstentions; zero simulation or canonical reproduction errors. Historical categories remain unchanged:

| Phase29N category | Count |
|---|---:|
| KNOWN_OPENING_COVERAGE_BOUNDARY | 3 |
| RULE20_POTENTIAL_OPENING | 46 |
| PROTECTED_STRONG_2C_DOMAIN | 0 |
| PROTECTED_PREEMPT_DOMAIN | 51 |
| PROTECTED_EQUAL_SUIT_DOMAIN | 11 |
| OTHER_PROTECTED_UNRESOLVED | 58 |
| SAFE_ORDINARY_PASS_CANDIDATE | 0 |
| SOURCE_OR_POLICY_INSUFFICIENT | 447 |

46 Rule20 +3 known boundaries +120 protected +447 insufficient +0 safe=616. The new tri-state analysis of the whole 616 yields SAFE=0, UNSAFE=45 and UNKNOWN=571: the three known opening-strength boundaries plus 42 approved 11-HCP strength qualifiers are unsafe for ordinary Pass. The other four low-HCP Rule20 qualifiers remain UNKNOWN, not invented approved openings. These overall counts are distinct from the target 447-subset counts below.

## L. Rule20 42 ->46

Phase29M counted only 11-HCP Rule20 qualifiers (42). Phase29N explicitly computes Rule20 at lower HCP too: four additional qualifiers, three from the old 65 protected and one from the old 506 insufficient. Therefore 42+3+1=46. Primary Rule20 precedence retains secondary distribution flags, without double-counting. Expected scope refinement, not a bug or new opening approval.

## M. Protected unresolved 65 ->120

Three low-HCP qualifiers leave the old protected bucket for Rule20, leaving 62 (51 long-suit and 11 equal-suit). Fifty-eight 11-HCP hands that fail Rule20 leave the old insufficient bucket for OTHER_PROTECTED_UNRESOLVED, since failed Rule20 is not Pass and the proposed ordinary domain is <=10. Thus 65-3+58=120. This is taxonomy/precedence refinement, not 55 newly discovered unsafe hands and not extra safety dimensions counted repeatedly.

| Phase29M category | Phase29N category | Count |
|---|---|---:|
| KNOWN_OPENING_COVERAGE_BOUNDARY | KNOWN_OPENING_COVERAGE_BOUNDARY | 3 |
| PROTECTED_UNRESOLVED | PROTECTED_EQUAL_SUIT_DOMAIN | 11 |
| PROTECTED_UNRESOLVED | PROTECTED_PREEMPT_DOMAIN | 51 |
| PROTECTED_UNRESOLVED | RULE20_POTENTIAL_OPENING | 3 |
| RULE20_POTENTIAL_OPENING | RULE20_POTENTIAL_OPENING | 42 |
| SOURCE_OR_POLICY_INSUFFICIENT | OTHER_PROTECTED_UNRESOLVED | 58 |
| SOURCE_OR_POLICY_INSUFFICIENT | RULE20_POTENTIAL_OPENING | 1 |
| SOURCE_OR_POLICY_INSUFFICIENT | SOURCE_OR_POLICY_INSUFFICIENT | 447 |

The old insufficient 506 becomes 1 Rule20 +58 protected eleven-HCP +447 insufficient. All original populations and transition sums reconcile exactly; regression tests assert these definitions.

## N. All dimensions SAFE

0 of 447 (0%). No new supported Pass candidate.

## O. Still UNKNOWN

447 of 447 (100%). UNKNOWN is retained, not relabeled UNSAFE.

## P. Positively UNSAFE

0 of the 447. Separately, 45 of the complete 616 have explicit normal/approved borderline opening-strength evidence barring ordinary Pass. This does not create a call or override unresolved suit-family selection.

## Q. Bounded representatives

### all-safe

None.
### PLAYING_TRICK_SAFETY-UNKNOWN

- Deal 1: `J987.962.94.J943`; HCP=2, SHDC=(4, 3, 2, 4), shape=balanced, Rule20=10; dealer/actor=E/E, position=1, vulnerability=NS (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 2: `974.KQT93.53.964`; HCP=5, SHDC=(3, 5, 2, 3), shape=balanced, Rule20=13; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 4: `854.A9853.J74.K4`; HCP=8, SHDC=(3, 5, 3, 2), shape=balanced, Rule20=16; dealer/actor=N/N, position=1, vulnerability=None (equal-nonvulnerable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
### EXCEPTION_POLICY_SAFETY-UNKNOWN

- Deal 1: `J987.962.94.J943`; HCP=2, SHDC=(4, 3, 2, 4), shape=balanced, Rule20=10; dealer/actor=E/E, position=1, vulnerability=NS (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 2: `974.KQT93.53.964`; HCP=5, SHDC=(3, 5, 2, 3), shape=balanced, Rule20=13; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 4: `854.A9853.J74.K4`; HCP=8, SHDC=(3, 5, 3, 2), shape=balanced, Rule20=16; dealer/actor=N/N, position=1, vulnerability=None (equal-nonvulnerable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
### CONTEXT_SAFETY-UNKNOWN

- Deal 1: `J987.962.94.J943`; HCP=2, SHDC=(4, 3, 2, 4), shape=balanced, Rule20=10; dealer/actor=E/E, position=1, vulnerability=NS (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 2: `974.KQT93.53.964`; HCP=5, SHDC=(3, 5, 2, 3), shape=balanced, Rule20=13; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 4: `854.A9853.J74.K4`; HCP=8, SHDC=(3, 5, 3, 2), shape=balanced, Rule20=16; dealer/actor=N/N, position=1, vulnerability=None (equal-nonvulnerable); previous=SOURCE_OR_POLICY_INSUFFICIENT; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
### positive-unsafe

- Deal 3: `KJT9874.A5.K2.96`; HCP=11, SHDC=(7, 2, 2, 2), shape=unbalanced, Rule20=20; dealer/actor=W/W, position=1, vulnerability=Both (equal-vulnerable); previous=RULE20_POTENTIAL_OPENING; overall=UNSAFE. Positive hazards: approved-11-hcp-rule20-strength-screen. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 42: `AKJ954.QJ65.42.5`; HCP=11, SHDC=(6, 4, 2, 1), shape=unbalanced, Rule20=21; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=RULE20_POTENTIAL_OPENING; overall=UNSAFE. Positive hazards: approved-11-hcp-rule20-strength-screen. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 57: `AJ543.AQJ63.74.2`; HCP=12, SHDC=(5, 5, 2, 1), shape=unbalanced, Rule20=22; dealer/actor=E/E, position=1, vulnerability=NS (favorable); previous=KNOWN_OPENING_COVERAGE_BOUNDARY; overall=UNSAFE. Positive hazards: approved-normal-opening-strength. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
### RULE20_POTENTIAL_OPENING

- Deal 3: `KJT9874.A5.K2.96`; HCP=11, SHDC=(7, 2, 2, 2), shape=unbalanced, Rule20=20; dealer/actor=W/W, position=1, vulnerability=Both (equal-vulnerable); previous=RULE20_POTENTIAL_OPENING; overall=UNSAFE. Positive hazards: approved-11-hcp-rule20-strength-screen. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 42: `AKJ954.QJ65.42.5`; HCP=11, SHDC=(6, 4, 2, 1), shape=unbalanced, Rule20=21; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=RULE20_POTENTIAL_OPENING; overall=UNSAFE. Positive hazards: approved-11-hcp-rule20-strength-screen. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 66: `K962.K6.KT.QT987`; HCP=11, SHDC=(4, 2, 2, 5), shape=semi-balanced, Rule20=20; dealer/actor=S/S, position=1, vulnerability=EW (favorable); previous=RULE20_POTENTIAL_OPENING; overall=UNSAFE. Positive hazards: approved-11-hcp-rule20-strength-screen. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNSAFE, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
### PROTECTED_PREEMPT_DOMAIN

- Deal 36: `4.T6.QT98732.K98`; HCP=5, SHDC=(1, 2, 7, 3), shape=unbalanced, Rule20=15; dealer/actor=N/N, position=1, vulnerability=None (equal-nonvulnerable); previous=PROTECTED_PREEMPT_DOMAIN; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 43: `85.Q72.43.KJT743`; HCP=6, SHDC=(2, 3, 2, 6), shape=semi-balanced, Rule20=15; dealer/actor=W/W, position=1, vulnerability=Both (equal-vulnerable); previous=PROTECTED_PREEMPT_DOMAIN; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.
- Deal 65: `43.JT8.QJ8652.87`; HCP=4, SHDC=(2, 3, 6, 2), shape=semi-balanced, Rule20=13; dealer/actor=E/E, position=1, vulnerability=NS (favorable); previous=PROTECTED_PREEMPT_DOMAIN; overall=UNKNOWN. Positive hazards: none established. Dimensions: PLAYING_TRICK_SAFETY=UNKNOWN, EXCEPTION_POLICY_SAFETY=UNKNOWN, CONTEXT_SAFETY=UNKNOWN, POSITIVE_PASS_POLICY=UNKNOWN.

Each representative group is bounded at three. Repeated examples across UNKNOWN dimensions intentionally show their intersection. All 447 assessment records are retained separately to meet the per-case audit requirement; no full Deal retained.

## R. Machine-readable gap matrix

Resolution types distinguish authoritative-source, partnership-decision, engine-helper and already-resolved evidence. ALREADY_RESOLVED on a coverage row means its policy/helper evidence is resolved, not that production coverage exists. No underlying policy/source gap is mislabeled ENGINE_HELPER_REQUIRED.

| gap_id | Domain / description | Kind / authority | Repository evidence | Partnership predicate defined? | Production? | Required resolution |
|---|---|---|---|---|---|---|
| playing-bound | PLAYING_TRICK_SAFETY: No exact 9+ evaluator or upper-bound exclusion proof | SOURCE_GAP / SOURCE_INSUFFICIENT | knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md, knowledge/bidding/systems/sayc.md | NO | NO | AUTHORITATIVE_SOURCE_REQUIRED |
| playing-treatment | PLAYING_TRICK_SAFETY: Choose/approve how strong playing-trick policy applies to the intended ordinary subset; protection remains in force | POLICY_GAP / UNRESOLVED | bridge/nisim_nily_opening_policy.py#strong-2c-playing-tricks | NO | NO | PARTNERSHIP_DECISION_REQUIRED |
| closed-exceptions | EXCEPTION_POLICY_SAFETY: Select a closed controls/distribution/optional-opening exception policy | POLICY_GAP / SUPPORTED_REFERENCE | knowledge/bidding/natural-bids/opening-bids/opening-requirements.md, knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md | NO | NO | PARTNERSHIP_DECISION_REQUIRED |
| seat-vulnerability | CONTEXT_SAFETY: Exact first-seat/vulnerability scope, later-seat exclusions and exception precedence | POLICY_GAP / SUPPORTED_REFERENCE | knowledge/bidding/principles/bidding-fundamentals/seat-position.md, knowledge/bidding/principles/bidding-fundamentals/vulnerability.md | NO | NO | PARTNERSHIP_DECISION_REQUIRED |
| activation | CONTEXT_SAFETY: Approve explicit nisim-nily activation rather than infer it from generic SAYC | POLICY_GAP / PROJECT_CONTRACT | bridge/system_profiles.py, bridge/nisim_nily_opening_policy.py | NO | NO | PARTNERSHIP_DECISION_REQUIRED |
| positive-domain | POSITIVE_PASS_POLICY: 29N proposed screen is not affirmative approved Pass policy | POLICY_GAP / SOURCE_INSUFFICIENT | bridge/nisim_nily_opening_policy.py#positive-pass, bridge/opening_pass_positive_predicate_audit.py | NO | NO | PARTNERSHIP_DECISION_REQUIRED |
| rule20-helper | strength arithmetic: Canonical Hand-based Rule20 helper already available | ALREADY_RESOLVED / NISIM_NILY_PARTNERSHIP_POLICY | bridge/nisim_nily_opening_policy.py#assess_rule_of_20 | YES | NO | ALREADY_RESOLVED |
| approved-opening-coverage | 11-HCP screen and exact 5-5 major preference: Policy/helper available, but production family integration absent; preserve existing boundaries | COVERAGE_GAP / NISIM_NILY_PARTNERSHIP_POLICY | bridge/nisim_nily_opening_policy.py, bridge/sayc.py | YES | NO | ALREADY_RESOLVED |

## S. Policy gaps

Exact controls/distribution/optional-opening exceptions; first-seat/vulnerability scope and later-seat boundaries; nisim–nily activation; positive Pass approval; the precise application of the already-protected strong playing-trick alternative. Existing protective policy is known; the missing predicates are its affirmative resolution, not permission to discard it.

## T. Source gaps

Playing-trick concept lacks complete authoritative estimator/upper-bound support, including suit texture/fit/partner assumptions. Quick-trick tables cannot supply it. Qualitative opening exceptions lack exact claim-level bounds. Metadata such as Standard, bibliography links and canonical use do not supply authenticated claim coverage. No external source was acquired in this phase.

## U. Engine gaps

No current blocker is safely an engine-only task. PT/QT evaluator code is absent, but PT policy/authority is incomplete and QT opening use is unapproved. Implementing either now would choose policy implicitly. Existing Hand evaluation, Rule20 arithmetic, seat/history, vulnerability and system-option representations already suffice for the defined facts. ENGINE_HELPER_REQUIRED is reserved for a later fully specified policy with missing calculation code.

## V. Coverage gaps

11-HCP Rule20 arithmetic/strength policy and exact 5-5-major preference are defined, but production opening-family integration is absent. 5♠–5♥=>1♠ remains explicit partnership policy; it is not universal SAYC. Equal-minor and playing-trick domains still have substantive unresolved predicates and cannot be called coverage-only gaps. No coverage work is performed.

## W. Exact human partnership decisions

These questions are for review; no answer or approval is inferred. Each affects all 447 potentially, but approving one alone unlocks zero because the other dimensions remain unknown. A justified narrower domain is acceptable; maximizing coverage is not the objective.

### playing

- Question: Which sourced playing-trick definition or justified narrow-domain exclusion should govern nisim-nily's protected strong branch?
- Why: Need proof, not a new guessed formula; protection remains until resolved.
- Affected ordinary audit cases: 447.
- Evidence: knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md, bridge/nisim_nily_opening_policy.py#strong-2c-playing-tricks.
- If unanswered: UNKNOWN / ABSTAIN.

### exceptions

- Question: Within the proposed <=10/max-length<=5/Rule20<20 domain, what exact control, suit-quality or distribution exceptions are retained, and how are they excluded?
- Why: Define a closed exception contract without universalizing qualitative notes.
- Affected ordinary audit cases: 447.
- Evidence: knowledge/bidding/natural-bids/opening-bids/opening-requirements.md, knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md.
- If unanswered: UNKNOWN / ABSTAIN.

### scope

- Question: Is the initial policy dealer-first-seat only, for which vulnerabilities, and how is nisim-nily explicitly selected apart from generic SAYC?
- Why: Known context facts do not determine approved contextual behavior; later seats may stay out of scope.
- Affected ordinary audit cases: 447.
- Evidence: knowledge/bidding/principles/bidding-fundamentals/seat-position.md, knowledge/bidding/principles/bidding-fundamentals/vulnerability.md, bridge/system_profiles.py.
- If unanswered: UNKNOWN / ABSTAIN.

### positive-pass

- Question: After those exclusions are proved, do you approve the exact bounded subset as affirmative Pass policy?
- Why: Earlier approvals explicitly withheld a positive Pass predicate; conditional approval is not assumed.
- Affected ordinary audit cases: 447.
- Evidence: bridge/nisim_nily_opening_policy.py#positive-pass, PHASE 29N G.
- If unanswered: UNKNOWN / ABSTAIN.

## X. Is a positive Pass predicate sufficiently supported?

NO. Repository/approved-policy evidence refines the unknowns and resolves the factual context, but does not supply any complete all-SAFE proof or an approved affirmative Pass domain.

## Y. Exact proposed Phase29P

Partnership decision and evidence-contract phase only: resolve W's minimum choices for a first-seat, explicitly activated, vulnerability-scoped subset; specify a sourced playing-trick exclusion proof and a closed exception contract; obtain explicit positive Pass approval. If an external source is required, acquire it only in a separately authorized later source phase. Then rerun the safety audit. NO production Pass implementation on the present evidence.

## Z. Focused tests

138 passed in 11.31s. Suites: Phase29O/N/M/L/K/J; SAYC openings, 2NT opening, strong2C, weak twos, three-level preempts; source-authority contract and registry audit; system profiles; route configuration. Tests cover tri-state conjunction/precedence, all original unknown dimensions, real context facts, known positive hazards, low-HCP Rule20 uncertainty, exact count migrations, deterministic registry/gaps/report, bounded representatives and unchanged routes. No full regression.

## AA. Route count

45 production SAYC routes. No opening rule added; existing opening rules unchanged.

## AB. Git status/diff/whitespace

Four untracked audit deliverables from C; no existing tracked modifications. `git diff --check` and `git diff --stat` empty. Separate trailing-whitespace/final-newline checks cover all four new files. Deterministic JSON verified and subset totals reconciled. HEAD unchanged. No commit or push.

## AC. Semantic guards

| Category changed? | YES/NO |
|---|---|
| Production opening semantics | NO |
| Pass recommendations | NO |
| Bidding rules | NO |
| Opening rules | NO |
| Routes | NO |
| Route count | NO |
| ABSTAIN behavior | NO |
| UNKNOWN behavior | NO |
| System profiles/treatments | NO |
| Auction | NO |
| Deal generation | NO |
| Simulator | NO |
| GUI | NO |
| Contract extraction | NO |
| Play | NO |
| Double dummy | NO |

## Required answers 1–20

1. All 447 passed only the numerical/shape screen; Phase29N had no affirmative playing-trick exclusion, closed exception policy or approved context contract. Positive Pass approval is independently still missing.
2. The three original dimensions tie: each blocks all 447. The additional positive-policy dimension also remains UNKNOWN for all 447.
3. NO usable canonical playing-trick opening evaluator was located.
4. Not applicable; the approximate source concept is not a complete authoritative safety predicate.
5. NO usable canonical quick-trick evaluator was located. Reference tables exist; controls/HCP are not substitutes, and Rule22 is not adopted.
6. Primarily SOURCE_GAP plus POLICY_GAP for exact partnership treatment/exclusion. It is not merely ENGINE_HELPER_REQUIRED.
7. Concrete residuals are controls/suit-quality/distribution upgrades, optional opening adjustments and lack of a closed approved exception set. Existing scoped strength/length/equal-suit exclusions are already established for the 447; playing tricks and context are separately modeled.
8. No exact approved seat-dependent nisim–nily Pass policy is defined. Repository guidance varies by opening position; compass seat is not opening position. All 447 are known first-seat dealer cases.
9. No exact approved vulnerability-dependent Pass threshold is defined; reference guidance does change opening/preempt style. Current production opening predicates' lack of adjustment does not establish approved invariance.
10. NO. Known context facts do not prove context irrelevant.
11. 0 of 447 become all-SAFE.
12. 447 remain UNKNOWN.
13. 0 of the target 447 are positively UNSAFE. Across all 616, 45 have approved normal/borderline strength barriers; 571 remain UNKNOWN.
14. 42 eleven-HCP qualifiers plus four lower-HCP qualifiers (three from old protected, one from old insufficient) equals46. Broader audit screening and precedence, not new opening authorization.
15. 65 minus three transferred low-HCP qualifiers plus 58 failed-screen eleven-HCP cases equals120: 51 long-suit +11 equal-suit +58 other.
16. Correct documented refinements, not bugs. Exact migration assertions pass.
17. Resolve the playing-trick definition/exclusion, closed opening exceptions, seat/vulnerability scope and partnership activation, then approve the affirmative positive Pass subset. Exact questions are in W.
18. Each affects all447, but none alone unlocks a safe hand. All independent exclusions and positive approval must be satisfied; no claim that one answer guarantees coverage.
19. NO. Phase29P cannot implement production Pass from the present evidence.
20. Formalize those minimal partnership/evidence contracts for a narrow first-seat subset and rerun the safety audit; leave unanswered cases UNKNOWN/ABSTAIN.

## Reproduction

```python
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.opening_pass_safety_evidence_audit import build_pass_safety_audit_report
report = build_pass_safety_audit_report(run_full_auction_simulation(SimulationConfig(100, 1000)))
print(report.to_json())
```

Stop after reviewable audit delivery. No production integration authorized by this phase.
