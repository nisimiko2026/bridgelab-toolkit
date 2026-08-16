# Index Title Disambiguation Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Outcome

The three remaining duplicate-title groups are intentional index/article pairs. Explicitly identifying the navigation pages as indexes removes title ambiguity without changing filenames, identifiers, or references.

## Proposed title changes

| Index file | Current title/H1 | Proposed title/H1 |
|---|---|---|
| `bidding/convention-cards/convention-cards-index.md` | Convention Cards | Convention Cards Index |
| `play/declarer-play/notrump-play/index-notrump-play.md` | Notrump Play | Notrump Play Index |
| `bidding/conventions/relay/relay-index.md` | Relay Bidding | Relay Bidding Index |

## Evidence

- Every filename explicitly identifies an index.
- The Convention Cards and Notrump pages describe themselves as index and navigation guides.
- All three pages contain directory maps, topic catalogs, guides, or learning paths.
- Their paired non-index articles provide the substantive concept treatment.
- Adding “Index” improves search results and navigation labels while preserving repository identifiers.

## Scope

For each file, change only:

1. The front-matter `title`.
2. The first H1 heading.

No paths, references, descriptions, categories, or body sections change.

## Expected result

- Articles remain at 446.
- Duplicate-title groups decrease from 3 to 0.
- No path or reference rewrites.
- Validation remains at 0 errors and 0 warnings.

## Guardrails

1. Back up all three files.
2. Abort if an expected current title or H1 is missing.
3. Change only the six reviewed lines.
4. Run all toolkit tests and validate every article.
5. Confirm duplicate-title analysis reports zero groups.

## Recommended approval

Approve all three high-confidence title/H1 disambiguations together.
