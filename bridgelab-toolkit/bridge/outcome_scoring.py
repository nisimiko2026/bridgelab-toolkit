"""Duplicate bridge scoring for measured contract outcomes.

A6.3 — Outcome Scoring Model.

Converts a canonical Contract plus declarer tricks and vulnerability into a
duplicate-bridge score. It contains no bidding-policy or recommendation logic.
"""
from __future__ import annotations
from dataclasses import dataclass

from .auction import Contract, Doubling, Strain
from .corpus import Vulnerability


def _is_vulnerable(contract: Contract, vulnerability: Vulnerability) -> bool:
    if vulnerability is Vulnerability.BOTH:
        return True
    if vulnerability is Vulnerability.NONE:
        return False
    if vulnerability is Vulnerability.NS:
        return contract.declarer.value in {"N", "S"}
    if vulnerability is Vulnerability.EW:
        return contract.declarer.value in {"E", "W"}
    raise ValueError(f"unsupported vulnerability: {vulnerability!r}")


@dataclass(frozen=True, slots=True)
class ContractOutcome:
    contract: Contract
    declarer_tricks: int
    vulnerability: Vulnerability
    declarer_vulnerable: bool
    target_tricks: int
    trick_delta: int
    made: bool
    declarer_score: int

    @property
    def ns_score(self) -> int:
        return self.declarer_score if self.contract.declarer.value in {"N", "S"} else -self.declarer_score


def score_contract_outcome(
    contract: Contract,
    declarer_tricks: int,
    vulnerability: Vulnerability,
) -> ContractOutcome:
    if not isinstance(contract, Contract):
        raise TypeError("contract must be Contract")
    if not isinstance(declarer_tricks, int) or isinstance(declarer_tricks, bool) or not 0 <= declarer_tricks <= 13:
        raise ValueError("declarer_tricks must be an integer from 0 to 13")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")

    vulnerable = _is_vulnerable(contract, vulnerability)
    target = contract.bid.level + 6
    delta = declarer_tricks - target

    if delta < 0:
        score = -_undertrick_penalty(-delta, contract.doubling, vulnerable)
    else:
        score = _made_score(contract, delta, vulnerable)

    return ContractOutcome(
        contract=contract,
        declarer_tricks=declarer_tricks,
        vulnerability=vulnerability,
        declarer_vulnerable=vulnerable,
        target_tricks=target,
        trick_delta=delta,
        made=delta >= 0,
        declarer_score=score,
    )


def _made_score(contract: Contract, overtricks: int, vulnerable: bool) -> int:
    level, strain = contract.bid.level, contract.bid.strain
    multiplier = {
        Doubling.UNDOUBLED: 1,
        Doubling.DOUBLED: 2,
        Doubling.REDOUBLED: 4,
    }[contract.doubling]

    if strain in {Strain.CLUBS, Strain.DIAMONDS}:
        base, over = level * 20, 20
    elif strain in {Strain.HEARTS, Strain.SPADES}:
        base, over = level * 30, 30
    else:
        base, over = 40 + (level - 1) * 30, 30

    contract_points = base * multiplier

    if contract.doubling is Doubling.UNDOUBLED:
        over_points, insult = overtricks * over, 0
    else:
        per_over = 200 if vulnerable else 100
        if contract.doubling is Doubling.REDOUBLED:
            per_over *= 2
        over_points = overtricks * per_over
        insult = 50 if contract.doubling is Doubling.DOUBLED else 100

    bonus = (500 if vulnerable else 300) if contract_points >= 100 else 50
    slam = 0
    if level == 6:
        slam = 750 if vulnerable else 500
    elif level == 7:
        slam = 1500 if vulnerable else 1000

    return contract_points + over_points + insult + bonus + slam


def _undertrick_penalty(undertricks: int, doubling: Doubling, vulnerable: bool) -> int:
    if doubling is Doubling.UNDOUBLED:
        return undertricks * (100 if vulnerable else 50)

    if vulnerable:
        doubled = 200 + (undertricks - 1) * 300
    elif undertricks == 1:
        doubled = 100
    elif undertricks == 2:
        doubled = 300
    elif undertricks == 3:
        doubled = 500
    else:
        doubled = 500 + (undertricks - 3) * 300

    return doubled * 2 if doubling is Doubling.REDOUBLED else doubled
