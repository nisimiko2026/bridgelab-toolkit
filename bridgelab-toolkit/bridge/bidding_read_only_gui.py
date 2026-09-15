"""Small local, read-only bidding view over the existing application boundary."""

from __future__ import annotations

from collections.abc import Mapping

from .full_deal_application import (
    analyze_full_deal_application,
    full_deal_application_request_from_dict,
)
from .sayc_route_configuration import create_standard_sayc_router
from .system_profiles import classify_system_profile


def analyze_bidding_view(payload: Mapping[str, object]) -> dict[str, object]:
    """Normalize one bidding position without making a bidding decision here."""
    try:
        request = full_deal_application_request_from_dict(payload)
    except (TypeError, ValueError) as exc:
        return {"status": "error", "errors": (str(exc),)}
    if request.bidding is None or request.requested_stages != ("auction",):
        return {"status": "error", "errors": ("Only one auction stage with a bidding hand is supported.",)}

    context = request.bidding
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
        ("Hand (S.H.D.C)", "hand", "KQJ876.32.43.543"),
        ("Dealer", "dealer", "N"),
        ("Calls (space separated)", "calls", ""),
        ("Vulnerability", "vulnerability", "None"),
        ("System", "system", "SAYC"),
    )
    entries: dict[str, ttk.Entry] = {}
    for row, (label, key, default) in enumerate(fields):
        ttk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        entry = ttk.Entry(root, width=42)
        entry.insert(0, default)
        entry.grid(row=row, column=1, padx=8, pady=4)
        entries[key] = entry

    output = tk.Text(root, width=70, height=12, wrap="word", state="disabled")
    output.grid(row=len(fields) + 1, column=0, columnspan=2, padx=8, pady=8)

    def show() -> None:
        payload = {
            "requested_stages": ["auction"],
            "bidding": {
                "hand": entries["hand"].get(),
                "auction": {
                    "dealer": entries["dealer"].get(),
                    "calls": entries["calls"].get().split(),
                },
                "vulnerability": entries["vulnerability"].get(),
                "system": {"id": entries["system"].get(), "options": {}},
            },
        }
        view = analyze_bidding_view(payload)
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
