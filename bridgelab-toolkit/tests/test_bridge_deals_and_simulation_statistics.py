from bridge import (
    AuctionSimulationResult, Deal, Seat, SimulationStopReason,
    full_deck, generate_deal, generate_deals, summarize_simulations,
)


def result(reason,steps=(),seat=None):
    return AuctionSimulationResult(
        dealer=Seat.NORTH,initial_auction="",final_auction="",
        steps=tuple(steps),stop_reason=reason,stopped_seat=seat,
        complete=reason is SimulationStopReason.AUCTION_COMPLETE,
    )


def test_full_deck_has_52_unique_cards():
    deck=full_deck()
    assert len(deck)==52
    assert len(set(deck))==52


def test_same_seed_replays_identical_deal():
    assert generate_deal(20260901).serialize()==generate_deal(20260901).serialize()


def test_different_seeds_normally_produce_different_deals():
    assert generate_deal(1).serialize()!=generate_deal(2).serialize()


def test_generated_deal_is_complete_physical_deal():
    deal=generate_deal(17)
    cards=[card for hand in deal.mapping.values() for card in hand.cards]
    assert len(cards)==52
    assert len(set(cards))==52
    assert all(len(hand.cards)==13 for hand in deal.mapping.values())


def test_serialized_deal_round_trips_exact_hands():
    deal=generate_deal(314159)
    replay=Deal.parse(deal.serialize(),seed=deal.seed)
    assert replay.serialize()==deal.serialize()
    assert replay.seed==deal.seed


def test_batch_seed_sequence_is_stable():
    deals=generate_deals(start_seed=10,count=3)
    assert [d.seed for d in deals]==[10,11,12]
    assert deals==generate_deals(start_seed=10,count=3)


def test_zero_count_is_allowed():
    assert generate_deals(start_seed=1,count=0)==()


def test_negative_count_rejected():
    try:
        generate_deals(start_seed=1,count=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_statistics_empty_batch():
    stats=summarize_simulations(())
    assert stats.runs==0
    assert stats.average_calls_added==0.0
    assert stats.max_calls_added==0


def test_statistics_count_stop_reasons_and_seats():
    # step contents are irrelevant to aggregation; use placeholders.
    a=result(SimulationStopReason.NO_RECOMMENDATION,(1,2),Seat.SOUTH)
    b=result(SimulationStopReason.NO_RECOMMENDATION,(1,),Seat.EAST)
    c=result(SimulationStopReason.AUCTION_COMPLETE,(1,2,3,4),None)
    stats=summarize_simulations((a,b,c))
    assert stats.runs==3
    assert stats.completed==1
    assert stats.abstained==2
    assert stats.max_steps==0
    assert stats.total_calls_added==7
    assert stats.max_calls_added==4
    assert stats.average_calls_added==7/3
    assert dict(stats.stopped_seat_counts)=={"E":1,"S":1}
