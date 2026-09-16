# Phase 29N — Positive Opening Pass predicate design and safety audit

**Result: 0 SAFE_ORDINARY_PASS_CANDIDATE hands (0% of 616). Production readiness: NO.**

447 hands meet the objective numerical/shape screen, but the repository cannot affirmatively discharge three safety checks. These are SOURCE_OR_POLICY_INSUFFICIENT, not safe Pass. The proposal is audited, not promoted to approved production policy. **PASS != FALLBACK_FOR_ABSTAIN.**

## A. Baseline verification

- Project directory: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit`
- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`
- Branch: `codex/phase18b`.
- Local HEAD, live remote HEAD and remote-tracking HEAD: `5f95e09b37fb6cfec063608a69447029a7f123c7`.
- Ahead/behind `0/0`; initial `git status --short` clean. Known cache permission warnings only.
- User-supplied full regression baseline: 2145 passed, 143 subtests passed; not rerun.

## B. Files inspected

Required policy/diagnostic inputs inspected and reused:

- `bridge/nisim_nily_opening_policy.py`
- `bridge/opening_pass_source_policy_audit.py`
- `bridge/opening_pass_policy_audit.py`
- `bridge/opening_abstention_root_cause_audit.py`
- `bridge/full_auction_abstention_audit.py`
- `bridge/full_auction_coverage.py`
- `bridge/deal_simulator.py`
- `bridge/sayc.py`
- `bridge/sayc_route_configuration.py`
- `bridge/evaluation.py`
- `tests/test_bridge_phase29j_opening_abstention_root_cause.py`
- `tests/test_bridge_phase29k_opening_pass_policy_audit.py`
- `tests/test_bridge_phase29l_opening_pass_source_policy_audit.py`
- `tests/test_bridge_phase29m_nisim_nily_opening_policy.py`
- `bridgelab_phase29l_opening_pass_source_policy_audit.md`
- `bridgelab_phase29m_nisim_nily_opening_policy.md`
- `../knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md`

No canonical Hand/HCP/shape/Auction logic duplicated. No external bridge policy acquired. Existing Phase29L evidence is preserved as a historical snapshot; Phase29M's explicit partnership approvals govern the new policy discussion.

## C. Files added

- `bridge/opening_pass_positive_predicate_audit.py`
- `tests/test_bridge_phase29n_positive_opening_pass_predicate_audit.py`
- `bridgelab_phase29n_positive_opening_pass_predicate_audit.md`
- `bridgelab_phase29n_positive_opening_pass_predicate_audit.json`

## D. Files modified

None. Existing production and Phase29J/K/L/M files remain unchanged.

## E. Positive Pass design

The hand assessor accepts a canonical Hand only. It accepts no route result, ABSTAIN flag, no-route flag, bid availability or caller-supplied safety override. Each hand gets immutable facts, policy version 29M.1, tri-state checks with reasons/provenance, blocked/unknown check identifiers and one primary classification. No Call or RuleDecision is returned.

ABSTAIN is used only to select the historical population in the report builder. It is never used as evidence in the hand assessor. SAFE requires every required check to be ESTABLISHED, with complete check identities, explanations and provenance. Empty/missing/duplicate/extra checks, EXCLUDED or UNKNOWN fail the conjunction. The all-established conjunction is a logical design, not evidence that a real hand meets it.

## F. Exact affirmative conditions

Proposed objective screen: canonical valid hand; HCP<=10; every suit length<=5; Rule20 score<20; no equal majors of length>=5; no equal minors of length>=5. This screen is necessary but not sufficient. In addition, all protected-domain exclusions and context/exception requirements below must be affirmatively established.

