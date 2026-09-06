# BridgeLab Phase 17D — Restricted Choice Probability Source Enrichment Audit

## Status

Phase 17D performs a source/provenance/readiness audit for a future
Restricted Choice probability capability.

No production probability engine is implemented in this phase.

## Candidate

**RESTRICTED_CHOICE**

The candidate was selected after Phase 17C left Safety Play blocked by
unresolved probability dependencies, including:

- Restricted Choice;
- Vacant Places;
- conditional percentage-play reasoning.

## Source Material Inspected

The audit inspected:

1. `knowledge/play/declarer-play/probability/percentage-plays.md`
2. `knowledge/play/counting/vacant-places.md`
3. `knowledge/play/declarer-play/general-techniques/restricted-choice.md`
4. `knowledge/play/declarer-play/probability/finesse/a8732-vs-k1065-restricted-choice.md`

These files were inspected read-only.

Phase 17D does not authorize automatic staging, rewriting, restoration,
normalization, or canonical adoption of protected pre-existing source files.

## Provenance Finding

The current workspace contains unresolved source provenance.

In particular, source material required by the Restricted Choice candidate
includes files currently classified as:

`UNTRACKED_PROVENANCE_UNRESOLVED`

Such files are:

- not safe to modify;
- not safe to stage;
- not automatically treated as canonical production knowledge.

The existing modified `percentage-plays.md` source is also treated as
pre-existing user-owned material and is not rewritten by Phase 17D.

Therefore the production source-provenance gate remains closed.

## Worked Restricted Choice Contract

The inspected worked source contains an explicit bounded Restricted Choice
example.

The audit confirms that the worked material contains:

- an observed defender card;
- competing locations for the missing queen;
- Restricted Choice weighting;
- Vacant Places conditioning;
- explicit posterior probability expressions;
- an exact subsequent card-play rule for the worked position.

The source states the bounded expressions:

`P(Q West | J played) = W / (W + E/2)`

and

`P(Q East | J played) = (E/2) / (W + E/2)`

where the worked material describes `W` and `E` as remaining vacant places
after accounting for known cards.

The worked source also states:

- if the queen is more likely with West, play the 10;
- if the queen is more likely with East, play the king.

Phase 17D records these statements as source observations only.

It does not generalize them into a production probability formula.

## Percentage-Play Dependency

The inspected percentage-play material explicitly requires decisions to use
current posterior probabilities rather than an unconditional memorized
pre-play percentage.

Therefore a future card-play recommendation cannot safely use the worked
Restricted Choice example without a complete probability-input contract.

## Passed Readiness Gates

The audit confirms:

- worked Restricted Choice formula present;
- worked subsequent-action rule present;
- posterior-probability dependency documented;
- no hidden-information invention in the Phase 17D audit;
- no new probability formula invented by Phase 17D.

## Failed / Unresolved Readiness Gates

### Source provenance

**FAILED**

All required production sources do not yet have resolved provenance.

### Vacant Places contract

**FAILED**

Vacant Places input semantics have not yet been established as a complete
production contract.

### Observation semantics

**FAILED**

Observed-card and forced-choice boundaries are not yet sufficiently specified
for production.

### Precision and rounding

**FAILED**

The exact output precision and rounding contract remains unresolved.

### Architecture readiness

**FAILED**

The current production probability architecture has not yet been proven to
represent every required Restricted Choice input safely.

## Unresolved Dependencies

The Phase 17D audit records:

- `SOURCE_PROVENANCE`
- `VACANT_PLACES_INPUT_CONTRACT`
- `OBSERVATION_SEMANTICS`
- `PRECISION_AND_ROUNDING`
- `ARCHITECTURE_READINESS`

## Classification

Restricted Choice is **not SOURCE_EXECUTABLE** at the end of Phase 17D.

The worked source is substantially more specific than a qualitative bridge
description, but the production-readiness contract is incomplete.

## Production Decision

`source_executable = false`

`production_implementation_authorized = false`

`new_production_recommendations = 0`

No Restricted Choice engine is registered.

The production probability-engine count remains:

`1`

The existing registered engine remains:

`KNOWN_CARD_COUNT`

unchanged.

## Safety

Phase 17D introduces:

- no production bridge rule;
- no bidding route;
- no declarer-play algorithm;
- no defensive-play algorithm;
- no opening-lead algorithm;
- no production probability formula;
- no default partnership policy;
- no hidden-card inference;
- no new production recommendation.

The audit does not infer missing bridge theory or missing probability rules.

## Validation

Focused Phase 17D tests:

`10 passed`

Combined Phase 17B + Phase 17C + Phase 17D tests:

`28 passed`

Ruff:

`clean`

## Historical Preservation

Phase 17B Safety Play source-enrichment conclusions remain unchanged.

Phase 17C Safety Play remains:

`SOURCE_PARTIAL`

and production implementation remains unauthorized.

`SIMPLE_UNBLOCK_KING` remains unchanged.

`KNOWN_CARD_COUNT` remains unchanged.

Production bidding routes remain unchanged.

Phase 14, Phase 15, and Phase 16 completion status remains unchanged.

## Phase 17E Direction

Selected direction:

**FURTHER_RESTRICTED_CHOICE_SOURCE_ENRICHMENT**

A production Restricted Choice implementation is premature.

The next phase should resolve the measured blockers rather than implement the
worked formula directly.

Priority should be:

1. source provenance;
2. exact Vacant Places input semantics;
3. Restricted Choice observation / forced-choice semantics;
4. exact output precision contract;
5. architecture representation.

Only after those gates are measured as complete should implementation of a
Restricted Choice probability engine be considered.

## Conclusion

Phase 17D confirms that the existing worked Restricted Choice material
contains both an explicit probability relationship and a bounded subsequent
card-play rule.

However, the presence of a worked equation is not sufficient for production
implementation.

Source provenance, Vacant Places semantics, observation boundaries,
precision, and architecture readiness remain unresolved.

Therefore Phase 17D deliberately abstains from implementing a new probability
engine.

This blocked result is intentional and source-safe.
