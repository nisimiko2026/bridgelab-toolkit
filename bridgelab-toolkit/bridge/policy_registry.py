"""BridgeLab partnership/system policy registry.

The registry binds explicit partnership/system option values to concrete policy
objects supplied by the application. It contains no bridge theory.

Supported policy roles are ``stopper_policy``, ``suit_quality_policy``, ``playing_strength_policy``, and ``offensive_hand_policy``.
"""
# ruff: noqa: E701, E702, F401 -- preserve established compact/import style

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .bidding_rules import BiddingContext, SystemContext
from .models import Suit
from .stopper_policy import StopperAssessment, StopperPolicy, assess_stopper
from .suit_quality_policy import SuitQualityAssessment, SuitQualityPolicy, assess_suit_quality
from .playing_strength_policy import PlayingStrengthAssessment, PlayingStrengthPolicy, assess_playing_strength
from .offensive_hand_policy import OffensiveHandAssessment, OffensiveHandPolicy, assess_offensive_hand
from .opponent_suit_shortness_policy import OpponentSuitShortnessAssessment, OpponentSuitShortnessPolicy, assess_opponent_suit_shortness
from .takeout_advancer_strength_policy import TakeoutAdvancerStrengthAssessment, TakeoutAdvancerStrengthPolicy, assess_takeout_advancer_strength
from .support_double_eligibility_policy import SupportDoubleEligibilityAssessment, SupportDoubleEligibilityPolicy, assess_support_double_eligibility
from .jacoby_continuation_strength_policy import JacobyContinuationStrengthAssessment, JacobyContinuationStrengthPolicy, assess_jacoby_continuation_strength
from .stayman_continuation_strength_policy import StaymanContinuationStrengthAssessment, StaymanContinuationStrengthPolicy, assess_stayman_continuation_strength
from .stayman_dual_major_response_policy import StaymanDualMajorResponseAssessment, StaymanDualMajorResponsePolicy, assess_stayman_dual_major_response


STOPPER_POLICY_OPTION = "stopper_policy"
SUIT_QUALITY_POLICY_OPTION = "suit_quality_policy"
PLAYING_STRENGTH_POLICY_OPTION = "playing_strength_policy"
OFFENSIVE_HAND_POLICY_OPTION = "offensive_hand_policy"
OPPONENT_SUIT_SHORTNESS_POLICY_OPTION = "opponent_suit_shortness_policy"
TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION = "takeout_advancer_strength_policy"
SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION = "support_double_eligibility_policy"
JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION = "jacoby_continuation_strength_policy"
STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION = "stayman_continuation_strength_policy"
STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION = "stayman_dual_major_response_policy"


