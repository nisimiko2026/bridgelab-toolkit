# BridgeLab Phase 17F — Restricted Choice Contract Enrichment Audit

## Status

Phase 17F performs a conservative Restricted Choice contract-enrichment audit.

The phase does **not** authorize a new production probability engine, does **not** add a new production recommendation, and does **not** modify any protected knowledge source.

Final classification:

**SOURCE_PARTIAL**

Production implementation:

**NOT AUTHORIZED**

New production recommendations:

**0**

Registered probability engines:

**1 — KNOWN_CARD_COUNT**

---

## 1. Objective

Phase 17F continues the source-readiness work established in Phases 17D and 17E.

The objective is to determine whether the available Restricted Choice and Vacant Places material now supplies enough explicit source-backed semantics to authorize a bounded production implementation.

The audit focuses on five unresolved dependencies:

1. `SOURCE_PROVENANCE`
2. `VACANT_PLACES_INPUT_CONTRACT`
3. `OBSERVATION_SEMANTICS`
4. `PRECISION_AND_ROUNDING`
5. `ARCHITECTURE_READINESS`

No missing bridge rule, probability formula, input semantic, precision rule, or production default is invented to close these gaps.

---

## 2. Sources Examined

The following knowledge sources were inspected read-only:

- `knowledge/play/counting/vacant-places.md`
- `knowledge/play/declarer-play/general-techniques/restricted-choice.md`
- `knowledge/play/declarer-play/probability/percentage-plays.md`
- `knowledge/play/declarer-play/probability/finesse/a8732-vs-k1065-restricted-choice.md`

No Phase 17F change was made to these files.

The current provenance state remains protected:

- `vacant-places.md` — untracked, provenance unresolved
- `restricted-choice.md` — untracked, provenance unresolved
- `a8732-vs-k1065-restricted-choice.md` — untracked, provenance unresolved
- `percentage-plays.md` — tracked but locally modified / user-owned

Accordingly, none of these sources is safe to stage as part of Phase 17F.

---

## 3. Source Provenance Reconciliation

Phase 17F extended the provenance investigation beyond Phase 17E.

A second file named `vacant-places.md` was discovered under:

`phase17c_fullkit_temp/bridgelab-toolkit/output/backups/spelling-repair-20260816-01/play/declarer-play/probabilty/vacant-places.md`

The discovered artifact is historical evidence only.

Measured comparison:

- historical artifact: 374 lines
- current `knowledge/play/counting/vacant-places.md`: 165 lines
- the SHA-256 hashes differ
- the files are not identical

The historical artifact is not Git-tracked.

Git searches also found no usable history for `vacant-places.md`.

Therefore the discovered backup does not establish canonical provenance for the current source.

Gate result:

`SOURCE_PROVENANCE = BLOCKED`

Production gate:

**FAILED**

---

## 4. Vacant Places Input Contract

The current Vacant Places source contains meaningful contract material.

### Relationship to Restricted Choice

The source explicitly distinguishes the two probability questions.

Vacant Places asks which hand has more room for an unknown card given known shapes.

Restricted Choice asks what an observed selection among equivalent cards implies about the remaining equivalent card.

The source further states that, when both principles apply, the Restricted Choice inference should be combined with distributional odds supplied by Vacant Places rather than applied in isolation.

This establishes an important conceptual boundary between the mechanisms.

### Practical Procedure

The source provides the following source-backed procedure:

1. reconstruct as much of each opponent's original shape as possible;
2. count the known cards in each hand;
3. determine the vacant places remaining;
4. incorporate specific evidence concerning the target card;
5. compare the resulting probabilities;
6. update the calculation when new distributional information appears.

### Uncertainty Guard

The source also explicitly warns:

`Do not count uncertain assumptions as established facts.`

This is a meaningful safety constraint.

### Remaining Gap

The source still does not provide a complete executable input and validation contract.

Among the unresolved semantics are formal representation of partial or uncertain shape information, precise treatment of known-card evidence, representation of target-card evidence, validation of conflicting constraints, and the exact probability-output contract.

Phase 17F does not invent those semantics.

Gate result:

`VACANT_PLACES_INPUT_CONTRACT = SOURCE_PARTIAL`

Production gate:

**FAILED**

---

## 5. Restricted Choice Observation Semantics

The Restricted Choice source contains a practical observation procedure.

When an apparently equivalent honor appears, the source instructs the reader to:

1. identify the relevant possible original holdings;
2. determine whether the observed card was forced from some holdings but optional from others;
3. check whether defensive agreements or technical considerations affect the choice;
4. incorporate the auction and all known distribution;
5. compare the remaining layouts before choosing the next play.

The source also contains an important non-certainty guard.

Restricted Choice does not state that the remaining honor must be in the other hand. Under appropriate assumptions, the observed choice changes the probabilities and often makes the other hand the better percentage play.

### Remaining Gap

This is meaningful source-backed reasoning, but it is not yet a complete executable observation contract.

The source does not fully formalize:

- representation of equivalent choices;
- forced versus optional observations;
- invalid or ambiguous observations;
- executable treatment of defensive agreements or technical considerations;
- complete validation semantics for observed play.

