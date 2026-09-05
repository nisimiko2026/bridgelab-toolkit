"""Immutable pre-dummy state for the opening-lead decision."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .auction import Auction, AuctionEntry, Contract
from .models import Card, Hand, Rank, Seat, Suit, Vulnerability
from .probability_engine import ProbabilityContext


class OpeningLeadStateFailureCode(str, Enum):
    MISSING_CONTRACT = "missing-contract"
    MISSING_DECLARER = "missing-declarer"
    MISSING_LEADER_HAND = "missing-leader-hand"
    MISSING_LEADER_SEAT = "missing-leader-seat"
    INVALID_LEADER_SEAT = "invalid-leader-seat"
    MISSING_REQUIRED_AUCTION = "missing-required-auction"
    EMPTY_HAND = "empty-hand"
    INVALID_CARD_STATE = "invalid-card-state"
    INCONSISTENT_CONTRACT_AUCTION = "inconsistent-contract-auction"


@dataclass(frozen=True, slots=True)
class OpeningLeadInput:
    contract: Contract | None = None
    declarer_seat: Seat | None = None
    opening_leader_seat: Seat | None = None
    opening_leader_hand: Hand | None = None
    vulnerability: Vulnerability | None = None
    auction: Auction | None = None
    require_auction: bool = False


@dataclass(frozen=True, slots=True)
class OpeningLeadState:
    contract: Contract
    opening_leader: Seat
    opening_leader_hand: Hand
    vulnerability: Vulnerability | None = None
    auction_entries: tuple[AuctionEntry, ...] | None = None

    def __post_init__(self) -> None:
        if self.opening_leader is not self.declarer.next():
            raise ValueError("opening leader must be the seat immediately left of declarer")
        if not self.opening_leader_hand.cards:
            raise ValueError("opening leader hand cannot be empty")
        if self.auction_entries is not None:
            object.__setattr__(self, "auction_entries", tuple(self.auction_entries))

    @property
    def declarer(self) -> Seat:
        return self.contract.declarer

    @property
    def partner(self) -> Seat:
        return self.opening_leader.partner()

    @property
    def legal_leads(self) -> tuple[Card, ...]:
        return tuple(self.opening_leader_hand)

    @property
    def known_cards(self) -> frozenset[Card]:
        return self.opening_leader_hand.cards

    @property
    def unknown_card_count(self) -> int:
        return 52 - len(self.known_cards)

    @property
    def suit_lengths(self) -> tuple[tuple[Suit, int], ...]:
        return tuple((suit, self.opening_leader_hand.length(suit)) for suit in Suit)

    @property
    def honor_holdings(self) -> tuple[tuple[Suit, tuple[Card, ...]], ...]:
        return tuple(
            (suit, tuple(card for card in self.opening_leader_hand.cards_in(suit) if card.rank >= Rank.TEN))
            for suit in Suit
        )


@dataclass(frozen=True, slots=True)
class OpeningLeadStateBuildResult:
    state: OpeningLeadState | None
    failure_code: OpeningLeadStateFailureCode | None = None
    explanation: str = ""

    @property
    def is_ready(self) -> bool:
        return self.state is not None


def build_opening_lead_state(source: OpeningLeadInput | None) -> OpeningLeadStateBuildResult:
    if source is None or source.contract is None:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.MISSING_CONTRACT, "Opening-lead contract is missing.")
    if source.declarer_seat is None:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.MISSING_DECLARER, "Declarer seat is missing.")
    if source.declarer_seat is not source.contract.declarer:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.INVALID_CARD_STATE, "Declarer seat conflicts with contract.")
    if source.opening_leader_seat is None:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.MISSING_LEADER_SEAT, "Opening leader seat is missing.")
    if source.opening_leader_seat is not source.declarer_seat.next():
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.INVALID_LEADER_SEAT, "Opening leader is not left of declarer.")
    if source.opening_leader_hand is None:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.MISSING_LEADER_HAND, "Opening leader hand is missing.")
    if not isinstance(source.opening_leader_hand, Hand):
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.INVALID_CARD_STATE, "Opening leader hand must be a canonical Hand.")
    if not source.opening_leader_hand.cards:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.EMPTY_HAND, "Opening leader hand is empty.")
    if source.require_auction and source.auction is None:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.MISSING_REQUIRED_AUCTION, "Caller required a complete auction.")
    if source.auction is not None:
        final = source.auction.final_contract
        if final is None or final != source.contract:
            return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.INCONSISTENT_CONTRACT_AUCTION, "Auction and contract are inconsistent.")
    try:
        state = OpeningLeadState(
            source.contract, source.opening_leader_seat, source.opening_leader_hand,
            source.vulnerability, None if source.auction is None else source.auction.entries,
        )
    except (TypeError, ValueError) as exc:
        return OpeningLeadStateBuildResult(None, OpeningLeadStateFailureCode.INVALID_CARD_STATE, str(exc))
    return OpeningLeadStateBuildResult(state)


def build_opening_lead_probability_context(state: OpeningLeadState) -> ProbabilityContext:
    return ProbabilityContext(state.known_cards, frozenset(), state.unknown_card_count)
