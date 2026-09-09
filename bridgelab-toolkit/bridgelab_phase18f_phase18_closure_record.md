# BridgeLab Phase 18F — Phase 18 Closure Record

## Closure decision

Phase 18 is complete through:

- Phase 18B: provenance gate
- Phase 18C: formula-neutral probability input contracts
- Phase 18D: public observation semantics
- Phase 18E: exact `ProbabilityValue` policy
- Phase 18F: readiness reassessment

Final decision: **PHASE_18_CLOSED_WITH_RC_VP_DEFERRED**.

No Phase 18G implementation is authorized under the current evidence state.

## Production-ready capabilities

- Typed Restricted Choice question contract
- Typed Vacant Places question contract
- Public-evidence-only adapters
- Deterministic Restricted Choice observation statuses
- Deterministic Vacant Places vacant-slot arithmetic
- Exact `ProbabilityValue` representation
- Provenance and authentication framework

## Deferred and unauthorized capabilities

- Restricted Choice numeric probability formula
- Vacant Places weighting formula
- Vacant Places normalization-to-probability formula
- Restricted Choice and Vacant Places numeric test oracles
- Restricted Choice and Vacant Places engine registration
- Probability-based recommendation thresholds

## Source states at closure

- `knowledge/play/declarer-play/probability/percentage-plays.md` = `TRACKED_BASELINE_PRESENT_BUT_HISTORICAL_CONTENT_UNAVAILABLE`
- `knowledge/play/counting/vacant-places.md` = `MISSING`
- `knowledge/play/declarer-play/general-techniques/restricted-choice.md` = `MISSING`
- `knowledge/play/declarer-play/probability/finesse/a8732-vs-k1065-restricted-choice.md` = `MISSING`

Authenticated historical Phase 17 recorded outputs are evidence of what Phase 17 recorded, but they are not reproducible source authority for production formulas.

## Reopening criteria

Restricted Choice may reopen only when all of the following are available:

- An authenticated source rule or formula
- Reproducible worked examples
- Observation semantics compatible with the existing public-evidence contract
- Exact expected numeric values suitable for deterministic tests

Vacant Places may reopen only when all of the following are available:

- An authenticated weighting rule
- An authenticated normalization rule if probabilities are produced
- Reproducible worked examples
- Exact expected numeric values suitable for deterministic tests

Display-rounding authority is not required if the core implementation returns an exact `ProbabilityValue`.

## Architecture invariants at closure

- Production recommendations: 4
- Routes: 45
- Registered probability engines: 1
- Registered probability type: `KnownCardCountQuestion` only
- Restricted Choice registered: false
- Vacant Places registered: false
- Restricted Choice formulas: 0
- Vacant Places formulas: 0

## Baseline identity

- Branch: `codex/phase18b`
- Closure baseline HEAD: `ed28fee4141e3a3354d055cf3b9c1d3227ab7a1e`

Phase 18 adds no Restricted Choice or Vacant Places formula, engine registration, numeric test oracle, recommendation threshold, or placeholder Phase 18G implementation.
