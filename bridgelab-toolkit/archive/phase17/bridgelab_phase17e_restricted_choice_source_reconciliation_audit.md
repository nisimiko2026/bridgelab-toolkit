# BridgeLab Phase 17E — Restricted Choice Source Reconciliation Audit

## Status

Phase 17E performs further source reconciliation and contract-readiness
analysis for Restricted Choice and its Vacant Places dependency.

No production probability engine is implemented in this phase.

## Baseline

Phase 17E starts from:

`dc49e39 — Phase 17D restricted choice source enrichment audit`

Branch:

`codex/phase17e`

## Candidate

**RESTRICTED_CHOICE**

Classification before:

`SOURCE_PARTIAL`

Classification after:

`SOURCE_PARTIAL`

## Source Provenance

Four relevant sources were inspected read-only:

1. `knowledge/play/declarer-play/probability/percentage-plays.md`
2. `knowledge/play/counting/vacant-places.md`
3. `knowledge/play/declarer-play/general-techniques/restricted-choice.md`
4. `knowledge/play/declarer-play/probability/finesse/a8732-vs-k1065-restricted-choice.md`

Git-history searches did not establish prior Git provenance for the three
currently untracked Restricted Choice / Vacant Places sources.

They therefore remain:

`UNTRACKED_PROVENANCE_UNRESOLVED`

and are not safe to modify or stage automatically.

`percentage-plays.md` is tracked but substantially locally modified. The
measured working-tree difference is:

- 88 insertions;
- 322 deletions.

It remains protected as pre-existing user-owned modified material.

Phase 17E does not stage, rewrite, restore, normalize, or automatically adopt
any of these protected source files.

## Vacant Places Contract

The Vacant Places source contains meaningful contract material.

It explicitly requires the analyst to:

- reconstruct as much of each opponent's original shape as possible;
- count known cards in each hand;
- determine the vacant places remaining;
- incorporate specific evidence concerning the target card;
- compare resulting probabilities;
- update the calculation when new distributional information appears.

It also warns:

`Do not count uncertain assumptions as established facts.`

The source distinguishes Vacant Places from Restricted Choice.

Vacant Places asks which hand has more room for an unknown card given known
shapes.

Restricted Choice asks what an observed selection among apparently equivalent
cards implies about the remaining equivalent card.

The source states that in some combinations both principles matter and should
be combined rather than applied in isolation.

This is substantial source evidence, but it is not yet a complete production
input contract.

Classification:

`VACANT_PLACES_INPUT_CONTRACT = SOURCE_PARTIAL`

Production gate:

`FAILED`

## Restricted Choice Observation Semantics

The Restricted Choice source contains a practical procedure for an apparently
equivalent honor.

It requires:

1. identifying relevant possible original holdings;
2. asking whether the observed card was forced from some holdings but optional
   from others;
3. considering defensive agreements and technical considerations;
4. incorporating the auction and all known distribution;
5. comparing remaining layouts before choosing the next play.

The source also makes clear that Restricted Choice does not prove that the
remaining honor must be in the other hand. The observation changes
probabilities under the appropriate assumptions.

However, the source does not yet define a complete executable production
representation for equivalent choices, forced versus optional observations,
or ambiguous/invalid observations.

Classification:

`OBSERVATION_SEMANTICS = SOURCE_PARTIAL`

Production gate:

`FAILED`

## Precision and Rounding

The worked Restricted Choice source contains exact probability examples and
also contains equality cases.

However, Phase 17E found no explicit production contract defining:

- required numerical precision;
- decimal-place policy;
- rounding policy.

Phase 17E therefore does not invent such a rule.

Classification:

`PRECISION_AND_ROUNDING = SOURCE_PARTIAL`

Production gate:

`FAILED`

## Architecture Reconciliation

Phase 17E found that the production architecture already anticipates both
Restricted Choice and Vacant Places.

`bridge/probability_questions.py` contains:

`RestrictedChoiceQuestion`

with fields including:

- `subject_suit`
- `observed_play`
- `known_cards`

and:

`VacantPlacesQuestion`

with fields including:

- `subject_suit`
- `known_seat_constraints`

Both question types are exported by the bridge package.

Phase 13F tests already exercise this scaffolding.

Therefore the architecture is not absent.

However, Phase 17E found no registered production evaluator for either
Restricted Choice or Vacant Places.

The production registry remains at:

`1`

registered probability engine:

`KNOWN_CARD_COUNT`

Therefore:

`restricted_choice_engine_registered = false`

`vacant_places_engine_registered = false`

Classification:

`ARCHITECTURE_READINESS = SOURCE_PARTIAL`

Production gate:

`FAILED`

## Unresolved Dependencies

The following blockers remain:

- `SOURCE_PROVENANCE`
- `VACANT_PLACES_INPUT_CONTRACT`
- `OBSERVATION_SEMANTICS`
- `PRECISION_AND_ROUNDING`
- `ARCHITECTURE_READINESS`

## Production Decision

`source_executable = false`

`production_implementation_authorized = false`

`new_production_recommendations = 0`

No Restricted Choice engine is added.

No Vacant Places engine is added.

No production probability formula is added.

## Safety

Phase 17E introduces:

- no new production bridge rule;
- no new probability engine;
- no new probability formula;
- no new declarer-play recommendation;
- no hidden-card inference;
- no invented precision or rounding rule;
- no automatic adoption of unresolved source material.

Protected knowledge sources remain read-only.

## Validation

Focused Phase 17E tests:

`10 passed`

Ruff:

`All checks passed!`

## Phase 17F Direction

Selected direction:

**RESTRICTED_CHOICE_CONTRACT_ENRICHMENT**

Phase 17F should continue resolving the measured contract blockers before any
production implementation.

Priority remains:

1. source provenance;
2. exact Vacant Places executable input semantics;
3. exact Restricted Choice observation semantics;
4. precision and rounding contract;
5. reconciliation of those contracts with the existing question scaffolding.

Implementation should be considered only after these gates are explicitly
measured as complete.

## Conclusion

Phase 17E improves the understanding of Restricted Choice readiness without
weakening BridgeLab's source-safety rules.

The source material contains substantial Vacant Places and Restricted Choice
reasoning, and the codebase already contains tested question scaffolding for
both concepts.

That does not yet make the capability source-executable.

The relevant sources still have unresolved provenance, the executable
contracts remain incomplete, and no corresponding production engines are
registered.

Restricted Choice therefore remains:

`SOURCE_PARTIAL`

and production implementation remains unauthorized.