@dataclass(frozen=True, slots=True)
class PolicyRegistry:
    """Immutable registry of explicitly supplied partnership policies."""

    _stoppers: tuple[tuple[str, StopperPolicy], ...] = ()
    _suit_qualities: tuple[tuple[str, SuitQualityPolicy], ...] = ()
    _playing_strengths: tuple[tuple[str, PlayingStrengthPolicy], ...] = ()
    _offensive_hands: tuple[tuple[str, OffensiveHandPolicy], ...] = ()
    _opponent_shortness: tuple[tuple[str, OpponentSuitShortnessPolicy], ...] = ()
    _takeout_advancer_strength: tuple[tuple[str, TakeoutAdvancerStrengthPolicy], ...] = ()
    _support_double_eligibility: tuple[tuple[str, SupportDoubleEligibilityPolicy], ...] = ()
    _jacoby_continuation_strength: tuple[tuple[str, JacobyContinuationStrengthPolicy], ...] = ()
    _stayman_continuation_strength: tuple[tuple[str, StaymanContinuationStrengthPolicy], ...] = ()
    _stayman_dual_major_response: tuple[tuple[str, StaymanDualMajorResponsePolicy], ...] = ()

    @classmethod
    def from_stopper_policies(
        cls,
        policies: Iterable[StopperPolicy],
    ) -> "PolicyRegistry":
        items: list[tuple[str, StopperPolicy]] = []
        seen: set[str] = set()

        for policy in policies:
            try:
                raw_id = policy.policy_id
            except AttributeError as exc:
                raise TypeError("stopper policy must expose policy_id") from exc

            if not isinstance(raw_id, str):
                raise TypeError("stopper policy policy_id must be a string")

            policy_id = raw_id.strip()
            if not policy_id:
                raise ValueError("stopper policy policy_id must not be blank")

            folded = policy_id.casefold()
            if folded in seen:
                raise ValueError(f"duplicate stopper policy_id: {policy_id}")

            seen.add(folded)
            items.append((policy_id, policy))

        items.sort(key=lambda item: item[0].casefold())
        return cls(tuple(items), (), (), (), (), (), (), ())

    @classmethod
    def from_policies(
        cls,
        *,
        stopper_policies: Iterable[StopperPolicy] = (),
        suit_quality_policies: Iterable[SuitQualityPolicy] = (),
        playing_strength_policies: Iterable[PlayingStrengthPolicy] = (),
        offensive_hand_policies: Iterable[OffensiveHandPolicy] = (),
        opponent_suit_shortness_policies: Iterable[OpponentSuitShortnessPolicy] = (),
        takeout_advancer_strength_policies: Iterable[TakeoutAdvancerStrengthPolicy] = (),
        support_double_eligibility_policies: Iterable[SupportDoubleEligibilityPolicy] = (),
        jacoby_continuation_strength_policies: Iterable[JacobyContinuationStrengthPolicy] = (),
        stayman_continuation_strength_policies: Iterable[StaymanContinuationStrengthPolicy] = (),
        stayman_dual_major_response_policies: Iterable[StaymanDualMajorResponsePolicy] = (),
    ) -> "PolicyRegistry":
        stopper_registry = cls.from_stopper_policies(stopper_policies)
        quality_items = _normalize_quality_policies(suit_quality_policies)
        strength_items = _normalize_playing_strength_policies(playing_strength_policies)
        offensive_items = _normalize_offensive_hand_policies(offensive_hand_policies)
        shortness_items = _normalize_opponent_shortness_policies(opponent_suit_shortness_policies)
        advancer_items = _normalize_takeout_advancer_strength_policies(takeout_advancer_strength_policies)
        support_double_items = _normalize_support_double_eligibility_policies(support_double_eligibility_policies)
        jacoby_items = _normalize_jacoby_continuation_strength_policies(jacoby_continuation_strength_policies)
        stayman_items = _normalize_stayman_continuation_strength_policies(stayman_continuation_strength_policies)
        dual_major_items = _normalize_stayman_dual_major_response_policies(stayman_dual_major_response_policies)
        return cls(stopper_registry._stoppers, quality_items, strength_items, offensive_items, shortness_items, advancer_items, support_double_items, jacoby_items, stayman_items, dual_major_items)

    @classmethod
    def from_suit_quality_policies(
        cls,
        policies: Iterable[SuitQualityPolicy],
    ) -> "PolicyRegistry":
        return cls((), _normalize_quality_policies(policies), (), (), (), (), (), ())

    @classmethod
    def from_playing_strength_policies(
        cls,
        policies: Iterable[PlayingStrengthPolicy],
    ) -> "PolicyRegistry":
        return cls((), (), _normalize_playing_strength_policies(policies), (), (), (), (), ())

    @property
    def stopper_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._stoppers)

    def stopper_policy(self, policy_id: str) -> StopperPolicy | None:
        if not isinstance(policy_id, str):
            raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted:
            raise ValueError("policy_id must not be blank")

        for stored_id, policy in self._stoppers:
            if stored_id.casefold() == wanted:
                return policy
        return None


    @property
    def suit_quality_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._suit_qualities)

    def suit_quality_policy(self, policy_id: str) -> SuitQualityPolicy | None:
        if not isinstance(policy_id, str):
            raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted:
            raise ValueError("policy_id must not be blank")

        for stored_id, policy in self._suit_qualities:
            if stored_id.casefold() == wanted:
                return policy
        return None


    @property
    def playing_strength_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._playing_strengths)

    def playing_strength_policy(self, policy_id: str) -> PlayingStrengthPolicy | None:
        if not isinstance(policy_id, str):
            raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted:
            raise ValueError("policy_id must not be blank")

        for stored_id, policy in self._playing_strengths:
            if stored_id.casefold() == wanted:
                return policy
        return None


    @classmethod
    def from_offensive_hand_policies(cls, policies: Iterable[OffensiveHandPolicy]) -> "PolicyRegistry":
        return cls((), (), (), _normalize_offensive_hand_policies(policies), (), (), (), ())

    @property
    def offensive_hand_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._offensive_hands)

    def offensive_hand_policy(self, policy_id: str) -> OffensiveHandPolicy | None:
        if not isinstance(policy_id, str): raise TypeError("policy_id must be a string")
        wanted=policy_id.strip().casefold()
        if not wanted: raise ValueError("policy_id must not be blank")
        for stored_id, policy in self._offensive_hands:
            if stored_id.casefold()==wanted: return policy
        return None

    @classmethod
    def from_opponent_suit_shortness_policies(cls, policies):
        return cls((), (), (), (), _normalize_opponent_shortness_policies(policies), (), (), ())

    def opponent_suit_shortness_policy(self, policy_id: str):
        if not isinstance(policy_id,str): raise TypeError("policy_id must be a string")
        wanted=policy_id.strip().casefold()
        if not wanted: raise ValueError("policy_id must not be blank")
        for stored_id,policy in self._opponent_shortness:
            if stored_id.casefold()==wanted: return policy
        return None

    @classmethod
    def from_takeout_advancer_strength_policies(cls, policies):
        return cls((), (), (), (), (), _normalize_takeout_advancer_strength_policies(policies), (), ())

    def takeout_advancer_strength_policy(self, policy_id: str):
        if not isinstance(policy_id,str): raise TypeError("policy_id must be a string")
        wanted=policy_id.strip().casefold()
        if not wanted: raise ValueError("policy_id must not be blank")
        for stored_id,policy in self._takeout_advancer_strength:
            if stored_id.casefold()==wanted:return policy
        return None

    @classmethod
    def from_support_double_eligibility_policies(cls, policies):
        return cls((), (), (), (), (), (), _normalize_support_double_eligibility_policies(policies), ())

    def support_double_eligibility_policy(self, policy_id: str):
        if not isinstance(policy_id,str): raise TypeError("policy_id must be a string")
        wanted=policy_id.strip().casefold()
        if not wanted: raise ValueError("policy_id must not be blank")
        for stored_id,policy in self._support_double_eligibility:
            if stored_id.casefold()==wanted:return policy
        return None

    @classmethod
    def from_jacoby_continuation_strength_policies(cls, policies):
        return cls((), (), (), (), (), (), (), _normalize_jacoby_continuation_strength_policies(policies))

    def jacoby_continuation_strength_policy(self, policy_id: str):
        if not isinstance(policy_id, str): raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted: raise ValueError("policy_id must not be blank")
        for stored_id, policy in self._jacoby_continuation_strength:
            if stored_id.casefold() == wanted: return policy
        return None

    @classmethod
    def from_stayman_continuation_strength_policies(cls, policies):
        return cls((), (), (), (), (), (), (), (), _normalize_stayman_continuation_strength_policies(policies))

    @property
    def stayman_continuation_strength_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._stayman_continuation_strength)

    def stayman_continuation_strength_policy(self, policy_id: str):
        if not isinstance(policy_id, str):
            raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted:
            raise ValueError("policy_id must not be blank")
        for stored_id, policy in self._stayman_continuation_strength:
            if stored_id.casefold() == wanted:
                return policy
        return None

    @classmethod
    def from_stayman_dual_major_response_policies(cls, policies):
        return cls((), (), (), (), (), (), (), (), (), _normalize_stayman_dual_major_response_policies(policies))

    @property
    def stayman_dual_major_response_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy_id for policy_id, _ in self._stayman_dual_major_response)

    def stayman_dual_major_response_policy(self, policy_id: str):
        if not isinstance(policy_id, str):
            raise TypeError("policy_id must be a string")
        wanted = policy_id.strip().casefold()
        if not wanted:
            raise ValueError("policy_id must not be blank")
        for stored_id, policy in self._stayman_dual_major_response:
            if stored_id.casefold() == wanted:
                return policy
        return None

