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

# Explicit opt-in revision: preserves the validated Phase 29Y profile snapshot.
# Authority is the user's B2.4A2 agreement, recorded in B2_4A2_NISIM_NILY_JACOBY_2NT.md.
JACOBY_2NT_FAMILY = "response.major.2nt"
JACOBY_2NT_TREATMENT = "nisim_nily_jacoby_2nt"
JACOBY_2NT_PARAMETERS = (("min_hcp", "13"), ("min_support", "4"))
JACOBY_2NT_APPROVAL = "B2_4A2_NISIM_NILY_JACOBY_2NT"

NISIM_NILY_JACOBY_2NT_PROFILE = PartnershipProfile(
    profile_id=NISIM_NILY_PROFILE.profile_id,
    version="B2.4A2",
    base_system=NISIM_NILY_PROFILE.base_system,
    agreements=NISIM_NILY_PROFILE.agreements + (
        AgreementSelection(JACOBY_2NT_FAMILY, AgreementResolution.ENABLE,
                           JACOBY_2NT_TREATMENT, JACOBY_2NT_PARAMETERS),
    ),
    sources=NISIM_NILY_PROFILE.sources + (JACOBY_2NT_APPROVAL,),
)

# B2.4B2 card revision is deliberately incomplete. Historical profile snapshots
# and the dedicated Jacoby API remain unchanged. No generic article is a card.
# Only the convention card's explicit fragments are recorded; missing upper
# support bounds, forcing flags and 3C/3D mappings are NOT inferred.
NISIM_NILY_BERGEN_PROFILE = PartnershipProfile(
    profile_id=NISIM_NILY_PROFILE.profile_id,
    version="B2.4B2",
    base_system=NISIM_NILY_PROFILE.base_system,
    agreements=tuple(a for a in NISIM_NILY_JACOBY_2NT_PROFILE.agreements
                     if a.family != "response.major.raises") + (
        AgreementSelection("response.major.raises", AgreementResolution.ENABLE,
            "BERGEN_RAISES", (
                ("card_source", "bidding/convention-cards/cc-nily-nisim"),
                ("simple_raise.call", "2M"),
                ("simple_raise.meaning", "simple raise"),
                ("simple_raise.min_hcp", "8"),
                ("simple_raise.max_hcp", "10"),
                ("simple_raise.min_support", "3"),
                ("three_clubs.call", "3C"),
                ("three_diamonds.call", "3D"),
                ("three_major.call", "3M"),
                ("three_major.meaning", "weak raise"),
                ("three_major.min_support", "4"),
            )),
    ),
    sources=NISIM_NILY_JACOBY_2NT_PROFILE.sources,
)
