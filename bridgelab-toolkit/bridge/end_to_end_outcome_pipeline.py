"""End-to-end outcome pipeline composition.

A6.14 — End-to-End Outcome Pipeline.

This module composes the already established simulation-provider, alternative
evaluation, descriptive reporting, and optional IMP/matchpoint measurement
layers. It preserves caller order and does not rank alternatives, choose a
winner, recommend a contract, or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .contract_alternative_evaluation import (
    ContractAlternative,
    ContractAlternativeEvaluationPipelineResult,
    evaluate_contract_alternatives,
)
from .corpus import Vulnerability
from .deals import Deal
from .outcome_comparison_report import (
    OutcomeComparisonReport,
    build_outcome_comparison_report,
)
from .outcome_conversion import (
    IMPOutcomeMeasurement,
    MatchpointOutcomeMeasurement,
    measure_imps,
    measure_matchpoints,
)
from .simulation_provider import (
    LiveSimulationProvider,
    SimulationSampleRequest,
    SimulationSampleResult,
    SimulationSampleStatus,
)


@dataclass(frozen=True, slots=True)
class AlternativeCompetitionMeasurement:
    alternative_id: str
    imps: IMPOutcomeMeasurement | None = None
    matchpoints: MatchpointOutcomeMeasurement | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.alternative_id, str) or not self.alternative_id.strip():
            raise ValueError("alternative_id must be a non-blank string")
        object.__setattr__(self, "alternative_id", self.alternative_id.strip())
        if self.imps is not None and not isinstance(self.imps, IMPOutcomeMeasurement):
            raise TypeError("imps must be IMPOutcomeMeasurement or None")
        if self.matchpoints is not None and not isinstance(
            self.matchpoints, MatchpointOutcomeMeasurement
        ):
            raise TypeError(
                "matchpoints must be MatchpointOutcomeMeasurement or None"
            )


@dataclass(frozen=True, slots=True)
class EndToEndOutcomePipelineResult:
    simulation_results: tuple[tuple[str, SimulationSampleResult], ...]
    evaluation: ContractAlternativeEvaluationPipelineResult
    report: OutcomeComparisonReport
    competition_measurements: tuple[AlternativeCompetitionMeasurement, ...]

    def simulation_result(self, alternative_id: str) -> SimulationSampleResult:
        for item_id, result in self.simulation_results:
            if item_id == alternative_id:
                return result
        raise KeyError(alternative_id)

    def competition_measurement(
        self, alternative_id: str
    ) -> AlternativeCompetitionMeasurement:
        for item in self.competition_measurements:
            if item.alternative_id == alternative_id:
                return item
        raise KeyError(alternative_id)


def run_end_to_end_outcome_pipeline(
    *,
    deal: Deal,
    vulnerability: Vulnerability,
    alternatives: Iterable[ContractAlternative],
    simulation_provider: LiveSimulationProvider,
    sample_count: int,
    imp_reference_ns_scores: Mapping[str, int] | None = None,
    matchpoint_comparison_ns_scores: Mapping[str, Iterable[int]] | None = None,
) -> EndToEndOutcomePipelineResult:
    """Run simulation -> scoring -> comparison -> report -> optional conversion."""
    if not isinstance(deal, Deal):
        raise TypeError("deal must be Deal")
    if not isinstance(vulnerability, Vulnerability):
        raise TypeError("vulnerability must be Vulnerability")
    if not isinstance(simulation_provider, LiveSimulationProvider):
        raise TypeError("simulation_provider must be LiveSimulationProvider")
    if (
        not isinstance(sample_count, int)
        or isinstance(sample_count, bool)
        or sample_count < 1
    ):
        raise ValueError("sample_count must be a positive integer")

    try:
        items = tuple(alternatives)
    except TypeError as exc:
        raise TypeError("alternatives must be an iterable") from exc

    if len(items) < 2:
        raise ValueError("pipeline requires at least two alternatives")
    if not all(isinstance(item, ContractAlternative) for item in items):
        raise TypeError("all alternatives must be ContractAlternative")

    ids = tuple(item.alternative_id for item in items)
    if len(set(ids)) != len(ids):
        raise ValueError("alternative_id values must be unique")

    expected = set(ids)
    for name, mapping in (
        ("imp_reference_ns_scores", imp_reference_ns_scores),
        ("matchpoint_comparison_ns_scores", matchpoint_comparison_ns_scores),
    ):
        if mapping is not None:
            if not isinstance(mapping, Mapping):
                raise TypeError(f"{name} must be a mapping or None")
            extra = set(mapping) - expected
            if extra:
                raise ValueError(
                    f"unexpected alternative ids in {name}: "
                    + ", ".join(sorted(extra))
                )

    simulation_results = []
    trick_samples: dict[str, tuple[int, ...]] = {}

    for alternative in items:
        result = simulation_provider.sample(
            SimulationSampleRequest(
                deal=deal,
                contract=alternative.contract,
                sample_count=sample_count,
            )
        )
        simulation_results.append((alternative.alternative_id, result))

        if result.status is not SimulationSampleStatus.SUCCESS:
            detail = result.error or result.status.value
            raise RuntimeError(
                f"simulation failed for {alternative.alternative_id}: {detail}"
            )
        if result.contract != alternative.contract:
            raise ValueError(
                f"simulation contract mismatch for {alternative.alternative_id}"
            )
        trick_samples[alternative.alternative_id] = result.declarer_tricks

    evaluation = evaluate_contract_alternatives(
        deal=deal,
        vulnerability=vulnerability,
        alternatives=items,
        declarer_tricks=trick_samples,
    )
    report = build_outcome_comparison_report(evaluation)

    competition_measurements = []
    for item in evaluation.evaluations:
        alternative_id = item.alternative_id
        summary = item.summary

        imp_measurement = None
        if (
            imp_reference_ns_scores is not None
            and alternative_id in imp_reference_ns_scores
        ):
            mean_ns_score = summary.mean_ns_score
            if not float(mean_ns_score).is_integer():
                raise ValueError(
                    f"mean NS score for {alternative_id} is not an integer; "
                    "IMP conversion requires an integer duplicate score"
                )
            imp_measurement = measure_imps(
                ns_score=int(mean_ns_score),
                reference_ns_score=imp_reference_ns_scores[alternative_id],
            )

        matchpoint_measurement = None
        if (
            matchpoint_comparison_ns_scores is not None
            and alternative_id in matchpoint_comparison_ns_scores
        ):
            mean_ns_score = summary.mean_ns_score
            if not float(mean_ns_score).is_integer():
                raise ValueError(
                    f"mean NS score for {alternative_id} is not an integer; "
                    "matchpoint conversion requires an integer duplicate score"
                )
            matchpoint_measurement = measure_matchpoints(
                ns_score=int(mean_ns_score),
                comparison_ns_scores=matchpoint_comparison_ns_scores[
                    alternative_id
                ],
            )

        competition_measurements.append(
            AlternativeCompetitionMeasurement(
                alternative_id=alternative_id,
                imps=imp_measurement,
                matchpoints=matchpoint_measurement,
            )
        )

    return EndToEndOutcomePipelineResult(
        simulation_results=tuple(simulation_results),
        evaluation=evaluation,
        report=report,
        competition_measurements=tuple(competition_measurements),
    )
