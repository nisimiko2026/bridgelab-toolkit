from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext,SystemContext
from bridge.models import Hand,Seat,Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router

CASES=(("1534",("P","P"),"T9843.AKJ32.7.65"),("4949",("P","P"),"AQ987.QJ974.-.862"),
("9577",("P","P","P"),"AK632.JT865.J.T6"),("nonqualifying",("P","P"),"JT753.K9742.6.AT"))

def main():
    router=create_standard_sayc_router()
    print("A9.7.2 SAYC Later-Seat Router Integration")
    print("routes",len(router.routes))
    for label,calls,hand in CASES:
        c=BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,calls),
            vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",{}))
        m=router.match(c); result=router.evaluate(c)
        call=None if result.recommended_call is None else result.recommended_call.serialize()
        print(label," ".join(calls),"route=",None if m is None else m.route_id,"->",call or "ABSTAIN")
if __name__=="__main__": main()
