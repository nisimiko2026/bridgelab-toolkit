from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_later_seat_opening import create_sayc_later_seat_opening_engine

CASES = (
    ("1534", ("P","P"), "T9843.AKJ32.7.65"),
    ("4949", ("P","P"), "AQ987.QJ974.-.862"),
    ("9577", ("P","P","P"), "AK632.JT865.J.T6"),
    ("nonqualifying", ("P","P"), "JT753.K9742.6.AT"),
)

def main():
    engine=create_sayc_later_seat_opening_engine()
    print("A9.7.1 SAYC Later-Seat Opening Adapter")
    for label,calls,hand_text in CASES:
        context=BiddingContext.create(
            hand=Hand.parse(hand_text),
            auction=Auction(Seat.NORTH,calls),
            vulnerability=Vulnerability.NONE,
            system=SystemContext.from_mapping("SAYC",{}),
        )
        result=engine.evaluate(context)
        call=None if result.recommended_call is None else result.recommended_call.serialize()
        print(label, " ".join(calls), hand_text, "->", call or "ABSTAIN")

if __name__=="__main__":
    main()
