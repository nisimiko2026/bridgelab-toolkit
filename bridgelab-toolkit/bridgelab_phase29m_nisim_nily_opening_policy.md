# Phase 29M — nisim–nily partnership opening policy formalization

**Policy only. PASS != FALLBACK_FOR_ABSTAIN. No production integration.**

## A. Baseline verification

- Project: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit`
- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`
- Branch: `codex/phase18b`.
- Local, live remote and remote-tracking HEAD: `9f6b89d470b9027c28ab9dc9662a377c45f433f9`.
- Ahead/behind: `0/0`; initial status: clean. Known cache permission warnings only.
- User-supplied full-regression baseline: 2131 passed, 143 subtests passed; not rerun.

## B. Files inspected

User approval: PHASE 29M specification, sections D-L. This report and the module preserve its substantive approved propositions; authority is the explicit user approval, not an inference from repository notes.

Approval attachment SHA-256: `00f481c490a70e1484638a0eaf0f0fbc4c4844171314cc64d0f7b37d74340540`.

Inspected current `bridge/evaluation.py`, `bridge/sayc.py`, `bridge/opening_pass_policy_audit.py`, `bridge/opening_abstention_root_cause_audit.py`, `bridge/opening_pass_source_policy_audit.py`, and Phase29L tests. Reused Phase29L's evidence inventory without changing it. Focused verification additionally exercised SAYC route configuration, system profiles and source-authority registry tests. No applicable AGENTS.md found.

## C. Files added

- `bridge/nisim_nily_opening_policy.py`
- `tests/test_bridge_phase29m_nisim_nily_opening_policy.py`
- `bridgelab_phase29m_nisim_nily_opening_policy.md` (this report, policy snapshot and optional audit)

## D. Files modified

None. No existing production, source, profile, route or diagnostic file modified.

## E. Exact partnership policies formalized

Policy identity `nisim-nily.opening-policy`, version `29M.1`. Immutable dataclasses and deterministic serialization; Rule20 helper uses canonical `Hand` evaluation and retains no hand/Deal.

| Proposition | Condition | Exact policy | Authority / status |
|---|---|---|---|
| strength-13-plus | HCP >= 13 | Normally opening strength; use existing sourced opening families for actual recommendations. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| strength-12 | HCP == 12 | Normally opening strength; Rule20 is not a universal gate; no arbitrary opening bid. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| strength-11 | HCP == 11 and Rule20Score >= 20 | May have sufficient partnership opening strength; not an opening-call selector. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| strength-10-or-less | HCP <= 10 | No general new opening entitlement. Existing covered weak/preempt recommendations remain unchanged; ordinary unsupported hands are only conditional future Pass candidates. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| rule20 | Borderline strength, primarily 11 HCP | HCP + lengths of two longest suits >=20 qualifies the strength screen. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| rule22 | Repository Rule22 guidance | Not production-adopted, not mandatory partnership opening requirement, not Pass policy. | SUPPORTED_REFERENCE / REFERENCE_ONLY |
| equal-five-card-majors | Spades == 5 and hearts == 5 | 5S-5H => 1S; supersedes the provisional 1H reference suggestion for this partnership. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| five-major-five-minor | One five-card major and one five-card minor | Prefer the five-card major where consistent with existing sourced opening rules. | NISIM_NILY_PARTNERSHIP_POLICY / APPROVED |
| equal-minors-3-3 | Clubs == 3 and diamonds == 3 | Existing sourced Better Minor selects 1C subject to current strength/major/NT/strong gates. | SUPPORTED_REFERENCE / REFERENCE_ONLY |
| equal-minors-4-4 | Clubs == 4 and diamonds == 4 | Existing sourced Better Minor selects 1D subject to current strength/major/NT/strong gates. | SUPPORTED_REFERENCE / REFERENCE_ONLY |
| equal-minors-5-5 | Clubs == 5 and diamonds == 5 | UNRESOLVED; not Pass. | UNRESOLVED / UNRESOLVED |
| other-equal-minors | Equal minors outside 3-3/4-4/5-5 | No universal selector; 6-6 remains unresolved. | UNRESOLVED / UNRESOLVED |
| pass-fallback-prohibition | ABSTAIN, UNKNOWN or no opening rule matched | Never convert these outcomes to Pass or define Pass as registry complement. | NISIM_NILY_PARTNERSHIP_POLICY / PROHIBITED |
| positive-pass | Future positive Opening Pass predicate | Not yet defined by these approvals. | SOURCE_INSUFFICIENT / INCOMPLETE |

