"""Optional endplay 0.5.12 adapter over Bo Haglund's DDS implementation.

The package is imported at call time so core evaluation can run without the
optional native wheel. Python 3.9–3.13 Windows x64 wheels are published for
endplay 0.5.12; the PT-1A validation uses Python 3.12.
"""

from __future__ import annotations

from time import perf_counter

from .deals import Deal
from .models import Card, Seat, Suit
from .trick_solver import TrickSolverResult, TrickSolverStatus


_SEATS = (Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST)


class EndplayTrickSolver:
    implementation = "endplay/DDS"

    def solve(self, deal: Deal, declarer: Seat, strain: Suit | None,
              *, opening_lead: Card | None = None) -> TrickSolverResult:
        if not isinstance(deal, Deal) or not isinstance(declarer, Seat):
            raise TypeError("canonical Deal and declarer Seat required")
        if strain is not None and not isinstance(strain, Suit):
            raise TypeError("strain must be Suit or None")
        deal_id = deal.serialize()
        start = perf_counter()
        if opening_lead is not None:
            return TrickSolverResult(
                self.implementation, None, deal_id, declarer, strain, opening_lead,
                TrickSolverStatus.UNAVAILABLE, None, perf_counter() - start,
                "fixed opening lead is not supported by this PT-1A adapter",
            )
        try:
            import endplay
            from endplay.dds import analyse_start
            from endplay.types import Deal as EndplayDeal, Denom, Player
        except ImportError as exc:
            return TrickSolverResult(
                self.implementation, None, deal_id, declarer, strain, None,
                TrickSolverStatus.UNAVAILABLE, None, perf_counter() - start,
                f"endplay is not installed: {exc}",
            )
        version = getattr(endplay, "__version__", None)
        try:
            pbn = "N:" + " ".join(deal.hand(seat).serialize().replace("-", "")
                                  for seat in _SEATS)
            first = Player[declarer.next().name.lower()]
            trump = Denom.nt if strain is None else Denom[strain.name.lower()]
            solver_deal = EndplayDeal(pbn, first=first, trump=trump)
            tricks = int(analyse_start(solver_deal))
            if not 0 <= tricks <= 13:
                raise ValueError(f"DDS returned invalid trick count {tricks}")
        except Exception as exc:
            return TrickSolverResult(
                self.implementation, version, deal_id, declarer, strain, None,
                TrickSolverStatus.FAILED, None, perf_counter() - start,
                f"{type(exc).__name__}: {exc}",
            )
        return TrickSolverResult(
            self.implementation, version, deal_id, declarer, strain, None,
            TrickSolverStatus.SUCCESS, tricks, perf_counter() - start,
        )
