import pytest

from bridge import Hand, Rank, Suit, all_suit_quality_evidence, evaluate_hand, suit_quality_evidence


def test_records_all_ranks_descending():
    evidence = suit_quality_evidence(Hand.parse("AKQ97.JT8.64.532"), Suit.SPADES)
    assert evidence.ranks == (Rank.ACE, Rank.KING, Rank.QUEEN, Rank.NINE, Rank.SEVEN)


def test_records_honors_without_quality_label():
    evidence = suit_quality_evidence(Hand.parse("KJT97.A82.64.Q53"), Suit.SPADES)
    assert evidence.honors == (Rank.KING, Rank.JACK, Rank.TEN)
    assert evidence.honor_count == 3
    assert not hasattr(evidence, "is_good")
    assert not hasattr(evidence, "quality")


def test_top_honor_count_is_objective_qka_count():
    evidence = suit_quality_evidence(Hand.parse("AKJ97.Q82.64.T53"), Suit.SPADES)
    assert evidence.top_honor_count == 2


def test_top_rank():
    evidence = suit_quality_evidence(Hand.parse("Q9876.AK2.J4.T53"), Suit.SPADES)
    assert evidence.top_rank is Rank.QUEEN


def test_void_has_no_top_rank():
    evidence = suit_quality_evidence(Hand.parse("-.AKQJ9.T876.5432"), Suit.SPADES)
    assert evidence.top_rank is None
    assert evidence.length == 0


def test_detects_akq_sequence():
    evidence = suit_quality_evidence(Hand.parse("AKQ97.JT8.64.532"), Suit.SPADES)
    assert evidence.sequences == ((Rank.ACE, Rank.KING, Rank.QUEEN),)


def test_detects_multiple_sequences():
    evidence = suit_quality_evidence(Hand.parse("AKJT98.Q76.54.32"), Suit.SPADES)
    assert evidence.sequences == (
        (Rank.ACE, Rank.KING),
        (Rank.JACK, Rank.TEN, Rank.NINE, Rank.EIGHT),
    )


def test_single_cards_are_not_sequence_runs():
    evidence = suit_quality_evidence(Hand.parse("AQJ97.K82.64.T53"), Suit.SPADES)
    assert evidence.sequences == ((Rank.QUEEN, Rank.JACK),)


def test_longest_sequence_length():
    evidence = suit_quality_evidence(Hand.parse("KQJT9.A82.64.753"), Suit.SPADES)
    assert evidence.longest_sequence_length == 5


def test_all_suits_are_in_shdc_order():
    all_evidence = all_suit_quality_evidence(Hand.parse("AKQ97.JT8.64.532"))
    assert tuple(item.suit for item in all_evidence) == (
        Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS
    )


def test_hand_evaluation_exposes_quality_evidence():
    evaluation = evaluate_hand(Hand.parse("AKQ97.JT8.64.532"))
    evidence = evaluation.quality_evidence(Suit.SPADES)
    assert evidence.length == 5
    assert evidence.longest_sequence_length == 3


def test_quality_evidence_matches_hand_length():
    hand = Hand.parse("AKQ97.JT8.64.532")
    evaluation = evaluate_hand(hand)
    for suit in Suit:
        assert evaluation.quality_evidence(suit).length == evaluation.length(suit)


def test_suit_type_validation():
    with pytest.raises(TypeError):
        suit_quality_evidence(Hand.parse("AKQ97.JT8.64.532"), None)


def test_hand_type_validation():
    with pytest.raises(TypeError):
        suit_quality_evidence(None, Suit.SPADES)


def test_accessor_type_validation():
    evaluation = evaluate_hand(Hand.parse("AKQ97.JT8.64.532"))
    with pytest.raises(TypeError):
        evaluation.quality_evidence("S")