All strength and suit-choice approvals remain subject to family applicability, shape, suit length, balanced requirements, strong-opening and preempt boundaries. A weak 5-5-major hand is not automatically opened 1S merely because the suit preference is settled. Exactly 5-5 does not approve 6-6.

## F. Authority classification

`NISIM_NILY_PARTNERSHIP_POLICY` identifies explicit Phase29M approvals. `SUPPORTED_REFERENCE` identifies existing Better-Minor and Rule22 reference facts. `SOURCE_INSUFFICIENT` marks the missing positive Pass predicate. `UNRESOLVED` marks remaining selectors/domains. `AUTHORITATIVE_REPOSITORY_SOURCE` is reserved but assigned to no new proposition: Phase29L found no authenticated external opening claim. Existing production remains the source of actual current recommendations; that operational status does not authenticate bridge theory. No global source-authority registry changes.

Safety-exclusion authority is the user's partnership prohibition; its UNRESOLVED status describes the protected domain or production integration, not doubt about the prohibition. Rule22's reference-only disposition is explicitly mandated by user section F.

## G. Rule-of-20 representation

Approved partnership formula: HCP + longest length + second-longest length >=20. `assess_rule_of_20(Hand)` returns HCP, two lengths, score, qualifies and whether this is the intended 11-HCP use. It never chooses a call. The formula may be calculated for other strengths without granting a new opening entitlement. It contains no quick-trick term.

- 11 + 5 + 4 = 20: qualifies.
- 11 + 4 + 4 = 19: does not qualify; does not imply Pass.

## H. Rule-of-22 status

Reference/evaluation guidance only. Not adopted by production, not a required partnership gate, not Pass policy.

## I. 12-HCP policy

Normally opening strength; Rule20 is not required. A flat 12-HCP hand can score 19 without losing normal partnership opening strength. No arbitrary bid or unresolved-selector bypass.

## J. 11-HCP policy

Rule20 qualification establishes potential opening strength only. The opening call still needs an applicable approved family. Production's current one-level 12-HCP floor remains untouched.

## K. Equal-five-card-major policy

**5♠–5♥ => 1♠ (1S), NOT 1H.** Explicit partnership decision, not universal SAYC. Supersedes the provisional reference suggestion for nisim–nily; Phase29L remains an unchanged historical source snapshot. Strength/strong-opening eligibility still applies. Production still abstains at its controlled boundary.

## L. Equal major+minor policy

With one five-card major and a five-card minor, prefer the major where existing sourced opening-family predicates support it. No new general selector or production predicate is installed.

## M. Equal-minor boundaries

Existing 3-3 ->1C and 4-4 ->1D remain subject to current family gates. 5-5 and 6-6 minors remain unresolved, not Pass. No selector is invented for other configurations. Equal minors of length <=2 imply a five-card major in a valid 13-card hand; this is not a newly alleged minor-only coverage gap.

## N. Strong-2C safety exclusion

The uncomputed below-22-HCP playing-trick branch remains protected UNKNOWN/ABSTAIN when unresolved. A failed HCP-only 2C predicate does not exclude strong opening strength. No playing-trick evaluator or new 2C semantics added.

## O. Weak-two/preempt safety exclusions

Protect multiple six-card qualifying D/H/S suits, seven plus six D/H/S overlap, competing long suits, strength/quality/seat exceptions and unsupported long-suit variants. Existing covered weak/preempt bids remain intact. Seven plus six clubs differs from a six-card D/H/S overlap; two seven-card suits are impossible in a valid hand. Generic 5-HCP references, six clubs and eight-plus/four-level gaps do not imply Pass.

## P. Pass fallback prohibition

ABSTAIN ->Pass, UNKNOWN ->Pass and no-rule-matched ->Pass are prohibited. Registry complements are not Pass. Future Pass requires its own positive strength/domain conditions, explicit exclusions, provenance and explanation. No such complete predicate is supplied by Phase29M.