def configured_stopper_policy_id(system: SystemContext) -> str | None:
    """Return the configured stopper policy ID, if any."""
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    configured = system.option(STOPPER_POLICY_OPTION)
    if configured is None:
        return None

    value = str(configured).strip()
    return value or None


def resolve_stopper_policy(
    system: SystemContext,
    registry: PolicyRegistry,
) -> StopperPolicy | None:
    """Resolve the stopper policy selected by ``SystemContext``."""
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")

    policy_id = configured_stopper_policy_id(system)
    if policy_id is None:
        return None
    return registry.stopper_policy(policy_id)


def assess_configured_stopper(
    context: BiddingContext,
    registry: PolicyRegistry,
    suit: Suit,
) -> StopperAssessment | None:
    """Apply the configured stopper policy for one suit.

    ``None`` means there is no configured/resolvable stopper policy. An
    explicitly resolved policy can still return ``StopperStatus.UNKNOWN``.
    """
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    policy = resolve_stopper_policy(context.system, registry)
    if policy is None:
        return None
    return assess_stopper(policy, context, suit)


def configured_suit_quality_policy_id(system: SystemContext) -> str | None:
    """Return the configured suit-quality policy ID, if any."""
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    configured = system.option(SUIT_QUALITY_POLICY_OPTION)
    if configured is None:
        return None

    value = str(configured).strip()
    return value or None


