"""Deterministic Phase 13I opening-lead policy architecture benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bridge import (
    KnowledgeSource, OpeningLeadHonorStyle, OpeningLeadLengthMethod,
    OpeningLeadPolicy, OpeningLeadTopOfNothing, PolicyRegistry,
    assess_opening_lead_policy,
)

FOURTH = KnowledgeSource("play/defence/opening-leads/fourth-best", "Basic Principle")
THIRD_FIFTH = KnowledgeSource("play/defence/opening-leads/third-fifth", "Basic Principle")
STANDARD = KnowledgeSource("play/defence/opening-leads/standard-leads", "Sequence Leads")
RUSINOW = KnowledgeSource("play/defence/opening-leads/rusinow", "Basic Principle")
TOP_NOTHING = KnowledgeSource("play/defence/opening-leads/top-of-nothing", "Definition")


@dataclass(frozen=True, slots=True)
class OpeningLeadPolicyBenchmark:
    policy_fixtures: int
    explicit_policies: int
    unknown_policies: int
    source_backed_policy_dimensions: int
    unsupported_dimensions: tuple[str, ...]
    invalid_policies: int
    recommendations_generated: int
    fixture_results: tuple[dict[str, object], ...]
    architecture: dict[str, int]
    source_inventory: tuple[dict[str, object], ...]
    phase13j_direction: str


def _policy(policy_id: str, **changes: object) -> OpeningLeadPolicy:
    return OpeningLeadPolicy(policy_id, **changes)


def run_opening_lead_policy_architecture_benchmark() -> OpeningLeadPolicyBenchmark:
    fixtures: tuple[tuple[str, OpeningLeadPolicy | None], ...] = (
        ("no-policy", None),
        ("fourth-best", _policy("fourth", length_method=OpeningLeadLengthMethod.FOURTH_BEST, sources=(FOURTH,))),
        ("third-fifth", _policy("third-fifth", length_method=OpeningLeadLengthMethod.THIRD_AND_FIFTH, sources=(THIRD_FIFTH,))),
        ("standard-honors", _policy("standard", honor_style=OpeningLeadHonorStyle.STANDARD, sources=(STANDARD,))),
        ("rusinow", _policy("rusinow", honor_style=OpeningLeadHonorStyle.RUSINOW, sources=(RUSINOW,))),
        ("top-enabled", _policy("top-enabled", top_of_nothing=OpeningLeadTopOfNothing.ENABLED, sources=(TOP_NOTHING,))),
        ("top-disabled", _policy("top-disabled", top_of_nothing=OpeningLeadTopOfNothing.DISABLED, sources=(TOP_NOTHING,))),
        ("all-unknown", _policy("unknown")),
        ("deterministic-repeat", _policy("fourth-repeat", length_method=OpeningLeadLengthMethod.FOURTH_BEST, sources=(FOURTH,))),
        ("source-preservation", _policy("evidence", honor_style=OpeningLeadHonorStyle.RUSINOW, sources=(RUSINOW,))),
    )
    results = []
    explicit = unknown = 0
    for name, policy in fixtures:
        assessed = assess_opening_lead_policy(policy)
        explicit += int(assessed.is_resolved)
        unknown += int(not assessed.is_resolved)
        results.append({
            "name": name, "policy_id": assessed.policy_id,
            "length_method": assessed.length_method.value,
            "honor_style": assessed.honor_style.value,
            "top_of_nothing": assessed.top_of_nothing.value,
            "resolved": assessed.is_resolved,
            "sources": [source.serialize() for source in assessed.sources],
            "recommendation": None,
        })
    policies = tuple(policy for _, policy in fixtures if policy is not None)
    registry = PolicyRegistry.from_opening_lead_policies(policies)
    assert len(registry.opening_lead_policy_ids) == 9
    inventory = (
        {"path": "knowledge/play/defence/opening-leads/fourth-best.md", "heading": "Basic Principle", "classification": "POLICY_EXECUTABLE", "contract_distinction": True, "exceptions": True},
        {"path": "knowledge/play/defence/opening-leads/third-fifth.md", "heading": "Basic Principle", "classification": "POLICY_EXECUTABLE", "contract_distinction": True, "exceptions": True},
        {"path": "knowledge/play/defence/opening-leads/standard-leads.md", "heading": "Sequence Leads", "classification": "POLICY_EXECUTABLE", "contract_distinction": True, "exceptions": True},
        {"path": "knowledge/play/defence/opening-leads/rusinow.md", "heading": "Basic Principle", "classification": "POLICY_EXECUTABLE", "contract_distinction": True, "exceptions": True},
        {"path": "knowledge/play/defence/opening-leads/top-of-nothing.md", "heading": "Definition", "classification": "POLICY_EXECUTABLE", "contract_distinction": True, "exceptions": True},
    )
    return OpeningLeadPolicyBenchmark(
        10, explicit, unknown, 3,
        ("mud", "coded-tens-nines", "journalist-leads", "attitude-leads", "unsupported-ace-king"),
        0, 0, tuple(results),
        {"total_positions_or_requests": 80, "auction_positions": 5, "opening_lead_positions": 14,
         "opening_lead_policy_requests": 10, "explicit_opening_lead_policies": explicit,
         "unresolved_policies": unknown, "declarer_positions": 23, "defensive_positions": 15,
         "bidding_recommendations": 2, "declarer_recommendations": 2,
         "opening_lead_recommendations": 0, "defensive_recommendations": 0,
         "probability_evidence_items": 3, "abstentions": 3, "no_decisions": 51, "errors": 0},
        inventory, "B. OPENING-LEAD SOURCE-READINESS AUDIT",
    )


def write_artifacts(benchmark: OpeningLeadPolicyBenchmark, output: Path) -> None:
    payload = asdict(benchmark)
    (output / "bridgelab_phase13i_opening_lead_policy_architecture.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# BridgeLab Phase 13I — Opening-Lead Policy Architecture", "",
        "## Outcome", "",
        "Policy architecture only: no card selection and no production recommendation.", "",
        "## Benchmark", "",
        f"- Fixtures: {benchmark.policy_fixtures}",
        f"- Explicit / unresolved: {benchmark.explicit_policies} / {benchmark.unknown_policies}",
        f"- Source-backed dimensions: {benchmark.source_backed_policy_dimensions}",
        "- Recommendations generated: 0", "",
        "## Policy dimensions", "",
        "- Length: FOURTH_BEST / THIRD_AND_FIFTH / OTHER / UNKNOWN",
        "- Honor: STANDARD / RUSINOW / UNKNOWN",
        "- Top of Nothing: ENABLED / DISABLED / UNKNOWN", "",
        "Missing policy remains unresolved; it never implies Standard. Policy and OpeningLeadState remain separate.", "",
        "## Source inventory", "",
    ]
    for source in benchmark.source_inventory:
        lines.append(f"- `{source['path']}` — {source['heading']} — {source['classification']}")
    lines += ["", "Unsupported axes: " + ", ".join(benchmark.unsupported_dimensions) + ".", "",
              "## Cumulative Phase 13", "", "```json", json.dumps(benchmark.architecture, indent=2, sort_keys=True), "```", "",
              "## Phase 13J", "", benchmark.phase13j_direction, ""]
    (output / "bridgelab_phase13i_opening_lead_policy_architecture.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_artifacts(run_opening_lead_policy_architecture_benchmark(), Path.cwd())
