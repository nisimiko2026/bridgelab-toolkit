"""Exact count-matrix/primary-HCP proposals, with explicit residual HCP rejection.

Target: uniform physical unseen-card assignments satisfying all hard evidence.
No real hidden cards, system interpretation or playing-value computation enters
this sampler. Setup counts subsets and count matrices, never full hidden deals.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from math import comb
import random

from .auction_information import (
    AuctionInformationState, ConstraintConflict, ConstraintProvenance, EvidenceOrigin,
)
from .deals import full_deck
from .evaluation import SUIT_ORDER, high_card_points
from .hidden_hand_probability import (
    HiddenHandResult, HiddenSample, SamplingConfig, _soft_evidence, _summarize_samples,
)
from .models import Hand, Rank, Seat

Shape = tuple[int, int, int, int]
Matrix = tuple[Shape, Shape, Shape]
ALGORITHM = "exact-shape-primary-hcp-conditional-v1"


class ConditionalStatus(Enum):
    READY = "ready"
    CONTRADICTORY = "contradictory"
    INFEASIBLE = "infeasible"


@dataclass(frozen=True, slots=True)
class ConditionalDiagnostics:
    status: ConditionalStatus
    matrix_count: int
    proposal_allocation_count: int
    primary_hcp_seat: Seat
    residual_hcp_seats: tuple[Seat, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class ConditionalResult:
    model: HiddenHandResult
    diagnostics: ConditionalDiagnostics


@dataclass(frozen=True, slots=True)
class _Choice:
    honors: tuple
    spots: int
    hcp: int
    mass: int


def _draw_weighted(rng, options, weights):
    total = sum(weights)
    if total <= 0:
        raise ValueError("cannot draw from zero combinatorial mass")
    ticket = rng.randrange(total)
    for item, weight in zip(options, weights):
        if ticket < weight:
            return item
        ticket -= weight
    raise AssertionError("integer cumulative mass mismatch")


class ConditionalSampler:
    """Reusable setup for one immutable visible state.

    sample(config) is repeatable and does not mutate setup. Setup timestamps and
    memory measurements are intentionally external to reproducible results.
    Full target HCP constraints at other seats are applied as residual rejection
    of entire proposals, including a fresh count matrix on every attempt.
    """

    def __init__(self, state: AuctionInformationState):
        if not isinstance(state, AuctionInformationState):
            raise TypeError("requires AuctionInformationState, never a source deal")
        self._state = state
        self._seats = (state.partner, *state.opponents)
        self._conflicts = state.conflicts
        info = tuple(state.for_seat(seat) for seat in self._seats)
        self._info = info
        self._primary = min(range(3), key=lambda i: (
            info[i].hcp.maximum - info[i].hcp.minimum if info[i].hcp is not None else 41, i))
        primary_seat = self._seats[self._primary]
        total_hcp = 40 - high_card_points(state.own_hand)
        residual = tuple(self._seats[i] for i in range(3) if i != self._primary and info[i].hcp is not None
                         and (info[i].hcp.minimum > 0 or info[i].hcp.maximum < total_hcp))
        self._matrices = ()
        self._cumulative = ()
        self._shape_tables = {}
        if self._conflicts:
            self.diagnostics = ConditionalDiagnostics(
                ConditionalStatus.CONTRADICTORY, 0, 0, primary_seat, residual,
                "PT-A0 detected contradictory hard evidence; no sampling performed.")
            return

        unseen = tuple(card for card in full_deck() if card not in state.own_hand.cards)
        self._cards = tuple(tuple(card for card in unseen if card.suit is suit) for suit in SUIT_ORDER)
        self._spots = tuple(tuple(card for card in cards if card.rank < Rank.JACK) for cards in self._cards)
        self._choices = {}
        points = {Rank.ACE: 4, Rank.KING: 3, Rank.QUEEN: 2, Rank.JACK: 1}
        for j, cards in enumerate(self._cards):
            honors = tuple(card for card in cards if card.rank >= Rank.JACK)
            for count in range(len(cards) + 1):
                choices = []
                for mask in range(1 << len(honors)):
                    chosen = tuple(card for i, card in enumerate(honors) if mask & (1 << i))
                    spots = count - len(chosen)
                    if 0 <= spots <= len(self._spots[j]):
                        choices.append(_Choice(chosen, spots, sum(points[c.rank] for c in chosen),
                                               comb(len(self._spots[j]), spots)))
                self._choices[j, count] = tuple(choices)

        # For each primary shape, exact integer counts by total primary HCP.
        band = info[self._primary].hcp
        for shape in info[self._primary].possible_shapes:
            suffix = [None] * 5
            suffix[4] = {0: 1}
            for j in range(3, -1, -1):
                counts = Counter()
                for choice in self._choices[j, shape[j]]:
                    for tail_hcp, tail_mass in suffix[j + 1].items():
                        counts[choice.hcp + tail_hcp] += choice.mass * tail_mass
                suffix[j] = dict(counts)
            mass = sum(n for hcp, n in suffix[0].items() if band.minimum <= hcp <= band.maximum)
            if mass:
                self._shape_tables[shape] = (tuple(suffix), mass)

        # Enumerate feasible matrices only. Use the smallest shape domains first.
        domains = [tuple(item.possible_shapes) for item in info]
        domains[self._primary] = tuple(self._shape_tables)
        order = sorted(range(3), key=lambda i: len(domains[i]))
        a, b, c = order
        third = set(domains[c])
        remaining = tuple(len(cards) for cards in self._cards)
        matrices, cumulative, total = [], [], 0
        other = next(i for i in range(3) if i != self._primary)
        for first in domains[a]:
            for second in domains[b]:
                last = tuple(remaining[j] - first[j] - second[j] for j in range(4))
                if last not in third:
                    continue
                matrix = [None] * 3
                matrix[a], matrix[b], matrix[c] = first, second, last
                shape = matrix[self._primary]
                mass = self._shape_tables[shape][1]
                for j in range(4):
                    mass *= comb(remaining[j] - shape[j], matrix[other][j])
                total += mass
                matrices.append(tuple(matrix))
                cumulative.append(total)
        self._matrices = tuple(matrices)
        self._cumulative = tuple(cumulative)
        if total:
            status = ConditionalStatus.READY
            explanation = ("Exact suit/shape and primary-seat HCP conditioning; "
                           "any remaining seat HCP restrictions use explicitly counted rejection.")
        else:
            status = ConditionalStatus.INFEASIBLE
            explanation = "No physical allocations satisfy shape constraints and primary-seat HCP."
            evidence = (item for update in state.updates
                        for item in (update.hcp, *(e for _, e in update.suit_lengths), update.shapes)
                        if item is not None and item.is_hard)
            sources = tuple(dict.fromkeys(item.provenance for item in evidence))
            sources += (ConstraintProvenance(EvidenceOrigin.OWN_HAND,
                                            "exact perspective hand determines unseen cards"),)
            self._conflicts = (ConstraintConflict("conditional allocation has zero combinatorial mass", sources + (
                ConstraintProvenance(EvidenceOrigin.DERIVED_ARITHMETIC,
                                     "exact unseen-card subset and suit-capacity counts"),)),)
        self.diagnostics = ConditionalDiagnostics(status, len(matrices), total, primary_seat, residual, explanation)

    @property
    def state(self):
        return self._state

    def count_matrix_masses(self) -> tuple[tuple[Matrix, int], ...]:
        """Exact proposal masses, prior to residual HCP checks or soft weights."""
        previous = (0,) + self._cumulative[:-1]
        return tuple((matrix, high - low) for matrix, high, low in zip(
            self._matrices, self._cumulative, previous))

    def _proposal(self, rng):
        matrix = self._matrices[bisect_right(self._cumulative, rng.randrange(self._cumulative[-1]))]
        shape = matrix[self._primary]
        suffix, _ = self._shape_tables[shape]
        band = self._info[self._primary].hcp
        totals = tuple(hcp for hcp in sorted(suffix[0]) if band.minimum <= hcp <= band.maximum)
        remaining_hcp = _draw_weighted(rng, totals, tuple(suffix[0][hcp] for hcp in totals))
        primary_cards = []
        for j, count in enumerate(shape):
            choices = self._choices[j, count]
            weights = tuple(choice.mass * suffix[j + 1].get(remaining_hcp - choice.hcp, 0)
                            for choice in choices)
            chosen = _draw_weighted(rng, choices, weights)
            primary_cards.extend(chosen.honors)
            primary_cards.extend(rng.sample(self._spots[j], chosen.spots))
            remaining_hcp -= chosen.hcp
        hands = [None] * 3
        hands[self._primary] = Hand.from_cards(primary_cards)
        rest = [i for i in range(3) if i != self._primary]
        cards_by_seat = [[], []]
        held = set(primary_cards)
        for j, cards in enumerate(self._cards):
            available = [card for card in cards if card not in held]
            rng.shuffle(available)
            cut = matrix[rest[0]][j]
            cards_by_seat[0].extend(available[:cut])
            cards_by_seat[1].extend(available[cut:])
        for k, i in enumerate(rest):
            hands[i] = Hand.from_cards(cards_by_seat[k])
        return HiddenSample(tuple(zip(self._seats, hands)))

    def sample(self, config: SamplingConfig = SamplingConfig()) -> ConditionalResult:
        if not isinstance(config, SamplingConfig):
            raise TypeError("requires SamplingConfig")
        keys = {item.key for item in _soft_evidence(self._state)}
        if any(rule.key not in keys for rule in config.likelihoods):
            raise ValueError("likelihoods must reference existing soft evidence")
        if self._conflicts:
            model = _summarize_samples(self._state, config, (), 0, (), conflicts=self._conflicts,
                                       algorithm=ALGORITHM)
            return ConditionalResult(model, self.diagnostics)
        rng = random.Random(config.seed)
        accepted = []
        rejected = Counter()
        proposals = 0
        while len(accepted) < config.requested and proposals < config.max_proposals:
            sample = self._proposal(rng)
            proposals += 1
            reason = None
            for i, seat in enumerate(self._seats):
                if i == self._primary:
                    continue
                points = high_card_points(sample.hand(seat))
                band = self._info[i].hcp
                if not band.minimum <= points <= band.maximum:
                    reason = f"{seat.value}:residual_hcp"
                    break
            if reason:
                rejected[reason] += 1
            else:
                accepted.append(sample)
        model = _summarize_samples(self._state, config, accepted, proposals,
                                   tuple(sorted(rejected.items())), algorithm=ALGORITHM)
        return ConditionalResult(model, self.diagnostics)


def sample_conditional_hidden_hands(state: AuctionInformationState,
                                    config: SamplingConfig = SamplingConfig()) -> ConditionalResult:
    """Convenience entry point; use ConditionalSampler to amortize setup."""
    return ConditionalSampler(state).sample(config)
