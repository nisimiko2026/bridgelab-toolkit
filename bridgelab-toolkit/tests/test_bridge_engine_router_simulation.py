from dataclasses import dataclass

from bridge import (
    Auction, BiddingEngine, BiddingEngineRouter, Call, ControlledAuctionSimulator,
    EngineRoute, Hand, KnowledgeSource, RuleDecision, Seat, SimulationStopReason,
    SystemContext, auction_calls,
)


SRC=KnowledgeSource("bidding/systems/sayc","Opening Bid Requirements")


@dataclass(frozen=True)
class FixedRule:
    rule_id:str
    call:str
    def evaluate(self,context):
        candidate=Call.parse(self.call)
        if not context.auction.is_legal(candidate):
            return RuleDecision.not_applicable(self.rule_id,"illegal")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=candidate,
            explanation="fixture",sources=(SRC,)
        )


def e(call): return BiddingEngine((FixedRule("fixture."+call,call),))


def deal():
    return {
        Seat.NORTH:Hand.parse("AKQJT98765432.-.-.-"),
        Seat.EAST:Hand.parse("-.AKQJT98765432.-.-"),
        Seat.SOUTH:Hand.parse("-.-.AKQJT98765432.-"),
        Seat.WEST:Hand.parse("-.-.-.AKQJT98765432"),
    }


def test_simulator_accepts_router_as_recommendation_engine():
    north=BiddingEngineRouter((EngineRoute("open",auction_calls(),e("1S")),))
    east=BiddingEngineRouter((EngineRoute("pass",auction_calls("1S"),e("P")),))
    south=BiddingEngineRouter((EngineRoute("pass",auction_calls("1S","P"),e("P")),))
    west=BiddingEngineRouter((EngineRoute("pass",auction_calls("1S","P","P"),e("P")),))
    engines={Seat.NORTH:north,Seat.EAST:east,Seat.SOUTH:south,Seat.WEST:west}
    systems={seat:SystemContext("SAYC") for seat in Seat}
    result=ControlledAuctionSimulator(hands=deal(),engines=engines,systems=systems).simulate(Auction(Seat.NORTH))
    assert result.stop_reason is SimulationStopReason.AUCTION_COMPLETE
    assert result.final_auction=="1S P P P"
