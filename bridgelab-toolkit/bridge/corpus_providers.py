"""Small provider adapters.  External package schemas stay outside the Core."""
from __future__ import annotations
from typing import Any, Mapping
from .auction import Auction, Contract
from .corpus import CanonicalBoardRecord, SourceProvenance
from .models import Seat, Vulnerability

_VUL={"NONE":Vulnerability.NONE,"-":Vulnerability.NONE,"NS":Vulnerability.NS,"EW":Vulnerability.EW,"BOTH":Vulnerability.BOTH,"ALL":Vulnerability.BOTH}

def _vul(value: str) -> Vulnerability:
    try: return _VUL[value.strip().upper()]
    except KeyError as exc: raise ValueError(f"invalid vulnerability: {value!r}") from exc

class BridgeDealsNormalizedAdapter:
    """Adapter for an explicit BridgeLab-owned normalized interchange mapping."""
    provider_name="bridge-deals-normalized"
    def adapt(self, raw: Mapping[str, Any]) -> CanonicalBoardRecord:
        dealer=Seat.parse(str(raw["dealer"]))
        auction=None
        if raw.get("auction") is not None:
            auction=Auction(dealer, tuple(str(x) for x in raw["auction"]))
        contract=Contract.parse(str(raw["contract"])) if raw.get("contract") else None
        return CanonicalBoardRecord(
            provenance=SourceProvenance(provider=self.provider_name,source=str(raw.get("source","unknown")),record_id=str(raw["record_id"]) if raw.get("record_id") is not None else None),
            dealer=dealer,vulnerability=_vul(str(raw.get("vulnerability","None"))),auction=auction,contract=contract,
            tricks=int(raw["tricks"]) if raw.get("tricks") is not None else None,
            board_number=int(raw["board_number"]) if raw.get("board_number") is not None else None,
            ns_system=raw.get("ns_system"),ew_system=raw.get("ew_system"))

class PbnNormalizedAdapter(BridgeDealsNormalizedAdapter):
    """Independent provider boundary for PBN-derived normalized mappings."""
    provider_name="pbn-normalized"
