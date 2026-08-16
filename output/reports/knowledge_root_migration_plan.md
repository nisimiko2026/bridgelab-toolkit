# Knowledge Root Migration Plan

Generated: 2026-08-16  
Status: Review required  
Source changes performed: none

## Outcome

Rename the misspelled repository root `knowladge/` to `knowledge/` without changing article identifiers or article content.

## Impact

- The current root exists and contains 448 files; all 448 are Markdown.
- The directory contains 3,866,967 bytes of content.
- The proposed `knowledge/` destination does not exist, so no collision was found.
- Two active toolkit source files depend on the current name.
- External consumers outside the BridgeLab Git repository cannot be verified automatically.

## Active dependencies

| File | Dependency | Required change |
|---|---|---|
| `config.py` | Default repository path | Change the sibling fallback from `knowladge` to `knowledge`. |
| `tests/test_cleanup_item_3.py` | Regression expectation for the default path | Expect the `knowledge` sibling directory. |

The `BRIDGELAB_REPOSITORY` environment override remains compatible and does not need a code change.

## Generated and recovery artifacts

| Artifact | Recommended handling |
|---|---|
| `output/repository.json` | Regenerate after the move because it contains stale absolute paths. |
| `../knowladge.zip` | Leave unchanged unless separately approved; it may be a recovery copy or external handoff. |
| Earlier spelling audit reports | Preserve as historical records of the decision. |

## Guardrails

1. Confirm that no editor, scheduled job, script, shortcut, or external integration requires the old absolute path.
2. Preserve a recoverable copy before moving the root.
3. Abort if `knowledge/` appears before application.
4. Perform a Git-aware directory rename; do not rewrite article-relative identifiers.
5. Update the toolkit default and its regression test in the same operation.
6. Regenerate path-bearing output rather than editing generated JSON manually.
7. Run the full toolkit test suite and validate all 448 articles from the new root.
8. Verify active source contains no `knowladge` reference and review Git rename detection before committing.

## Approval boundary

Approval should cover the root directory move and the two active toolkit dependency updates. Renaming or deleting `knowladge.zip` is a separate decision and is not part of the recommended migration.