| Required check | Meaning | Current evidence |
|---|---|---|
| `bounded_strength` | HCP=2; proposed ordinary domain requires <=10. | ESTABLISHED on ordinary example |
| `bounded_suit_lengths` | Longest=4; requires every suit <=5. | ESTABLISHED on ordinary example |
| `ordinary_preempt_excluded` | Every suit <=5 excludes ordinary six/seven-card shapes only; not a universal preempt theorem. | ESTABLISHED on ordinary example |
| `known_hcp_strong_excluded` | 22+ HCP strong branch checked separately from playing tricks. | ESTABLISHED on ordinary example |
| `opening_strength_boundary_excluded` | 12+ normal opening strength and all 11-HCP policy cases remain outside this domain. | ESTABLISHED on ordinary example |
| `equal_minor_boundary_excluded` | Equal 5-5/6-6 minors remain protected; 3-3/4-4 alone are not unresolved selectors. | ESTABLISHED on ordinary example |
| `equal_major_boundary_excluded` | Exactly 5S-5H has partnership preference 1S; 6-6 remains unresolved; neither can be Pass. | ESTABLISHED on ordinary example |
| `strong_playing_tricks_excluded` | No sourced deterministic proof excludes 9+ playing tricks for this hand; low HCP/short suits are not an approved substitute. | UNKNOWN on ordinary example |
| `weak_preempt_overlap_excluded` | Bounded lengths exclude ordinary 6-6 and 7-6 long-suit overlap; long hands remain protected without selecting a preempt. | ESTABLISHED on ordinary example |
| `rule20_candidate_excluded` | Rule20=10; compute at every HCP, including <=10; score>=20 excludes safe Pass without itself choosing an opening. | ESTABLISHED on ordinary example |
| `other_opening_exceptions_excluded` | No complete approved control/distribution/optional-opening exception contract proves exclusion. | UNKNOWN on ordinary example |
| `context_scope_established` | First-seat sample does not approve a partnership Pass context/vulnerability policy; proposal is audit-only. | UNKNOWN on ordinary example |

`context_scope_established` is about the unresolved first-seat/vulnerability policy contract, not a claim that the known sample is in the wrong seat. The candidate was explicitly proposed for audit, not approved for production. Even if its context were approved now, the playing-trick and opening-exception checks would still block safety.

## G. Exact safety exclusions

Protect all 11+ HCP from this <=10 ordinary domain; all six-plus-card suits; Rule20>=20 at any low HCP; equal 5-5/6-6 majors/minors; known strong HCP eligibility; unresolved playing-trick eligibility; ordinary weak/preempt overlaps and unsupported long-suit variants; undefined opening exceptions and context. Existing 3-3/4-4 Better-Minor guidance does not establish Pass but does not create a new unresolved equal-minor boundary by itself.

All checks are retained even when an earlier primary category wins. UNKNOWN strong exclusion means 'not proven outside the strong domain', not 'proven to be a strong opening'. No approximate playing-trick table is converted into a universal upper bound.

## H. Classification precedence

One primary category per hand, in this deterministic order:

1. KNOWN_OPENING_COVERAGE_BOUNDARY: 12-21 HCP with equal majors or minors of length>=5, matching the documented controlled shape boundaries.
2. RULE20_POTENTIAL_OPENING: HCP<=11 and Rule20>=20; not an opening recommendation, especially below 11.
3. PROTECTED_STRONG_2C_DOMAIN: HCP>=22.
4. PROTECTED_PREEMPT_DOMAIN: any suit>=6 (protective distribution screen, not a preempt recommendation).
5. PROTECTED_EQUAL_SUIT_DOMAIN: equal majors/minors of length>=5 after earlier categories.
6. OTHER_PROTECTED_UNRESOLVED: remaining 11+ HCP, including failed Rule20 at 11.
7. SAFE_ORDINARY_PASS_CANDIDATE: complete affirmative check conjunction only.
8. SOURCE_OR_POLICY_INSUFFICIENT: remaining unresolved evidence, never an inferred Pass.

Known physical/strength exclusions precede the ubiquitous unknown playing-trick check so the report remains informative. All unknown flags remain visible regardless of primary category. This order is an audit taxonomy, not bidding priority. Higher-HCP hands do not get the Rule20 primary label because they already have normal/strong strength and Rule20 is not their opening gate.

## I. Rule-of-20 interaction

Reuses Phase29M's canonical helper: HCP + two longest lengths. Score is computed for every hand. Below-11 qualification is a reason to exclude the proposed Pass domain, not new approval to open. Rule22 remains unadopted. Strength and suit-choice approvals are not production changes.

## J. 10-HCP and lower findings

