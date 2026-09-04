from bridge import Auction,BiddingContext,Hand,Seat,SystemContext,Vulnerability,Call
from bridge.sayc_1d_notrump import create_sayc_one_diamond_notrump_engine

def ctx(hand,system="SAYC",calls=("1D","P")):
    return BiddingContext.create(
        hand=Hand.parse(hand), auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE, system=SystemContext(system)
    )

def test_10_balanced_no_major_gives_2nt():
    assert create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.8764.932")).recommended_call==Call.parse("2NT")

def test_12_balanced_no_major_gives_2nt():
    assert create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.Q764.932")).recommended_call==Call.parse("2NT")

def test_13_balanced_no_major_gives_3nt():
    assert create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.K764.932")).recommended_call==Call.parse("3NT")

def test_15_balanced_no_major_gives_3nt():
    assert create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.K764.Q32")).recommended_call==Call.parse("3NT")

def test_four_hearts_blocks_notrump():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ82.Q76.932")).has_recommendation

def test_four_spades_blocks_notrump():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ83.AJ2.Q76.932")).has_recommendation

def test_unbalanced_blocks_notrump():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.Q76542.9")).has_recommendation

def test_1nt_band_is_not_implemented():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.J82.8764.932")).has_recommendation

def test_non_sayc_rejected():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.8764.932","Acol")).has_recommendation

def test_wrong_auction_rejected():
    assert not create_sayc_one_diamond_notrump_engine().evaluate(ctx("KQ3.AJ2.8764.932",calls=("1C","P"))).has_recommendation
