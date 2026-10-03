"""A7.7 bidding-to-outcome connection tests."""

import pytest

from bridge.auction import Bid, Contract, Strain
from bridge.bidding_outcome_connection import (
    BiddingOutcomeCandidates,
    EvidenceContract,
    OutcomeCandidate,
    build_bidding_outcome_candidates,
)
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.contract_alternative_evaluation import ContractAlternative
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import DecisionEvidence, EvidenceScope
from bridge.isolated_bidding_evidence import IsolatedMultiAdviserBiddingResult
from bridge.models import Seat
from bridge.multi_adviser_disagreement import MultiAdviserDisagreementResult
from bridge.multi_bidding_adviser import (
    BiddingAdviserEvidence,
    MultiAdviserBiddingResult,
)


def _evidence(provider_id, recommendation=None, status=ProviderStatus.SUCCESS):
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )
    if status is ProviderStatus.SUCCESS:
        from bridge.auction import Call
        recommendation = Call.parse(recommendation or "3NT")
    else:
        recommendation = None
    return DecisionEvidence(
        result=CapabilityResult(
            provider=descriptor,
            status=status,
            recommendation=recommendation,
        ),
        scope=EvidenceScope.PROVIDER,
    )


def _analysis(externals=()):
    bridge = _evidence("bridgelab", "3NT")
    gathered = MultiAdviserBiddingResult(
        tuple(
            BiddingAdviserEvidence(x.result.provider.provider_id, x)
            for x in externals
        )
    )
    isolated = IsolatedMultiAdviserBiddingResult(gathered)
    case = DecisionCase(
        case_id="a77",
        bridgelab=bridge,
        external=tuple(externals),
        disagreements=(),
    )
    # A7.6 invariant: one context/disagreement slot per gathered adviser.
    # A7.7 does not inspect these values, but its fixture must still construct
    # a valid MultiAdviserDisagreementResult.
    from bridge.decision_evidence import DisagreementContext

    return MultiAdviserDisagreementResult(
        gathered=isolated,
        contexts=tuple(DisagreementContext() for _ in externals),
        disagreements=tuple(None for _ in externals),
        decision_case=case,
    )


def _contract(level, strain, declarer=Seat.NORTH):
    return Contract(Bid(level, strain), declarer)


def test_explicit_bridge_and_external_contracts_become_a6_alternatives():
    analysis = _analysis((_evidence("ben", "4S"),))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", _contract(3, Strain.NOTRUMP)),
            EvidenceContract("ben", _contract(4, Strain.SPADES)),
        ),
    )

    assert isinstance(result, BiddingOutcomeCandidates)
    assert tuple(x.alternative.alternative_id for x in result.candidates) == (
        "candidate-1",
        "candidate-2",
    )
    assert all(isinstance(x, ContractAlternative) for x in result.alternatives)
    assert result.candidates[0].provider_ids == ("bridgelab",)
    assert result.candidates[1].provider_ids == ("ben",)


def test_identical_contracts_are_deduplicated_for_measurement_only():
    analysis = _analysis((_evidence("ben", "4S"), _evidence("ai2", "4S")))
    same = _contract(4, Strain.SPADES)

    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("ben", same),
            EvidenceContract("ai2", same),
        ),
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].contract == same
    assert result.candidates[0].provider_ids == ("ben", "ai2")


def test_duplicate_contract_does_not_create_votes_or_weight():
    analysis = _analysis((_evidence("a", "4S"), _evidence("b", "4S")))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("a", _contract(4, Strain.SPADES)),
            EvidenceContract("b", _contract(4, Strain.SPADES)),
        ),
    )

    assert len(result.alternatives) == 1
    for name in ("winner", "votes", "weight", "ranking", "preferred", "selected"):
        assert not hasattr(result, name)


def test_provider_without_explicit_contract_is_omitted_not_fabricated():
    analysis = _analysis((_evidence("ben", "4S"),))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", _contract(3, Strain.NOTRUMP)),
        ),
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].provider_ids == ("bridgelab",)


