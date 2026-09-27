"""Render the verified PT-1B JSON outputs as one reviewable Markdown report."""

import gzip
import json
from pathlib import Path
from statistics import mean, median, stdev
from math import sqrt


ROOT = Path(r"C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit")
OUT = ROOT / "output" / "pt1b_shortness_validation"
s = json.loads((OUT / "pt1b_summary.json").read_text(encoding="utf-8"))
a = json.loads((OUT / "pt1b_integrity_audit.json").read_text(encoding="utf-8"))
lines = []


def add(*items):
    lines.extend(items)


def f(value):
    return "—" if value is None else f"{value:.3f}"


def stat_row(label, item):
    ci = item["mean_95_percent_normal_ci"]
    interval = "—" if ci is None else f"[{f(ci[0])}, {f(ci[1])}]"
    return (f"| {label} | {item['n']} | {f(item['mean_delta'])} | "
            f"{f(item['median_delta'])} | {f(item['sample_sd'])} | {interval} | "
            f"{f(item['p_positive'])} | {f(item['p_zero'])} | {f(item['p_negative'])} | "
            f"{f(item['p_ge_1'])} | {f(item['p_le_minus_1'])} |")


def table(title, rows):
    add(f"### {title}", "",
        "| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|")
    add(*(stat_row(label, item) for label, item in rows))
    add("")


add("# BridgeLab PT-1B — matched shortness effect validation", "",
    "## A. Repository state and interrupted-run recovery", "",
    "Branch `codex/phase18b`; HEAD `a3007ee510c2bf8aceea4dd72895a95b3fa12994`. "
    "No tracked files changed; PT-1/PT-1A and PT-1B artifacts remain untracked. "
    "No commit or push was made. `git diff --check` is clean.", "",
    "The interrupted run had already completed its main study. The gzip CRC and every JSON row "
    "were verified: 14,000 unique source IDs, 11 × 1,000 ordinary matched pairs, and "
    "6 × 500 reciprocal comparisons. All 2,500 feasible four-corner records retained "
    "both steps on both paths. No main cohort was rerun. The original sensitivity "
    "aggregates lacked individual exchange outcomes. Only that 220-source subset was replayed "
    "to write complete per-exchange DDS provenance; its recomputed statistics matched "
    "all saved source summaries exactly.", "",
    "## B. Transformation and preservation contract", "",
    "For a singleton in hand H and side suit X, one rank-2–10 card of X moves from partner "
    "to H while a rank-2–10 card of another nontrump suit moves from H to partner. "
    "Two successive swaps make a three-card control when possible. Candidate paths are "
    "enumerated in stable suit/rank order, then selected by a seeded uniform index. "
    "The audit verifies every move forward and backward to the identical deal.", "",
    "Exactly preserved: all 52 unique cards, both defender hands, HCP and every J-or-higher "
    "honor by partnership hand, all trump cards and their allocation, side aces/entry indicators, "
    "declarer North, spade strain, and actual defender trump split. Necessarily changed: "
    "studied-suit and compensation-suit lengths and spot-card locations. The source's "
    "opposite studied-suit length, natural top winners, and ruffable-loser proxy are recorded "
    "for stratification; they are not claimed constant after the exchange. Other source "
    "shortness, if present, remains unchanged within a pair and is reported separately.", "",
    "Reciprocal cases use a commuting four-corner design: reciprocal R, North singleton removed N, "
    "South singleton removed S, and neither 0. Standalone `effect_N = DD(S) − DD(0)` and "
    "`effect_S = DD(N) − DD(0)`; `reciprocal_effect = DD(R) − DD(0)`; "
    "`interaction = DD(R) − DD(N) − DD(S) + DD(0)`. The two conditional removal contrasts "
    "`DD(R) − DD(N)` and `DD(R) − DD(S)` are also reported. All DDS results are reference "
    "measurements, never NPT or APT coefficients.", "",
    "## C. Acceptance and structural limits", "",
    "| Family | Generated | Accepted | Rejected for legal exchange | Solver rejection |",
    "|---|---:|---:|---:|---:|")

