# Phase 27E - Two-over-One Opener Rebid Source-Gap Audit

## Scope

This audit measures the four canonical uncontested Two-over-One opener-rebid auctions under explicit `two_over_one=game_force`.

It does not add bidding rules, routes, policies, treatments, defaults, or knowledge content.

Frozen source: `bidding/systems/2-over-1` - `Opener's Rebids`.

## Canonical family matrix

| Auction | Route | Production coverage | Source status | Current probe action | Decision |
|---|---|---|---|---|---|
| 1H-P-2C-P | sayc.2over1.opener.1h.2c | NONE | SOURCE_INSUFFICIENT | ABSTAIN | DEFER |
| 1H-P-2D-P | sayc.2over1.opener.1h.2d | PARTIAL | SOURCE_PARTIAL | ABSTAIN | KEEP_EXISTING_RULES |
| 1S-P-2C-P | sayc.2over1.opener.1s.2c | PARTIAL | SOURCE_PARTIAL | ABSTAIN | KEEP_EXISTING_RULES |
| 1S-P-2D-P | sayc.2over1.opener.1s.2d | NONE | SOURCE_INSUFFICIENT | ABSTAIN | DEFER |

## Source finding

The frozen source gives the general opener-rebid priority:

1. show a second suit;
2. support responder;
3. rebid opener's own suit;
4. make a balanced rebid.

BridgeLab already implements only the source-explicit deterministic branches. It does not infer a complete rebid table from that priority list.

`1H-P-2C-P` and `1S-P-2D-P` have canonical routes but no exact frozen-source contract for a production opener rebid. They therefore remain intentionally routed and abstaining.

`1H-P-2D-P` and `1S-P-2C-P` retain their existing partial source-grounded production coverage. No broader semantics are inferred from those examples.

The single probe hand is used only to verify route reachability and
unsupported-route abstention. An `ABSTAIN` result on a partially supported
route does not mean that the route has no executable production branches.

## Router guards

- Canonical family count: 4
- Production route count: 45
- All four canonical routes reachable: True
- Unsupported canonical routes all abstain: True
- Unsupported routes: ('sayc.2over1.opener.1h.2c', 'sayc.2over1.opener.1s.2d')
- Partially supported routes: ('sayc.2over1.opener.1h.2d', 'sayc.2over1.opener.1s.2c')

## Decision

**DEFER UNSUPPORTED TWO-OVER-ONE OPENER REBIDS.**

Do not add opener-rebid recommendations for `1H-P-2C-P` or `1S-P-2D-P` until a frozen source supplies an exact executable contract.

Guards: production rules added=0; routes added=0; policies added=0; defaults changed=False; knowledge Markdown changes=0.
