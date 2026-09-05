# Phase 13A — End-to-End Deal Analysis Pipeline Architecture

## Architecture

```text
DealAnalysisContext
  -> deterministic stage detection
  -> production subsystem adapter
       -> bidding router (active)
       -> declarer play (explicit gap)
       -> defensive play (explicit gap)
       -> probability/counting (evidence gap)
  -> immutable DealAnalysisResult
       -> typed action + status + abstention code
       -> subsystem results + KnowledgeSource evidence
```

Stages: `AUCTION`, `OPENING_LEAD`, `DECLARER_PLAY`, `DEFENSIVE_PLAY`, `DEAL_SUMMARY`.
Statuses: `RECOMMENDATION`, `ABSTAIN`, `NO_DECISION`, `ERROR`.
Actions distinguish bids, general card plays, opening leads, defensive cards, and no action.
Abstention codes cover no route, routed rule abstention, insufficient source, policy required, missing state, unsupported stage, and ambiguity.

The bidding adapter calls the unchanged production router, preserves `KnowledgeSource` items and rule explanations, and never supplies fallback intelligence. Declarer-play, defense, and probability currently have no production recommendation entry point in the `bridge` package; their immutable subsystem results remain explicitly non-attempted.

## Deterministic fixtures and baseline

- Analyzed: 8
- Recommendations: 2
- Abstentions: 3
- Unsupported/no-decision: 3
- Stages: {'auction': 5, 'deal-summary': 1, 'declarer-play': 1, 'defensive-play': 1}
- Ordinary 10,000-deal guard: {'seeds': 10000, 'production_calls': 7871, 'completed': 761, 'abstained': 9239}
- Phase 12 guards: {'routes': 45, 'phase12n': 24, 'phase12o': 23, 'phase12q': 1194, 'phase12r': 166, 'phase12s': 540, 'phase12t': 33, 'phase12g': {'4H': 17, '4S': 21}, 'stayman_residual': 197, 'jacoby': {'hearts': 62, 'spades': 61}}

No numeric confidence score is introduced. Debug metadata contains only stable route/rule identifiers.

## Phase 13B

Selected: **A. DECLARER-PLAY ADAPTER / RECOMMENDATION INTEGRATION**. It is the first missing decision-producing stage in deal order and the largest gap between the bidding adapter and a true end-to-end deal pipeline.

Production bidding rules added: 0. Routes added: 0. Routes remain 45. Defaults and canonical knowledge unchanged.

Current cumulative Full Kit: Phase 13A
