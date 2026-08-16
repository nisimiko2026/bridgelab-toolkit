# Spelling and Rename Audit

Generated: 2026-08-16  
Repository: 448 Markdown articles  
Source changes performed: none

## Summary

- 8 direct repair groups covering 24 source Markdown files.
- 7 high-confidence groups and 1 medium-confidence naming choice.
- 0 destination collisions.
- 3 broader naming-policy decisions are intentionally deferred.

Reference counts below are counts of files containing the old identifier. They are impact estimates; files may overlap between repair groups.

## Direct repair candidates

| Confidence | Current path | Proposed path | Source files | Referencing files | Notes |
|---|---|---|---:|---:|---|
| High | `play/declarer-play/probabilty/` | `play/declarer-play/probability/` | 12 | 78 | Clear spelling correction. |
| High | `play/declarer-play/elemination-and-endplays/` | `play/declarer-play/elimination-and-endplays/` | 6 | 85 | Also rename `elemination-index.md` to `elimination-index.md`; that nested identifier appears in 23 files. |
| High | `play/declarer-play/index-declearer-play.md` | `play/declarer-play/index-declarer-play.md` | 1 | 68 | Clear spelling correction. |
| High | `bidding/principals/bidding-fundamentals/kaplan-rubens-hand-hvaluation.md` | `bidding/principals/bidding-fundamentals/kaplan-rubens-hand-evaluation.md` | 1 | 1 | Correct the front-matter title from “Hvaluation” to “Evaluation” too. |
| High | `play/defence/opening-leads/tthird-fifth.md` | `play/defence/opening-leads/third-fifth.md` | 1 | 6 | Duplicated initial letter. |
| Medium | `bidding/natural-bids/rebids/natural-rebid-indexs.md` | `bidding/natural-bids/rebids/natural-rebids-index.md` | 1 | 16 | `indexs` is invalid; proposed plural matches sibling naming. |
| High | `bidding/conventions/competitive/cappaletti.md` | `bidding/conventions/competitive/cappelletti.md` | 1 | 1 | Front-matter title confirms “Cappelletti.” |
| High | `bidding/conventions/competitive/gesthem.md` | `bidding/conventions/competitive/ghestem.md` | 1 | 1 | Front-matter title confirms “Ghestem.” |

## Deferred naming-policy decisions

| Current path | Proposed path | Source files | Referencing files | Recommendation |
|---|---|---:|---:|---|
| `bidding/principals/` | `bidding/principles/` | 23 | 324 | Handle as a dedicated terminology migration, including nested index names and metadata values. |
| `play/principals/` | `play/principles/` | 6 | 19 | Combine with the bidding terminology migration. |
| repository root `knowladge/` | `knowledge/` | 448 | At least 3 toolkit files | Defer to a repository-root migration because external integrations may depend on the current path. |

## Recommended application order

1. Apply the seven high-confidence direct repair groups with backups and exact reference rewriting.
2. Validate filenames, metadata, all reference targets, duplicate names, and orphan coverage.
3. Review the single medium-confidence `natural-rebids-index.md` choice.
4. Decide whether to perform the `principals` → `principles` terminology migration.
5. Treat `knowladge` → `knowledge` as a separate root migration with an external dependency check.
