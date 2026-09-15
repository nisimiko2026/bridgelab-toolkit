"""Small local, read-only bidding view over the existing application boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .auction import Auction, Call
from .full_deal_application import (
    analyze_full_deal_application,
    full_deal_application_request_from_dict,
)
from .sayc_route_configuration import create_standard_sayc_router
from .models import Seat, Vulnerability
from .system_profiles import SystemProfile, classify_system_profile


DEALER_VALUES = tuple(seat.value for seat in Seat)
VULNERABILITY_VALUES = tuple(value.value for value in Vulnerability)
SYSTEM_VALUES = tuple(
    profile.value for profile in SystemProfile if profile is not SystemProfile.UNKNOWN
)


@dataclass(frozen=True, slots=True)
class BiddingForm:
    """Framework-neutral strings collected by the read-only bidding form."""

    hand: str
    dealer: str = Seat.NORTH.value
    auction_calls: tuple[str, ...] = ()
    vulnerability: str = Vulnerability.NONE.value
    system: str = SystemProfile.SAYC.value
    system_options: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "auction_calls", tuple(self.auction_calls))
        object.__setattr__(self, "system_options", tuple(self.system_options))

    def to_payload(self) -> dict[str, object]:
        """Create fresh application input; canonical parsing remains downstream."""
        return {
            "requested_stages": ["auction"],
            "bidding": {
                "hand": self.hand,
                "auction": {"dealer": self.dealer, "calls": list(self.auction_calls)},
                "vulnerability": self.vulnerability,
                "system": {"id": self.system, "options": dict(self.system_options)},
            },
        }


@dataclass(frozen=True, slots=True)
class AuctionEntryModel:
    """Immutable incremental view backed by the canonical Auction implementation."""

    dealer: Seat = Seat.NORTH
    calls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.dealer, Seat):
            raise TypeError("dealer must be Seat")
        auction = Auction(self.dealer, self.calls)
        object.__setattr__(
            self, "calls", tuple(call.serialize() for call in auction.calls)
        )

    @classmethod
    def create(cls, dealer: str = Seat.NORTH.value) -> "AuctionEntryModel":
        return cls(Seat.parse(dealer))

    @property
    def auction(self) -> Auction:
        return Auction(self.dealer, self.calls)

    @property
    def next_seat(self) -> Seat:
        return self.auction.next_seat

    @property
    def is_complete(self) -> bool:
        return self.auction.is_complete

    @property
    def legal_call_values(self) -> tuple[str, ...]:
        return tuple(call.serialize() for call in self.auction.legal_calls())

    def add(self, value: str) -> "AuctionEntryModel":
        """Return a new state after canonical parsing and legality validation."""
        auction = self.auction
        auction.add(Call.parse(value))
        return type(self)(self.dealer, tuple(call.serialize() for call in auction.calls))

    def undo(self) -> "AuctionEntryModel":
        return type(self)(self.dealer, self.calls[:-1])

    def clear(self) -> "AuctionEntryModel":
        return type(self)(self.dealer)

    def change_dealer(self, dealer: str) -> "AuctionEntryModel":
        """Reset calls so an existing auction is never silently reinterpreted."""
        return type(self).create(dealer)

    def to_bidding_calls(self) -> tuple[str, ...]:
        return self.calls


def analyze_bidding_view(payload: Mapping[str, object]) -> dict[str, object]:
    """Normalize one bidding position without making a bidding decision here."""
    try:
        request = full_deal_application_request_from_dict(payload)
    except (TypeError, ValueError) as exc:
        return {"status": "error", "errors": (str(exc),)}
    if request.bidding is None or request.requested_stages != ("auction",):
        return {"status": "error", "errors": ("Only one auction stage with a bidding hand is supported.",)}

    context = request.bidding
    if classify_system_profile(context.system) is SystemProfile.UNKNOWN:
        return {
            "status": "error",
            "errors": (f"Unsupported system/profile: {context.system.system}.",),
        }
    response = analyze_full_deal_application(
        request, bidding_router=create_standard_sayc_router()
    )
    if not response.success or response.canonical_result is None:
        return {"status": "error", "errors": tuple(error.message for error in response.errors)}

    result = response.canonical_result.subsystem_results[0]
    trace = dict(result.debug_metadata)
    return {
        "status": result.status.value,
        "call": None if result.action.bid is None else result.action.bid.serialize(),
        "explanation": result.explanation,
        "sources": tuple(
            evidence.source.serialize()
            for evidence in result.evidence
            if evidence.source is not None
        ),
        "rule_id": trace.get("rule"),
        "route_id": trace.get("route"),
        "abstention_code": (
            None if result.abstention_code is None else result.abstention_code.value
        ),
        "system": context.system.system,
        "profile": classify_system_profile(context.system).value,
        "seat": context.seat.value,
        "errors": (),
    }


def main() -> None:
    """Launch a standard-library local form; analysis never modifies the engine."""
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("BridgeLab bidding view")
    fields = (
        ("Hand (S.H.D.C)", "hand", "KQJ876.32.43.543", None),
        ("Dealer", "dealer", DEALER_VALUES[0], DEALER_VALUES),
        ("Vulnerability", "vulnerability", VULNERABILITY_VALUES[0], VULNERABILITY_VALUES),
        ("System/profile", "system", SYSTEM_VALUES[0], SYSTEM_VALUES),
    )
    entries: dict[str, ttk.Entry | ttk.Combobox] = {}
    for row, (label, key, default, values) in enumerate(fields):
        ttk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        if values is None:
            entry = ttk.Entry(root, width=42)
            entry.insert(0, default)
        else:
            entry = ttk.Combobox(root, width=39, values=values, state="readonly")
            entry.set(default)
        entry.grid(row=row, column=1, padx=8, pady=4)
        entries[key] = entry

    auction_state = AuctionEntryModel.create()
    auction_text = tk.StringVar()
    entry_message = tk.StringVar()
    call_choice = ttk.Combobox(root, width=12, state="readonly")
    ttk.Label(root, text="Next call").grid(row=len(fields), column=0, sticky="w", padx=8)
    call_choice.grid(row=len(fields), column=1, sticky="w", padx=8)
    ttk.Label(root, textvariable=auction_text).grid(
        row=len(fields) + 1, column=0, columnspan=2, sticky="w", padx=8, pady=4
    )
    ttk.Label(root, textvariable=entry_message).grid(
        row=len(fields) + 3, column=0, columnspan=2, sticky="w", padx=8
    )

    output = tk.Text(root, width=70, height=12, wrap="word", state="disabled")
    output.grid(row=len(fields) + 5, column=0, columnspan=2, padx=8, pady=8)

    def refresh_auction() -> None:
        values = auction_state.legal_call_values
        call_choice.configure(values=values)
        call_choice.set(values[0] if values else "")
        calls = " ".join(auction_state.calls) or "(empty)"
        auction_text.set(
            f"Dealer: {auction_state.dealer.value} | Calls: {calls} | "
            f"Next: {auction_state.next_seat.value} | Complete: "
            f"{'yes' if auction_state.is_complete else 'no'}"
        )

    def add_call() -> None:
        nonlocal auction_state
        try:
            auction_state = auction_state.add(call_choice.get())
            entry_message.set("")
        except (TypeError, ValueError) as exc:
            entry_message.set(f"Input error: {exc}")
        refresh_auction()

    def undo_call() -> None:
        nonlocal auction_state
        auction_state = auction_state.undo()
        entry_message.set("")
        refresh_auction()

    def clear_auction() -> None:
        nonlocal auction_state
        auction_state = auction_state.clear()
        entry_message.set("")
        refresh_auction()

    def dealer_changed(_event: object = None) -> None:
        nonlocal auction_state
        auction_state = auction_state.change_dealer(entries["dealer"].get())
        entry_message.set("Auction cleared after dealer change.")
        refresh_auction()

    controls = ttk.Frame(root)
    controls.grid(row=len(fields) + 2, column=0, columnspan=2, pady=4)
    ttk.Button(controls, text="Add", command=add_call).pack(side="left", padx=3)
    ttk.Button(controls, text="Undo", command=undo_call).pack(side="left", padx=3)
    ttk.Button(controls, text="Clear", command=clear_auction).pack(side="left", padx=3)
    entries["dealer"].bind("<<ComboboxSelected>>", dealer_changed)

    def show() -> None:
        form = BiddingForm(
            hand=entries["hand"].get(),
            dealer=auction_state.dealer.value,
            auction_calls=auction_state.to_bidding_calls(),
            vulnerability=entries["vulnerability"].get(),
            system=entries["system"].get(),
        )
        view = analyze_bidding_view(form.to_payload())
        if view["status"] == "error":
            lines = ["Input error", *view["errors"]]
        else:
            lines = [
                f"Status: {view['status'].upper()}",
                f"Call: {view['call'] or 'No recommendation'}",
                f"Explanation: {view['explanation']}",
                f"Source: {', '.join(view['sources']) or 'None supplied'}",
                f"Rule: {view['rule_id'] or 'None'}",
                f"Route: {view['route_id'] or 'None'}",
                f"System/profile: {view['system']} / {view['profile']}",
                f"Seat: {view['seat']}",
                f"Abstention code: {view['abstention_code'] or 'None'}",
            ]
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("end", "\n".join(lines))
        output.configure(state="disabled")

    ttk.Button(root, text="Analyze", command=show).grid(
        row=len(fields) + 4, column=0, columnspan=2, pady=6
    )
    refresh_auction()
    show()
    root.mainloop()


if __name__ == "__main__":
    main()
