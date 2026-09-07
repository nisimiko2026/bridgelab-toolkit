# BridgeLab Phase 17H — Restricted Choice Contract Gap Resolution Audit

## Status

**Phase:** 17H  
**Baseline Phase:** 17G  
**Candidate:** Restricted Choice Contract Gap Resolution Audit  
**Classification Before:** SOURCE_PARTIAL  
**Classification After:** SOURCE_PARTIAL  
**Production Implementation Authorized:** No  
**New Production Recommendations:** 0  
**Registered Probability Engines:** 1  
**Phase 17I Direction:** RESTRICTED_CHOICE_CONTRACT_ENRICHMENT

---

## 1. Objective

Phase 17H performs a conservative gap-resolution audit for the Restricted
Choice / Vacant Places probability work carried forward from Phase 17G.

The purpose of this phase is not to implement a new probability engine and
not to promote Restricted Choice to production.

The audit asks whether the evidence already available is sufficient to close
any of the five unresolved dependencies:

1. SOURCE_PROVENANCE
2. VACANT_PLACES_INPUT_CONTRACT
3. OBSERVATION_SEMANTICS
4. PRECISION_AND_ROUNDING
5. ARCHITECTURE_READINESS

No bridge rule, probability formula, precision rule, production default, or
hidden distributional fact is invented in order to close a gap.

---

## 2. Safety Constraints

Phase 17H preserves the safety constraints established by the preceding
Restricted Choice phases.

The audit:

- does not modify canonical knowledge sources;
- does not authorize production implementation;
- does not register a Restricted Choice probability engine;
- does not register a Vacant Places probability engine;
- does not introduce new production recommendations;
- does not infer hidden defender cards;
- does not invent probability formulas;
- does not invent precision or rounding defaults;
- does not convert supporting descriptive evidence into an executable
  contract.

---

## 3. Source Provenance

The provenance blocker remains unresolved.

The historical Vacant Places backup was found, but it is not identical to the
current Vacant Places source and is not Git-tracked.

The current audit therefore does not treat the historical backup as proof of
source provenance.

Relevant Restricted Choice / Vacant Places provenance remains unresolved.

### Gap result

**SOURCE_PROVENANCE: BLOCKED**

**Gap resolved:** No

---

## 4. Vacant Places Input Contract

The Vacant Places source contains useful contract evidence.

The audit confirms the presence of:

- the conceptual relationship between Vacant Places and Restricted Choice;
- a practical procedure for reconstructing shape and counting known cards;
- determination of remaining vacant places;
- incorporation of specific evidence concerning the target card;
- comparison of resulting probabilities;
- updating when new distributional information becomes available;
- an explicit uncertainty guard against treating uncertain assumptions as
  established facts.

This evidence is useful but does not provide a complete executable
input/validation contract.

The audit therefore does not infer missing input semantics, validation rules,
error handling, normalization rules, or production defaults.

### Gap result

**VACANT_PLACES_INPUT_CONTRACT: SOURCE_PARTIAL**

**Gap resolved:** No

---

## 5. Restricted Choice Observation Semantics

The Restricted Choice source contains practical observation guidance.

The audit confirms evidence covering:

- an apparently equivalent honor being observed;
- identification of relevant possible original holdings;
- forced-versus-optional play reasoning;
- defensive agreements or technical considerations;
- auction and known distributional information;
- comparison of remaining layouts;
- an explicit guard that the remaining honor is not certain to be in the
  other hand.

This is sufficient to support the conceptual Restricted Choice procedure, but
it is not a complete formal executable contract for interpreting observed
play.

Phase 17H does not invent the missing formal semantics.

### Gap result

**OBSERVATION_SEMANTICS: SOURCE_PARTIAL**

**Gap resolved:** No

---

## 6. Precision and Rounding

The worked Restricted Choice material contains percentage outputs.

The audit also confirms an equal-choice worked case containing:

- Either K or 10
- 50.00%

These worked outputs demonstrate presentation examples, but they do not
establish a universal production precision rule.

No explicit source contract was found defining:

- required decimal places;
- rounding behavior;
- comparison tolerance;
- equality tolerance;
- production precision defaults.