ordinary = [v["counts"] for v in s["cohorts"].values() if "singleton_vs_doubleton" in v]
recip = [v["counts"] for v in s["cohorts"].values() if "comparisons" in v]
add(f"| Ordinary singleton (11 cohorts) | {sum(v['generated'] for v in ordinary)} | "
    f"{sum(v['accepted'] for v in ordinary)} | "
    f"{sum(v.get('no_valid_doubleton_exchange', 0) for v in ordinary)} | 0 |",
    f"| Reciprocal (five squares + 7–3 direct) | {sum(v['generated'] for v in recip)} | "
    f"{sum(v['accepted'] for v in recip)} | "
    f"{sum(v.get('no_valid_four_corner_exchange', 0) + v.get('no_valid_direct_exchange', 0) for v in recip)} | 0 |",
    "",
    f"Among 11,000 accepted ordinary sources, {sum(v.get('three_card_complete', 0) for v in ordinary)} "
    "also supported exact three-card controls; the remainder were explicitly unavailable. "
    "No impossible transformation was forced.", "",
    "For 7–3 reciprocal deals, the long-trump hand has only six side cards and cannot "
    "support a clean four-corner square without creating another singleton. Its 500 "
    "observations are direct reciprocal-to-neither controls only; interaction is unavailable. "
    "For 7–3 short-hand singleton controls, all 1,000 accepted sources have preserved "
    "additional shortness in the seven-trump hand. Their estimate is conditional on that "
    "context, not an isolated-singleton estimate.", "")

table("D. Singleton versus doubleton by structure and location",
      [(key.replace("_", " "), value["singleton_vs_doubleton"])
       for key, value in sorted(s["cohorts"].items()) if "singleton_vs_doubleton" in value])
table("E. Singleton versus three-card controls, where feasible",
      [(key.replace("_", " "), value["singleton_vs_three_card"])
       for key, value in sorted(s["cohorts"].items()) if "singleton_vs_three_card" in value])
table("F. Pooled location strata (descriptive across structures)",
      sorted(s["by_location"].items()))
add("Short-hand and long-hand source populations are distinct; the pooled location difference "
    "is descriptive, not a within-deal causal contrast. The per-structure rows above are the "
    "primary location evidence.", "")
table("G. Studied-suit ruffable-loser groups", sorted(s["by_ruffable_loser_bucket"].items()))
table("H1. Opposite studied-suit length", sorted(s["by_opposite_length"].items(), key=lambda x: int(x[0])))
table("H2. Natural top winners in the studied suit", sorted(s["by_natural_winners"].items(), key=lambda x: int(x[0])))
table("I1. Predefined Trump Honor Control category", sorted(s["by_trump_quality"].items()))
table("I2. Actual defender trump split", sorted(s["by_defender_trump_split"].items()))
add("Trump Honor Control was fixed before looking at outcomes: A=2, K=1, Q=1, J=0; "
    "weak 0–1, medium 2–3, strong 4. These are observed defender splits, not "
    "unconditional break probabilities. `pt1b_summary.json` additionally gives every "
    "split, quality, length, winner, and loser stratum within each cohort and reciprocal "
    "comparison.", "")
table("J. Other side shortness in ordinary source deals",
      sorted(s["within_cohort_strata"]["source_context"].items()))

sens = s["exchange_sensitivity"]
selected = {}
with gzip.open(OUT / s["case_file"], "rt", encoding="utf-8") as stream:
    for line in stream:
        row = json.loads(line)
        if isinstance(row.get("delta_doubleton"), int):
            selected[(row["cohort"], row["case"]["deal_seed"])] = row["delta_doubleton"]
selection_error = [selected[(x["cohort"], x["source_seed"])] - x["mean_delta"]
                   for x in sens["records"]]