10+5+5=20, 9+6+5=20 and 8+6+6=20 are independently tested and rejected from safe Pass. Their secondary equal-suit/long-suit flags remain. Sample: four <=10-HCP qualifiers join the 42 historical 11-HCP qualifiers, making 46. Three came from the old protected group; one from the old 506 insufficient group.

## K. 11-HCP findings

42 qualify under approved Rule20 strength screening; no call is selected. The other 58 fail that screen but remain outside the proposed <=10 domain, classified OTHER_PROTECTED_UNRESOLVED. Neither failed Rule20 nor absence of a production opening implies Pass. 12 HCP does not require Rule20; 13+ remains normal opening strength subject to family requirements.

## L. Equal-major protection

**5♠–5♥ =>1♠ (1S)** for nisim–nily, never 1H in the approved exact tie choice. This is partnership policy, subject to eligibility/strong-family precedence. All equal-five-major hands remain excluded from safe Pass; 6-6 is also protected without extending the exact 5-5 approval. The reproduced strong cases are deals 57, 184, 613; indexes are observations/assertions, not hand-classification inputs.

## M. Equal-minor protection

5-5 and 6-6 remain protected. 3-3->1C and 4-4->1D are existing sourced selectors under current family gates, not unconditional opening bids or Pass evidence. No universal equal-minor selector is added.

## N. Strong-2C protection

Source: `sayc#Strong 2♣ Opening` says 22+ HCP OR 9+ playing tricks. Production implements only HCP>=22. The playing-tricks article explicitly lacks a universal formula and uses approximate fit/partner-dependent estimates. Phase29L explicitly rejected replacing proof with an HCP/max-length screen. Phase29M preserved that exclusion, and Phase29N supplies no additional bound. Therefore every present assessment records playing-trick exclusion UNKNOWN; no hand is positively certified outside it. This is an evidence gap, not an assertion that every weak hand has nine tricks.

## O. Weak-two/preempt protection

Any six-plus suit fails the proposed bounded-shape domain. This covers ordinary six/seven-card openings, 6-6/7-6 overlaps, six-club variants and longer-suit gaps without copying the opening engine. Shorter suits exclude those ordinary length domains, but do not establish completeness of partnership exceptions. The earlier Rule20 category can take precedence while long-suit flags remain.

## P. 1,000-deal audit totals

Seed=100; total/completed=1000/1000; depth-0 ABSTAIN=616; simulation errors=0; reproduction errors=0.

| Primary category | Count | % of 616 |
|---|---:|---:|
| KNOWN_OPENING_COVERAGE_BOUNDARY | 3 | 0.487013% |
| RULE20_POTENTIAL_OPENING | 46 | 7.467532% |
| PROTECTED_STRONG_2C_DOMAIN | 0 | 0.000000% |
| PROTECTED_PREEMPT_DOMAIN | 51 | 8.279221% |
| PROTECTED_EQUAL_SUIT_DOMAIN | 11 | 1.785714% |
| OTHER_PROTECTED_UNRESOLVED | 58 | 9.415584% |
| SAFE_ORDINARY_PASS_CANDIDATE | 0 | 0.000000% |
| SOURCE_OR_POLICY_INSUFFICIENT | 447 | 72.564935% |

Protected unresolved aggregate=120 (0 strong +51 preempt +11 equal +58 other). Source/policy insufficient=447. Sum: 3+46+120+0+447=616.

## Q. Safe-candidate count

**0 (0%).** Objective screen count=447, but none clears all safety checks. These counts must not be conflated.

## R. Safe-candidate distributions

HCP, shape, longest-suit and Rule20-score distributions are all empty because the safe set is empty. The JSON artifact contains those empty distributions explicitly, and corresponding nonempty distributions for every rejected category.

## S. Representative safe candidates

None supported by current evidence. No example is fabricated. Ordinary `J987.962.94.J943` has 2 HCP, maximum length 4 and Rule20=10, but still has the three UNKNOWN safety checks listed in F.

## T. Representative rejected candidates and reasons

### KNOWN_OPENING_COVERAGE_BOUNDARY

