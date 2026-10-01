"""BEN REST transport for BridgeLab external bidding advice.

This module is BEN-specific.  It translates BridgeLab bidding state to BEN's
stateless /bid REST contract and translates the response into the provider-
neutral ExternalBiddingObservation introduced in A3.1.

It does not decide whether BEN is correct, does not interpret BEN output as
BridgeLab policy, and does not select among providers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .auction import CallType
from .bidding_rules import BiddingContext
from .capability_providers import ProviderStatus
from .external_bidding_adviser import ExternalBiddingObservation
from .models import Vulnerability


@dataclass(frozen=True, slots=True)
class BenTransportConfig:
    base_url: str = "http://127.0.0.1:8085"
    timeout_seconds: float = 10.0
    details: bool = True
    tournament: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.base_url, str) or not self.base_url.strip():
            raise ValueError("base_url must be a non-blank string")

        object.__setattr__(
            self,
            "base_url",
            self.base_url.strip().rstrip("/"),
        )

        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
        ):
            raise TypeError("timeout_seconds must be numeric")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if not isinstance(self.details, bool):
            raise TypeError("details must be bool")

        if self.tournament is not None:
            if not isinstance(self.tournament, str):
                raise TypeError("tournament must be None or a string")

            tournament = self.tournament.strip().lower()

            if tournament not in {"mp", "imps"}:
                raise ValueError(
                    "tournament must be None, 'mp', or 'imps'"
                )

            object.__setattr__(self, "tournament", tournament)


class BenBiddingTransport:
    """Call BEN's stateless /bid endpoint."""

    def __init__(
        self,
        config: BenTransportConfig = BenTransportConfig(),
    ) -> None:
        if not isinstance(config, BenTransportConfig):
            raise TypeError("config must be BenTransportConfig")

        self.config = config

    def observe(
        self,
        context: BiddingContext,
    ) -> ExternalBiddingObservation:
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")

        params = build_ben_bid_params(
            context,
            details=self.config.details,
            tournament=self.config.tournament,
        )

        url = (
            f"{self.config.base_url}/bid?"
            f"{urlencode(params)}"
        )

        try:
            with urlopen(
                url,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read()

        except HTTPError as exc:
            return ExternalBiddingObservation(
                status=ProviderStatus.FAILED,
                notes=(f"BEN HTTP {exc.code}",),
                explanation="BEN /bid request failed.",
            )

        except (URLError, TimeoutError, OSError) as exc:
            return ExternalBiddingObservation(
                status=ProviderStatus.UNAVAILABLE,
                notes=(type(exc).__name__,),
                explanation="BEN service is unavailable.",
            )

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ExternalBiddingObservation(
                status=ProviderStatus.FAILED,
                explanation="BEN returned an invalid JSON response.",
            )

        return parse_ben_bid_response(payload)


def build_ben_bid_params(
    context: BiddingContext,
    *,
    details: bool = True,
    tournament: str | None = None,
) -> dict[str, str]:
    """Translate BridgeLab bidding state to BEN /bid parameters."""

    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")

    params = {
        "hand": context.hand.serialize(),
        "seat": context.auction.next_seat.value,
        "dealer": context.auction.dealer.value,
        "vul": _ben_vulnerability(context.vulnerability),
        "ctx": _ben_auction(context),
    }

    if details:
        params["details"] = "true"

    if tournament is not None:
        normalized = tournament.strip().lower()
        if normalized not in {"mp", "imps"}:
            raise ValueError(
                "tournament must be None, 'mp', or 'imps'"
            )
        params["tournament"] = normalized

    return params


def parse_ben_bid_response(
    payload: Any,
) -> ExternalBiddingObservation:
    """Translate BEN JSON into the A3.1 provider-neutral observation."""

    if not isinstance(payload, dict):
        return ExternalBiddingObservation(
            status=ProviderStatus.FAILED,
            explanation="BEN /bid response must be a JSON object.",
        )

    error = payload.get("error")
    if error is not None:
        return ExternalBiddingObservation(
            status=ProviderStatus.FAILED,
            notes=(str(error),),
            explanation="BEN reported an error.",
        )

    bid = payload.get("bid")

    if not isinstance(bid, str) or not bid.strip():
        return ExternalBiddingObservation(
            status=ProviderStatus.ABSTAIN,
            explanation="BEN returned no bidding recommendation.",
        )

    try:
        recommendation = _normalize_ben_call(bid)
    except ValueError as exc:
        return ExternalBiddingObservation(
            status=ProviderStatus.FAILED,
            notes=(str(exc),),
            explanation="BEN returned an unsupported bid encoding.",
        )

    alternatives: list[str] = []

    candidates = payload.get("candidates", ())
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            raw_call = candidate.get("call")
            if not isinstance(raw_call, str):
                continue

            try:
                call = _normalize_ben_call(raw_call)
            except ValueError:
                continue

            if call != recommendation and call not in alternatives:
                alternatives.append(call)

    notes: list[str] = []

    who = payload.get("who")
    if isinstance(who, str) and who.strip():
        notes.append(f"who={who.strip()}")

    quality = payload.get("quality")
    if isinstance(quality, str) and quality.strip():
        notes.append(f"quality={quality.strip()}")

    return ExternalBiddingObservation(
        status=ProviderStatus.SUCCESS,
        recommendation=recommendation,
        alternatives=tuple(alternatives),
        model_id=who.strip() if isinstance(who, str) and who.strip() else None,
        notes=tuple(notes),
        explanation="BEN /bid recommendation.",
    )


def _ben_vulnerability(
    vulnerability: Vulnerability,
) -> str:
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    return {
        Vulnerability.NONE: "",
        Vulnerability.NS: "NS",
        Vulnerability.EW: "EW",
        Vulnerability.BOTH: "Both",
    }[vulnerability]


def _ben_auction(
    context: BiddingContext,
) -> str:
    encoded = [
        _encode_ben_call(entry.call)
        for entry in context.auction.entries
    ]
    return "-".join(encoded)


def _encode_ben_call(call) -> str:
    if call.kind is CallType.PASS:
        return "P"

    if call.kind is CallType.DOUBLE:
        return "X"

    if call.kind is CallType.REDOUBLE:
        return "XX"

    assert call.bid is not None

    text = call.bid.serialize()
    if text.endswith("NT"):
        return f"{text[0]}N"

    return text


def _normalize_ben_call(value: str) -> str:
    text = value.strip().upper().replace(" ", "")

    if text in {"--", "PA", "P", "PASS"}:
        return "P"

    if text in {"DB", "DBL", "X", "DOUBLE"}:
        return "X"

    if text in {"RD", "RDBL", "XX", "REDOUBLE"}:
        return "XX"

    if (
        len(text) == 2
        and text[0] in "1234567"
        and text[1] in "CDHSN"
    ):
        if text[1] == "N":
            return f"{text[0]}NT"
        return text

    if (
        len(text) == 3
        and text[0] in "1234567"
        and text[1:] == "NT"
    ):
        return text

    raise ValueError(f"unsupported BEN call: {value!r}")