selection_mean = mean(selection_error)
selection_sd = stdev(selection_error)
selection_half = 1.96 * selection_sd / sqrt(len(selection_error))
add("## K. Exchange sensitivity", "",
    f"All legal one-step low-card exchanges were solved for {sens['sources']} deterministic sources "
    f"({s['sensitivity_replay_solver_calls']} candidate records; candidate count 2–40). "
    f"{sens['all_exchange_solver_complete_sources']} sources had every candidate solved. "
    f"The mean within-source range was {f(sens['mean_within_source_range'])} tricks and "
    f"the mean within-source SD was {f(sens['mean_within_source_sd'])}. "
    f"A different legal exchange changed Δ for {f(sens['p_sources_with_exchange_sensitive_delta'])} "
    "of sources: 144 ranges were 0, 71 were 1, and 5 were 2 tricks. "
    f"The seeded selected-exchange Δ minus the all-exchange mean averaged {f(selection_mean)} "
    f"tricks (approximate 95% CI [{f(selection_mean-selection_half)}, "
    f"{f(selection_mean+selection_half)}]); no systematic selection shift is evident in this subset, "
    "but individual spot-card choice sometimes matters.", "")

recip_rows = []
for cohort, value in sorted(s["cohorts"].items()):
    if "comparisons" not in value:
        continue
    for name, stats in value["comparisons"].items():
        recip_rows.append((f"{cohort}: {name}", stats))
table("L. Reciprocal singleton effects and interaction", recip_rows)
add("The 7–3 direct row has no effect_N, effect_S, or interaction. Across the five "
    "feasible four-corner structures, interaction means are all negative; this does "
    "not justify a positive crossruff bonus or a final Playing-Trick coefficient.", "")

add("## M. Tests, runtime, and production safety", "",
    "- PT-1 under project Python 3.14: **14 passed**.",
    "- PT-1A under solver Python 3.12: **17 passed**.",
    "- PT-1B under solver Python 3.12: **16 passed**.",
    "- Relevant hand evaluation, structured hand, probability, Strong-2C, and Playing-Trick dependency tests under Python 3.14: **105 passed**.",
    "- Historical suite under Python 3.14: **2,672 passed, 9 solver-dependent skipped, 143 subtests passed** in 1,201.44 s. Later changes were confined to PT-1B reporting and output audit; their focused tests and complete output audit passed.",
    "- The three pre-existing `VacantPlacesQuestion` dataclass `super()` tests fail only under Python 3.12; they pass in the project Python 3.14 environment. Production code was not changed to address an environment-only issue.",
    f"- Main DDS run: **{s['solver_calls']:,} calls**, all successful, "
    f"{s['validation_wall_seconds']:.2f} s wall time. Sensitivity provenance recovery: "
    f"**{s['sensitivity_replay_solver_calls']:,} calls**, all successful, "
    f"{s['sensitivity_replay_wall_seconds']:.2f} s. Total executed calls: "
    f"**{s['total_solver_calls_including_replay']:,}**. Solver: endplay/DDS "
    f"{', '.join(s['solver_versions'])}.",
    f"- Full output audit: **{a['main']['main_source_rows']:,}** main sources, "
    f"**{a['main']['verified_card_moves']:,}** main forward/reverse card moves, "
    f"and **{a['sensitivity']['sensitivity_records']:,}** sensitivity exchanges verified; "
    "gzip/JSON integrity passed.",
    "- `production_changed = False`; production routes **45 before / 45 after**. "
    "No tracked diff, bidding rule, or route changed. No commit or push.", "",
    "## N. Recommendation", "",
    "**Another methodological revision required.** The matched DDS data show a measurable "
    "studied-singleton contribution and consistent negative reciprocal interaction, but "
    "the necessary compensation-suit shape change, spot-exchange sensitivity in 34.5% "
    "of tested sources, and 7–3's unavoidable additional-shortness context limit a single "
    "transportable coefficient. The next revision should predefine how compensation-suit "
    "effects and source-context interactions enter calibration. PT-2 and final Playing-Trick "
    "coefficients remain deferred.", "",
    "## Files", "",
    "- `pt1b_summary.json`: full comparison statistics and within-cohort strata.",
    "- `pt1b_cases.jsonl.gz`: all main source/control deals, selected exchanges, and DDS provenance.",
    "- `pt1b_exchange_sensitivity.jsonl.gz`: every sensitivity exchange, delta, and DDS result.",
    "- `pt1b_integrity_audit.json`: case-file integrity and reverse-replay counts.", "")

(OUT / "pt1b_report.md").write_text("\n".join(lines), encoding="utf-8")
print(OUT / "pt1b_report.md")
