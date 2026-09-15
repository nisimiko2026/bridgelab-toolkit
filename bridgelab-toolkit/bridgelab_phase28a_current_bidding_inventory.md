# Phase 28A - Current Bidding Inventory

## Purpose

Re-audit the two Phase 12U families that were still marked `NOT_YET_AUDITED`, using the current production tree rather than the old Phase 12 simulation snapshot.

This phase is audit-only. It adds no bidding rule, route, policy, default, or knowledge semantics.

## Production router

- Current production route count: **45**

## One-level response inventory

| Module | Rules | Source pointers | not_applicable guards |
|---|---:|---:|---:|
| bridge/sayc_responses.py | 5 | 5 | 7 |
| bridge/sayc_1d_responses.py | 3 | 5 | 5 |
| bridge/sayc_1h_responses.py | 4 | 6 | 13 |
| bridge/sayc_1s_responses.py | 3 | 6 | 10 |
| bridge/sayc_1d_notrump.py | 2 | 4 | 9 |
| bridge/sayc_major_one_notrump.py | 2 | 4 | 8 |
| bridge/two_over_one_responses.py | 0 | 6 | 10 |

## Opener-rebid inventory

| Module | Rules | Source pointers | not_applicable guards |
|---|---:|---:|---:|
| bridge/sayc_1c1d_opener_rebids.py | 4 | 3 | 10 |
| bridge/sayc_1c1h_opener_rebids.py | 4 | 3 | 12 |
| bridge/sayc_1c1s_opener_rebids.py | 6 | 5 | 20 |
| bridge/sayc_1d1h_opener_rebids.py | 6 | 5 | 18 |
| bridge/sayc_1d1s_opener_rebids.py | 6 | 7 | 21 |
| bridge/sayc_1h1s_opener_rebids.py | 4 | 4 | 15 |
| bridge/sayc_major_raise_opener_rebids.py | 0 | 4 | 4 |
| bridge/two_over_one_opener_rebids.py | 4 | 4 | 17 |

## Phase 12U family re-audit

| Family | Phase 12U | Current rules | Routes | Sources | Guards | Classification | Decision |
|---|---|---:|---:|---:|---:|---|---|
| response.one-level-existing-rule | NOT_YET_AUDITED | 19 | 4 | 36 | 62 | CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE | AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION |
| opener.one-level-rebid-existing-rule | NOT_YET_AUDITED | 34 | 12 | 35 | 117 | CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE | AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION |

## Interpretation

The Phase 12U `NOT_YET_AUDITED` labels are historical. Current production contains explicit source-grounded rules and routes for both families. Phase 28A records that current structure without claiming that every possible SAYC branch is source-complete.

Explicit `not_applicable` guards are treated as normal conservative rule eligibility/precedence behavior, not automatically as coverage defects.

## Previously audited deferred families

| Family | Classification | Decision |
|---|---|---|
| Stayman residuals | SOURCE_PARTIAL | DEFER |
| strong-2C residuals | SOURCE_PARTIAL | DEFER |
| natural 1NT responses | SOURCE_PARTIAL | DEFER |
| responder rebids | SOURCE_PARTIAL | DEFER |
| three-level preempt responses | SOURCE_PARTIAL | DEFER |
| weak-two responses | PARTNERSHIP_DEPENDENT | DEFER_POLICY_REQUIRED |
| 2NT response residuals | SOURCE_PARTIAL | DEFER |
| Two-over-One unsupported opener rebids | SOURCE_INSUFFICIENT | DEFER |

These families remain deferred unless a frozen source or explicit partnership policy supplies an executable contract. Phase 28A does not convert approximate, qualitative, or partnership-dependent wording into hard production thresholds.

## Guards

- production rules added: 0
- routes added: 0
- policies added: 0
- production defaults changed: False
- knowledge Markdown changed: 0

## Closure readiness

- closure_ready: **True**
- decision: **PROCEED TO PHASE 28 FINAL CLOSURE AUDIT**

Phase 28A does not claim complete SAYC coverage. It establishes whether the two old Phase 12U untouched buckets now have enough current source-grounded production structure to move to a final closure audit instead of expanding production merely to reduce abstention counts.
