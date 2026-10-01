"""Validation and independent-provider comparison for corpus ingestion."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .corpus import CanonicalBoardRecord

class ValidationStatus(Enum):
    ACCEPT="ACCEPT"
    ACCEPT_WITH_WARNINGS="ACCEPT_WITH_WARNINGS"
    INGESTION_CONFLICT="INGESTION_CONFLICT"
    REJECT="REJECT"

@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: ValidationStatus
    issues: tuple[str, ...] = ()


def validate_record(record: CanonicalBoardRecord) -> ValidationResult:
    issues=[]
    if record.deal is None: issues.append("deal missing")
    if record.auction is None: issues.append("auction missing")
    if record.contract is not None and record.auction is not None and record.auction.is_complete:
        if record.auction.final_contract != record.contract:
            return ValidationResult(ValidationStatus.REJECT,("contract conflicts with completed auction",))
    return ValidationResult(ValidationStatus.ACCEPT_WITH_WARNINGS if issues else ValidationStatus.ACCEPT, tuple(issues))


def compare_provider_records(a: CanonicalBoardRecord, b: CanonicalBoardRecord) -> ValidationResult:
    fields=("dealer","vulnerability","deal","contract","opening_lead","tricks","board_number")
    conflicts=[name for name in fields if getattr(a,name) != getattr(b,name)]
    if (a.auction is None) != (b.auction is None): conflicts.append("auction")
    elif a.auction is not None and b.auction is not None:
        if tuple(c.serialize() for c in a.auction.calls) != tuple(c.serialize() for c in b.auction.calls): conflicts.append("auction")
    if conflicts:
        return ValidationResult(ValidationStatus.INGESTION_CONFLICT, tuple(f"provider disagreement: {x}" for x in conflicts))
    return ValidationResult(ValidationStatus.ACCEPT)