The audit therefore does not infer a universal two-decimal rule from the
worked examples.

### Gap result

**PRECISION_AND_ROUNDING: SOURCE_PARTIAL**

**Gap resolved:** No

---

## 7. Architecture Readiness

Probability question scaffolding exists for both target concepts.

The audit confirms:

- RestrictedChoiceQuestion exists;
- VacantPlacesQuestion exists;
- Restricted Choice engine is not registered;
- Vacant Places engine is not registered.

The existing production probability registry continues to contain one
registered probability engine:

**KNOWN_CARD_COUNT**

Question scaffolding alone is not sufficient to declare production
architecture readiness.

### Gap result

**ARCHITECTURE_READINESS: SOURCE_PARTIAL**

**Gap resolved:** No

---

## 8. Supporting Sources

Phase 17H continues to recognize the supporting evidence identified in
Phase 17G.

Supporting material is present in:

- eight-ever-nine-never.md
- bridge-glossary.md
- bridge-terminology.md
- common-bridge-abbreviations.md

These sources support Restricted Choice / Vacant Places concepts and
terminology.

They are not promoted to executable contract sources.

Supporting evidence therefore does not close any of the five production
blockers.

---

## 9. Gate Matrix

| Gate | Classification | Production Gate Passed |
|---|---|---:|
| SOURCE_PROVENANCE | BLOCKED | No |
| VACANT_PLACES_INPUT_CONTRACT | SOURCE_PARTIAL | No |
| OBSERVATION_SEMANTICS | SOURCE_PARTIAL | No |
| PRECISION_AND_ROUNDING | SOURCE_PARTIAL | No |
| ARCHITECTURE_READINESS | SOURCE_PARTIAL | No |
| NO_HIDDEN_INFORMATION | COMPLETE | Yes |
| NO_FORMULA_INVENTION | COMPLETE | Yes |

---

## 10. Gap Resolution Matrix

| Contract Gap | Resolved |
|---|---:|
| SOURCE_PROVENANCE | No |
| VACANT_PLACES_INPUT_CONTRACT | No |
| OBSERVATION_SEMANTICS | No |
| PRECISION_AND_ROUNDING | No |
| ARCHITECTURE_READINESS | No |

No blocker is promoted merely because supporting evidence exists.

---

## 11. Production Status

Phase 17H does not authorize production implementation.

Final production state:

- Source executable: **False**
- Production implementation authorized: **False**
- New production recommendations: **0**
- Restricted Choice engine registered: **False**
- Vacant Places engine registered: **False**
- Registered probability engines: **1**

The existing production baseline remains unchanged.

---

## 12. Validation

Phase 17H focused test suite:

**12 passed in 8.02s**

Phase 17G + Phase 17H:

**23 passed in 15.54s**

Phase 17B–17H:

**72 passed in 31.93s**

Phase 12–17H scoped regression suite:

**464 passed in 692.82s (0:11:32)**

Additional validation:

- Python compilation: passed
- Ruff checks: passed

No measured test result is replaced by an estimated count.

---

## 13. Generated Audit Artifact

The Phase 17H JSON audit artifact was generated as:

`bridgelab_phase17h_restricted_choice_contract_gap_resolution_audit.json`

Measured size:

**12,152 bytes**

---

## 14. Phase 17H Conclusion

Phase 17H confirms that the available Restricted Choice and Vacant Places
material provides meaningful conceptual, procedural, worked-example, and
architectural evidence.

However, the evidence does not close the remaining production contract gaps.

The five unresolved dependencies remain:

1. SOURCE_PROVENANCE
2. VACANT_PLACES_INPUT_CONTRACT
3. OBSERVATION_SEMANTICS
4. PRECISION_AND_ROUNDING
5. ARCHITECTURE_READINESS

Accordingly:

**Classification remains SOURCE_PARTIAL.**

**Production implementation remains unauthorized.**

**No new production recommendation is introduced.**

**No new probability engine is registered.**

The selected next direction is:

**Phase 17I — RESTRICTED_CHOICE_CONTRACT_ENRICHMENT**