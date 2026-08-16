# Post-Migration Health Audit

Generated: 2026-08-16  
Source changes performed: none

## Baseline

- 448 articles
- 0 validation errors and 0 warnings
- 0 orphan articles
- 9 duplicate-title groups
- 59 toolkit tests passing

## Metadata coverage

| Field | Missing |
|---|---:|
| Category | 0 |
| Systems | 242 |
| Tags | 0 |
| References | 0 |
| Description | 0 |

`systems` is the only incomplete field. It is optional under current validation and should be handled as a later enrichment project, not a structural repair.

## Duplicate-title classification

### Analyzer false positives

The analyzer currently removes suit symbols while normalizing titles. This incorrectly groups:

- `1♦ Opening Bid`, `1♥ Opening Bid`, and `1♠ Opening Bid`
- `Response to 1♣ Opening` and `Response to 1♦ Opening`

These five articles are correctly titled and should not be consolidated.

### Intentional index/article pairs

- Convention Cards: navigation index versus partnership concept article
- Notrump Play: navigation index versus introductory article
- Relay Bidding: navigation index versus detailed convention article

These pairs serve different roles. Their titles may later be clarified, but they are not duplicate files.

### Near-identical duplicates

| Pair | Comparison | Recommendation |
|---|---|---|
| `first-round-finesse.md` / `marked-finesse.md` | One deleted line | Audit inbound references, then remove or replace the mislabeled `marked-finesse.md` copy. |
| `index-transfers.md` / `transfers-index.md` | One changed line | Select one canonical transfer index and rewrite exact inbound references. |

### Editorial review

- `play/counting/inference.md` and `play/declarer-play/probability/probability-inference.md` are distinct treatments with overlapping titles.
- `entry-management-technique.md` and `planning/preserving-entries.md` are distinct articles with overlapping titles and scope.

These should be reviewed for scope and naming after the near-identical duplicates are resolved.

## Recommended next step

Generate a guarded consolidation plan for the two near-identical duplicate pairs. Keep the analyzer false positives, intentional index/article pairs, and editorial-review pairs out of the automatic repair scope.
