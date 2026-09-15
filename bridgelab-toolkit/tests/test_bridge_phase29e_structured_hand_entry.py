"""Phase 29E structured input delegates validity to canonical Hand."""

from dataclasses import FrozenInstanceError

import pytest

from bridge.bidding_read_only_gui import (
    AuctionEntryModel,
    BiddingForm,
    StructuredHandEntry,
    analyze_bidding_view,
)
from bridge.models import Hand


def _entry(**changes):
    fields = dict(spades="KQJ876", hearts="32", diamonds="43", clubs="543")
    fields.update(changes)
    return StructuredHandEntry(**fields)


def test_example_serializes_in_existing_s_h_d_c_notation():
    assert _entry().to_canonical_hand() == "KQJ876.32.43.543"
    assert Hand.parse(_entry().to_canonical_hand()).serialize() == "KQJ876.32.43.543"


def test_case_and_harmless_whitespace_normalize():
    assert _entry(spades=" k q j 8 7 6 ", hearts=" 3 2 ").to_canonical_hand() == (
        "KQJ876.32.43.543"
    )


def test_void_uses_existing_dash_notation():
    entry = StructuredHandEntry("AKQJ9876", "KQJ", "AK", "")
    assert entry.to_canonical_hand() == "AKQJ9876.KQJ.AK.-"


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"clubs": "54"}, "exactly 13"),
        ({"clubs": "A543"}, "exactly 13"),
        ({"spades": "KQJ87Z"}, "invalid rank"),
        ({"spades": "KQJ8876"}, "duplicate"),
        ({"hearts": "3.2"}, "four dot-separated suits"),
    ],
)
def test_invalid_or_incomplete_hand_is_canonical_input_error(changes, message):
    with pytest.raises(ValueError, match=message):
        _entry(**changes).to_canonical_hand()


def test_bidding_form_receives_canonical_hand_unchanged():
    hand = _entry().to_canonical_hand()
    form = BiddingForm(hand)
    assert form.hand == form.to_payload()["bidding"]["hand"] == hand


def test_valid_hand_reaches_existing_analysis_and_preserves_sources():
    view = analyze_bidding_view(BiddingForm(_entry().to_canonical_hand()).to_payload())
    assert view["status"] == "recommendation" and view["call"]
    assert view["explanation"] and view["sources"] and view["rule_id"]
    assert view["route_id"] == "sayc.opening"


def test_invalid_hand_is_error_never_abstain():
    with pytest.raises(ValueError):
        _entry(clubs="54").to_canonical_hand()
    view = analyze_bidding_view(BiddingForm("KQJ876.32.43.54").to_payload())
    assert view["status"] == "error"


def test_valid_unsupported_auction_remains_abstain_without_call():
    auction = AuctionEntryModel.create().add("1C").add("1D")
    view = analyze_bidding_view(
        BiddingForm(_entry().to_canonical_hand(), auction_calls=auction.calls).to_payload()
    )
    assert (view["status"], view["call"]) == ("abstain", None)


def test_auction_display_and_controlled_calls_are_unaffected():
    auction = AuctionEntryModel.create().add("1C").add("P")
    assert auction.table_rows == (("1♣", "Pass", "", ""),)
    assert auction.to_bidding_calls() == ("1C", "P")


def test_model_is_immutable_and_contains_no_bidding_decision_state():
    entry = _entry()
    with pytest.raises(FrozenInstanceError):
        entry.spades = "A"
    assert set(StructuredHandEntry.__dataclass_fields__) == {
        "spades", "hearts", "diamonds", "clubs"
    }
