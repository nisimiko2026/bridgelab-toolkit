"""Conservative routing configuration for existing BridgeLab SAYC engines.

This module adds no bidding rules.  It wires already-implemented engines to
the exact uncontested auction states they were built to handle.

Where several existing engines own the same response position, their existing
rule registries are combined into one ``BiddingEngine``.  No rule is modified,
and normal engine priority/candidate handling remains authoritative.
"""

from __future__ import annotations

from .sayc_1c1d_opener_rebids import create_sayc_one_club_one_diamond_opener_rebid_engine
from .sayc_major_raise_opener_rebids import create_sayc_simple_major_raise_opener_rebid_engine
from .sayc_1h1s_opener_rebids import create_sayc_one_heart_one_spade_opener_rebid_engine
from .sayc_1c1h_opener_rebids import create_sayc_one_club_one_heart_opener_rebid_engine
from .sayc_1c1s_opener_rebids import create_sayc_one_club_one_spade_opener_rebid_engine
from .sayc_1d1s_opener_rebids import create_sayc_one_diamond_one_spade_opener_rebid_engine
from .sayc_1d1h_opener_rebids import create_sayc_one_diamond_one_heart_opener_rebid_engine
from .auction import Strain
from .bidding_engine import BiddingEngine
from .engine_router import BiddingEngineRouter, EngineRoute, auction_calls
from .policy_registry import PolicyRegistry
from .sayc import create_sayc_opening_engine
from .sayc_strong_two_club import create_sayc_strong_two_club_response_engine
from .sayc_2nt_texas import create_sayc_two_notrump_texas_accept_engine
from .sayc_1nt_jacoby import (
    create_sayc_one_notrump_jacoby_response_engine,
    create_sayc_one_notrump_jacoby_accept_engine,
    create_sayc_one_notrump_jacoby_continuation_engine,
)
from .sayc_1nt_stayman import create_sayc_one_notrump_stayman_opener_response_engine
from .sayc_1nt_stayman_continuations import (
    create_sayc_one_notrump_stayman_major_fit_game_continuation_engine,
)
from .sayc_2nt_stayman import create_sayc_two_notrump_stayman_opener_response_engine
from .sayc_2nt_jacoby import (
    create_sayc_two_notrump_jacoby_response_engine,
    create_sayc_two_notrump_jacoby_accept_engine,
)
from .sayc_responses import create_sayc_one_club_response_engine
from .sayc_1d_responses import create_sayc_one_diamond_response_engine
from .sayc_1d_notrump import create_sayc_one_diamond_notrump_engine
from .sayc_1h_responses import create_sayc_one_heart_response_engine
from .sayc_1s_responses import create_sayc_one_spade_response_engine
from .sayc_major_one_notrump import create_sayc_major_one_notrump_response_engine
from .two_over_one_responses import create_sayc_two_over_one_response_engine
from .two_over_one_opener_rebids import create_sayc_two_over_one_opener_rebid_engine
from .sayc_natural_overcalls import create_sayc_natural_one_level_overcall_engine
from .sayc_weak_jump_overcalls import create_sayc_weak_jump_overcall_engine
from .sayc_takeout_double import create_sayc_takeout_double_engine
from .sayc_takeout_advancer import create_sayc_takeout_advancer_minimum_engine
from .sayc_support_double import create_sayc_support_double_example_engine
from .sayc_direct_notrump_overcall import create_sayc_direct_one_notrump_overcall_engine


def combine_existing_engines(*engines: BiddingEngine) -> BiddingEngine:
    """Combine existing rule registries without adding or changing theory."""
    rules=[]
    seen=set()
    for engine in engines:
        if not isinstance(engine,BiddingEngine):
            raise TypeError("engines must be BiddingEngine")
        for rule in engine.rules:
            key=rule.rule_id.casefold()
            if key in seen:
                raise ValueError(f"duplicate bidding rule_id while combining engines: {rule.rule_id}")
            seen.add(key)
            rules.append(rule)
    return BiddingEngine(rules)