## Q. Optional 1,000-deal read-only audit

Reproduced with `run_full_auction_simulation(SimulationConfig(100, 1000))`, reused existing Phase29J/K reports, canonical Hand parsing/evaluation and the new strength helper. No results entered the production router. Existing four-pass behavior is unaffected.

Reproduced: 616 depth-0 ABSTAIN, Phase29K screen 542, strong coverage-boundary indexes 57/184/613. Indexes were asserted only after reproduction; classification uses the cases supplied by the existing root-cause report, not a hard-coded index lookup.

Classification precedence (diagnostic, not exhaustive bridge eligibility): existing Phase29J strong cases; then 11 HCP with Rule20>=20; then long suit >=6 or equal five-card majors/minors; remaining cases SOURCE_OR_POLICY_INSUFFICIENT. Long/equal-shape screens flag unresolved risk without implementing weak/preempt predicates. Qualifying Rule20 cases may also have unresolved family/playing-trick risks; their category asserts strength only.

POLICY_SUPPORTED_POTENTIAL_PASS is zero because no positive Pass predicate is approved. Neither max-length<=5 nor failed Rule20 is a safety proof. The insufficient category remains explicitly ambiguous; even other categories do not produce calls. Percentages use all 616 depth-0 cases.

| Category | Count | % of 616 | HCP distribution | Shape distribution (sorted lengths) |
|---|---:|---:|---|---|
| POLICY_SUPPORTED_POTENTIAL_PASS | 0 | 0.0000% | {} | {} |
| RULE20_POTENTIAL_OPENING | 42 | 6.8182% | {"11": 42} | {"5-4-2-2": 10, "5-4-3-1": 8, "5-4-4-0": 2, "5-5-2-1": 4, "5-5-3-0": 1, "6-3-2-2": 2, "6-3-3-1": 3, "6-4-2-1": 4, "6-4-3-0": 2, "6-5-2-0": 2, "7-2-2-2": 1, "7-3-2-1": 1, "7-4-1-1": 1, "7-4-2-0": 1} |
| KNOWN_OPENING_COVERAGE_BOUNDARY | 3 | 0.4870% | {"12": 2, "20": 1} | {"5-5-2-1": 2, "5-5-3-0": 1} |
| PROTECTED_UNRESOLVED | 65 | 10.5519% | {"1": 1, "2": 4, "3": 6, "4": 8, "5": 14, "6": 10, "7": 7, "8": 6, "9": 7, "10": 2} | {"5-5-2-1": 9, "5-5-3-0": 2, "6-3-2-2": 22, "6-3-3-1": 8, "6-4-2-1": 10, "6-4-3-0": 4, "6-5-1-1": 2, "6-5-2-0": 1, "7-2-2-2": 1, "7-3-2-1": 3, "7-4-1-1": 2, "8-3-1-1": 1} |
| SOURCE_OR_POLICY_INSUFFICIENT | 506 | 82.1429% | {"0": 4, "1": 6, "2": 13, "3": 13, "4": 32, "5": 47, "6": 54, "7": 70, "8": 71, "9": 70, "10": 68, "11": 58} | {"4-3-3-3": 74, "4-4-3-2": 140, "4-4-4-1": 27, "5-3-3-2": 103, "5-4-2-2": 66, "5-4-3-1": 72, "5-4-4-0": 11, "5-5-2-1": 11, "5-5-3-0": 2} |

11-HCP Rule20 qualifiers inside the old 542-case screen: **25**. This demonstrates why the old screen must not become Pass.

Bounded representatives and complete audit summary (at most three representatives per category; no Deal objects):

