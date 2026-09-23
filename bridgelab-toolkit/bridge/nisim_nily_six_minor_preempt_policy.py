"""Phase 29T Nisim–Nily exact six-card minor three-level preempt policy.

Additive partnership-policy/audit module only. Historical Phase 29M/29Q
modules remain unchanged, and no production bidding route is registered.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum

from .models import Hand, Seat, Vulnerability
from .nisim_nily_opening_policy import assess_rule_of_20


class _Serializable:
    __slots__ = ()

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )


class SixMinorQuality(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"


class SixMinorVulnerability(str, Enum):
    FAVORABLE = "FAVORABLE"
    EQUAL = "EQUAL"
    UNFAVORABLE = "UNFAVORABLE"


class SixMinorDecision(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ONE_LEVEL = "ONE_LEVEL"
    THREE_LEVEL = "THREE_LEVEL"
    NO_THREE_LEVEL = "NO_THREE_LEVEL"


@dataclass(frozen=True, slots=True)
class SixMinorPreemptAssessment(_Serializable):
    decision: SixMinorDecision
    minor: str | None
    quality: SixMinorQuality | None
    quality_score: int | None
    required_score: int | None
    vulnerability_relation: SixMinorVulnerability | None
    opening_position: int
    rule20_score: int
    has_four_card_major: bool
    outside_hcp: int
    total_aces: int
    preferred_call: str | None
    reason: str
    production_adopted: bool = False
    policy_version: str = "nisim-nily.six-minor-preempt@29T.1"


def _serialized_suit_groups(hand: Hand) -> tuple[str, str, str, str]:
    groups = hand.serialize().split(".")
    if len(groups) != 4:
        raise ValueError("canonical Hand serialization must contain S.H.D.C groups")
    return tuple("" if group == "-" else group for group in groups)  # type: ignore[return-value]


def _six_minor_quality(cards: str) -> tuple[SixMinorQuality, int]:
    """Return the deterministic A+/A/B+/B/C+/C/D quality ladder."""
    if len(cards) != 6:
        raise ValueError("six-card minor quality requires exactly six cards")
    ranks = set(cards)
    top5 = sum(rank in ranks for rank in "AKQJT")
    akq = sum(rank in ranks for rank in "AKQ")

    # A examples: AQJTxx, KQJTxx, AKJ9xx.
    a = ("A" in ranks and sum(rank in ranks for rank in "KQJ") >= 2) or all(
        rank in ranks for rank in "KQJT"
    )
    if a:
        plus = all(rank in ranks for rank in "AKQ") or top5 >= 4
        return (SixMinorQuality.A_PLUS if plus else SixMinorQuality.A, 5 if plus else 4)

    # B examples: AQTxxx, KQTxxx, KQJxxx, QJT9xx.
    b = (akq >= 2 and any(rank in ranks for rank in "JT")) or all(
        rank in ranks for rank in "QJT9"
    )
    if b:
        plus = akq >= 2 and top5 >= 3
        return (SixMinorQuality.B_PLUS if plus else SixMinorQuality.B, 3 if plus else 2)

    # C examples: KJTxxx, QJTxxx, KQ9xxx.
    c = (
        all(rank in ranks for rank in "KQ")
        or ("J" in ranks and "T" in ranks and any(rank in ranks for rank in "AKQ"))
        or ("A" in ranks and any(rank in ranks for rank in "QJT"))
    )
    if c:
        plus = top5 >= 3
        return (SixMinorQuality.C_PLUS if plus else SixMinorQuality.C, 1 if plus else 0)

    return SixMinorQuality.D, -1


def _six_minor_vulnerability_relation(
    seat: Seat, vulnerability: Vulnerability
) -> SixMinorVulnerability:
    value = vulnerability.value
    if value in ("None", "Both"):
        return SixMinorVulnerability.EQUAL
    ns = seat.value in ("N", "S")
    actor_vulnerable = (value == "NS" and ns) or (value == "EW" and not ns)
    return (
        SixMinorVulnerability.UNFAVORABLE
        if actor_vulnerable
        else SixMinorVulnerability.FAVORABLE
    )


def _six_minor_required_score(
    opening_position: int, relation: SixMinorVulnerability
) -> int | None:
    # A+=5, A=4, B+=3, B=2, C+=1, C=0, D=-1.
    table = {
        1: {
            SixMinorVulnerability.FAVORABLE: 2,   # A or B
            SixMinorVulnerability.EQUAL: 3,       # A or especially strong B
            SixMinorVulnerability.UNFAVORABLE: 4, # A only
        },
        2: {
            SixMinorVulnerability.FAVORABLE: 3,   # A; occasionally strong B
            SixMinorVulnerability.EQUAL: 4,       # A only
            SixMinorVulnerability.UNFAVORABLE: 5, # very strong A only
        },
        3: {
            SixMinorVulnerability.FAVORABLE: 1,   # A/B; occasionally good C
            SixMinorVulnerability.EQUAL: 2,       # A or B
            SixMinorVulnerability.UNFAVORABLE: 3, # A; especially strong B
        },
        4: {},
    }
    return table.get(opening_position, {}).get(relation)


def assess_six_minor_three_level_preempt(
    hand: Hand,
    *,
    seat: Seat,
    vulnerability: Vulnerability,
    opening_position: int,
) -> SixMinorPreemptAssessment:
    """Assess the approved Nisim–Nily 3C/3D exception with exactly six cards.

    Rule of 20 has priority.  Seven-card or longer preempts, 6-5/6-6 hands,
    and production routing remain outside this additive Phase 29T policy.
    """
    if opening_position not in (1, 2, 3, 4):
        raise ValueError("opening_position must be 1..4")
    if not isinstance(seat, Seat) or not isinstance(vulnerability, Vulnerability):
        raise TypeError("canonical Seat and Vulnerability required")

    s_cards, h_cards, d_cards, c_cards = _serialized_suit_groups(hand)
    groups = (s_cards, h_cards, d_cards, c_cards)
    lengths = tuple(len(group) for group in groups)
    d, c = lengths[2], lengths[3]
    candidates = [("D", d_cards)] if d == 6 else []
    if c == 6:
        candidates.append(("C", c_cards))
    r20 = assess_rule_of_20(hand)

    other_minor_length = c if candidates and candidates[0][0] == "D" else d
    if len(candidates) != 1 or max(lengths[:2] + (other_minor_length,)) >= 5:
        return SixMinorPreemptAssessment(
            SixMinorDecision.NOT_APPLICABLE, None, None, None, None, None,
            opening_position, r20.score, max(lengths[:2]) == 4, 0,
            sum(group.count("A") for group in groups), None,
            "Exact six-card-minor exception requires one and only one six-card minor and no other five-card-or-longer suit.",
        )

    minor, minor_cards = candidates[0]
    quality, quality_score = _six_minor_quality(minor_cards)
    relation = _six_minor_vulnerability_relation(seat, vulnerability)
    has_four_major = max(lengths[0], lengths[1]) == 4
    outside_groups = groups[:2] + ((c_cards,) if minor == "D" else (d_cards,))
    hcp_value = {"A": 4, "K": 3, "Q": 2, "J": 1}
    outside_hcp = sum(
        hcp_value.get(rank, 0) for group in outside_groups for rank in group
    )
    total_aces = sum(group.count("A") for group in groups)

    if r20.qualifies:
        return SixMinorPreemptAssessment(
            SixMinorDecision.ONE_LEVEL, minor, quality, quality_score, None, relation,
            opening_position, r20.score, has_four_major, outside_hcp, total_aces,
            f"1{minor}",
            "Rule of 20 is satisfied; partnership policy uses the one-level minor opening, not a three-level preempt.",
        )

    if opening_position == 4:
        return SixMinorPreemptAssessment(
            SixMinorDecision.NO_THREE_LEVEL, minor, quality, quality_score, None, relation,
            opening_position, r20.score, has_four_major, outside_hcp, total_aces,
            None,
            "Fourth seat does not use the six-card-minor three-level preempt exception.",
        )

    if total_aces >= 2 or outside_hcp >= 7:
        return SixMinorPreemptAssessment(
            SixMinorDecision.NO_THREE_LEVEL, minor, quality, quality_score, None, relation,
            opening_position, r20.score, has_four_major, outside_hcp, total_aces,
            None,
            "Outside defensive strength is too high for the approved six-card-minor preempt exception.",
        )

    required = _six_minor_required_score(opening_position, relation)
    if required is None:
        return SixMinorPreemptAssessment(
            SixMinorDecision.NO_THREE_LEVEL, minor, quality, quality_score, None, relation,
            opening_position, r20.score, has_four_major, outside_hcp, total_aces,
            None,
            "Seat/vulnerability table does not authorize this six-card-minor preempt.",
        )

    # With a four-card major, require one quality step more.
    if has_four_major:
        required += 1

    if quality_score >= required and quality is not SixMinorQuality.D:
        return SixMinorPreemptAssessment(
            SixMinorDecision.THREE_LEVEL, minor, quality, quality_score, required, relation,
            opening_position, r20.score, has_four_major, outside_hcp, total_aces,
            f"3{minor}",
            "Six-card minor meets the approved quality threshold for seat and vulnerability.",
        )

    return SixMinorPreemptAssessment(
        SixMinorDecision.NO_THREE_LEVEL, minor, quality, quality_score, required, relation,
        opening_position, r20.score, has_four_major, outside_hcp, total_aces,
        None,
        "Six-card minor is below the approved quality threshold for seat and vulnerability.",
    )
