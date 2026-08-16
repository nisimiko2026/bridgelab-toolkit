# Principles Terminology Migration Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Outcome

Replace the incorrect structural term `principals` with `principles` while preserving legitimate prose uses of “principal.” Human-facing article titles already use “Principles,” so this migration primarily affects paths, identifiers, subcategories, and tags.

## Impact

- 2 directories move.
- 29 Markdown articles move.
- 338 unique files contain affected path references.
- 28 exact `subcategory: principals` values become `principles`.
- 28 exact `principals` tag values become `principles`.
- 3 nested index filenames change.
- 0 destination collisions were found.

## Directory moves

| Current | Proposed | Articles | Files containing path references | Collision |
|---|---|---:|---:|---|
| `bidding/principals/` | `bidding/principles/` | 23 | 324 | No |
| `play/principals/` | `play/principles/` | 6 | 19 | No |

The reference counts overlap; the combined unique impact is 338 files.

## Nested index filenames

| Confidence | Current | Proposed |
|---|---|---|
| High | `bidding/principals/principals-index.md` | `bidding/principles/principles-index.md` |
| High | `play/principals/play-principals-index.md` | `play/principles/play-principles-index.md` |
| Medium | `bidding/principals/partnership/index-principal-partnership.md` | `bidding/principles/partnership/partnership-principles-index.md` |

The medium-confidence proposal matches the existing title “Partnership Principles” and the repository’s common `*-index.md` suffix convention.

## Metadata normalization

Only exact metadata values will change:

- `subcategory: principals` → `subcategory: principles`
- tag list item `principals` → `principles`

Categories such as `Bidding – Principles` and titles such as `Card Play Principles` are already correct. Prose will not receive a global replacement because “principal” can be a legitimate noun.

## Guardrails

1. Abort if a source is missing or any destination exists.
2. Back up every moved or rewritten file.
3. Rewrite exact repository identifiers only.
4. Normalize exact metadata values only.
5. Verify all old identifiers are gone.
6. Run the complete toolkit tests.
7. Validate all 448 articles, reference targets, duplicates, indexes, and orphan coverage.
8. Commit toolkit and content changes separately.

## Recommended approval

Approve the two directory moves, both high-confidence nested index renames, the exact metadata normalization, and—separately—the medium-confidence rename to `partnership-principles-index.md`.