```json
{
  "seed": 100,
  "deals": 1000,
  "depth0_abstains": 616,
  "phase29k_screen": 542,
  "rule20_11_hcp_inside_phase29k_screen": 25,
  "categories": {
    "POLICY_SUPPORTED_POTENTIAL_PASS": {
      "count": 0,
      "hcp": {},
      "shape": {},
      "examples": [],
      "percentage_of_616": 0.0
    },
    "RULE20_POTENTIAL_OPENING": {
      "count": 42,
      "hcp": {
        "11": 42
      },
      "shape": {
        "5-4-2-2": 10,
        "5-4-3-1": 8,
        "5-4-4-0": 2,
        "5-5-2-1": 4,
        "5-5-3-0": 1,
        "6-3-2-2": 2,
        "6-3-3-1": 3,
        "6-4-2-1": 4,
        "6-4-3-0": 2,
        "6-5-2-0": 2,
        "7-2-2-2": 1,
        "7-3-2-1": 1,
        "7-4-1-1": 1,
        "7-4-2-0": 1
      },
      "examples": [
        {
          "deal_index": 3,
          "dealer": "W",
          "vulnerability": "Both",
          "hand": "KJT9874.A5.K2.96",
          "hcp": 11,
          "suit_lengths_SHDC": [
            7,
            2,
            2,
            2
          ],
          "rule20_score": 20
        },
        {
          "deal_index": 42,
          "dealer": "S",
          "vulnerability": "EW",
          "hand": "AKJ954.QJ65.42.5",
          "hcp": 11,
          "suit_lengths_SHDC": [
            6,
            4,
            2,
            1
          ],
          "rule20_score": 21
        },
        {
          "deal_index": 66,
          "dealer": "S",
          "vulnerability": "EW",
          "hand": "K962.K6.KT.QT987",
          "hcp": 11,
          "suit_lengths_SHDC": [
            4,
            2,
            2,
            5
          ],
          "rule20_score": 20
        }
      ],
      "percentage_of_616": 6.8182
    },
    "KNOWN_OPENING_COVERAGE_BOUNDARY": {
      "count": 3,
      "hcp": {
        "12": 2,
        "20": 1
      },
      "shape": {
        "5-5-2-1": 2,
        "5-5-3-0": 1
      },
      "examples": [
        {
          "deal_index": 57,
          "dealer": "E",
          "vulnerability": "NS",
          "hand": "AJ543.AQJ63.74.2",
          "hcp": 12,
          "suit_lengths_SHDC": [
            5,
            5,
            2,
            1
          ],
          "rule20_score": 22
        },
        {
          "deal_index": 184,
          "dealer": "N",
          "vulnerability": "None",
          "hand": "AKJT7.AKJ74.A54.-",
          "hcp": 20,
          "suit_lengths_SHDC": [
            5,
            5,
            3,
            0
          ],
          "rule20_score": 30
        },
        {
          "deal_index": 613,
          "dealer": "E",
          "vulnerability": "NS",
          "hand": "AKQT8.87532.JT.Q",
          "hcp": 12,
          "suit_lengths_SHDC": [
            5,
            5,
            2,
            1
          ],
          "rule20_score": 22
        }
      ],
      "percentage_of_616": 0.487
    },
    "PROTECTED_UNRESOLVED": {
      "count": 65,
      "hcp": {
        "1": 1,
        "2": 4,
        "3": 6,
        "4": 8,
        "5": 14,
        "6": 10,
        "7": 7,
        "8": 6,
        "9": 7,
        "10": 2
      },
      "shape": {
        "5-5-2-1": 9,
        "5-5-3-0": 2,
        "6-3-2-2": 22,
        "6-3-3-1": 8,
        "6-4-2-1": 10,
        "6-4-3-0": 4,
        "6-5-1-1": 2,
        "6-5-2-0": 1,
        "7-2-2-2": 1,
        "7-3-2-1": 3,
        "7-4-1-1": 2,
        "8-3-1-1": 1
      },
      "examples": [
        {
          "deal_index": 36,
          "dealer": "N",
          "vulnerability": "None",
          "hand": "4.T6.QT98732.K98",
          "hcp": 5,
          "suit_lengths_SHDC": [
            1,
            2,
            7,
            3
          ],
          "rule20_score": 15
        },
        {
          "deal_index": 43,
          "dealer": "W",
          "vulnerability": "Both",
          "hand": "85.Q72.43.KJT743",
          "hcp": 6,
          "suit_lengths_SHDC": [
            2,
            3,
            2,
            6
          ],
          "rule20_score": 15
        },
        {
          "deal_index": 52,
          "dealer": "N",
          "vulnerability": "None",
          "hand": "KT984.QJ986.9.42",
          "hcp": 6,
          "suit_lengths_SHDC": [
            5,
            5,
            1,
            2
          ],
          "rule20_score": 16
        }
      ],
      "percentage_of_616": 10.5519
    },
    "SOURCE_OR_POLICY_INSUFFICIENT": {
      "count": 506,
      "hcp": {
        "0": 4,
        "1": 6,
        "2": 13,
        "3": 13,
        "4": 32,
        "5": 47,
        "6": 54,
        "7": 70,
        "8": 71,
        "9": 70,
        "10": 68,
        "11": 58
      },
      "shape": {
        "4-3-3-3": 74,
        "4-4-3-2": 140,
        "4-4-4-1": 27,
        "5-3-3-2": 103,
        "5-4-2-2": 66,
        "5-4-3-1": 72,
        "5-4-4-0": 11,
        "5-5-2-1": 11,
        "5-5-3-0": 2
      },
      "examples": [
        {
          "deal_index": 1,
          "dealer": "E",
          "vulnerability": "NS",
          "hand": "J987.962.94.J943",
          "hcp": 2,
          "suit_lengths_SHDC": [
            4,
            3,
            2,
            4
          ],
          "rule20_score": 10
        },
        {
          "deal_index": 2,
          "dealer": "S",
          "vulnerability": "EW",
          "hand": "974.KQT93.53.964",
          "hcp": 5,
          "suit_lengths_SHDC": [
            3,
            5,
            2,
            3
          ],
          "rule20_score": 13
        },
        {
          "deal_index": 4,
          "dealer": "N",
          "vulnerability": "None",
          "hand": "854.A9853.J74.K4",
          "hcp": 8,
          "suit_lengths_SHDC": [
            3,
            5,
            3,
            2
          ],
          "rule20_score": 16
        }
      ],
      "percentage_of_616": 82.1429
    }
  }
}
```

