# Systems Metadata Audit

Generated: 2026-08-16  
Status: Policy decision required  
Source changes performed: none

## Outcome

The `systems` field is not simply incomplete. Existing values mix complete bidding systems, system families, conventions, treatments, and terms detected incidentally in prose or references. Bulk-filling empty values would make the metadata less reliable.

## Coverage

| State | Articles |
|---|---:|
| Populated `systems` | 205 |
| Empty `systems` | 241 |
| Total | 446 |

Empty values by repository area:

| Area | Empty |
|---|---:|
| Play | 179 |
| Bidding | 56 |
| Duplicates | 3 |
| References | 2 |
| Root | 1 |

Most missing values are on play articles, where bidding-system metadata is normally inapplicable.

## Evidence of pollution

- `bidding/systems/precision.md` has 14 assigned values, mixing Precision with unrelated systems and conventions.
- `play/declarer-play/squeezes/squeezes-index.md` is labeled `multi`, apparently because the word appears in its content or references.
- `references/common-bridge-abbreviations.md` has 10 system values for terms it merely documents.
- Eleven non-bidding articles have populated `systems` lists.
- Common values such as Cappelletti, DONT, Jacoby, Lebensohl, Multi, Puppet Stayman, and Walsh are conventions or methods, not complete bidding systems.

The current enrichment therefore appears to infer applicability from mentions rather than article meaning.

## Recommended policy: strict applicability

Define `systems` as:

> Complete bidding systems or recognized system families that the article directly defines or specifically applies to.

Under this policy:

- Play, reference, duplicate, bibliography, and generic navigation articles normally keep `systems: []`.
- A system article identifies itself and genuine parent/family relationships only.
- A convention article lists a system only when the article explicitly describes system-specific use—not merely because the system is mentioned or linked.
- Conventions and treatments remain represented by tags, references, and their own articles rather than being treated as systems.

### Candidate controlled taxonomy

- Acol
- Blue Club
- Carrot Club
- EHAA
- Moscito
- Polish Club
- Precision
- Roman Club
- SAYC
- Standard American
- Strong Club
- Super Precision
- Two Over One

This taxonomy is provisional and should be reviewed against the contents of `bidding/systems/` before validation is enforced.

## Recommended sequence

1. Approve the strict-applicability meaning and a controlled taxonomy.
2. Generate a removal-first repair plan for clearly inapplicable assignments.
3. Review bidding articles for explicit system applicability.
4. Leave empty play/reference values empty.
5. Add validation for controlled values and unlikely non-bidding assignments.
6. Apply reviewed changes with backups and regenerate the cache.

## Approval boundary

The next approval should establish the field semantics and authorize a read-only removal plan. It should not yet authorize automatic metadata deletion or bulk filling.