def create_standard_sayc_router(
    registry: PolicyRegistry | None = None,
) -> BiddingEngineRouter:
    """Wire production SAYC engines only to their already-supported positions.

    Unsupported auctions intentionally have no route and therefore abstain.
    """
    if registry is None:
        registry=PolicyRegistry()
    if not isinstance(registry,PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")

    opening=create_sayc_opening_engine()
    natural_one_level_overcall=create_sayc_natural_one_level_overcall_engine(registry)
    weak_jump_overcall=create_sayc_weak_jump_overcall_engine(registry)
    takeout_double=create_sayc_takeout_double_engine(registry)
    takeout_advancer=create_sayc_takeout_advancer_minimum_engine(registry)
    support_double=create_sayc_support_double_example_engine(registry)
    direct_one_notrump=create_sayc_direct_one_notrump_overcall_engine(registry)
    strong_two_club_response=create_sayc_strong_two_club_response_engine()
    one_notrump_jacoby=create_sayc_one_notrump_jacoby_response_engine()
    one_notrump_jacoby_accept=create_sayc_one_notrump_jacoby_accept_engine()
    one_notrump_jacoby_continuation=create_sayc_one_notrump_jacoby_continuation_engine(registry)
    one_notrump_stayman_response=create_sayc_one_notrump_stayman_opener_response_engine(registry)
    one_notrump_stayman_continuation=(
        create_sayc_one_notrump_stayman_major_fit_game_continuation_engine(registry)
    )
    two_notrump_jacoby=create_sayc_two_notrump_jacoby_response_engine()
    two_notrump_jacoby_accept=create_sayc_two_notrump_jacoby_accept_engine()
    two_notrump_stayman_response=create_sayc_two_notrump_stayman_opener_response_engine()
    two_notrump_texas_accept=create_sayc_two_notrump_texas_accept_engine()
    one_club=create_sayc_one_club_response_engine()
    one_diamond=combine_existing_engines(
        create_sayc_one_diamond_response_engine(),
        create_sayc_one_diamond_notrump_engine(),
    )
    one_heart=combine_existing_engines(
        create_sayc_one_heart_response_engine(),
        create_sayc_major_one_notrump_response_engine(),
        create_sayc_two_over_one_response_engine(registry),
    )
    one_spade=combine_existing_engines(
        create_sayc_one_spade_response_engine(),
        create_sayc_major_one_notrump_response_engine(),
        create_sayc_two_over_one_response_engine(registry),
    )
    opener_rebid=create_sayc_two_over_one_opener_rebid_engine()
    one_diamond_one_heart_rebid=create_sayc_one_diamond_one_heart_opener_rebid_engine()
    one_diamond_one_spade_rebid=create_sayc_one_diamond_one_spade_opener_rebid_engine()
    one_club_one_spade_rebid=create_sayc_one_club_one_spade_opener_rebid_engine()
    one_club_one_heart_rebid=create_sayc_one_club_one_heart_opener_rebid_engine()
    one_heart_one_spade_rebid=create_sayc_one_heart_one_spade_opener_rebid_engine()
    one_spade_two_spade_rebid=create_sayc_simple_major_raise_opener_rebid_engine(Strain.SPADES)
    one_heart_two_heart_rebid=create_sayc_simple_major_raise_opener_rebid_engine(Strain.HEARTS)
    one_club_one_diamond_rebid=create_sayc_one_club_one_diamond_opener_rebid_engine()

    return BiddingEngineRouter((
        EngineRoute("sayc.opening",auction_calls(),opening,100),
        EngineRoute("sayc.overcall.direct.after.1c",auction_calls("1C"),combine_existing_engines(natural_one_level_overcall,weak_jump_overcall,takeout_double,direct_one_notrump),98),
        EngineRoute("sayc.overcall.direct.after.1d",auction_calls("1D"),combine_existing_engines(natural_one_level_overcall,weak_jump_overcall,takeout_double,direct_one_notrump),98),
        EngineRoute("sayc.overcall.direct.after.1h",auction_calls("1H"),combine_existing_engines(natural_one_level_overcall,weak_jump_overcall,takeout_double,direct_one_notrump),98),
        EngineRoute("sayc.overcall.direct.after.1s",auction_calls("1S"),combine_existing_engines(natural_one_level_overcall,weak_jump_overcall,takeout_double,direct_one_notrump),98),
        EngineRoute("sayc.advancer.takeout.after.1c",auction_calls("1C","X","P"),takeout_advancer,97),
        EngineRoute("sayc.advancer.takeout.after.1d",auction_calls("1D","X","P"),takeout_advancer,97),
        EngineRoute("sayc.advancer.takeout.after.1h",auction_calls("1H","X","P"),takeout_advancer,97),
        EngineRoute("sayc.advancer.takeout.after.1s",auction_calls("1S","X","P"),takeout_advancer,97),
        EngineRoute("sayc.support_double.1d.1h.1s",auction_calls("1D","P","1H","1S"),support_double,97),
        EngineRoute("sayc.support_double.1c.1h.1s",auction_calls("1C","P","1H","1S"),support_double,97),
        EngineRoute("sayc.support_double.1d.1s.2c",auction_calls("1D","P","1S","2C"),support_double,97),
        EngineRoute("sayc.support_double.1h.1s.2d",auction_calls("1H","P","1S","2D"),support_double,97),
        EngineRoute("sayc.response.2c.waiting",auction_calls("2C","P"),strong_two_club_response,96),
        EngineRoute("sayc.response.1nt.jacoby",auction_calls("1NT","P"),one_notrump_jacoby,95),
        EngineRoute("sayc.opener.1nt.jacoby.2d",auction_calls("1NT","P","2D","P"),one_notrump_jacoby_accept,94),
        EngineRoute("sayc.opener.1nt.jacoby.2h",auction_calls("1NT","P","2H","P"),one_notrump_jacoby_accept,94),
        EngineRoute("sayc.responder.1nt.jacoby.hearts.continuation",auction_calls("1NT","P","2D","P","2H","P"),one_notrump_jacoby_continuation,93),
        EngineRoute("sayc.responder.1nt.jacoby.spades.continuation",auction_calls("1NT","P","2H","P","2S","P"),one_notrump_jacoby_continuation,93),
        EngineRoute("sayc.opener.1nt.stayman",auction_calls("1NT","P","2C","P"),one_notrump_stayman_response,94),
        EngineRoute("sayc.responder.1nt.stayman.after.2h",auction_calls("1NT","P","2C","P","2H","P"),one_notrump_stayman_continuation,93),
        EngineRoute("sayc.responder.1nt.stayman.after.2s",auction_calls("1NT","P","2C","P","2S","P"),one_notrump_stayman_continuation,93),
        EngineRoute("sayc.response.2nt.jacoby",auction_calls("2NT","P"),two_notrump_jacoby,95),
        EngineRoute("sayc.opener.2nt.jacoby.3d",auction_calls("2NT","P","3D","P"),two_notrump_jacoby_accept,94),
        EngineRoute("sayc.opener.2nt.jacoby.3h",auction_calls("2NT","P","3H","P"),two_notrump_jacoby_accept,94),
        EngineRoute("sayc.opener.2nt.stayman",auction_calls("2NT","P","3C","P"),two_notrump_stayman_response,94),
        EngineRoute("sayc.opener.2nt.texas.4d",auction_calls("2NT","P","4D","P"),two_notrump_texas_accept,94),
        EngineRoute("sayc.opener.2nt.texas.4h",auction_calls("2NT","P","4H","P"),two_notrump_texas_accept,94),
        EngineRoute("sayc.response.1c",auction_calls("1C","P"),one_club,90),
        EngineRoute("sayc.response.1d",auction_calls("1D","P"),one_diamond,90),
        EngineRoute("sayc.response.1h",auction_calls("1H","P"),one_heart,90),
        EngineRoute("sayc.response.1s",auction_calls("1S","P"),one_spade,90),

        EngineRoute("sayc.opener.1d.1h",auction_calls("1D","P","1H","P"),one_diamond_one_heart_rebid,85),
        EngineRoute("sayc.opener.1d.1s",auction_calls("1D","P","1S","P"),one_diamond_one_spade_rebid,85),
        EngineRoute("sayc.opener.1c.1s",auction_calls("1C","P","1S","P"),one_club_one_spade_rebid,85),
        EngineRoute("sayc.opener.1c.1h",auction_calls("1C","P","1H","P"),one_club_one_heart_rebid,85),
        EngineRoute("sayc.opener.1h.1s",auction_calls("1H","P","1S","P"),one_heart_one_spade_rebid,85),
        EngineRoute("sayc.opener.1s.2s",auction_calls("1S","P","2S","P"),one_spade_two_spade_rebid,85),
        EngineRoute("sayc.opener.1h.2h",auction_calls("1H","P","2H","P"),one_heart_two_heart_rebid,85),
        EngineRoute("sayc.opener.1c.1d",auction_calls("1C","P","1D","P"),one_club_one_diamond_rebid,85),
        # Only the four canonical automatic 2/1 GF pairs audited in Phase 5Q.
        EngineRoute("sayc.2over1.opener.1h.2c",auction_calls("1H","P","2C","P"),opener_rebid,80),
        EngineRoute("sayc.2over1.opener.1h.2d",auction_calls("1H","P","2D","P"),opener_rebid,80),
        EngineRoute("sayc.2over1.opener.1s.2c",auction_calls("1S","P","2C","P"),opener_rebid,80),
        EngineRoute("sayc.2over1.opener.1s.2d",auction_calls("1S","P","2D","P"),opener_rebid,80),
    ))