def resolve_suit_quality_policy(
    system: SystemContext,
    registry: PolicyRegistry,
) -> SuitQualityPolicy | None:
    """Resolve the suit-quality policy selected by ``SystemContext``."""
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")

    policy_id = configured_suit_quality_policy_id(system)
    if policy_id is None:
        return None
    return registry.suit_quality_policy(policy_id)


def assess_configured_suit_quality(
    context: BiddingContext,
    registry: PolicyRegistry,
    suit: Suit,
) -> SuitQualityAssessment | None:
    """Apply the configured suit-quality policy for one suit.

    ``None`` means no configured/resolvable policy. A resolved policy may still
    return ``SuitQualityStatus.UNKNOWN``.
    """
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    if not isinstance(suit, Suit):
        raise TypeError("suit must be Suit")

    policy = resolve_suit_quality_policy(context.system, registry)
    if policy is None:
        return None
    return assess_suit_quality(policy, context, suit)


def configured_playing_strength_policy_id(system: SystemContext) -> str | None:
    """Return the configured playing-strength policy ID, if any."""
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")

    configured = system.option(PLAYING_STRENGTH_POLICY_OPTION)
    if configured is None:
        return None

    value = str(configured).strip()
    return value or None


def resolve_playing_strength_policy(
    system: SystemContext,
    registry: PolicyRegistry,
) -> PlayingStrengthPolicy | None:
    """Resolve the playing-strength policy selected by ``SystemContext``."""
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")

    policy_id = configured_playing_strength_policy_id(system)
    if policy_id is None:
        return None
    return registry.playing_strength_policy(policy_id)


def assess_configured_playing_strength(
    context: BiddingContext,
    registry: PolicyRegistry,
) -> PlayingStrengthAssessment | None:
    """Apply the configured playing-strength policy.

    ``None`` means no configured/resolvable policy. A resolved policy may still
    return ``PlayingStrengthStatus.UNKNOWN``.
    """
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")

    policy = resolve_playing_strength_policy(context.system, registry)
    if policy is None:
        return None
    return assess_playing_strength(policy, context)


def configured_offensive_hand_policy_id(system: SystemContext) -> str | None:
    if not isinstance(system,SystemContext): raise TypeError("system must be SystemContext")
    configured=system.option(OFFENSIVE_HAND_POLICY_OPTION)
    if configured is None: return None
    value=str(configured).strip()
    return value or None