## R. Remaining unresolved domains

- `equal-minors`: Equal 5-5/6-6 minors and other unsupported minor selectors. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `strong-2c-playing-tricks`: Below-22-HCP strong-2C playing-trick eligibility not fully formalized. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `weak-two-preempt`: Multiple/competing long suits; 6-6 weak-two qualifiers; 7-6 weak-two/preempt overlaps; strength or distributional exceptions. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `long-suit-variants`: Uncovered six clubs, six-card preempt exceptions, eight-plus/four-level and generic 5-HCP preempt variants. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `equal-majors-6-6`: 6S-6H is outside the exact 5S-5H approval. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `unimplemented-approved-openings`: Exact 5-5 majors and 11-HCP Rule20 strength may now have approved policy but remain production coverage boundaries. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- `context-and-evaluation`: Unspecified seat/vulnerability exceptions, optional NT adjustments and unresolved opening-family applicability. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.
- Positive Pass domain itself, including approved HCP/shape/control conditions and proof that protected domains cannot qualify.

## S. Readiness for future implementation

Approved strength-screen arithmetic and the exact 5-5-major preference are precise as policy. They do not supply a positive Pass predicate. No entire or narrow production Pass domain is yet justified merely by these approvals. Any later opening integration must also isolate the partnership policy from generic SAYC, define its activation/context, and preserve stronger-family precedence. This phase deliberately does none of that.

## T. Exact proposed Phase29N

Narrowest safe next phase: specify and obtain approval for one affirmative Pass domain, with exact seat/vulnerability scope, HCP/shape/control conditions, exception precedence and a sound proof/exclusion for strong playing tricks and preempts. Keep all remaining cases unsupported. Review readiness before production integration. If implementation is authorized after that contract exists, limit it to that explicitly positive subset, under an explicit partnership activation contract; do not implement the entire Pass domain. The present phase does not authorize that integration.

## U. Focused test results

109 passed in 7.86s. Suites: Phase29M/L/K/J; SAYC openings, 2NT, strong2C, weak twos, three-level preempts; system profiles; source authority and registry audit; route configuration. No full regression. Bundled Python used existing local venv pytest packages with PYTHONDONTWRITEBYTECODE=1 and cacheprovider disabled. Optional audit aggregation repeated on the same canonical batch and matched deterministically.

