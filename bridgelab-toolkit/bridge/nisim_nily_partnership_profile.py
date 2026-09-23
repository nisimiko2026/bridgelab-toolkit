"""Canonical Nisim–Nily partnership profile data.

This constant identifies selected treatments and their source. It does not
load the convention card, evaluate hands, or register production bidding rules.
"""

from __future__ import annotations

from .partnership_profiles import (
    AgreementResolution,
    AgreementSelection,
    PartnershipProfile,
)
from .system_profiles import SystemProfile


NISIM_NILY_PROFILE = PartnershipProfile(
    profile_id="nisim-nily",
    version="29Y.1",
    base_system=SystemProfile.TWO_OVER_ONE_GF,
    agreements=(
        AgreementSelection(
            "response.major.two_over_one", AgreementResolution.ENABLE, "game_force"
        ),
        AgreementSelection(
            "response.major.1nt", AgreementResolution.ENABLE, "forcing"
        ),
        AgreementSelection(
            "response.major.raises", AgreementResolution.ENABLE, "bergen"
        ),
        AgreementSelection(
            "opening.2d", AgreementResolution.REPLACE, "multi_2d"
        ),
        AgreementSelection(
            "opening.2h", AgreementResolution.REPLACE, "nisim_nily_5h_5minor"
        ),
        AgreementSelection(
            "opening.2s", AgreementResolution.REPLACE, "nisim_nily_5s_5minor"
        ),
        AgreementSelection(
            "opening.2nt", AgreementResolution.REPLACE, "nisim_nily_5c_5d"
        ),
        AgreementSelection(
            "opening.three_level.six_minor",
            AgreementResolution.ENABLE,
            "nisim_nily_six_minor_preempt",
        ),
    ),
    sources=("bidding/convention-cards/cc-nily-nisim",),
)
