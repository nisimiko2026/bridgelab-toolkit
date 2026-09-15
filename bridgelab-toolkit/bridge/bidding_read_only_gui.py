"""Small local, read-only bidding view over the existing application boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .auction import Auction, Bid, Call, CallType, Strain
from .full_deal_application import (
    analyze_full_deal_application,
    full_deal_application_request_from_dict,
)
from .sayc_route_configuration import create_standard_sayc_router
from .models import Hand, Seat, Vulnerability
from .system_profiles import SystemProfile, classify_system_profile


DEALER_VALUES = tuple(seat.value for seat in Seat)
VULNERABILITY_VALUES = tuple(value.value for value in Vulnerability)
SYSTEM_VALUES = tuple(
    profile.value for profile in SystemProfile if profile is not SystemProfile.UNKNOWN
)
SEAT_COLUMNS = tuple(Seat)


@dataclass(frozen=True, slots=True)
class StructuredHandEntry:
    """Editable suit text; the canonical Hand parser owns card validity."""

    spades: str
    hearts: str
    diamonds: str
    clubs: str

    def to_canonical_hand(self) -> str:
        groups = tuple(
            "".join(value.split()).upper() or "-"
            for value in (self.spades, self.hearts, self.diamonds, self.clubs)
        )
        return Hand.parse(".".join(groups)).serialize()


def friendly_call(canonical: str) -> str:
    """Translate one canonical call into a presentation-only label."""
    call = Call.parse(canonical)
    if call.kind is CallType.PASS:
        return "Pass"
    if call.kind is CallType.DOUBLE:
        return "Double"
    if call.kind is CallType.REDOUBLE:
        return "Redouble"
    assert call.bid is not None
    strain = {
        Strain.CLUBS: "♣",
        Strain.DIAMONDS: "♦",
        Strain.HEARTS: "♥",
        Strain.SPADES: "♠",
        Strain.NOTRUMP: "NT",
    }[call.bid.strain]
    return f"{call.bid.level}{strain}"


def canonical_call(label: str) -> str:
    """Reverse a friendly label without changing the domain parser."""
    aliases = {"Pass": "P", "Double": "X", "Redouble": "XX"}
    value = aliases.get(label, label)
    value = value.replace("♣", "C").replace("♦", "D")
    value = value.replace("♥", "H").replace("♠", "S")
    return Call.parse(value).serialize()


ALL_CANONICAL_CALLS = (
    "P",
    "X",
    "XX",
    *tuple(Bid(level, strain).serialize() for level in range(1, 8) for strain in Strain),
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

    @property
    def table_rows(self) -> tuple[tuple[str, str, str, str], ...]:
        """Arrange canonical seat-tagged entries into four display columns."""
        rows: list[list[str]] = []
        row = ["", "", "", ""]
        previous_column = -1
        for entry in self.auction.entries:
            column = SEAT_COLUMNS.index(entry.seat)
            if column <= previous_column:
                rows.append(row)
                row = ["", "", "", ""]
            row[column] = friendly_call(entry.call.serialize())
            previous_column = column
        if any(row):
            rows.append(row)
        return tuple(tuple(row) for row in rows)  # type: ignore[misc]


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
        ("♠ Spades", "spades", "KQJ876", None),
        ("♥ Hearts", "hearts", "32", None),
        ("♦ Diamonds", "diamonds", "43", None),
        ("♣ Clubs", "clubs", "543", None),
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
    table = ttk.Treeview(
        root, columns=DEALER_VALUES, show="headings", height=5, selectmode="none"
    )
    for seat in DEALER_VALUES:
        table.heading(seat, text=seat)
        table.column(seat, width=100, anchor="center")
    table.grid(row=len(fields) + 1, column=0, columnspan=2, padx=8, pady=4)
    ttk.Label(root, textvariable=auction_text).grid(
        row=len(fields) + 2, column=0, columnspan=2, sticky="w", padx=8
    )
    ttk.Label(root, textvariable=entry_message).grid(
        row=len(fields) + 4, column=0, columnspan=2, sticky="w", padx=8
    )

    output = tk.Text(root, width=70, height=12, wrap="word", state="disabled")
    output.grid(row=len(fields) + 7, column=0, columnspan=2, padx=8, pady=8)

    def refresh_auction() -> None:
        canonical_values = auction_state.legal_call_values
        labels = tuple(friendly_call(value) for value in canonical_values)
        call_choice.configure(values=labels, state="readonly" if labels else "disabled")
        call_choice.set(labels[0] if labels else "")
        for item in table.get_children():
            table.delete(item)
        for row in auction_state.table_rows:
            table.insert("", "end", values=row)
        auction_text.set(
            f"Dealer: {auction_state.dealer.value} | "
            f"Next: {auction_state.next_seat.value} | Complete: "
            f"{'yes' if auction_state.is_complete else 'no'}"
        )
        add_button.configure(state="disabled" if auction_state.is_complete else "normal")
        undo_button.configure(state="normal" if auction_state.calls else "disabled")

    def add_call() -> None:
        nonlocal auction_state
        try:
            auction_state = auction_state.add(canonical_call(call_choice.get()))
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
    controls.grid(row=len(fields) + 3, column=0, columnspan=2, pady=4)
    add_button = ttk.Button(controls, text="Add", command=add_call)
    add_button.pack(side="left", padx=3)
    undo_button = ttk.Button(controls, text="Undo", command=undo_call)
    undo_button.pack(side="left", padx=3)
    ttk.Button(controls, text="Clear", command=clear_auction).pack(side="left", padx=3)
    entries["dealer"].bind("<<ComboboxSelected>>", dealer_changed)

    def show() -> None:
        try:
            hand = StructuredHandEntry(
                spades=entries["spades"].get(),
                hearts=entries["hearts"].get(),
                diamonds=entries["diamonds"].get(),
                clubs=entries["clubs"].get(),
            ).to_canonical_hand()
        except (TypeError, ValueError) as exc:
            lines = ["Input error", str(exc)]
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("end", "\n".join(lines))
            output.configure(state="disabled")
            return
        form = BiddingForm(
            hand=hand,
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
        row=len(fields) + 6, column=0, columnspan=2, pady=6
    )
    refresh_auction()
    show()
    root.mainloop()


if __name__ == "__main__":
    main()
