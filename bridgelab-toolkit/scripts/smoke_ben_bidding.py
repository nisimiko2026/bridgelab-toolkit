"""Manual live smoke test for the BEN bidding provider.

Run explicitly:

    python scripts/smoke_ben_bidding.py

Optional BEN endpoint:

    python scripts/smoke_ben_bidding.py --base-url http://127.0.0.1:8085

This script is intentionally outside the normal pytest suite. BEN is an
optional external evidence provider and must not become a BridgeLab runtime or
test-suite requirement.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Allow direct execution from the repository root without installing BridgeLab.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from bridge.auction import Auction
from bridge.ben_bidding_transport import BenTransportConfig
from bridge.ben_provider import create_ben_bidding_adviser
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import ProviderStatus
from bridge.models import Hand, Seat, Vulnerability


DEFAULT_HAND = "AKQJ5.K82.976.A7"


def build_context() -> BiddingContext:
    """Build one deterministic BridgeLab bidding position."""

    return BiddingContext.create(
        hand=Hand.parse(DEFAULT_HAND),
        auction=Auction(
            Seat.NORTH,
            ("1C", "P"),
        ),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one live BridgeLab -> BEN bidding smoke test."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8085",
        help="BEN REST base URL",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--tournament",
        choices=("mp", "imps"),
        default=None,
        help="Optional BEN tournament scoring mode",
    )

    args = parser.parse_args()

    config = BenTransportConfig(
        base_url=args.base_url,
        timeout_seconds=args.timeout,
        details=True,
        tournament=args.tournament,
    )

    adviser = create_ben_bidding_adviser(
        config=config,
        version="live-smoke",
    )

    context = build_context()

    print("BridgeLab BEN live smoke test")
    print("-----------------------------")
    print(f"Endpoint: {config.base_url}")
    print(f"Hand:     {context.hand.serialize()}")
    print(f"Dealer:   {context.auction.dealer.value}")
    print(f"Auction:  {context.auction.serialize()}")
    print(f"Next:     {context.auction.next_seat.value}")
    print(f"Vul:      {context.vulnerability.value}")
    print()

    evidence = adviser.evidence(context)

    result = evidence.result

    print(f"Provider: {result.provider.provider_id}")
    print(f"Status:   {result.status.value}")

    if result.status is ProviderStatus.SUCCESS:
        print(
            "Bid:      "
            f"{result.recommendation.serialize()}"
        )

        if result.alternatives:
            print(
                "Other:    "
                + ", ".join(
                    call.serialize()
                    for call in result.alternatives
                )
            )

        if result.evidence.model_id:
            print(
                f"Model:    {result.evidence.model_id}"
            )

        if result.explanation:
            print(
                f"Explain:  {result.explanation}"
            )

        print()
        print(
            "Evidence scope: "
            f"{evidence.scope.value}"
        )
        print(
            "External system: "
            f"{evidence.system_id or 'UNKNOWN'}"
        )

        return 0

    if result.status is ProviderStatus.ABSTAIN:
        print("BEN returned no bidding recommendation.")

        if result.explanation:
            print(
                f"Explain:  {result.explanation}"
            )

        return 2

    if result.status is ProviderStatus.UNAVAILABLE:
        print("BEN is not reachable at the configured endpoint.")

        if result.explanation:
            print(
                f"Reason:   {result.explanation}"
            )

        print()
        print(
            "This is expected when the optional BEN service "
            "is not running."
        )

        return 3

    print("BEN request failed.")

    if result.explanation:
        print(
            f"Reason:   {result.explanation}"
        )

    return 4


if __name__ == "__main__":
    raise SystemExit(main())
