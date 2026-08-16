# Systems Metadata Removal Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Scope

This removal-first phase implements the approved strict-applicability policy conservatively. It removes system assignments from non-bidding articles and removes convention/method values that are outside the controlled system taxonomy. It does not fill empty values or remove taxonomy-valid assignments from bidding articles.

## Impact

- 154 files have proposed removals.
- 385 exact assignments are proposed for removal.
- 42 assignments occur on non-bidding articles.
- 343 assignments are convention or method names outside the system taxonomy.
- 510 taxonomy-valid assignments remain for a later applicability review.

## Removed values

| Value | Assignments |
|---|---:|
| `jacoby` | 90 |
| `lebensohl` | 56 |
| `multi` | 46 |
| `cappelletti` | 36 |
| `dont` | 31 |
| `puppet stayman` | 30 |
| `drury` | 17 |
| `crash` | 14 |
| `kokish` | 14 |
| `walsh` | 13 |
| `standard american` | 6 |
| `precision` | 6 |
| `flannery` | 5 |
| `sayc` | 4 |
| `mathe` | 4 |
| `acol` | 3 |
| `strong club` | 2 |
| `wolff signoff` | 2 |
| `croc` | 2 |
| `namyats` | 2 |
| `roman keycard` | 1 |
| `two over one` | 1 |


## Controlled taxonomy retained in this phase

- `acol`
- `blue club`
- `carrot club`
- `ehaa`
- `moscito`
- `polish club`
- `precision`
- `roman club`
- `sayc`
- `standard american`
- `strong club`
- `super precision`
- `two over one`

## Guardrails

1. Back up every changed article.
2. Remove only the exact file/value pairs in the JSON plan.
3. Do not fill any empty `systems` list.
4. Do not remove taxonomy-valid bidding assignments during this phase.
5. Run all toolkit tests and validate every article.
6. Regenerate the cache and rerun the systems audit.

## Approval boundary

Approval applies only to the 385 exact removals recorded in the JSON plan. The 510 retained assignments require a separate applicability audit.
