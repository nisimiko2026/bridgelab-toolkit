"""Stable public identity for registered production capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityType(str, Enum):
    BIDDING_ROUTE = "bidding-route"
    PROBABILITY_ENGINE = "probability-engine"
    DECLARER_TECHNIQUE = "declarer-technique"
    DEFENSIVE_ALGORITHM = "defensive-algorithm"
    OPENING_LEAD_ALGORITHM = "opening-lead-algorithm"


@dataclass(frozen=True, slots=True)
class CapabilityIdentity:
    capability_type: CapabilityType
    capability_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.capability_type, CapabilityType):
            raise TypeError("capability type must be a CapabilityType")
        if not isinstance(self.capability_id, str):
            raise TypeError("capability id must be a string")
        normalized = self.capability_id.strip()
        if not normalized:
            raise ValueError("capability id must not be blank")
        object.__setattr__(self, "capability_id", normalized)

    def serialize(self) -> dict[str, str]:
        return {"type": self.capability_type.value, "id": self.capability_id}


KNOWN_CARD_COUNT_CAPABILITY = CapabilityIdentity(
    CapabilityType.PROBABILITY_ENGINE,
    "known-card-count",
)

SIMPLE_UNBLOCK_KING_CAPABILITY = CapabilityIdentity(
    CapabilityType.DECLARER_TECHNIQUE,
    "simple-unblock-king",
)


def bidding_route_capability(route_id: str) -> CapabilityIdentity:
    return CapabilityIdentity(CapabilityType.BIDDING_ROUTE, route_id)