## V. Production route count

45. Opening rule count remains 14; no added Pass or other opening rule.

## W. Git/diff/whitespace

Three untracked deliverables listed in C; no tracked modifications. `git diff --check` and `git diff --stat` are empty. Separate whitespace/EOF check covers all untracked deliverables. HEAD unchanged. No commit/push.

## X. Semantic guards

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
| System profiles | NO |
| Treatments | NO |
| Auction | NO |
| Deal generation | NO |
| Phase29F simulator | NO |
| Phase29G full-auction simulator | NO |
| Phase29H coverage | NO |
| Phase29I diagnostics | NO |
| Phase29J root-cause audit | NO |
| Phase29K Pass audit | NO |
| Phase29L source-policy audit | NO |
| GUI | NO |
| Contract extraction | NO |
| Play | NO |
| Double dummy | NO |

## Y. Stop-condition review

Expected baseline present. No production change needed. Approved policy represented without universal-SAYC authority claims. Existing diagnostics unchanged and tested. No full regression, commit or push. Stop for review; no production implementation in this phase.

## Required answers 1–20

1. YES. Rule20 is explicitly approved nisim–nily partnership strength policy, primarily for 11 HCP.
2. NO. It is not universal SAYC policy.
3. YES. 11+5+4=20 meets the screen, without choosing a call.
4. NO. 11+4+4=19 fails the screen, without implying Pass.
5. NO. 12 HCP is normally opening strength without a universal Rule20 gate; family boundaries remain.
6. 1S. Exactly 5♠–5♥ =>1♠, subject to opening eligibility and stronger-family boundaries.
7. NO. The 1S choice is partnership policy, not an authoritative universal SAYC claim.
8. NO. Rule22 is reference-only and not production-adopted.
9. NO. Unresolved equal minors cannot become Pass.
10. NO. Unresolved strong-2C playing tricks cannot become Pass.
11. NO. Unresolved weak-two/preempt overlaps cannot become Pass.
12. NO. ABSTAIN cannot automatically become Pass.
13. NO. UNKNOWN cannot automatically become Pass.
14. NO. Failure of all current opening rules is not evidence of Pass.
15. NO. Phase29M creates no production Pass recommendation.
16. NO. Production bidding semantics are unchanged.
17. YES. Production SAYC route count is 45.
18. Still missing: a positive approved Pass predicate; exact context/seat/vulnerability scope; controls/distribution and exception rules; sound strong-playing-trick exclusion; preempt/long-suit and equal-minor exclusion or resolution; safe partnership activation/integration. Rule20 failure and <=10 HCP alone supply none of this proof.
19. Do not implement the entire domain. Only a narrowly defined positive subset could be implemented after its missing affirmative contract and safety proof are approved; no such subset is specified yet.
20. Phase29N should first acquire/approve that narrow positive Pass specification and validate its exclusions. Production implementation remains contingent on that contract and subsequent review, not on a complement or coverage screen.

## Machine-readable policy snapshot

This is the exact deterministic `to_dict()` content; `to_json()` uses compact sorted keys.

