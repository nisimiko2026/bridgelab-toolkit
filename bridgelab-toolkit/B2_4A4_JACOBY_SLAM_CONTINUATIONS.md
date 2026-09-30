# B2.4A4 Nisim-Nily Jacoby 2NT slam continuations

## Approved cue and maximum-opener rules

Authority: the user's B2.4A4 specification, applied to the existing explicit
Nisim-Nily Jacoby agreement. B2.4A3 was uncommitted at the starting checkpoint
`87e6c2c8549d8639879f141919f1e307259140e7`; its work is retained and extended.
No commit or staging was performed.

A first cue in a side suit shows first-round control. A second cue in that same
suit requires a previously shown first-round cue and shows second-round control.
Both partners may cue. Every selected cue must be legal and justified by actual
core `HandEvaluation` control facts in the current player's hand. HCP, direction
metadata, and a partner's past cue never create a missing control in that hand.

The existing core defines first-round control as Ace or void, and second-round
control as guarded King or singleton. These definitions are reused without new
arithmetic. The returned `control_basis` states `ace`, `void`, `guarded king`, or
`singleton`, so a shortness control is never mislabeled as a held honor. A4 tests
exercise actual Aces and Kings, as well as the core shortness-control cases.

The original opener's three-level shortness rebid is not recorded as an Ace cue:
it can show either a singleton or void, so first-round control is not established
by that call alone. Outside the explicitly approved maximum-opener 4S path,
repeating that suit without an established cue meaning abstains. A third cue
of an already twice-cued suit has no approved meaning and abstains.

## History and ownership

`CueControlEvidence` records suit, control round, bidding seat, zero-based auction
index, exact call, basis and A4 source. Earlier cues are recorded as **auction
control claims**, not verified hidden card holdings. The currently selected cue
records its actual hand control basis. No complete deal or other hand is used.

For the user's sequence (opponent passes included in executable inputs):

`1H P 2NT P 3C P 3D P 3S P`, then responder's `4S`:

- 3C is opener's shortness, not an Ace cue.
- 3D at index 6 is responder's first-round diamond control claim.
- 3S at index 8 is opener's first-round spade control claim.
- 4S at index 10 requires responder's second-round spade control. A guarded King
  selects 4S with basis `guarded king`; the opener's earlier Ace claim cannot
  substitute for responder's missing King/control.

The same player can later show the other control round when its actual holding
supports it. Ownership is derived from auction seats, not hard-coded North/South;
all four dealer orientations are tested. Interference, unsupported calls, or
unknown control histories stop interpretation rather than granting cue rights.

## Continuation API and deterministic selection

The existing `bridge.nisim_nily_jacoby_2nt` module, profile resolver/gates,
`BiddingContext`, core evaluation, `BiddingEngine`, `RuleDecision`, legality and
provenance handling are reused. No parallel convention family or router exists.

New public entry point:

`assess_jacoby_2nt_slam_continuation(hand, auction=..., vulnerability=...,
profile=..., base_agreements=(), intent=None, strength=None)`

It dispatches the initial responder position to the existing responder function,
the conditional-4M position to the existing conditional-stop function, and
interprets subsequent approved cue/ace-ask positions for either partnership seat.
The existing responder API now also checks actual controls, so it cannot bypass
A4. The existing conditional-stop API gains the optional `intent` argument.

`JacobyContinuationIntent` and `JacobyContinuationEvidence` alias the existing
responder direction types for use by either player. Evidence remains bound to
the exact hand and auction snapshot with explanation and sources. A cue contains
its selected `cue_call`; optional `cue_round=1/2` asserts the intended round and
must agree with history. Without that field, the round follows established cue
history. Control is always checked from the hand.

No priority among several available cue suits, ace ask, and direct slam was
approved. Therefore direction and the exact cue remain explicit sourced input,
yielding one deterministic outcome. Missing/unsupported direction abstains.
The GOOD_NO_CUE path still requires a sourced good-hand/slam-interest assessment,
and now rejects that fallback when a legal approved control cue is available.
Only the previously approved immediate 3M fallback is used, and only when legal.
No general later trump-signoff or no-cue fallback is invented.

## Maximum after conditional 4M

The distinction between signoff after opener's 3NT and conditional stop after
shortness is retained. After shortness-4M:

- Sourced MINIMUM -> Pass, unchanged.
- Sourced MAXIMUM + ACE_ASK direction -> 4NT, ace ask.
- Sourced MAXIMUM + hearts trump + legal 4S cue direction -> 4S, requiring the
  actual appropriate spade control. This explicit approval also applies when
  the original shortness suit was spades; that original bid still does not
  establish an Ace or authorize a second-round King cue.
- Sourced MAXIMUM + DIRECT_SLAM direction -> the explicitly selected 6M or 7M.
  This direction attests sufficient strength for that specific trump slam,
  with explanation and provenance. There is no numeric classifier or inferred
  choice between small/grand slam. Other strains and levels remain unapproved.
- Absent/UNKNOWN/merely EXTRAS classification is not automatically MAXIMUM.
- Missing or unsupported maximum direction leaves `continuation_needed=True`,
  with ABSTAIN, no selected call, and preserved reason/source evidence.

Answers to 4NT, further bidding after a direct slam, and unrelated slam methods
are not defined. History replay stops at ace asks, hard signoffs, or direct slams.
No Blackwood/RKCB variant, response scale, or subsequent keycard method is added.

## Typed meanings and compatibility

`JacobyMeaning` adds `control_round`, `control_basis`, and `direct_slam`.
`JacobyAssessment.control_history` preserves interpreted and selected cue evidence.
The existing artificial/GF, cue, ace-ask, signoff, conditional-stop, and
continuation-needed metadata remain intact. Selected A4 cues/maximum actions cite
A4 approval plus prior agreement and caller evidence sources.

The opt-in profile is unchanged; SAYC, generic 2/1, other partnerships and the
legacy non-Jacoby Nisim-Nily snapshot do not acquire these continuations.
Existing initial 13+ HCP / 4+ support and opener rules remain unchanged.

A3 fixture updates are intentional: positive cue fixtures now contain actual
Aces; no-cue fixtures contain no first-round control. The maximum-without-direction
expectation now says a direction must be supplied rather than claiming no exact
call is approved. A3 still tests all its prior 103 cases. Its report is retained
as the historical stage report with an A4 supersession note.

## Validation

- B2.4A4 focused: **59 passed**.
- B2.4A3 directly related: **103 passed**.
- B2.4A2 directly related: **107 passed**.
- Phase 29Y Nisim-Nily profile: **20 passed**.
- Total: **289 passed**, no failures or skips.

Tests cover first/second controls; missing prior first control; wrong suit,
wrong round, missing current control and third repetition; both players and
seat ownership; shortness versus an Ace claim; core void/singleton control bases;
4NT; conditional 4M/minimum Pass; maximum ace ask, heart-trump 4S, and direct
trump slam; no-cue 3M fallback; partnership isolation; deterministic results;
unapproved follow-ups; and unchanged production routing.

No historical regression, DDS, PT datasets, or unrelated compatibility suites
were run. No PT/research code, global system option, evaluation arithmetic or
production routing was changed. `git diff --check` passed.

`production_changed = False`; routes before = 45; routes after = 45.
No staging, commit, push, Bergen, Drury, Splinter, or Swiss work. OneDrive untouched.

**Ready to commit.** Remaining gaps are sourced automatic strength/direction
classification, cue-choice policy, ace-ask answers and further unapproved slam
sequences; these remain explicit abstentions rather than new meanings.
