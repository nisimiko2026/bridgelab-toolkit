# B2.4B3 — Nisim–Nily Standard Bergen activation

## Authority and active card

The user's B2.4B3-FINAL agreement is the authority for this card revision.
It replaces the earlier 3C/3D mapping and explicitly defines 3M as a 0–5 HCP
weak direct raise with exactly four trumps. Generic reference prose supplies
no executable defaults.

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
| 3C | 6–9 | Exactly 4 | Artificial Bergen raise | Nonforcing |
| 3D | 10–12 | Exactly 4 | Artificial Bergen limit raise | Invitational, not game forcing |
| 3M | 0–5 | Exactly 4 | Weak natural direct raise | Nonforcing |
| 2NT | 13+ | 4+ | Existing artificial Jacoby raise | Game forcing |

The 3M, 3C and 3D branches each require exactly four trumps. Their HCP
ranges are 0–5, 6–9 and 10–12 respectively, with no overlap. Simple 2M uses
exactly three trumps; Jacoby uses 13+ HCP and 4+ trumps. The existing generic
selector consumes these resolved predicates unchanged. No generic Bergen rule
contains this partnership's numeric mapping.

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

- Below 13 HCP with 5+ trumps.
- 0–5 or 10+ HCP with exactly three trumps.
- Fewer than three trumps, regardless of strength.

No fallback bid is invented for those bands in the active card composition.
Other profiles' existing non-Bergen logic is preserved. Passed-hand prefixes and
competitive auctions remain unsupported here. No Bergen opener continuations
or subsequent responder continuations were added. Jacoby continuation meanings
remain unchanged. No Drury, Splinter, Swiss, DDS or PT valuation work is included.

## Focused validation

Final correction validation: **741 passed**, no failures or skips, exit 0.
This includes 143 B2.4B3 cases covering both majors, HCP/support boundaries,
exact support limits, unique selected calls, meaning/provenance, interference
(including 0 and 5 HCP weak raises), seat orientation, deterministic selection,
partnership isolation and absence of Bergen opener continuations. B2.4B2,
related first-response/profile tests and Jacoby A2/A3/A4 compatibility passed.

```text
python -m pytest -q tests/test_bridge_b24b3_standard_bergen.py tests/test_bridge_b24b2_bergen_configuration.py tests/test_bridge_b21_first_response.py tests/test_bridge_phase29x_partnership_profiles.py tests/test_bridge_phase29y_nisim_nily_partnership_profile.py tests/test_bridge_b24a2_nisim_nily_jacoby_2nt.py tests/test_bridge_b24a3_jacoby_continuations.py tests/test_bridge_b24a4_jacoby_slam_continuations.py
```

No historical regression or research datasets were run.
`production_changed = False`; routes before = 45; routes after = 45.
Activation is in the opt-in first-response API, not the production router.
All work used the Documents phase18b worktree on `codex/phase18b`, starting at
`86537c983301136731cdc0b55b29259ee0544a0b`. OneDrive was untouched.
The earlier B2.4B3 work was committed as
`d7d5645e9388b6dd717beef81adb4ee40e2c110f` before this correction request.
This correction starts from that actual HEAD; no history is rewritten and no
correction is staged, committed or pushed. Ready to commit the final mapping.
The knowledge reference `knowledge/bidding/conventions/responses/bergen-raises.md`
now states 3M = 0–5 HCP, 3C = 6–9 HCP and 3D = 10–12 HCP, each with exactly
four-card support. Its table, 3M section, examples and summary agree.