- Deal 57, dealer E, vulnerability NS: `AJ543.AQJ63.74.2`; HCP 12; SHDC (5, 5, 2, 1); Rule20 22. Blocked: bounded_strength, opening_strength_boundary_excluded, equal_major_boundary_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 184, dealer N, vulnerability None: `AKJT7.AKJ74.A54.-`; HCP 20; SHDC (5, 5, 3, 0); Rule20 30. Blocked: bounded_strength, opening_strength_boundary_excluded, equal_major_boundary_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 613, dealer E, vulnerability NS: `AKQT8.87532.JT.Q`; HCP 12; SHDC (5, 5, 2, 1); Rule20 22. Blocked: bounded_strength, opening_strength_boundary_excluded, equal_major_boundary_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
### RULE20_POTENTIAL_OPENING

- Deal 3, dealer W, vulnerability Both: `KJT9874.A5.K2.96`; HCP 11; SHDC (7, 2, 2, 2); Rule20 20. Blocked: bounded_strength, bounded_suit_lengths, ordinary_preempt_excluded, opening_strength_boundary_excluded, weak_preempt_overlap_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 42, dealer S, vulnerability EW: `AKJ954.QJ65.42.5`; HCP 11; SHDC (6, 4, 2, 1); Rule20 21. Blocked: bounded_strength, bounded_suit_lengths, ordinary_preempt_excluded, opening_strength_boundary_excluded, weak_preempt_overlap_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 66, dealer S, vulnerability EW: `K962.K6.KT.QT987`; HCP 11; SHDC (4, 2, 2, 5); Rule20 20. Blocked: bounded_strength, opening_strength_boundary_excluded, rule20_candidate_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
### PROTECTED_PREEMPT_DOMAIN

- Deal 36, dealer N, vulnerability None: `4.T6.QT98732.K98`; HCP 5; SHDC (1, 2, 7, 3); Rule20 15. Blocked: bounded_suit_lengths, ordinary_preempt_excluded, weak_preempt_overlap_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 43, dealer W, vulnerability Both: `85.Q72.43.KJT743`; HCP 6; SHDC (2, 3, 2, 6); Rule20 15. Blocked: bounded_suit_lengths, ordinary_preempt_excluded, weak_preempt_overlap_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 65, dealer E, vulnerability NS: `43.JT8.QJ8652.87`; HCP 4; SHDC (2, 3, 6, 2); Rule20 13. Blocked: bounded_suit_lengths, ordinary_preempt_excluded, weak_preempt_overlap_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
### PROTECTED_EQUAL_SUIT_DOMAIN

- Deal 52, dealer N, vulnerability None: `KT984.QJ986.9.42`; HCP 6; SHDC (5, 5, 1, 2); Rule20 16. Blocked: equal_major_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 70, dealer S, vulnerability EW: `A9842.98732.K83.-`; HCP 7; SHDC (5, 5, 3, 0); Rule20 17. Blocked: equal_major_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 220, dealer N, vulnerability None: `T.K5.T8752.AJ954`; HCP 8; SHDC (1, 2, 5, 5); Rule20 18. Blocked: equal_minor_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
### OTHER_PROTECTED_UNRESOLVED

- Deal 9, dealer E, vulnerability NS: `Q852.A2.J92.A642`; HCP 11; SHDC (4, 2, 3, 4); Rule20 19. Blocked: bounded_strength, opening_strength_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 23, dealer W, vulnerability Both: `AK4.JT2.KT6.8754`; HCP 11; SHDC (3, 3, 3, 4); Rule20 18. Blocked: bounded_strength, opening_strength_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 26, dealer S, vulnerability EW: `J.T874.AJ72.AJ73`; HCP 11; SHDC (1, 4, 4, 4); Rule20 19. Blocked: bounded_strength, opening_strength_boundary_excluded. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
### SOURCE_OR_POLICY_INSUFFICIENT

- Deal 1, dealer E, vulnerability NS: `J987.962.94.J943`; HCP 2; SHDC (4, 3, 2, 4); Rule20 10. Blocked: none of the objective checks. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 2, dealer S, vulnerability EW: `974.KQT93.53.964`; HCP 5; SHDC (3, 5, 2, 3); Rule20 13. Blocked: none of the objective checks. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.
- Deal 4, dealer N, vulnerability None: `854.A9853.J74.K4`; HCP 8; SHDC (3, 5, 3, 2); Rule20 16. Blocked: none of the objective checks. UNKNOWN: strong_playing_tricks_excluded, other_opening_exceptions_excluded, context_scope_established.

