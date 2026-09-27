"""One-off report renderer; production consumes neither this script nor its results."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(r"C:\Users\nisim\Documents\BridgeLab-phase18b-worktree")
sys.path.insert(0, str(ROOT / "bridgelab-toolkit"))
from bridge.deal_simulator import AuctionOutcome, SimulationConfig, run_full_auction_simulation
from bridge.evaluation import evaluate_hand
from bridge.models import Hand
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy, assess_rule_of_20
from bridge.opening_abstention_root_cause_audit import build_opening_root_cause_report
from bridge.opening_pass_policy_audit import build_opening_pass_policy_report

policy = build_nisim_nily_opening_policy()
batch = run_full_auction_simulation(SimulationConfig(100, 1000))
old_k = build_opening_pass_policy_report(batch)
old_j = build_opening_root_cause_report(batch)
assert (old_k.depth0_abstains, old_k.diagnostic_screen_count) == (616, 542)
assert tuple(c.deal_index for c in old_j.strong_cases) == (57, 184, 613)
strong_ids = {c.deal_index for c in old_j.strong_cases}
categories = (
    "POLICY_SUPPORTED_POTENTIAL_PASS", "RULE20_POTENTIAL_OPENING",
    "KNOWN_OPENING_COVERAGE_BOUNDARY", "PROTECTED_UNRESOLVED", "SOURCE_OR_POLICY_INSUFFICIENT",
)

def summarize():
    groups = {key: {"count": 0, "hcp": Counter(), "shape": Counter(), "examples": []} for key in categories}
    rule20_in_k_screen = 0
    for auction in batch.auctions:
        if auction.outcome is not AuctionOutcome.ABSTAIN or not auction.steps:
            continue
        step = auction.steps[-1]
        if step.auction_before:
            continue
        hand = Hand.parse(step.hand)
        facts = evaluate_hand(hand)
        strength = assess_rule_of_20(hand)
        spades, hearts, diamonds, clubs = facts.suit_lengths
        if auction.deal_index in strong_ids:
            category = "KNOWN_OPENING_COVERAGE_BOUNDARY"
        elif facts.hcp == 11 and strength.qualifies:
            category = "RULE20_POTENTIAL_OPENING"
            if max(facts.suit_lengths) <= 5:
                rule20_in_k_screen += 1
        elif max(facts.suit_lengths) >= 6 or spades == hearts == 5 or diamonds == clubs == 5:
            category = "PROTECTED_UNRESOLVED"
        else:
            category = "SOURCE_OR_POLICY_INSUFFICIENT"
        group = groups[category]
        group["count"] += 1
        group["hcp"][str(facts.hcp)] += 1
        group["shape"]["-".join(map(str, sorted(facts.suit_lengths, reverse=True)))] += 1
        if len(group["examples"]) < 3:
            group["examples"].append({"deal_index": auction.deal_index, "dealer": auction.dealer.value,
                "vulnerability": auction.vulnerability.value, "hand": step.hand, "hcp": facts.hcp,
                "suit_lengths_SHDC": facts.suit_lengths, "rule20_score": strength.score})
    for group in groups.values():
        group["percentage_of_616"] = round(100 * group["count"] / 616, 4)
        group["hcp"] = dict(sorted(group["hcp"].items(), key=lambda p: int(p[0])))
        group["shape"] = dict(sorted(group["shape"].items()))
    assert sum(g["count"] for g in groups.values()) == 616
    return {"seed": 100, "deals": 1000, "depth0_abstains": 616, "phase29k_screen": 542,
            "rule20_11_hcp_inside_phase29k_screen": rule20_in_k_screen, "categories": groups}

audit = summarize()
assert audit == summarize()
print(json.dumps(audit, indent=2))

lines = ["# Phase 29M — nisim–nily partnership opening policy formalization", "",
    "**Policy only. PASS != FALLBACK_FOR_ABSTAIN. No production integration.**", "",
    "## A. Baseline verification", "",
    f"- Project: `{ROOT / 'bridgelab-toolkit'}`", f"- Git root: `{ROOT}`",
    "- Branch: `codex/phase18b`.",
    "- Local, live remote and remote-tracking HEAD: `9f6b89d470b9027c28ab9dc9662a377c45f433f9`.",
    "- Ahead/behind: `0/0`; initial status: clean. Known cache permission warnings only.",
    "- User-supplied full-regression baseline: 2131 passed, 143 subtests passed; not rerun.", "",
    "## B. Files inspected", "",
    "User approval: PHASE 29M specification, sections D-L. This report and the module preserve its substantive approved propositions; authority is the explicit user approval, not an inference from repository notes.", "",
    "Approval attachment SHA-256: `" + hashlib.sha256(Path(r"C:\Users\nisim\.codex\attachments\c169bc3b-c7c1-4113-bca3-4137ae7e3a44\pasted-text.txt").read_bytes()).hexdigest() + "`.", "",
    "Inspected current `bridge/evaluation.py`, `bridge/sayc.py`, `bridge/opening_pass_policy_audit.py`, `bridge/opening_abstention_root_cause_audit.py`, `bridge/opening_pass_source_policy_audit.py`, and Phase29L tests. Reused Phase29L's evidence inventory without changing it. Focused verification additionally exercised SAYC route configuration, system profiles and source-authority registry tests. No applicable AGENTS.md found.", "",
    "## C. Files added", "",
    "- `bridge/nisim_nily_opening_policy.py`", "- `tests/test_bridge_phase29m_nisim_nily_opening_policy.py`",
    "- `bridgelab_phase29m_nisim_nily_opening_policy.md` (this report, policy snapshot and optional audit)", "",
    "## D. Files modified", "", "None. No existing production, source, profile, route or diagnostic file modified.", "",
    "## E. Exact partnership policies formalized", "",
    "Policy identity `nisim-nily.opening-policy`, version `29M.1`. Immutable dataclasses and deterministic serialization; Rule20 helper uses canonical `Hand` evaluation and retains no hand/Deal.", "",
    "| Proposition | Condition | Exact policy | Authority / status |", "|---|---|---|---|"]
for p in policy.propositions:
    lines.append(f"| {p.policy_id} | {p.condition} | {p.policy} | {p.authority.value} / {p.status.value} |")
lines += ["", "All strength and suit-choice approvals remain subject to family applicability, shape, suit length, balanced requirements, strong-opening and preempt boundaries. A weak 5-5-major hand is not automatically opened 1S merely because the suit preference is settled. Exactly 5-5 does not approve 6-6.", "",
    "## F. Authority classification", "",
    "`NISIM_NILY_PARTNERSHIP_POLICY` identifies explicit Phase29M approvals. `SUPPORTED_REFERENCE` identifies existing Better-Minor and Rule22 reference facts. `SOURCE_INSUFFICIENT` marks the missing positive Pass predicate. `UNRESOLVED` marks remaining selectors/domains. `AUTHORITATIVE_REPOSITORY_SOURCE` is reserved but assigned to no new proposition: Phase29L found no authenticated external opening claim. Existing production remains the source of actual current recommendations; that operational status does not authenticate bridge theory. No global source-authority registry changes.", "",
    "Safety-exclusion authority is the user's partnership prohibition; its UNRESOLVED status describes the protected domain or production integration, not doubt about the prohibition. Rule22's reference-only disposition is explicitly mandated by user section F.", "",
    "## G. Rule-of-20 representation", "",
    "Approved partnership formula: HCP + longest length + second-longest length >=20. `assess_rule_of_20(Hand)` returns HCP, two lengths, score, qualifies and whether this is the intended 11-HCP use. It never chooses a call. The formula may be calculated for other strengths without granting a new opening entitlement. It contains no quick-trick term.", "",
    "- 11 + 5 + 4 = 20: qualifies.", "- 11 + 4 + 4 = 19: does not qualify; does not imply Pass.", "",
    "## H. Rule-of-22 status", "", "Reference/evaluation guidance only. Not adopted by production, not a required partnership gate, not Pass policy.", "",
    "## I. 12-HCP policy", "", "Normally opening strength; Rule20 is not required. A flat 12-HCP hand can score 19 without losing normal partnership opening strength. No arbitrary bid or unresolved-selector bypass.", "",
    "## J. 11-HCP policy", "", "Rule20 qualification establishes potential opening strength only. The opening call still needs an applicable approved family. Production's current one-level 12-HCP floor remains untouched.", "",
    "## K. Equal-five-card-major policy", "", "**5♠–5♥ => 1♠ (1S), NOT 1H.** Explicit partnership decision, not universal SAYC. Supersedes the provisional reference suggestion for nisim–nily; Phase29L remains an unchanged historical source snapshot. Strength/strong-opening eligibility still applies. Production still abstains at its controlled boundary.", "",
    "## L. Equal major+minor policy", "", "With one five-card major and a five-card minor, prefer the major where existing sourced opening-family predicates support it. No new general selector or production predicate is installed.", "",
    "## M. Equal-minor boundaries", "", "Existing 3-3 ->1C and 4-4 ->1D remain subject to current family gates. 5-5 and 6-6 minors remain unresolved, not Pass. No selector is invented for other configurations. Equal minors of length <=2 imply a five-card major in a valid 13-card hand; this is not a newly alleged minor-only coverage gap.", "",
    "## N. Strong-2C safety exclusion", "", "The uncomputed below-22-HCP playing-trick branch remains protected UNKNOWN/ABSTAIN when unresolved. A failed HCP-only 2C predicate does not exclude strong opening strength. No playing-trick evaluator or new 2C semantics added.", "",
    "## O. Weak-two/preempt safety exclusions", "", "Protect multiple six-card qualifying D/H/S suits, seven plus six D/H/S overlap, competing long suits, strength/quality/seat exceptions and unsupported long-suit variants. Existing covered weak/preempt bids remain intact. Seven plus six clubs differs from a six-card D/H/S overlap; two seven-card suits are impossible in a valid hand. Generic 5-HCP references, six clubs and eight-plus/four-level gaps do not imply Pass.", "",
    "## P. Pass fallback prohibition", "", "ABSTAIN ->Pass, UNKNOWN ->Pass and no-rule-matched ->Pass are prohibited. Registry complements are not Pass. Future Pass requires its own positive strength/domain conditions, explicit exclusions, provenance and explanation. No such complete predicate is supplied by Phase29M.", "",
    "## Q. Optional 1,000-deal read-only audit", "",
    "Reproduced with `run_full_auction_simulation(SimulationConfig(100, 1000))`, reused existing Phase29J/K reports, canonical Hand parsing/evaluation and the new strength helper. No results entered the production router. Existing four-pass behavior is unaffected.", "",
    "Reproduced: 616 depth-0 ABSTAIN, Phase29K screen 542, strong coverage-boundary indexes 57/184/613. Indexes were asserted only after reproduction; classification uses the cases supplied by the existing root-cause report, not a hard-coded index lookup.", "",
    "Classification precedence (diagnostic, not exhaustive bridge eligibility): existing Phase29J strong cases; then 11 HCP with Rule20>=20; then long suit >=6 or equal five-card majors/minors; remaining cases SOURCE_OR_POLICY_INSUFFICIENT. Long/equal-shape screens flag unresolved risk without implementing weak/preempt predicates. Qualifying Rule20 cases may also have unresolved family/playing-trick risks; their category asserts strength only.", "",
    "POLICY_SUPPORTED_POTENTIAL_PASS is zero because no positive Pass predicate is approved. Neither max-length<=5 nor failed Rule20 is a safety proof. The insufficient category remains explicitly ambiguous; even other categories do not produce calls. Percentages use all 616 depth-0 cases.", "",
    "| Category | Count | % of 616 | HCP distribution | Shape distribution (sorted lengths) |", "|---|---:|---:|---|---|"]
for name, group in audit["categories"].items():
    lines.append(f"| {name} | {group['count']} | {group['percentage_of_616']:.4f}% | {json.dumps(group['hcp'])} | {json.dumps(group['shape'])} |")
lines += ["", f"11-HCP Rule20 qualifiers inside the old 542-case screen: **{audit['rule20_11_hcp_inside_phase29k_screen']}**. This demonstrates why the old screen must not become Pass.", "",
    "Bounded representatives and complete audit summary (at most three representatives per category; no Deal objects):", "", "```json", json.dumps(audit, indent=2), "```", "",
    "## R. Remaining unresolved domains", ""]
for e in policy.safety_exclusions:
    lines.append(f"- `{e.exclusion_id}`: {e.domain}. Exclude from future Pass; unresolved disposition UNKNOWN / ABSTAIN.")
lines += ["- Positive Pass domain itself, including approved HCP/shape/control conditions and proof that protected domains cannot qualify.", "",
    "## S. Readiness for future implementation", "",
    "Approved strength-screen arithmetic and the exact 5-5-major preference are precise as policy. They do not supply a positive Pass predicate. No entire or narrow production Pass domain is yet justified merely by these approvals. Any later opening integration must also isolate the partnership policy from generic SAYC, define its activation/context, and preserve stronger-family precedence. This phase deliberately does none of that.", "",
    "## T. Exact proposed Phase29N", "",
    "Narrowest safe next phase: specify and obtain approval for one affirmative Pass domain, with exact seat/vulnerability scope, HCP/shape/control conditions, exception precedence and a sound proof/exclusion for strong playing tricks and preempts. Keep all remaining cases unsupported. Review readiness before production integration. If implementation is authorized after that contract exists, limit it to that explicitly positive subset, under an explicit partnership activation contract; do not implement the entire Pass domain. The present phase does not authorize that integration.", "",
    "## U. Focused test results", "", "109 passed in 7.86s. Suites: Phase29M/L/K/J; SAYC openings, 2NT, strong2C, weak twos, three-level preempts; system profiles; source authority and registry audit; route configuration. No full regression. Bundled Python used existing local venv pytest packages with PYTHONDONTWRITEBYTECODE=1 and cacheprovider disabled. Optional audit aggregation repeated on the same canonical batch and matched deterministically.", "",
    "## V. Production route count", "", "45. Opening rule count remains 14; no added Pass or other opening rule.", "",
    "## W. Git/diff/whitespace", "", "Three untracked deliverables listed in C; no tracked modifications. `git diff --check` and `git diff --stat` are empty. Separate whitespace/EOF check covers all untracked deliverables. HEAD unchanged. No commit/push.", "",
    "## X. Semantic guards", "", "| Category changed? | YES/NO |", "|---|---|"]
for label in ("Production opening semantics", "Pass recommendations", "Bidding rules", "Opening rules", "Routes", "Route count", "ABSTAIN behavior", "UNKNOWN behavior", "System profiles", "Treatments", "Auction", "Deal generation", "Phase29F simulator", "Phase29G full-auction simulator", "Phase29H coverage", "Phase29I diagnostics", "Phase29J root-cause audit", "Phase29K Pass audit", "Phase29L source-policy audit", "GUI", "Contract extraction", "Play", "Double dummy"):
    lines.append(f"| {label} | NO |")
lines += ["", "## Y. Stop-condition review", "", "Expected baseline present. No production change needed. Approved policy represented without universal-SAYC authority claims. Existing diagnostics unchanged and tested. No full regression, commit or push. Stop for review; no production implementation in this phase.", "",
    "## Required answers 1–20", ""]
answers = [
    "YES. Rule20 is explicitly approved nisim–nily partnership strength policy, primarily for 11 HCP.",
    "NO. It is not universal SAYC policy.",
    "YES. 11+5+4=20 meets the screen, without choosing a call.",
    "NO. 11+4+4=19 fails the screen, without implying Pass.",
    "NO. 12 HCP is normally opening strength without a universal Rule20 gate; family boundaries remain.",
    "1S. Exactly 5♠–5♥ =>1♠, subject to opening eligibility and stronger-family boundaries.",
    "NO. The 1S choice is partnership policy, not an authoritative universal SAYC claim.",
    "NO. Rule22 is reference-only and not production-adopted.",
    "NO. Unresolved equal minors cannot become Pass.",
    "NO. Unresolved strong-2C playing tricks cannot become Pass.",
    "NO. Unresolved weak-two/preempt overlaps cannot become Pass.",
    "NO. ABSTAIN cannot automatically become Pass.",
    "NO. UNKNOWN cannot automatically become Pass.",
    "NO. Failure of all current opening rules is not evidence of Pass.",
    "NO. Phase29M creates no production Pass recommendation.",
    "NO. Production bidding semantics are unchanged.",
    "YES. Production SAYC route count is 45.",
    "Still missing: a positive approved Pass predicate; exact context/seat/vulnerability scope; controls/distribution and exception rules; sound strong-playing-trick exclusion; preempt/long-suit and equal-minor exclusion or resolution; safe partnership activation/integration. Rule20 failure and <=10 HCP alone supply none of this proof.",
    "Do not implement the entire domain. Only a narrowly defined positive subset could be implemented after its missing affirmative contract and safety proof are approved; no such subset is specified yet.",
    "Phase29N should first acquire/approve that narrow positive Pass specification and validate its exclusions. Production implementation remains contingent on that contract and subsequent review, not on a complement or coverage screen.",
]
for i, answer in enumerate(answers, 1):
    lines.append(f"{i}. {answer}")
lines += ["", "## Machine-readable policy snapshot", "", "This is the exact deterministic `to_dict()` content; `to_json()` uses compact sorted keys.", "", "```json", json.dumps(policy.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), "```", ""]
Path(__file__).with_name("bridgelab_phase29m_nisim_nily_opening_policy.md").write_text("\n".join(lines), encoding="utf-8")