Phase 17F therefore does not promote the source to executable status.

Gate result:

`OBSERVATION_SEMANTICS = SOURCE_PARTIAL`

Production gate:

**FAILED**

---

## 6. Precision and Rounding

The worked Restricted Choice source contains explicit numerical examples.

Observed evidence includes percentage outputs such as:

- `75.86%`
- `78.57%`
- `81.48%`
- `84.62%`
- `91.67%`
- `88.00%`
- `50.00%`
- `54.55%`
- `60.00%`
- `66.67%`
- `85.71%`
- `75.00%`

The worked material also contains an explicit equal-play example:

`Either K or 10 — 50.00%`

This provides useful worked-output formatting evidence.

However, no explicit production contract was found specifying:

- a required number of decimal places;
- a rounding rule;
- a comparison tolerance;
- a near-equality rule;
- a production precision standard.

The presence of two-decimal worked examples is not treated as authorization to invent a universal two-decimal production rule.

Gate result:

`PRECISION_AND_ROUNDING = SOURCE_PARTIAL`

Production gate:

**FAILED**

---

## 7. Architecture Readiness

The existing probability architecture already contains explicit scaffolding for the two relevant question types.

`RestrictedChoiceQuestion` contains:

- `subject_suit`
- `observed_play`
- `known_cards`

`VacantPlacesQuestion` contains:

- `subject_suit`
- `known_seat_constraints`

Therefore the architecture is not absent.

However, the default production registry remains:

`KnownCardCountQuestion -> _known_card_count`

Neither `RestrictedChoiceQuestion` nor `VacantPlacesQuestion` has a registered production evaluator.

Unsupported probability questions continue to return the existing engine-not-registered behavior.

Accordingly, the architecture is best classified as tested/scaffolded but not production-ready for Restricted Choice or Vacant Places.

Gate result:

`ARCHITECTURE_READINESS = SOURCE_PARTIAL`

Production gate:

**FAILED**

---

## 8. Safety Gates

Two safety gates remain satisfied.

### NO_HIDDEN_INFORMATION

Classification:

`COMPLETE`

Phase 17F introduces no hidden defender cards and no unsupported distributional facts.

### NO_FORMULA_INVENTION

Classification:

`COMPLETE`

Phase 17F introduces no new probability formula, bridge rule, precision rule, observation semantic, or production default.

---

## 9. Final Gate Matrix

| Gate | Classification | Production Gate |
|---|---|---|
| SOURCE_PROVENANCE | BLOCKED | FAILED |
| VACANT_PLACES_INPUT_CONTRACT | SOURCE_PARTIAL | FAILED |
| OBSERVATION_SEMANTICS | SOURCE_PARTIAL | FAILED |
| PRECISION_AND_ROUNDING | SOURCE_PARTIAL | FAILED |
| ARCHITECTURE_READINESS | SOURCE_PARTIAL | FAILED |
| NO_HIDDEN_INFORMATION | COMPLETE | PASSED |
| NO_FORMULA_INVENTION | COMPLETE | PASSED |

Because the required source and semantic gates remain unresolved, production implementation remains unauthorized.

---

## 10. Production Impact

Phase 17F makes no production probability change.

Measured production impact:

- new production probability engines: `0`
- new production recommendations: `0`
- registered probability engines: `1`
- Restricted Choice engine registered: `false`
- Vacant Places engine registered: `false`
- source executable: `false`
- production implementation authorized: `false`

The existing `KNOWN_CARD_COUNT` production engine remains unchanged.

---

## 11. Validation

Phase 17F focused tests:

`11 passed in 7.48s`

Combined Phase 17E + Phase 17F:

`21 passed in 13.02s`

Cumulative scoped Phase 12–17 suite:

`441 passed in 949.15s (0:15:49)`

Ruff validation for the Phase 17F benchmark and test files passed.

---

## 12. Phase 17F Conclusion

Phase 17F enriched the evidence surrounding the Restricted Choice production contract without crossing the source-safety boundary.

The audit established that:

- a historical Vacant Places backup exists but does not resolve canonical provenance;
- Vacant Places contains a meaningful relationship contract, practical procedure, and uncertainty guard;
- Restricted Choice contains meaningful forced-versus-optional observation guidance and a non-certainty guard;
- worked percentage outputs and an exact equal-play example exist;
- no explicit production precision/rounding contract was found;
- Restricted Choice and Vacant Places question scaffolding exists;
- neither question has a registered production evaluator.

These findings improve contract understanding but do not eliminate the five unresolved dependencies.

Final classification remains:

`SOURCE_PARTIAL`

Production implementation remains:

`NOT AUTHORIZED`

---

## 13. Recommended Phase 17G Direction

The measured next direction is:

`RESTRICTED_CHOICE_CONTRACT_ENRICHMENT`

Phase 17G should continue resolving explicit contract gaps without inventing missing semantics and without modifying protected knowledge sources unless provenance is independently resolved.

Production implementation should remain blocked until the required source and semantic contracts become explicit and verifiable.