### Low-HCP Rule20 examples

- Deal 299: `AKJ82.T.3.Q87543`, HCP=10, SHDC=(5, 1, 1, 6), Rule20=21; not safe Pass and not an automatically approved opening.
- Deal 461: `94.7.AKQ9.J87543`, HCP=10, SHDC=(2, 1, 4, 6), Rule20=20; not safe Pass and not an automatically approved opening.
- Deal 735: `KJ876532.K.QT2.9`, HCP=9, SHDC=(8, 1, 3, 1), Rule20=20; not safe Pass and not an automatically approved opening.

At most three representatives per category plus three low-HCP Rule20 examples. No full Deal objects retained in the report. Every representative's full reasons/provenance appear in deterministic JSON.

## U. Reconciliation with Phase29M

Historical report unchanged. Reproduced its documented classification algorithm from the canonical sample and existing Phase29J cases; no hard-coded classification indexes. Historical counts: 42 Rule20, 3 boundaries, 65 protected, 506 insufficient, 0 supported Pass. Phase29K screen also reproduces 542.

| Old category | New category | Count |
|---|---|---:|
| KNOWN_OPENING_COVERAGE_BOUNDARY | KNOWN_OPENING_COVERAGE_BOUNDARY | 3 |
| PROTECTED_UNRESOLVED | PROTECTED_EQUAL_SUIT_DOMAIN | 11 |
| PROTECTED_UNRESOLVED | PROTECTED_PREEMPT_DOMAIN | 51 |
| PROTECTED_UNRESOLVED | RULE20_POTENTIAL_OPENING | 3 |
| RULE20_POTENTIAL_OPENING | RULE20_POTENTIAL_OPENING | 42 |
| SOURCE_OR_POLICY_INSUFFICIENT | OTHER_PROTECTED_UNRESOLVED | 58 |
| SOURCE_OR_POLICY_INSUFFICIENT | RULE20_POTENTIAL_OPENING | 1 |
| SOURCE_OR_POLICY_INSUFFICIENT | SOURCE_OR_POLICY_INSUFFICIENT | 447 |

The old 506 becomes 1 low-HCP Rule20 +58 failed-screen 11-HCP protected +447 still insufficient +0 safe. The old 65 becomes 3 low-HCP Rule20 +51 preempt +11 equal. All 42 old Rule20 and three known boundaries remain in their matching categories. No double-counting.

## V. Passed-out auction compatibility

Phase29K's canonical `P P P P` yields `is_passed_out=True` and `final_contract=None`. Future explicit Pass is architecturally compatible. No Auction, contract, play or DD changes are needed for this audit and none are made.

## W. Remaining source/policy gaps

1. A sourced deterministic playing-trick evaluator OR a valid approved sufficient bound proving the selected ordinary domain cannot enter the unresolved strong branch.
2. A closed partnership exception contract for the selected domain, including controls/distribution and any optional opening treatments.
3. Exact first-seat/other-seat and vulnerability scope, and explicit approval of the proposed positive Pass domain. Being listed as a candidate for audit is not approval.
4. Safe future partnership activation/integration; preserve all uncovered equal-suit, Rule20, long-suit and strong domains as unsupported. Resolving every domain is not required if the narrow subset can positively exclude it.

## X. Is a narrow production rule safe now?

**NO.** No real hand has all safety checks established by the current evidence contract. The design has an explicit positive conjunction, but no demonstrated nonempty safe set. There is no basis to broaden coverage or treat UNKNOWN as established merely to obtain a nonzero result.

## Y. Exact proposed Phase29O scope

Acquire/formalize the three missing affirmative contracts for the 447-case objective domain, or an even narrower justified subset. Specify exact hand/context conditions and prove the protected exclusions, then rerun this audit. Production implementation is contingent on those proofs and approval. Do not implement a Pass rule in 29O merely from HCP<=10, maximum length<=5 and Rule20<20.

