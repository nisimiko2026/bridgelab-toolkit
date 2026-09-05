# BridgeLab Phase 13J — Opening-Lead Source-Readiness Audit

## Decision

E. OPENING-LEAD SOURCE ENRICHMENT REQUIRED

No frozen-source candidate passes all twelve executability gates. The sources describe carding agreements within a chosen suit, but do not uniquely select a suit from the complete state or fully settle scope, exceptions, and precedence.

## Benchmark

- Source files audited: 10
- Candidate rules / fixtures: 10 / 15
- Executable candidates / fixtures: 0 / 0
- Non-executable fixtures: 15
- Policy-required fixtures: 14
- Recommendations generated: 0

## Candidate audit

### fourth-best from length

- Source: `knowledge/play/defence/opening-leads/fourth-best.md` — Basic Principle
- Rule: Fourth-highest from a long suit without a touching sequence.
- Policy: FOURTH_BEST
- Classification: **POLICY_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: No deterministic suit choice, minimum length, or complete suit/NT scope.

### third-and-fifth

- Source: `knowledge/play/defence/opening-leads/third-fifth.md` — Basic Principle
- Rule: Third-highest from odd length and fifth-highest from even length.
- Policy: THIRD_AND_FIFTH
- Classification: **POLICY_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: No deterministic suit choice; short-length and contract exceptions are incomplete.

### standard honor sequence

- Source: `knowledge/play/defence/opening-leads/standard-leads.md` — Sequence Leads
- Rule: Lead the top card from a sequence.
- Policy: STANDARD
- Classification: **EXCEPTION_INCOMPLETE**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: Several eligible suits and ace/king/interior-sequence variants remain.

### Rusinow touching sequence

- Source: `knowledge/play/defence/opening-leads/rusinow.md` — Basic Principle
- Rule: Lead the second-highest honor from a touching sequence.
- Policy: RUSINOW
- Classification: **POLICY_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: Contract scope and ace/king/interior-sequence agreements remain unresolved.

### top of nothing

- Source: `knowledge/play/defence/opening-leads/top-of-nothing.md` — Definition
- Rule: Lead the highest card from a suit containing no honors.
- Policy: ENABLED
- Classification: **EXCEPTION_INCOMPLETE**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: Suit selection, minimum length, NT scope, and precedence over length are incomplete.

### singleton lead

- Source: `knowledge/play/defence/opening-leads/standard-leads.md` — Short Suit Leads
- Rule: Lead a singleton against a suit contract to seek a ruff.
- Policy: none identified
- Classification: **SOURCE_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: yes / no
- Blocker: Source calls this preferred/usually, with no tie-break or exceptions.

### partner's suit

- Source: `knowledge/play/defence/opening-leads/lead-partners-suit.md` — Opening Lead
- Rule: Prefer partner's bid suit subject to holding and auction context.
- Policy: none identified
- Classification: **SOURCE_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / partial
- Blocker: Exact auction trigger, card, and competing-suit precedence are incomplete.

### longest/strongest versus NT

- Source: `knowledge/play/defence/opening-leads/standard-leads.md` — Against Notrump Contracts
- Rule: Prefer the longest and strongest suit, commonly using fourth-best.
- Policy: FOURTH_BEST
- Classification: **AMBIGUOUS_CARD_CHOICE**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: partial / yes
- Blocker: Longest and strongest may identify different or tied suits.

### trump lead

- Source: `knowledge/play/defence/opening-leads/standard-leads.md` — Suit Contract Opening Leads
- Rule: A trump lead is occasionally preferred.
- Policy: none identified
- Classification: **SOURCE_PARTIAL**
- State / unique card / exceptions / precedence: True / False / False / False
- Suit / NT scope: yes / no
- Blocker: No source-complete trigger or exception contract.

### MUD

- Source: `knowledge/play/defence/opening-leads/opening-leads-index.md` — Opening Leads
- Rule: No executable MUD contract.
- Policy: none identified
- Classification: **NOT_PRESENT**
- State / unique card / exceptions / precedence: False / False / False / False
- Suit / NT scope: partial / partial
- Blocker: Named/absent without a usable rule contract.

## Precedence and state boundary

Honor sequences override within-suit length leads in the length articles, and Rusinow replaces Standard for its defined sequences when explicitly agreed. Cross-suit priority and Top-of-Nothing versus length precedence are not complete. Leader hand, contract, legal cards, and optional auction are sufficient inputs; hidden hands and probability are neither used nor needed. The remaining blocker is the source contract, not state representation.

## Cumulative Phase 13

```json
{
  "abstentions": 3,
  "bidding_recommendations": 2,
  "cumulative_positions_or_requests": 95,
  "declarer_recommendations": 2,
  "defensive_recommendations": 0,
  "errors": 0,
  "no_decisions": 51,
  "opening_lead_recommendations": 0,
  "opening_lead_states": 14,
  "policy_requests": 10,
  "source_readiness_audit_requests": 15
}
```

## Guards

Phase 13I remains 10 / 8 / 2 with three policy dimensions and zero recommendations. OpeningLeadState remains NO_DECISION/NONE/ENGINE_UNAVAILABLE for valid state, all 13 leader cards legal, 13 known and 39 unknown. Defensive recommendations remain zero; SIMPLE_UNBLOCK_KING remains two king recommendations; one probability engine remains registered. Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. No production defaults, algorithms, formulas, routes, or canonical knowledge Markdown changed.

Current cumulative Full Kit: Phase 13J