def resolve_offensive_hand_policy(system:SystemContext,registry:PolicyRegistry)->OffensiveHandPolicy|None:
    if not isinstance(registry,PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    pid=configured_offensive_hand_policy_id(system)
    return None if pid is None else registry.offensive_hand_policy(pid)

def assess_configured_offensive_hand(context:BiddingContext,registry:PolicyRegistry)->OffensiveHandAssessment|None:
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    if not isinstance(registry,PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    policy=resolve_offensive_hand_policy(context.system,registry)
    return None if policy is None else assess_offensive_hand(policy,context)

def configured_opponent_suit_shortness_policy_id(system: SystemContext) -> str | None:
    if not isinstance(system,SystemContext): raise TypeError("system must be SystemContext")
    value=system.option(OPPONENT_SUIT_SHORTNESS_POLICY_OPTION)
    if value is None:return None
    value=str(value).strip()
    return value or None

def resolve_opponent_suit_shortness_policy(system:SystemContext,registry:PolicyRegistry):
    pid=configured_opponent_suit_shortness_policy_id(system)
    return None if pid is None else registry.opponent_suit_shortness_policy(pid)

def assess_configured_opponent_suit_shortness(context,registry,opponent_suit,suit_length):
    policy=resolve_opponent_suit_shortness_policy(context.system,registry)
    return None if policy is None else assess_opponent_suit_shortness(policy,context,opponent_suit,suit_length)

def configured_takeout_advancer_strength_policy_id(system:SystemContext) -> str | None:
    if not isinstance(system,SystemContext): raise TypeError("system must be SystemContext")
    value=system.option(TAKEOUT_ADVANCER_STRENGTH_POLICY_OPTION)
    if value is None:return None
    value=str(value).strip()
    return value or None

def resolve_takeout_advancer_strength_policy(system:SystemContext,registry:PolicyRegistry):
    pid=configured_takeout_advancer_strength_policy_id(system)
    return None if pid is None else registry.takeout_advancer_strength_policy(pid)

def assess_configured_takeout_advancer_strength(context,registry):
    policy=resolve_takeout_advancer_strength_policy(context.system,registry)
    return None if policy is None else assess_takeout_advancer_strength(policy,context)

def configured_support_double_eligibility_policy_id(system:SystemContext) -> str | None:
    if not isinstance(system,SystemContext): raise TypeError("system must be SystemContext")
    value=system.option(SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION)
    if value is None:return None
    value=str(value).strip()
    return value or None

def resolve_support_double_eligibility_policy(system:SystemContext,registry:PolicyRegistry):
    if not isinstance(registry,PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    pid=configured_support_double_eligibility_policy_id(system)
    return None if pid is None else registry.support_double_eligibility_policy(pid)

def assess_configured_support_double_eligibility(context,registry):
    if not isinstance(context,BiddingContext): raise TypeError("context must be BiddingContext")
    if not isinstance(registry,PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    policy=resolve_support_double_eligibility_policy(context.system,registry)
    return None if policy is None else assess_support_double_eligibility(policy,context)

def configured_jacoby_continuation_strength_policy_id(system: SystemContext) -> str | None:
    if not isinstance(system, SystemContext): raise TypeError("system must be SystemContext")
    value = system.option(JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION)
    if value is None: return None
    value = str(value).strip()
    return value or None

def resolve_jacoby_continuation_strength_policy(system: SystemContext, registry: PolicyRegistry):
    if not isinstance(registry, PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    pid = configured_jacoby_continuation_strength_policy_id(system)
    return None if pid is None else registry.jacoby_continuation_strength_policy(pid)

def assess_configured_jacoby_continuation_strength(context: BiddingContext, registry: PolicyRegistry) -> JacobyContinuationStrengthAssessment | None:
    if not isinstance(context, BiddingContext): raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry): raise TypeError("registry must be PolicyRegistry")
    policy = resolve_jacoby_continuation_strength_policy(context.system, registry)
    return None if policy is None else assess_jacoby_continuation_strength(policy, context)

def configured_stayman_continuation_strength_policy_id(system: SystemContext) -> str | None:
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")
    value = system.option(STAYMAN_CONTINUATION_STRENGTH_POLICY_OPTION)
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def resolve_stayman_continuation_strength_policy(
    system: SystemContext, registry: PolicyRegistry
) -> StaymanContinuationStrengthPolicy | None:
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    policy_id = configured_stayman_continuation_strength_policy_id(system)
    return None if policy_id is None else registry.stayman_continuation_strength_policy(policy_id)

def assess_configured_stayman_continuation_strength(
    context: BiddingContext, registry: PolicyRegistry
) -> StaymanContinuationStrengthAssessment | None:
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    policy = resolve_stayman_continuation_strength_policy(context.system, registry)
    return None if policy is None else assess_stayman_continuation_strength(policy, context)

def configured_stayman_dual_major_response_policy_id(system: SystemContext) -> str | None:
    if not isinstance(system, SystemContext):
        raise TypeError("system must be SystemContext")
    value = system.option(STAYMAN_DUAL_MAJOR_RESPONSE_POLICY_OPTION)
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def resolve_stayman_dual_major_response_policy(
    system: SystemContext, registry: PolicyRegistry
) -> StaymanDualMajorResponsePolicy | None:
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    policy_id = configured_stayman_dual_major_response_policy_id(system)
    return None if policy_id is None else registry.stayman_dual_major_response_policy(policy_id)

def assess_configured_stayman_dual_major_response(
    context: BiddingContext, registry: PolicyRegistry
) -> StaymanDualMajorResponseAssessment | None:
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    policy = resolve_stayman_dual_major_response_policy(context.system, registry)
    return None if policy is None else assess_stayman_dual_major_response(policy, context)

def _normalize_quality_policies(
    policies: Iterable[SuitQualityPolicy],
) -> tuple[tuple[str, SuitQualityPolicy], ...]:
    items: list[tuple[str, SuitQualityPolicy]] = []
    seen: set[str] = set()

    for policy in policies:
        try:
            raw_id = policy.policy_id
        except AttributeError as exc:
            raise TypeError("suit-quality policy must expose policy_id") from exc

        if not isinstance(raw_id, str):
            raise TypeError("suit-quality policy policy_id must be a string")

        policy_id = raw_id.strip()
        if not policy_id:
            raise ValueError("suit-quality policy policy_id must not be blank")

        folded = policy_id.casefold()
        if folded in seen:
            raise ValueError(f"duplicate suit-quality policy_id: {policy_id}")

        seen.add(folded)
        items.append((policy_id, policy))

    items.sort(key=lambda item: item[0].casefold())
    return tuple(items)


def _normalize_playing_strength_policies(
    policies: Iterable[PlayingStrengthPolicy],
) -> tuple[tuple[str, PlayingStrengthPolicy], ...]:
    items: list[tuple[str, PlayingStrengthPolicy]] = []
    seen: set[str] = set()

    for policy in policies:
        try:
            raw_id = policy.policy_id
        except AttributeError as exc:
            raise TypeError("playing-strength policy must expose policy_id") from exc

        if not isinstance(raw_id, str):
            raise TypeError("playing-strength policy policy_id must be a string")

        policy_id = raw_id.strip()
        if not policy_id:
            raise ValueError("playing-strength policy policy_id must not be blank")

        folded = policy_id.casefold()
        if folded in seen:
            raise ValueError(f"duplicate playing-strength policy_id: {policy_id}")

        seen.add(folded)
        items.append((policy_id, policy))

    items.sort(key=lambda item: item[0].casefold())
    return tuple(items)


def _normalize_offensive_hand_policies(policies: Iterable[OffensiveHandPolicy]) -> tuple[tuple[str, OffensiveHandPolicy], ...]:
    items=[]; seen=set()
    for policy in policies:
        raw=getattr(policy,"policy_id",None)
        if not isinstance(raw,str): raise TypeError("offensive-hand policy policy_id must be a string")
        pid=raw.strip()
        if not pid: raise ValueError("offensive-hand policy policy_id must not be blank")
        folded=pid.casefold()
        if folded in seen: raise ValueError(f"duplicate offensive-hand policy_id: {pid}")
        seen.add(folded); items.append((pid,policy))
    items.sort(key=lambda item:item[0].casefold())
    return tuple(items)


def _normalize_opponent_shortness_policies(policies):
    items=[];seen=set()
    for policy in policies:
        raw=getattr(policy,"policy_id",None)
        if not isinstance(raw,str): raise TypeError("shortness policy policy_id must be a string")
        pid=raw.strip()
        if not pid: raise ValueError("shortness policy policy_id must not be blank")
        folded=pid.casefold()
        if folded in seen: raise ValueError(f"duplicate shortness policy_id: {pid}")
        seen.add(folded);items.append((pid,policy))
    items.sort(key=lambda x:x[0].casefold())
    return tuple(items)


def _normalize_takeout_advancer_strength_policies(policies):
    items=[];seen=set()
    for policy in policies:
        raw=getattr(policy,"policy_id",None)
        if not isinstance(raw,str): raise TypeError("advancer strength policy policy_id must be a string")
        pid=raw.strip()
        if not pid: raise ValueError("advancer strength policy policy_id must not be blank")
        folded=pid.casefold()
        if folded in seen: raise ValueError(f"duplicate advancer strength policy_id: {pid}")
        seen.add(folded);items.append((pid,policy))
    items.sort(key=lambda x:x[0].casefold())
    return tuple(items)


def _normalize_support_double_eligibility_policies(policies):
    items=[];seen=set()
    for policy in policies:
        raw=getattr(policy,"policy_id",None)
        if not isinstance(raw,str): raise TypeError("support-double eligibility policy policy_id must be a string")
        pid=raw.strip()
        if not pid: raise ValueError("support-double eligibility policy policy_id must not be blank")
        folded=pid.casefold()
        if folded in seen: raise ValueError(f"duplicate support-double eligibility policy_id: {pid}")
        seen.add(folded);items.append((pid,policy))
    items.sort(key=lambda x:x[0].casefold())
    return tuple(items)


def _normalize_jacoby_continuation_strength_policies(policies):
    items=[]; seen=set()
    for policy in policies:
        raw=getattr(policy,"policy_id",None)
        if not isinstance(raw,str): raise TypeError("Jacoby continuation strength policy policy_id must be a string")
        pid=raw.strip()
        if not pid: raise ValueError("Jacoby continuation strength policy policy_id must not be blank")
        folded=pid.casefold()
        if folded in seen: raise ValueError(f"duplicate Jacoby continuation strength policy_id: {pid}")
        seen.add(folded); items.append((pid,policy))
    items.sort(key=lambda x:x[0].casefold())
    return tuple(items)


def _normalize_stayman_continuation_strength_policies(policies):
    items = []
    seen = set()
    for policy in policies:
        raw = getattr(policy, "policy_id", None)
        if not isinstance(raw, str):
            raise TypeError("Stayman continuation strength policy policy_id must be a string")
        policy_id = raw.strip()
        if not policy_id:
            raise ValueError("Stayman continuation strength policy policy_id must not be blank")
        folded = policy_id.casefold()
        if folded in seen:
            raise ValueError(f"duplicate Stayman continuation strength policy_id: {policy_id}")
        seen.add(folded)
        items.append((policy_id, policy))
    items.sort(key=lambda item: item[0].casefold())
    return tuple(items)


def _normalize_stayman_dual_major_response_policies(policies):
    items = []
    seen = set()
    for policy in policies:
        raw = getattr(policy, "policy_id", None)
        if not isinstance(raw, str):
            raise TypeError("Stayman dual-major response policy policy_id must be a string")
        policy_id = raw.strip()
        if not policy_id:
            raise ValueError("Stayman dual-major response policy policy_id must not be blank")
        folded = policy_id.casefold()
        if folded in seen:
            raise ValueError(f"duplicate Stayman dual-major response policy_id: {policy_id}")
        seen.add(folded)
        items.append((policy_id, policy))
    items.sort(key=lambda item: item[0].casefold())
    return tuple(items)
