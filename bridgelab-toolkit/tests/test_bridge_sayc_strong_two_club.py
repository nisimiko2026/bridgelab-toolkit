from bridge import Auction, BiddingContext, Call, Hand, Seat, SystemContext, Vulnerability
from bridge.sayc import SaycStrongTwoClubOpeningRule, create_sayc_opening_engine
from bridge.sayc_strong_two_club import SaycStrongTwoClubWaitingResponseRule

def ctx(hand,calls=(),system="SAYC"):
    return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,calls),
      vulnerability=Vulnerability.NONE,system=SystemContext(system))

def test_22_hcp_opens_2c():
    r=create_sayc_opening_engine().evaluate(ctx("AKQ.AKQ.Q74.Q843"))
    assert r.recommended_call==Call.parse("2C")

def test_21_hcp_not_strong_2c():
    d=SaycStrongTwoClubOpeningRule().evaluate(ctx("AKQ.AKQ.J74.Q843"))
    assert not d.applicable

def test_strong_2c_is_sayc_only():
    d=SaycStrongTwoClubOpeningRule().evaluate(ctx("AKQ.AKQ.Q74.Q843",system="Acol"))
    assert not d.applicable

def test_waiting_2d_after_exact_2c_pass():
    d=SaycStrongTwoClubWaitingResponseRule().evaluate(ctx("743.852.J974.843",calls=("2C","P")))
    assert d.candidate==Call.parse("2D")

def test_waiting_rule_does_not_apply_elsewhere():
    d=SaycStrongTwoClubWaitingResponseRule().evaluate(ctx("743.852.J974.843",calls=("2NT","P")))
    assert not d.applicable
