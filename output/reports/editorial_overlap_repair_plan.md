# Editorial Overlap Repair Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Outcome

Both editorial-overlap groups have high-confidence repairs, but they require different operations: one content consolidation and one metadata-only correction.

## 1. Consolidate Inference

Canonical article:

`play/declarer-play/probability/probability-inference.md`

Outline proposed for removal:

`play/counting/inference.md`

### Evidence

- The canonical article contains 964 words and has 41 inbound-reference files.
- The outline contains 167 words and has only 2 inbound-reference files.
- The outline covers the same auction, lead, play, signaling, elimination, and restricted-choice concepts as the comprehensive article.
- Both files that reference the outline already reference the canonical article:
  - `play/counting/counting-index.md`
  - `play/declarer-play/general-techniques/finesses/marked-finesse.md`

Therefore, no redirect is needed. Remove the two redundant outline references and delete the outline after backing up all three affected files.

Confidence: high.

## 2. Correct Entry Management title

Article:

`play/declarer-play/general-techniques/entry-management-technique.md`

Current front-matter title:

`Preserving Entries`

Proposed title:

`Entry Management Technique`

The filename and H1 already say “Entry Management Technique,” and the article covers entry types, creating entries, blocking, timing, and broader entry management. The duplicate title is therefore a copied front-matter value rather than a duplicate article.

Only the front-matter title should change. The path, H1, description, and references remain unchanged.

Confidence: high.

## Expected result

- Article count: 447 → 446
- Duplicate-title groups: 5 → 3
- The three remaining groups are intentional index/article pairs:
  - Convention Cards
  - Notrump Play
  - Relay Bidding

## Guardrails

1. Back up every changed or removed file.
2. Abort if any expected source text or file is missing.
3. Remove only exact `play/counting/inference` reference list items.
4. Change only the entry-management article's front-matter title.
5. Verify the removed Inference identifier is absent.
6. Run all toolkit tests and validate every article.
7. Confirm duplicate groups decrease by exactly two.

## Recommended approval

Approve both high-confidence actions. They can be applied together with independent backup and verification counts.
