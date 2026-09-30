# B2.4A3 Nisim-Nily Jacoby 2NT responder continuations

> Historical B2.4A3 report. B2.4A4 now verifies actual first/second controls,
> supports repeated cues with seat-specific history, and supplies approved
> maximum-opener options. See B2_4A4_JACOBY_SLAM_CONTINUATIONS.md for current
> behavior and validation. The earlier undefined-control/maximum-call limits
> below describe the A3 checkpoint, not the completed A4 implementation.

## Approved continuations

Authority: the user's B2.4A3 specification. M is opener's original major.
These meanings apply only to the explicit Nisim-Nily Jacoby profile already
introduced in B2.4A2, after uncontested 1M-P-2NT-P and an approved opener rebid.

| Opener rebid | Approved responder direction | Implemented call/meaning |
| --- | --- | --- |
| 3M: extras/slam interest | Cue-bidding for slam | Explicit legal new suit is a cue-bid showing slam interest. |
| 3M | Ace ask | 4NT asks for aces. No extra signoff or trump-rebid meaning is inferred. |
| 3NT: balanced 14-15 | Stop | 4M is signoff. |
| 3NT | Ace ask | 4NT asks for aces. |
| 3NT | Slam exploration | Explicit legal new suit is a cue-bid. |
| Three-level side-suit shortness | Cue-bid | Explicit legal new suit is a cue-bid, including at the four level. |
| Shortness | Good hand, slam interest, no suitable/available cue | 3M, only if still legal. 1S-2NT-3H-3S is supported. |
| Shortness | Ace ask | 4NT asks for aces. |
| Shortness | Insufficient strength for a direct cue/ask | 4M is a conditional stop, not a hard signoff; decision returns to opener. |
| Shortness followed by responder's 4M | Explicit minimum opener | Pass. |
| Shortness followed by responder's 4M | Explicit maximum opener | Continuation required; no exact call is defined, so abstain without Pass. |

No ace-response scheme, Blackwood/RKCB variant, cue control-round requirement,
new HCP range, or unrelated slam tool is supplied by this approval. No meaning
is inferred for repeating the previously bid shortness suit; it is not a new
suit. Unavailable cues or 3M bids abstain rather than selecting another call.

## API and reuse

Implementation extends the existing `bridge.nisim_nily_jacoby_2nt` module:

- `assess_jacoby_2nt_responder(hand, auction=..., vulnerability=..., profile=...,
  base_agreements=(), intent=None)` handles responder's exact six-call position.
- `assess_jacoby_2nt_conditional_stop(hand, auction=..., vulnerability=...,
  profile=..., base_agreements=(), strength=None)` handles opener's exact
  eight-call position after shortness and conditional 4M.
- `ResponderContinuationEvidence` carries one typed `ResponderIntent`, exact
  own hand, auction, explanation and sources. CUE_BID also supplies its specific
  `cue_call`. The auction is bound by a dealer/entry snapshot, so evidence from
  another hand, seat orientation, auction, or subsequently mutated auction is
  rejected. No partner cards or complete deal are accepted.
- Existing `OpenerStrengthEvidence` is reused. `OpenerStrength.MAXIMUM` is added
  for the approved final decision; it is not silently equated with EXTRAS and
  does not change the previous opener-rebid definitions.

The user supplied call meanings, not numeric thresholds for responder direction,
cue suitability, good hands, or maximum/minimum opener strength. Consistent with
B2.4A2, these qualitative choices require explicit sourced input. Missing input
abstains; the implementation never classifies these choices from guessed HCP
ranges. GOOD_NO_CUE is the caller's sourced assessment of all three requirements:
good hand, slam interest, and no suitable/available cue. CONDITIONAL_STOP is the
sourced assessment of insufficient strength for a direct cue/ace ask.

Existing profile resolution, exact partnership/base-system gating, supported
agreement parameter checks, shared fallback guards, core `HandEvaluation`,
`BiddingEngine`, `RuleDecision`, conflict handling, and `Auction.is_legal` are
reused. A supplied intention must have an approved meaning for the observed
opener branch and a legal call. A typed single intention yields at most one
selected call; alternatives are not guessed or ranked using new conventions.

## Explicit state and provenance

`JacobyMeaning` adds `cue_suit`, `ace_ask`, `signoff`, `good_hand`,
`no_suitable_cue`, and `conditional_stop`. Thus identical 4M calls after 3NT and
after shortness retain different meanings. The established `game_forcing` flag
continues to record the Jacoby agreement context; it is not a force beyond game.

`JacobyAssessment` adds `continuation_needed` and `continuation_sources`. For a
maximum opener after conditional 4M it returns:

- disposition ABSTAIN;
- no selected call or selected-call meaning;
- `continuation_needed=True`;
- reason/blocker explicitly stating that opener must continue and the exact call
  has not been approved;
- original approval and supplied maximum-classification sources.

Unknown, absent, or merely EXTRAS classification does not become maximum or
minimum. A blocked/wrong partnership never acquires continuation-needed status.
Selected responder and minimum-Pass decisions retain both the B2.4A2/B2.4A3
approval sources and the caller's evidence sources/explanation.

The prior response/opener APIs and their precedence remain unchanged. The new
functions do not replay earlier decisions or inspect hidden cards to requalify
the visible auction. No production route adopts these opt-in functions.

## Validation

- B2.4A3 focused tests: **103 passed**.
- Directly related B2.4A2 Jacoby tests: **107 passed**.
- Directly related Phase 29Y Nisim-Nily profile tests: **20 passed**.
- Total: **230 passed**, no failures or skips.

Coverage includes both majors; cues after extras, balanced and shortness rebids;
ace asks on all approved branches; hard versus conditional 4M; legal/unavailable
3M; minimum Pass; maximum continuation-required abstention; missing qualitative
inputs; no EXTRAS-to-MAXIMUM inference; cue legality and new-suit checks; profile
isolation/disablement; unsupported auctions; provenance; exact evidence binding;
all dealer orientations; deterministic immutable outcomes; and router isolation.

No full historical regression, unrelated compatibility suites, DDS benchmarks,
or PT research datasets were run. `git diff --check` passed.

## Remaining limits and status

Automatic responder-direction/control suitability and minimum/maximum
classification remain undefined. Maximum opener's exact continuation, answers
to 4NT, subsequent cue/slam sequences, passed-hand and interference agreements,
and production adoption remain outside this phase. No Bergen, Drury, Splinter,
or Swiss logic was added.

`production_changed = False`; routes before = 45; routes after = 45.
OneDrive was not touched. No files were staged, committed or pushed.

**Ready to commit** the approved opt-in meanings and explicit unresolved states.