## Z. Focused test results and test limitation

122 focused tests passed in 3.89s: Phase29N/M/L/K/J; SAYC openings, 2NT, strong2C, weak twos, three-level preempts; canonical Auction; route configuration. After adding exact reproduced-count regression assertions, the 17 Phase29N tests passed again in 1.40s. No full regression.

The requested real ordinary-safe positive fixture cannot honestly be established because its safety evidence is incomplete. Tests explicitly verify this limitation. A separate abstract all-established-check truth-table test verifies the positive conjunction, and replacing any check with UNKNOWN/EXCLUDED prevents success. That hypothetical test is labeled TEST_ONLY and is not a hand certification or partnership approval. The public hand assessor accepts no proof override. This is a source limitation disclosed by the audit, not a speculative bridge-policy test.

## AA. Production route count

45; opening rules remain 14. No production Pass rule or recommendation.

## AB. Git status/diff/whitespace

Four untracked audit files listed in C only. No existing tracked modifications. `git diff --check` and `git diff --stat` empty. Explicit trailing-whitespace and final-newline checks cover all four untracked files; JSON matches the module report. HEAD unchanged. No commit or push.

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
| Coverage reporting | NO |
| GUI | NO |
| Contract extraction | NO |
| Play | NO |
| Double dummy | NO |

Existing coverage reporting is unchanged; only the new standalone audit reports new categories. No stop condition was breached: baseline matched, no production edits required. Source gaps are reported as the result. Stop for review.

## Required answers 1–22

1. Not yet for any real hand under current evidence. The positive conjunction is specified; essential exclusions remain UNKNOWN. Absence of another bid is never used.
2. Proposed: valid hand, HCP<=10, max suit length<=5, Rule20<20, no protected equal majors/minors, with affirmative exclusion of all strong/ordinary-preempt/overlap/other-opening domains and established context/exception scope. Every required check must be ESTABLISHED; see F. Currently not fully discharged.
3. NO. HCP<=10 alone is insufficient.
4. NO. A 10-HCP 5-5 Rule20 hand cannot automatically be passed.
5. NO. A low-HCP six-card hand is protected from this ordinary predicate.
6. NO. A low-HCP seven-card hand is protected.
7. NO under this proposed Pass domain. 11-HCP 5-4 is a Rule20 strength candidate, not a Pass candidate or automatically selected bid.
8. NO. 12 HCP is outside safe ordinary Pass, without requiring Rule20.
9. NO. Equal 5-5 majors are protected.
10. 1S. This is the nisim–nily exact-five-five partnership preference, subject to opening eligibility.
11. NO. Unresolved equal minors cannot be passed.
12. NO. Unresolved strong playing-trick cases cannot be passed.
13. NO. Unresolved weak-two/preempt cases cannot be passed.
14. NO. UNKNOWN safety status cannot be treated as exclusion or Pass.
15. NO. ABSTAIN cannot be converted to Pass.
16. NO. No-route cannot be converted to Pass; the assessor accepts no route result.
17. 0 of the 616 satisfy the complete evidence-backed conjunction; 447 meet only its objective screen.
18. 0% safe candidates.
19. 447 lack strong/exception/context proof; 58 failed-screen 11-HCP cases are protected; 51 long-suit and 11 equal-suit cases remain protected. 46 Rule20 cases and 3 known boundaries require their applicable opening policies. Secondary unknown strong checks remain visible for every category.
20. NO. The subset is not proven safe for production; the candidate is proposed, not approved.
21. Not applicable yet. After sourcing/approving W's missing contracts, implement only an explicitly approved version of F's complete conjunction, never just the numerical screen.
22. Continue honest ABSTAIN/UNKNOWN wherever current production has no supported bid and strong/equal-suit/preempt/Rule20/context/exception safety remains unresolved. Preserve existing valid bid recommendations; do not blanket-abstain currently covered families.

## Reproduction

```python
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.opening_pass_positive_predicate_audit import build_positive_pass_audit_report
batch = run_full_auction_simulation(SimulationConfig(100, 1000))
report = build_positive_pass_audit_report(batch)
print(report.to_json())
```
