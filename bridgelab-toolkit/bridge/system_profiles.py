"""System-profile classification and capability eligibility.

This module separates bidding-system identity from partnership treatment
options.  It does not define bridge bidding semantics.

Phase 26C initially recognizes:

* SAYC;
* Two-over-One Game Force as a distinct system profile;
* unknown systems conservatively.

Two-over-One production eligibility still requires an explicit
``two_over_one = game_force`` partnership treatment.  System identity alone
does not silently enable the treatment.
"""

from __future__ import annotations

from enum import Enum

from .bidding_rules import SystemContext
from .major_response_options import (
    TwoOverOneTreatment,
    two_over_one_treatment,
)


class SystemProfile(Enum):
    """Recognized BridgeLab bidding-system profiles."""

    SAYC = "SAYC"
    TWO_OVER_ONE_GF = "TWO_OVER_ONE_GF"
    UNKNOWN = "UNKNOWN"


_SAYC_NAMES = {
    "sayc",
    "standard american yellow card",
}

_TWO_OVER_ONE_GF_NAMES = {
    "two_over_one_gf",
}


def classify_system_profile(system: SystemContext) -> SystemProfile:
    """Return the recognized system profile without guessing."""

    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    name = system.system.casefold()

    if name in _SAYC_NAMES:
        return SystemProfile.SAYC

    if name in _TWO_OVER_ONE_GF_NAMES:
        return SystemProfile.TWO_OVER_ONE_GF

    return SystemProfile.UNKNOWN


def supports_two_over_one_game_force(system: SystemContext) -> bool:
    """Whether the configured profile explicitly enables 2/1 Game Force."""

    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    profile = classify_system_profile(system)
    if profile not in {
        SystemProfile.SAYC,
        SystemProfile.TWO_OVER_ONE_GF,
    }:
        return False

    return (
        two_over_one_treatment(system)
        is TwoOverOneTreatment.GAME_FORCE
    )
