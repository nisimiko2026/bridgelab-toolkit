# PT-A2D DDS capability inspection (before implementation)

Inspected installed endplay 0.5.12, `dds/solve.py`, `dds/analyse.py`, and `types/deal.py` on 2026-09-28.

- BridgeLab EndplayTrickSolver uses analyse_start and returns only optimum trick totals.
- solve_board(Default) returns legal candidate cards with continuation scores for the side to play. SolvedBoard expands DDS equivalent-rank masks into individual cards.
- solve_board(OptimalAll) returns all tied optimum next cards. OptimalOne chooses one; it is not a unique principal variation.
- analyse_play consumes a supplied sequence and reports continuation totals; it does not generate a complete line.
- Deal.play advances a physical position; repeated optimal queries can construct a line or explore tied branches. There is no complete multiple-line attribution result in this API.
- None of these wrappers exposes a persistent rule banning selected ruff actions. Filtering one DDS move list is not a restricted-game solution: subsequent continuation scores still assume unrestricted play.
- Ruff counts require actual card/trick events, never subtraction from a DDS trick total.

Research design: exact independent minimax on bounded endgames, plus budgeted traversal of the DDS optimal-action DAG on full deals. Preserve unresolved bounds when traversal is incomplete. Distinguish strict prohibition (possibly infeasible), prohibition only when a legal discard exists (forced ruffs allowed), and a separate non-credit payoff experiment. The latter changes reward, not cards or legal actions, and is not essential ruff value by definition.