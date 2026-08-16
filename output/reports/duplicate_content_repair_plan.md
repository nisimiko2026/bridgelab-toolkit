# Duplicate Content Repair Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Outcome

The two near-identical pairs require different treatments. One is a genuine duplicate index and can be consolidated safely. The other is a cloned-body defect in an article that represents a legitimate separate topic.

## High-confidence consolidation

### Transfer Bids index

Canonical file:

`bidding/conventions/transfers/transfers-index.md`

Duplicate file:

`bidding/conventions/transfers/index-transfers.md`

The files differ by only one reciprocal reference line. The canonical `transfers-index` identifier appears in 12 files, including 11 files outside the duplicate pair. The `index-transfers` identifier appears only in the canonical file, so no external inbound reference needs redirecting.

Proposed actions:

1. Back up both index files.
2. Remove the canonical file's reference to `index-transfers`.
3. Delete `index-transfers.md`.
4. Verify the old identifier is absent.
5. Validate the complete repository and confirm the duplicate-title group count falls by one.

Confidence: high.

## Editorial restoration—not consolidation

### Marked Finesse

`marked-finesse.md` is effectively a clone of `first-round-finesse.md`; the only difference is one omitted reference. However, four files intentionally refer to the Marked Finesse topic:

- `finesses-index.md`
- `first-round-finesse.md`
- `delayed-finesse.md`
- `repeat-finesse.md`

Deleting or redirecting `marked-finesse.md` would erase a legitimate bridge concept and make those relationships semantically wrong. The safe repair is to preserve its path and replace the cloned title, description, metadata, and body with a distinct Marked Finesse article. That content restoration requires editorial review and is excluded from automatic consolidation.

## Guardrails

1. Abort if either transfer-index file is missing.
2. Back up every changed or removed file.
3. Do not modify `marked-finesse.md` in the automatic step.
4. Remove only the exact duplicate identifier from the canonical transfer index.
5. Run all toolkit tests and validate every article.
6. Confirm the duplicate-title count decreases from 9 to 8—not further.

## Approval boundary

Approve the high-confidence Transfer Bids index consolidation separately. The Marked Finesse article should remain pending until its replacement content is reviewed.
