from dataclasses import dataclass

import pytest

from bridge import (
    Auction, BiddingEngine, Call, ControlledAuctionSimulator, Hand, KnowledgeSource,
    RuleDecision, Seat, SimulationStopReason, SystemContext, Vulnerability,
)


SRC = KnowledgeSource("bidding/systems/sayc", "Opening Bid Requirements")


@dataclass(frozen=True)
class FixedRule:
    rule_id: str
    call: str
    priority: int = 1

    def evaluate(self, context):
        candidate = Call.parse(self.call)
        if not context.auction.is_legal(candidate):
            return RuleDecision.not_applicable(self.rule_id, "fixed call is not legal")
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=candidate,
            explanation="fixture recommendation",
            sources=(SRC,),
            priority=self.priority,
        )


def deal():
    # Deterministic complete deck split; simulator tests orchestration, not bidding theory.
    return {
        Seat.NORTH: Hand.parse("AKQJT98765432.-.-.-"),
        Seat.EAST: Hand.parse("- .AKQJT98765432.-.-".replace(" ", "")),
        Seat.SOUTH: Hand.parse("-.-.AKQJT98765432.-"),
        Seat.WEST: Hand.parse("-.-.-.AKQJT98765432"),
    }


def systems():
    return {seat: SystemContext("SAYC") for seat in Seat}


def engines(**calls):
    mapping = {}
    for seat in Seat:
        call = calls.get(seat.value)
        mapping[seat] = BiddingEngine(()) if call is None else BiddingEngine((FixedRule(f"fixture.{seat.value}", call),))
    return mapping


def test_stops_without_guessing_when_first_engine_abstains():
    sim = ControlledAuctionSimulator(hands=deal(), engines=engines(), systems=systems())
    result = sim.simulate(Auction(Seat.NORTH))
    assert result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    assert result.stopped_seat is Seat.NORTH
    assert result.final_auction == ""
    assert result.steps == ()


def test_one_recommendation_then_stops_at_next_unknown_position():
    sim = ControlledAuctionSimulator(
        hands=deal(),
        engines=engines(N="1S"),
        systems=systems(),
    )
    result = sim.simulate(Auction(Seat.NORTH))
    assert result.final_auction == "1S"
    assert result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    assert result.stopped_seat is Seat.EAST
    assert result.steps[0].rule_id == "fixture.N"
    assert result.steps[0].sources == (SRC,)


def test_explicit_pass_rules_can_complete_an_auction():
    sim = ControlledAuctionSimulator(
        hands=deal(),
        engines=engines(N="1S", E="P", S="P", W="P"),
        systems=systems(),
    )
    result = sim.simulate(Auction(Seat.NORTH))
    assert result.complete
    assert result.stop_reason is SimulationStopReason.AUCTION_COMPLETE
    assert result.final_auction == "1S P P P"
    assert len(result.steps) == 4


def test_pass_is_not_an_implicit_fallback():
    sim = ControlledAuctionSimulator(
        hands=deal(),
        engines=engines(N="1S"),
        systems=systems(),
    )
    result = sim.simulate(Auction(Seat.NORTH))
    assert result.final_auction == "1S"
    assert result.stopped_seat is Seat.EAST


def test_simulation_can_continue_from_existing_auction():
    sim = ControlledAuctionSimulator(
        hands=deal(),
        engines=engines(S="2C"),
        systems=systems(),
    )
    result = sim.simulate(Auction(Seat.NORTH, ("1S", "P")))
    assert result.initial_auction == "1S P"
    assert result.final_auction == "1S P 2C"
    assert result.stopped_seat is Seat.WEST


def test_max_steps_stops_without_extra_call():
    sim = ControlledAuctionSimulator(
        hands=deal(),
        engines=engines(N="1C", E="1D", S="1H", W="1S"),
        systems=systems(),
    )
    result = sim.simulate(Auction(Seat.NORTH), max_steps=2)
    assert result.stop_reason is SimulationStopReason.MAX_STEPS
    assert result.final_auction == "1C 1D"
    assert result.stopped_seat is Seat.SOUTH


def test_step_preserves_alternative_calls():
    high = FixedRule("fixture.high", "1S", 10)
    low = FixedRule("fixture.low", "1NT", 5)
    es = engines()
    es[Seat.NORTH] = BiddingEngine((high, low))
    sim = ControlledAuctionSimulator(hands=deal(), engines=es, systems=systems())
    result = sim.simulate(Auction(Seat.NORTH))
    assert result.steps[0].call.serialize() == "1S"
    assert tuple(c.serialize() for c in result.steps[0].alternatives) == ("1NT",)


def test_rejects_duplicate_cards_across_hands():
    hands = deal()
    hands[Seat.EAST] = hands[Seat.NORTH]
    with pytest.raises(ValueError):
        ControlledAuctionSimulator(hands=hands, engines=engines(), systems=systems())


def test_requires_all_four_seats_for_hands_engines_and_systems():
    hands = deal()
    del hands[Seat.WEST]
    with pytest.raises(ValueError):
        ControlledAuctionSimulator(hands=hands, engines=engines(), systems=systems())


def test_max_steps_validation():
    sim = ControlledAuctionSimulator(hands=deal(), engines=engines(), systems=systems())
    with pytest.raises(ValueError):
        sim.simulate(Auction(Seat.NORTH), max_steps=0)