def test_abstain_without_contract_does_not_create_candidate():
    analysis = _analysis((_evidence("ben", status=ProviderStatus.ABSTAIN),))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("bridgelab", _contract(3, Strain.NOTRUMP)),
        ),
    )
    assert tuple(x.provider_ids for x in result.candidates) == (("bridgelab",),)


def test_failed_provider_can_remain_evidence_without_outcome_candidate():
    analysis = _analysis((_evidence("broken", status=ProviderStatus.FAILED),))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(),
    )
    assert result.candidates == ()
    assert result.alternatives == ()


def test_evidence_order_controls_candidate_order_not_mapping_order():
    analysis = _analysis((_evidence("ben", "4S"), _evidence("ai2", "4H")))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("ai2", _contract(4, Strain.HEARTS)),
            EvidenceContract("ben", _contract(4, Strain.SPADES)),
            EvidenceContract("bridgelab", _contract(3, Strain.NOTRUMP)),
        ),
    )

    assert tuple(x.provider_ids for x in result.candidates) == (
        ("bridgelab",),
        ("ben",),
        ("ai2",),
    )


def test_same_contract_preserves_provider_order_from_evidence():
    analysis = _analysis((_evidence("first", "4S"), _evidence("second", "4S")))
    same = _contract(4, Strain.SPADES)
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(
            EvidenceContract("second", same),
            EvidenceContract("first", same),
        ),
    )
    assert result.candidates[0].provider_ids == ("first", "second")


def test_contract_mapping_provider_match_is_case_insensitive():
    analysis = _analysis((_evidence("BEN", "4S"),))
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(EvidenceContract("ben", _contract(4, Strain.SPADES)),),
    )
    assert result.candidates[0].provider_ids == ("BEN",)


def test_unknown_provider_contract_mapping_is_rejected():
    analysis = _analysis()
    with pytest.raises(ValueError, match="not present in evidence"):
        build_bidding_outcome_candidates(
            analysis=analysis,
            contracts=(EvidenceContract("ghost", _contract(3, Strain.NOTRUMP)),),
        )


def test_duplicate_provider_contract_mapping_is_rejected_case_insensitively():
    analysis = _analysis((_evidence("ben", "4S"),))
    with pytest.raises(ValueError, match="duplicate contract mapping"):
        build_bidding_outcome_candidates(
            analysis=analysis,
            contracts=(
                EvidenceContract("ben", _contract(4, Strain.SPADES)),
                EvidenceContract("BEN", _contract(4, Strain.SPADES)),
            ),
        )


def test_explicit_declarer_is_preserved():
    analysis = _analysis()
    contract = _contract(3, Strain.NOTRUMP, Seat.SOUTH)
    result = build_bidding_outcome_candidates(
        analysis=analysis,
        contracts=(EvidenceContract("bridgelab", contract),),
    )
    assert result.candidates[0].contract.declarer is Seat.SOUTH


def test_evidence_contract_requires_contract_object():
    with pytest.raises(TypeError, match="contract must be Contract"):
        EvidenceContract("ben", object())


def test_evidence_contract_requires_nonblank_provider_id():
    with pytest.raises(ValueError, match="non-blank"):
        EvidenceContract(" ", _contract(4, Strain.SPADES))


def test_builder_requires_analysis_type():
    with pytest.raises(TypeError, match="analysis must be"):
        build_bidding_outcome_candidates(analysis=object(), contracts=())


def test_builder_requires_contract_tuple():
    with pytest.raises(TypeError, match="contracts must be a tuple"):
        build_bidding_outcome_candidates(analysis=_analysis(), contracts=[])


def test_outcome_candidate_requires_nonempty_provenance():
    with pytest.raises(ValueError, match="non-empty tuple"):
        OutcomeCandidate(
            ContractAlternative("x", _contract(3, Strain.NOTRUMP)),
            (),
        )
