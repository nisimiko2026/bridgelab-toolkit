from __future__ import annotations

import unittest

from bridge import (
    Auction,
    Bid,
    Call,
    CallType,
    Doubling,
    Seat,
    Strain,
)


class BidAndCallTests(unittest.TestCase):
    def test_strain_and_bid_parsing(self):
        self.assertIs(Strain.parse("NT"), Strain.NOTRUMP)
        self.assertIs(Strain.parse("♠"), Strain.SPADES)
        self.assertEqual(Bid.parse("1nt").serialize(), "1NT")
        self.assertEqual(str(Bid.parse("4h")), "4♥")

    def test_bid_order(self):
        self.assertTrue(Bid.parse("1D").outranks(Bid.parse("1C")))
        self.assertTrue(Bid.parse("1NT").outranks(Bid.parse("1S")))
        self.assertTrue(Bid.parse("2C").outranks(Bid.parse("1NT")))
        self.assertFalse(Bid.parse("3H").outranks(Bid.parse("3S")))

    def test_call_parsing(self):
        self.assertIs(Call.parse("pass").kind, CallType.PASS)
        self.assertIs(Call.parse("x").kind, CallType.DOUBLE)
        self.assertIs(Call.parse("xx").kind, CallType.REDOUBLE)
        self.assertEqual(Call.parse("2S").bid, Bid.parse("2S"))

    def test_invalid_bid_level_rejected(self):
        with self.assertRaises(ValueError):
            Bid.parse("8C")


class AuctionLegalityTests(unittest.TestCase):
    def test_seats_rotate_from_dealer(self):
        auction = Auction(Seat.SOUTH)
        self.assertIs(auction.add("1C").seat, Seat.SOUTH)
        self.assertIs(auction.add("P").seat, Seat.WEST)
        self.assertIs(auction.add("1H").seat, Seat.NORTH)
        self.assertIs(auction.next_seat, Seat.EAST)

    def test_new_bid_must_outrank_current_bid(self):
        auction = Auction(Seat.NORTH, ["1H"])
        self.assertFalse(auction.is_legal("1D"))
        self.assertFalse(auction.is_legal("1H"))
        self.assertTrue(auction.is_legal("1S"))
        self.assertTrue(auction.is_legal("2C"))
        with self.assertRaisesRegex(ValueError, "illegal call"):
            auction.add("1D")

    def test_double_requires_opponents_current_contract(self):
        auction = Auction(Seat.NORTH, ["1H"])
        self.assertTrue(auction.is_legal("X"))

        auction = Auction(Seat.NORTH, ["1H", "P"])
        self.assertFalse(auction.is_legal("X"))  # South is opener's partner.

        auction = Auction(Seat.NORTH, ["1H", "P", "P"])
        self.assertTrue(auction.is_legal("X"))  # West is an opponent.

    def test_redouble_requires_opponents_double(self):
        auction = Auction(Seat.NORTH, ["1H", "X"])
        self.assertTrue(auction.is_legal("XX"))
        self.assertFalse(auction.is_legal("X"))

        auction = Auction(Seat.NORTH, ["1H", "X", "P"])
        self.assertFalse(auction.is_legal("XX"))  # West is doubler's partner.

        auction = Auction(Seat.NORTH, ["1H", "X", "P", "P"])
        self.assertTrue(auction.is_legal("XX"))  # North is declaring side.

    def test_new_bid_resets_double_state(self):
        auction = Auction(Seat.NORTH, ["1H", "X", "2H"])
        self.assertIs(auction.doubling, Doubling.UNDOUBLED)
        self.assertTrue(auction.is_legal("X"))
        self.assertFalse(auction.is_legal("XX"))

    def test_passed_out_after_four_initial_passes(self):
        auction = Auction(Seat.WEST, ["P", "P", "P", "P"])
        self.assertTrue(auction.is_complete)
        self.assertTrue(auction.is_passed_out)
        self.assertIsNone(auction.final_contract)
        with self.assertRaisesRegex(ValueError, "already complete"):
            auction.add("1C")

    def test_three_passes_complete_auction_after_a_bid(self):
        auction = Auction(Seat.NORTH, ["1S", "P", "2S", "P", "P", "P"])
        self.assertTrue(auction.is_complete)
        self.assertFalse(auction.is_passed_out)
        self.assertEqual(auction.serialize(), "1S P 2S P P P")


class ContractTests(unittest.TestCase):
    def test_final_contract_and_declarer_first_strain_bidder(self):
        auction = Auction(
            Seat.NORTH,
            ["1H", "P", "2C", "P", "2H", "P", "4H", "P", "P", "P"],
        )
        contract = auction.final_contract
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract.bid, Bid.parse("4H"))
        self.assertIs(contract.declarer, Seat.NORTH)
        self.assertIs(contract.doubling, Doubling.UNDOUBLED)
        self.assertEqual(contract.serialize(), "4H N")

    def test_partner_can_be_declarer_if_partner_named_strain_first(self):
        auction = Auction(
            Seat.NORTH,
            ["1C", "P", "1S", "P", "2S", "P", "4S", "P", "P", "P"],
        )
        contract = auction.final_contract
        assert contract is not None
        self.assertIs(contract.declarer, Seat.SOUTH)

    def test_doubled_and_redoubled_contract_state(self):
        doubled = Auction(Seat.NORTH, ["1S", "X", "P", "P", "P"])
        self.assertIs(doubled.final_contract.doubling, Doubling.DOUBLED)

        redoubled = Auction(Seat.NORTH, ["1S", "X", "XX", "P", "P", "P"])
        self.assertIs(redoubled.final_contract.doubling, Doubling.REDOUBLED)

    def test_contract_unavailable_before_completion(self):
        auction = Auction(Seat.NORTH, ["1NT", "P"])
        self.assertIsNone(auction.final_contract)


if __name__ == "__main__":
    unittest.main()
