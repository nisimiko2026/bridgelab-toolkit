# B1.3 Opening Policy consolidation

The existing `assess_opening_policy_with_six_minor` API is the current,
partnership-only consolidation entry point. It returns one immutable decision
(or explicit unresolved evidence), with selected family, reason and provenance.
It does not register production routes. Its version is now B1.3.

## Reused evaluation and policy evidence

- `HandEvaluation` supplies HCP, suit lengths, shape, suit HCP, ace evidence and
  Rule-of-20 arithmetic. Six-minor thresholds and quality meanings are unchanged.
- Phase 29S supplies the existing family checks and approved, incomplete strong
  2C component evidence. No additional playing-trick formula is introduced.
- Phase 29T supplies exact-six-minor quality/seat/vulnerability qualification.
- Phase 30N supplies approved 1NT shapes, minor selection and strong precedence.
- The B1.3 instruction supplies the explicit <=9 HCP exact-five-five-major Pass
  invariant. It does not extend to six-five/six-six or 10 HCP.

## Selection order

1. A qualified Strong 2C precedes every other call, including strong-minor Multi
   and the six-minor policy's local one-level result. Unknown Strong 2C
   qualification blocks a lower call.
2. Preserve the already approved strong Multi meanings (20-22 balanced and
   qualified 20-21 strong minor) and approved 1NT openings. These hands are not
   ordinary one-level candidates. Replacing these calls with a Rule20 suit
   opening would change the approved meanings. Unresolved strong Multi stays
   unresolved.
3. Ordinary one-level strength (12+ HCP or core Rule20 >=20) selects an approved
   major/minor denomination before weak or preemptive treatments. Phase 30N
   resolves the old six-major/five-minor and unequal-minor selector gaps.
4. Apply the explicitly approved Nisim-Nily shape exceptions after ordinary
   one-level selection:
   - Exact 4441 with exactly 11 HCP and singleton below Jack opens 1D when diamonds
     have four cards, otherwise 1C. Ten qualifies; J/Q/K/A do not. No other HCP or
     shape is admitted by this exception.
   - Exact 4333 passes unless its four-card suit is spades, position is third or
     fourth, and spades contain at least King (King or Ace), or all of Q/J/T.
     That qualifying case opens 1C. Earlier seats, a non-spade four-card suit,
     or insufficient spade quality explicitly select Pass.
   - These exceptions cannot override Strong 2C, approved strong-Multi/1NT, or
     ordinary one-level rules. No extra HCP floor was added to the 4333 exception.
   Exact five-five majors <=9 pass by the explicit B1.3 instruction; that shape
   cannot enter the six-minor preempt branch.
5. Retain unresolved weak-Multi/preempt and weak-two-suited qualifications.
   The approved six-minor preempt applies only below one-level strength and when
   no independent blocker remains.
6. Otherwise preserve the historical all-negative-family Pass evidence or its
   explicit unresolved disposition. Failure to select an opening is not Pass.

## Approval provenance and remaining boundaries

The user's B1.3 completion instruction explicitly supplied the previously
approved 4333 and 4441 agreements. Both are now encoded in the existing
integration function, using core distribution, HCP and suit honor evidence.
Selected results carry the B1.3 completion provenance, reason and family.
The former missing-shape-agreement limitation is resolved.

Existing unresolved domains remain: incomplete Strong 2C component evidence,
semi-balanced strong-minor Multi, unapproved strong balanced Multi shapes,
weak-Multi versus preempt level choice, qualitative weak-two-suited strength and
quality, and later-seat/individual-review cases. No new thresholds fill these gaps.

## API and migration

The existing integration function name and required arguments remain. Optional
`profile` and `decisions` arguments accept only the canonical Nisim-Nily profile
and approved decision contract. Other systems/partnerships, altered treatments,
duplicate family evidence, contradictory call/state evidence and contradictory
six-minor results are rejected. The result adds `selected_family` and `provenance`.

Historical `assess_opening_policy` retains Phase 29S assessment semantics for
historical audit reproducibility; only its duplicated Rule20 arithmetic changed
to core evaluation. Its result is included as `base`, not a competing current
selected outcome. Use the existing integration entry point for consolidated
B1.3 selection. `assess_six_minor_three_level_preempt` remains a local family
assessment, not a complete opening decision. The profile pilot adapter remains
limited to that family and is not promoted to a complete opening policy.

## Validation

The initial consolidation run passed 295 focused tests, including 62 B1.3 tests. It included existing
29M, 29Q, 29R, 29S, 29T, 29U, 30C, 30D, 30L, 30M and 30O tests, plus B1.2 core
hand evaluation. Two 29U expectations explicitly migrate to the B1.3 version and
later-approved 30N unequal-minor selector. The 29S historical evidence tests
remain unchanged and pass.

The completion run passed **284 opening-policy focused tests**, including all
**155 B1.3 tests** (93 added cases and two updated prior shape expectations).
The other selected modules were 29S, 29T, 29U, 30C, 30D and 30O. Coverage includes
all singleton orientations, low singleton 2/T, J/Q/K/A exclusion, exact HCP/shape
boundaries, all seats, King/Ace/QJT and insufficient spade holdings, higher-priority
opening preservation, explicit provenance and partnership/system isolation.
The production router count was checked before and after: 45 in both cases.

No full historical regression, DDS or PT-A datasets were run. No PT-A code,
production router or general-system opening rule was changed.

`production_changed = False`; routes before = 45; routes after = 45.
No staging, commit, push or Batch-1 checkpoint work.