```json
{
  "abstain_to_pass_allowed": false,
  "approval_provenance": "User-approved PHASE 29M sections D-L; explicit partnership approval, not universal SAYC",
  "equal_five_card_majors_choice": "1S",
  "equal_major_choice_requires_opening_eligibility": true,
  "failure_to_open_is_evidence_to_pass": false,
  "invariant": "PASS != FALLBACK_FOR_ABSTAIN",
  "policy_id": "nisim-nily.opening-policy",
  "positive_pass_status": "INCOMPLETE",
  "production_integration": false,
  "propositions": [
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "HCP >= 13",
      "limitations": "Strength or suit preference alone selects no actual bid. Preserve sourced family, shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements.",
      "normal_opening_strength": true,
      "policy": "Normally opening strength; use existing sourced opening families for actual recommendations.",
      "policy_id": "strength-13-plus",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M D1"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "HCP == 12",
      "limitations": "Strength or suit preference alone selects no actual bid. Preserve sourced family, shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements.",
      "normal_opening_strength": true,
      "policy": "Normally opening strength; Rule20 is not a universal gate; no arbitrary opening bid.",
      "policy_id": "strength-12",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M D2"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "HCP == 11 and Rule20Score >= 20",
      "limitations": "Strength or suit preference alone selects no actual bid. Preserve sourced family, shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements. Failing the screen does not imply Pass.",
      "normal_opening_strength": false,
      "policy": "May have sufficient partnership opening strength; not an opening-call selector.",
      "policy_id": "strength-11",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M D3/E",
        "knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md"
      ],
      "requires_rule20": true,
      "status": "APPROVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "HCP <= 10",
      "limitations": "A future positive Pass predicate and every safety exclusion are still required; exceptional or distributional uncertainty remains UNKNOWN / ABSTAIN.",
      "normal_opening_strength": false,
      "policy": "No general new opening entitlement. Existing covered weak/preempt recommendations remain unchanged; ordinary unsupported hands are only conditional future Pass candidates.",
      "policy_id": "strength-10-or-less",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M D4"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "Borderline strength, primarily 11 HCP",
      "limitations": "Not universal SAYC. Not a universal 12-HCP gate. No call choice or failed-screen Pass.",
      "normal_opening_strength": false,
      "policy": "HCP + lengths of two longest suits >=20 qualifies the strength screen.",
      "policy_id": "rule20",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M E"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "SUPPORTED_REFERENCE",
      "condition": "Repository Rule22 guidance",
      "limitations": "No quick-trick requirement is added to approved Rule20.",
      "normal_opening_strength": false,
      "policy": "Not production-adopted, not mandatory partnership opening requirement, not Pass policy.",
      "policy_id": "rule22",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M F",
        "knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md"
      ],
      "requires_rule20": false,
      "status": "REFERENCE_ONLY"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "Spades == 5 and hearts == 5",
      "limitations": "Strength or suit preference alone selects no actual bid. Preserve sourced family, shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements. Exactly 5-5 only; no extension to 6-6; not universal SAYC.",
      "normal_opening_strength": false,
      "policy": "5S-5H => 1S; supersedes the provisional 1H reference suggestion for this partnership.",
      "policy_id": "equal-five-card-majors",
      "preferred_call": "1S",
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M G"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "One five-card major and one five-card minor",
      "limitations": "Strength or suit preference alone selects no actual bid. Preserve sourced family, shape, length, balanced, strong-opening, preempt and unresolved-boundary requirements.",
      "normal_opening_strength": false,
      "policy": "Prefer the five-card major where consistent with existing sourced opening rules.",
      "policy_id": "five-major-five-minor",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M H",
        "bridge/sayc.py"
      ],
      "requires_rule20": false,
      "status": "APPROVED"
    },
    {
      "authority": "SUPPORTED_REFERENCE",
      "condition": "Clubs == 3 and diamonds == 3",
      "limitations": "Canonical production reference is not authenticated external authority.",
      "normal_opening_strength": false,
      "policy": "Existing sourced Better Minor selects 1C subject to current strength/major/NT/strong gates.",
      "policy_id": "equal-minors-3-3",
      "preferred_call": "1C",
      "production_adopted": true,
      "provenance": [
        "User-approved PHASE 29M I",
        "knowledge/bidding/systems/sayc.md#Better Minor",
        "bridge/sayc.py"
      ],
      "requires_rule20": false,
      "status": "REFERENCE_ONLY"
    },
    {
      "authority": "SUPPORTED_REFERENCE",
      "condition": "Clubs == 4 and diamonds == 4",
      "limitations": "No new universal equal-minor selector.",
      "normal_opening_strength": false,
      "policy": "Existing sourced Better Minor selects 1D subject to current strength/major/NT/strong gates.",
      "policy_id": "equal-minors-4-4",
      "preferred_call": "1D",
      "production_adopted": true,
      "provenance": [
        "User-approved PHASE 29M I",
        "knowledge/bidding/systems/sayc.md#Better Minor",
        "bridge/sayc.py"
      ],
      "requires_rule20": false,
      "status": "REFERENCE_ONLY"
    },
    {
      "authority": "UNRESOLVED",
      "condition": "Clubs == 5 and diamonds == 5",
      "limitations": "No approved selector.",
      "normal_opening_strength": false,
      "policy": "UNRESOLVED; not Pass.",
      "policy_id": "equal-minors-5-5",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M I",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "requires_rule20": false,
      "status": "UNRESOLVED"
    },
    {
      "authority": "UNRESOLVED",
      "condition": "Equal minors outside 3-3/4-4/5-5",
      "limitations": "Equal <=2 entails a five-card major in a 13-card hand; family gates still apply; not an independent minor-gap claim.",
      "normal_opening_strength": false,
      "policy": "No universal selector; 6-6 remains unresolved.",
      "policy_id": "other-equal-minors",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M I",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "requires_rule20": false,
      "status": "UNRESOLVED"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "condition": "ABSTAIN, UNKNOWN or no opening rule matched",
      "limitations": "Future Pass requires positive strength/domain conditions, exclusions, provenance and explanation.",
      "normal_opening_strength": false,
      "policy": "Never convert these outcomes to Pass or define Pass as registry complement.",
      "policy_id": "pass-fallback-prohibition",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M L/X"
      ],
      "requires_rule20": false,
      "status": "PROHIBITED"
    },
    {
      "authority": "SOURCE_INSUFFICIENT",
      "condition": "Future positive Opening Pass predicate",
      "limitations": "Normal strength and protected exclusions alone do not specify a positive Pass domain.",
      "normal_opening_strength": false,
      "policy": "Not yet defined by these approvals.",
      "policy_id": "positive-pass",
      "preferred_call": null,
      "production_adopted": false,
      "provenance": [
        "User-approved PHASE 29M D4/L",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "requires_rule20": false,
      "status": "INCOMPLETE"
    }
  ],
  "registry_complement_is_pass": false,
  "rule20_authority": "NISIM_NILY_PARTNERSHIP_POLICY",
  "rule20_definition": "HCP + longest_suit_length + second_longest_suit_length >= 20",
  "rule20_primary_hcp": 11,
  "rule22_status": "REFERENCE_ONLY",
  "safety_exclusions": [
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Equal 5-5/6-6 minors and other unsupported minor selectors",
      "exclude_from_future_pass": true,
      "exclusion_id": "equal-minors",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M I",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Below-22-HCP strong-2C playing-trick eligibility not fully formalized",
      "exclude_from_future_pass": true,
      "exclusion_id": "strong-2c-playing-tricks",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M J",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Multiple/competing long suits; 6-6 weak-two qualifiers; 7-6 weak-two/preempt overlaps; strength or distributional exceptions",
      "exclude_from_future_pass": true,
      "exclusion_id": "weak-two-preempt",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M K",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Uncovered six clubs, six-card preempt exceptions, eight-plus/four-level and generic 5-HCP preempt variants",
      "exclude_from_future_pass": true,
      "exclusion_id": "long-suit-variants",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M D4/K",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "6S-6H is outside the exact 5S-5H approval",
      "exclude_from_future_pass": true,
      "exclusion_id": "equal-majors-6-6",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M G",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Exact 5-5 majors and 11-HCP Rule20 strength may now have approved policy but remain production coverage boundaries",
      "exclude_from_future_pass": true,
      "exclusion_id": "unimplemented-approved-openings",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M D3/G"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    },
    {
      "authority": "NISIM_NILY_PARTNERSHIP_POLICY",
      "domain": "Unspecified seat/vulnerability exceptions, optional NT adjustments and unresolved opening-family applicability",
      "exclude_from_future_pass": true,
      "exclusion_id": "context-and-evaluation",
      "implies_pass": false,
      "provenance": [
        "User-approved PHASE 29M D1/D2/L",
        "bridge/opening_pass_source_policy_audit.py"
      ],
      "status": "UNRESOLVED",
      "unresolved_disposition": "UNKNOWN / ABSTAIN"
    }
  ],
  "unknown_to_pass_allowed": false,
  "unresolved_domains": [
    "equal-minors",
    "strong-2c-playing-tricks",
    "weak-two-preempt",
    "long-suit-variants",
    "equal-majors-6-6",
    "unimplemented-approved-openings",
    "context-and-evaluation",
    "positive-pass-domain"
  ],
  "version": "29M.1"
}
```
