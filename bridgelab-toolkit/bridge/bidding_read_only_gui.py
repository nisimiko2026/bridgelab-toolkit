"""Small local, read-only bidding view over the existing application boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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
        ("Calls (space separated)", "calls", "", None),
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

    output = tk.Text(root, width=70, height=12, wrap="word", state="disabled")
    output.grid(row=len(fields) + 1, column=0, columnspan=2, padx=8, pady=8)

    def show() -> None:
        form = BiddingForm(
            hand=entries["hand"].get(),
            dealer=entries["dealer"].get(),
            auction_calls=tuple(entries["calls"].get().split()),
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
        row=len(fields), column=0, columnspan=2, pady=6
    )
    show()
    root.mainloop()


if __name__ == "__main__":
    main()
