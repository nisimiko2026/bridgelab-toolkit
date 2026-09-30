# B2.4B3 — Nisim–Nily Standard Bergen activation

## Authority and active card

The user's B2.4B3 agreement is the authority for this card revision. It supersedes
older incomplete Nisim–Nily Bergen fragments (8–10 simple raise / weak 3M) for
this explicit opt-in profile. Generic Bergen reference prose supplies no values.

Use `NISIM_NILY_BERGEN_PROFILE`, version `B2.4B3`, layered on `TWO_OVER_ONE_GF`.
The original Phase 29Y and Jacoby profile snapshots are unchanged. The incomplete
B2.4B2 snapshot remains available as `NISIM_NILY_BERGEN_PROFILE_B24B2`; its tests
now name that snapshot explicitly. Its incompleteness safeguards remain intact.

The active `response.major.raises` selection is `BERGEN_RAISES` with all four
branches enabled, `variant=STANDARD`, `competition=UNCONTESTED_ONLY`,
`strength_metric=hcp`, and `branch_policy=exclusive`.

| Response after 1H/1S–Pass | HCP | Support | Meaning | Forcing status |
| --- | --- | --- | --- | --- |
| 2M | 6–9 | Exactly 3 | Natural simple raise | Nonforcing |
| 3C | 10–12 | 4+ | Artificial Bergen limit raise | Invitational, not game forcing |
| 3D | 0–6 | 4+ | Artificial Bergen preemptive raise | Nonforcing |
| 3M | 7–9 | Exactly 4 | Natural mixed raise | Nonforcing |
| 2NT | 13+ | 4+ | Existing artificial Jacoby raise | Game forcing |

The card records a support maximum of 13 for 4+ branches: the physical hand
limit. HCP and support predicates together are mutually exclusive. No generic
Bergen rule contains this partnership's numeric mapping.

## First-response selection and compatibility

`assess_first_response(..., profile=NISIM_NILY_BERGEN_PROFILE)` composes the
existing card-driven `assess_bergen_response` and the existing dedicated Jacoby
assessor. The card's `defer_to_jacoby` relationship references the separate
`nisim_nily_jacoby_2nt` treatment and its unchanged parameters. Bergen itself
never selects 2NT or duplicates Jacoby's rule. Generic direct Bergen callers
still receive `DEFER_TO_JACOBY` for that region.

The generic parser now preserves optional `variant` and `competition` metadata.
A variant label supplies no implicit call mapping. An explicitly requested
competition mode other than `UNCONTESTED_ONLY` is rejected. Earlier complete
B2.4B2 cards remain supported with their existing exact-uncontested scope.

Only exact first-response prefixes `1H P` and `1S P` are enabled. Unsupported
auctions, interference and uncovered hands abstain. Other existing profiles
retain their prior routing/guards. Card-based results have `route_id=None`
because no standard production route executed them; selected-rule provenance
and the complete resolved profile are preserved. Invalid card configurations
still raise, incomplete cards abstain, and unresolved overlaps never select an
arbitrary winner. No new public evaluator or alternative resolver was added.

Provenance includes `bidding/convention-cards/cc-nily-nisim` and this approval ID,
`B2_4B3_STANDARD_BERGEN`. Resolved parameters retain PARTNERSHIP source scope.
The historical corpus card is not parsed at runtime or silently rewritten.

## Deliberate gaps

Within the major-raise selector, these bands remain uncovered:

- 7–9 HCP with 5+ trumps (mixed raise requires exactly four).
- 0–5 or 10+ HCP with exactly three trumps.
- Fewer than three trumps, regardless of strength.

No fallback bid is invented for those bands in the active card composition.
Other profiles' existing non-Bergen logic is preserved. Passed-hand prefixes and
competitive auctions remain unsupported here. No Bergen opener continuations
or subsequent responder continuations were added. Jacoby continuation meanings
remain unchanged. No Drury, Splinter, Swiss, DDS or PT valuation work is included.

## Focused validation

788 passed, no failures or skips, exit 0. This includes 135 new B2.4B3 cases:
both majors, HCP/support boundaries, exact support limits, disjoint candidates,
meaning/provenance, intervention, seat orientation, deterministic first-response
selection, partnership isolation and absence of Bergen opener continuations.

```text
python -m pytest -q tests/test_bridge_b24b3_standard_bergen.py tests/test_bridge_b24b2_bergen_configuration.py tests/test_bridge_b24b_bergen_audit.py tests/test_bridge_b21_first_response.py tests/test_bridge_phase29x_partnership_profiles.py tests/test_bridge_phase29y_nisim_nily_partnership_profile.py tests/test_bridge_b24a2_nisim_nily_jacoby_2nt.py tests/test_bridge_b24a3_jacoby_continuations.py tests/test_bridge_b24a4_jacoby_slam_continuations.py
```

No historical regression or research datasets were run.
`production_changed = False`; routes before = 45; routes after = 45.
Activation is in the opt-in first-response API, not the production router.
All work used the Documents phase18b worktree on `codex/phase18b`, starting at
`86537c983301136731cdc0b55b29259ee0544a0b`. OneDrive was untouched.
Nothing was staged, committed or pushed. Ready to commit this responder-only phase.
