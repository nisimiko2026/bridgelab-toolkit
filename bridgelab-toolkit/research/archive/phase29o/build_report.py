from pathlib import Path
import json
import sys

ROOT = Path(r"C:\Users\nisim\Documents\BridgeLab-phase18b-worktree")
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "bridgelab-toolkit"))
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.opening_pass_safety_evidence_audit import build_pass_safety_audit_report

r = build_pass_safety_audit_report(run_full_auction_simulation(SimulationConfig(100, 1000)))
name = "bridgelab_phase29o_opening_pass_safety_evidence_audit"
(OUT / (name + ".json")).write_text(r.to_json() + "\n", encoding="utf-8")
lines = ["# Phase 29O — Opening Pass safety evidence resolution", "",
    "**447 candidates: SAFE 0; UNSAFE 0; UNKNOWN 447. Production Pass readiness: NO.**",
    "", "PASS != FALLBACK_FOR_ABSTAIN. This audit resolves what the missing evidence consists of; it does not invent the missing bridge policy. No web research, production implementation, full regression, commit or push.", "",
    "## A. Baseline verification", "",
    f"- Project: `{ROOT / 'bridgelab-toolkit'}`", f"- Git root: `{ROOT}`",
    "- Branch `codex/phase18b`.",
    "- Local HEAD, live remote HEAD and remote-tracking HEAD: `dadc425bfac59bf5e217c756a73373abac9a2097`.",
    "- Ahead/behind `0/0`; initial working tree clean. Known `.pytest_cache` permission warnings only.",
    "- Supplied regression baseline 2162 passed, 143 subtests passed; not rerun.", "",
    "## B. Files inspected and methodology", "",
    "Reused the Phase29N report builder, which already invokes canonical Phase29I/J/K/H audit/reproduction checks. Each of the 616 depth-0 cases is evaluated from its recorded canonical Hand with its actual dealer, vulnerability and the simulator's explicit SAYC system. The new report retains full evidence records for all 447 insufficient cases, plus bounded representatives of other groups. No Deal objects are retained. Canonical HCP, lengths, shapes, Rule20, Auction and vulnerability methods are reused.", "",
    "Required inputs inspected/reused: `bridge/opening_pass_positive_predicate_audit.py`, `nisim_nily_opening_policy.py`, `opening_pass_source_policy_audit.py`, `opening_pass_policy_audit.py`, `opening_abstention_root_cause_audit.py`, `full_auction_abstention_audit.py`, `full_auction_coverage.py`, `deal_simulator.py`, and the Phase29L/M/N Markdown reports. Also inspected `bridge/sayc.py`, `evaluation.py`, `models.py`, `bidding_rules.py`, `system_profiles.py` and route configuration. Existing Phase29J–N tests were run.", "",
    "Repository search: `rg -n -i 'playing.?trick|quick.?trick'` across toolkit Python files, followed by opening/evaluation inspections. Matches were notes/audits, metadata maintenance, tests and the explicit unevaluated strong2C message; no usable canonical PT/QT evaluator was found. Controls (A=2, K=1), suit-quality facts, double-dummy/declarer analysis and HCP are not substituted for a partnership opening playing-trick metric.", "",
    "Knowledge reviewed: SAYC; opening-requirements; 1NT; strong 2C; weak-two/three-level/four-level preempt articles; Rule20; Rule22; playing-tricks; quick-tricks; seat-position; vulnerability; and the nily–nisim convention card. Evidence identifiers appear in the exception and gap matrices. The convention card is 2/1, not the production SAYC profile; it does not silently supply this Pass policy. No applicable AGENTS.md found in the inspected target paths.", "",
    "## C. Files added", "", "- `bridge/opening_pass_safety_evidence_audit.py`",
    "- `tests/test_bridge_phase29o_opening_pass_safety_evidence_audit.py`",
    f"- `{name}.md`", f"- `{name}.json`", "",
    "## D. Files modified", "", "None. Existing production, profile, source and Phase29J–N files unchanged.", "",
    "## E. Safety evidence model", "",
    "Immutable typed SAFE / UNSAFE / UNKNOWN evidence carries authority, source identifiers and an explanation for each dimension. SAFE means the required affirmative safety contract is satisfied, UNSAFE means a known positive opening/approved strength predicate applies, UNKNOWN means exclusion cannot be proved. UNKNOWN is not UNSAFE. Overall UNSAFE takes precedence if a known hazard applies; otherwise every required dimension must be SAFE. Missing/duplicate/incomplete evidence cannot satisfy the all-safe conjunction.", "",
    "Known existing opening recommendations are observed by reusing the unchanged SAYC opening engine, not duplicating its rules. Failed rules supply no SAFE evidence. Approved 12+ strength and 11-HCP Rule20 strength are separately explicit barriers to this ordinary <=10 Pass design; they do not select an arbitrary call. A <=10 Rule20 score>=20 is a protected potential opening, not an approved positive OPEN verdict. The module creates no Pass RuleDecision or router.", "",
    "Authority distinction: CANONICAL_PRODUCTION_REFERENCE describes existing repository provenance; it does not authenticate external bridge correctness. Explicit Phase29M partnership choices remain NISIM_NILY_PARTNERSHIP_POLICY. Qualified notes remain supported references. The source-authority registry is not modified.", "",
    "## F. Playing-trick findings", "",
    "No canonical playing-trick evaluator and no canonical quick-trick evaluator were located. Neither is used by production openings. The current evaluator supplies HCP, controls, shape and honor/quality facts only. `sayc.py` implements strong2C at HCP>=22 and explicitly says the 9+ playing-trick alternative is not evaluated.", "",
    "`knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md` defines expected declarer tricks with little/no partner help under suitable fit/contract assumptions, explicitly says there is no universally accepted formula, and supplies approximate examples. That is not a complete deterministic estimator or upper-bound theorem. `quick-tricks.md` supplies AK=2, AQ=1.5, A=1, KQ=1, K=0.5 tables; quick tricks are not playing tricks. Rule22 incorporates QT but is explicitly unadopted. None proves an ordinary low-HCP hand lies outside every protected strong-opening domain.", "",
    "The strong2C mapping '22+ OR 9+ playing tricks' is conceptually present in the repository, but the alternative's measurement/assumptions/exclusion predicate lack authenticated complete support. This is a source gap plus a partnership treatment gap, not merely an engine-helper task. Do not write a formula to make UNKNOWN disappear. Below-22 HCP excludes only the HCP branch, not the alternative.", "",
    "## G. Exception-policy findings", "",
    "For the 447, existing evidence affirmatively establishes the bounded HCP/length/Rule20/equal-suit exclusions recorded per case. Thus normal >=12 strength, the approved 11-HCP screen, the current >=22 branch, ordinary six/seven/eight-plus domains, 6-6/7-6 overlaps and equal>=5 selectors can be excluded within their stated scopes. These are scoped exclusions, not proof that all possible exceptions are covered.", "",
    "Residual exception UNKNOWN is concrete: control-rich light openings; excellent suit/honor texture; unusual distribution upgrades; unresolved optional opening/NT adjustment rules; and lack of an adopted closed exception set. `opening-requirements#Controls` allows lighter openings qualitatively. `rule-of-20#Exceptions` allows opening below20 for controls/excellent six-card suits and passing above20 for poor placement/suits. Six-card shapes are absent from the 447, but controls/quality guidance has no threshold or approved exclusion. Strong playing tricks and context are separated into their own dimensions rather than counted as extra primary populations.", "",
    "### Audit exception registry", "",
    "YES/NO predicate availability is limited to the scope column. A known shape-exclusion predicate does not mean the bid selector inside that shape is resolved. This registry inventories located material; it is not declared exhaustive partnership policy.", "",
    "| ID / name | Authority | Positive predicate? | Exclusion? | Production? | Pass relevant? | Scope and evidence |", "|---|---|---|---|---|---|---|"]
for e in r.exceptions:
    yn = lambda b: "YES" if b else "NO"
    lines.append(f"| {e.exception_id}: {e.name} | {e.authority} | {yn(e.positive_predicate_available)} | {yn(e.exclusion_predicate_available)} | {yn(e.production_implemented)} | {yn(e.relevant_to_pass_safety)} | {e.scope}. Sources: {', '.join(e.evidence)}. {e.unresolved_consequence} |")
lines += ["", "## H. Context findings", "",
    "The source distinguishes opening position (first/second/third/fourth) from compass seat (N/E/S/W). The entire 447-case subset is dealer-first-seat, empty auction, actor not previously passed, explicit simulator SystemContext('SAYC') with empty options. These facts can be established; they were not missing data in Phase29N. Later-seat and passed-hand questions are out of this particular population, but matter if a future rule's scope expands.", "",
    "The seat-position source describes disciplined first/second openings, lighter tactical third-seat openings and fourth-seat Rule15. The vulnerability source describes more aggressive favorable and more disciplined unfavorable style. Dedicated Rule20/22 sources restrict first/second seat, whereas the generic Standard American fourth-seat discussion lists them too (Phase29L discrepancy). No complete approved nisim–nily seat/vulnerability Pass contract resolves these choices.", "",
    "Production SAYC opening gates use system identity and an unopened auction; the current opening predicates do not vary their thresholds by seat or vulnerability. That implementation omission is not partnership approval that context is irrelevant. SystemContext options are explicit opaque facts, system profiles separate SAYC from 2/1, and no nisim–nily activation option exists. Empty options mean no selected options, not an approved assertion that every contextual exception is absent.", "",
    "Relative vulnerability is computed with canonical `Vulnerability.is_vulnerable` for actor and opponent, not inferred from labels alone:", ""]
for label, count in r.context_distribution:
    lines.append(f"- {label}: {count}")
lines += ["", "The deterministic dealer/vulnerability cycles may correlate these contexts; this sample does not independently validate all seat/vulnerability combinations. Known context facts therefore refine the diagnosis without changing CONTEXT_SAFETY from UNKNOWN.", "",
    "## I. Additional independent dimension", "",
    "POSITIVE_PASS_POLICY: even complete exclusions would still require an affirmative approved Pass domain. Phase29M explicitly records positive-pass INCOMPLETE; Phase29N G is a proposal to audit, not production approval. This approval gap is distinct from the substance of exception or context predicates. All 447 remain UNKNOWN on it. Quick-trick policy is not added as a mandatory independent gate because Rule22 is unadopted. No extra speculative safety dimensions are introduced.", "",
    "## J. 447-case decomposition", "",
    "Each of the 447 JSON records contains canonical HCP/SHDC lengths/shape/Rule20, previous classification, actual context, all evidence dimensions, positive hazard list, scoped exclusions and overall result. All 447 have no positive hazard located; that absence is not used to infer SAFE.", "",
    "| Dimension | SAFE | UNSAFE | UNKNOWN |", "|---|---:|---:|---:|"]
for dimension in dict.fromkeys(d for d,_,_ in r.dimension_counts):
    counts = {s:n for d,s,n in r.dimension_counts if d == dimension}
    lines.append(f"| {dimension} | {counts['SAFE']} | {counts['UNSAFE']} | {counts['UNKNOWN']} |")
lines += ["", "Intersections of the original three dimensions (mutually exclusive; fourth dimension also UNKNOWN for every case):", "",
    "| UNKNOWN dimensions | Count |", "|---|---:|"]
for label, count in r.unknown_intersections:
    lines.append(f"| {label} | {count} |")
lines += ["", "Only playing-trick unknown=0; only exception unknown=0; only context unknown=0; exactly two unknown=0; all three unknown=447; all required dimensions safe=0. All three original dimensions tie as blockers of 447 cases. No single decision alone unlocks any safe candidate because the other independent gaps remain.", "",
    "## K. 616-case reconciliation", "",
    "1000 deals; 616 depth-0 opening abstentions; zero simulation or canonical reproduction errors. Historical categories remain unchanged:", "",
    "| Phase29N category | Count |", "|---|---:|"]
for label, count in r.phase29n_counts:
    lines.append(f"| {label} | {count} |")
lines += ["", "46 Rule20 +3 known boundaries +120 protected +447 insufficient +0 safe=616. The new tri-state analysis of the whole 616 yields SAFE=0, UNSAFE=45 and UNKNOWN=571: the three known opening-strength boundaries plus 42 approved 11-HCP strength qualifiers are unsafe for ordinary Pass. The other four low-HCP Rule20 qualifiers remain UNKNOWN, not invented approved openings. These overall counts are distinct from the target 447-subset counts below.", "",
    "## L. Rule20 42 ->46", "",
    "Phase29M counted only 11-HCP Rule20 qualifiers (42). Phase29N explicitly computes Rule20 at lower HCP too: four additional qualifiers, three from the old 65 protected and one from the old 506 insufficient. Therefore 42+3+1=46. Primary Rule20 precedence retains secondary distribution flags, without double-counting. Expected scope refinement, not a bug or new opening approval.", "",
    "## M. Protected unresolved 65 ->120", "",
    "Three low-HCP qualifiers leave the old protected bucket for Rule20, leaving 62 (51 long-suit and 11 equal-suit). Fifty-eight 11-HCP hands that fail Rule20 leave the old insufficient bucket for OTHER_PROTECTED_UNRESOLVED, since failed Rule20 is not Pass and the proposed ordinary domain is <=10. Thus 65-3+58=120. This is taxonomy/precedence refinement, not 55 newly discovered unsafe hands and not extra safety dimensions counted repeatedly.", "",
    "| Phase29M category | Phase29N category | Count |", "|---|---|---:|"]
for old,new,count in r.phase29m_to_n:
    lines.append(f"| {old} | {new} | {count} |")
lines += ["", "The old insufficient 506 becomes 1 Rule20 +58 protected eleven-HCP +447 insufficient. All original populations and transition sums reconcile exactly; regression tests assert these definitions.", "",
    "## N. All dimensions SAFE", "", "0 of 447 (0%). No new supported Pass candidate.", "",
    "## O. Still UNKNOWN", "", "447 of 447 (100%). UNKNOWN is retained, not relabeled UNSAFE.", "",
    "## P. Positively UNSAFE", "", "0 of the 447. Separately, 45 of the complete 616 have explicit normal/approved borderline opening-strength evidence barring ordinary Pass. This does not create a call or override unresolved suit-family selection.", "",
    "## Q. Bounded representatives", ""]
for label, cases in r.representatives:
    lines += [f"### {label}", ""]
    if not cases:
        lines.append("None.")
    for case in cases:
        a = case.phase29n
        lines.append(f"- Deal {case.deal_index}: `{case.hand}`; HCP={a.hcp}, SHDC={a.suit_lengths}, shape={a.shape_class}, Rule20={a.rule20_score}; dealer/actor={case.dealer}/{case.acting_seat}, position={case.opening_position}, vulnerability={case.vulnerability} ({case.relative_vulnerability}); previous={a.classification.value}; overall={case.overall.value}. Positive hazards: {', '.join(case.positive_hazards) or 'none established'}. Dimensions: " + ", ".join(f"{d.dimension.value}={d.status.value}" for d in case.dimensions) + ".")
lines += ["", "Each representative group is bounded at three. Repeated examples across UNKNOWN dimensions intentionally show their intersection. All 447 assessment records are retained separately to meet the per-case audit requirement; no full Deal retained.", "",
    "## R. Machine-readable gap matrix", "",
    "Resolution types distinguish authoritative-source, partnership-decision, engine-helper and already-resolved evidence. ALREADY_RESOLVED on a coverage row means its policy/helper evidence is resolved, not that production coverage exists. No underlying policy/source gap is mislabeled ENGINE_HELPER_REQUIRED.", "",
    "| gap_id | Domain / description | Kind / authority | Repository evidence | Partnership predicate defined? | Production? | Required resolution |", "|---|---|---|---|---|---|---|"]
for g in r.gaps:
    lines.append(f"| {g.gap_id} | {g.domain}: {g.description} | {g.gap_kind} / {g.current_authority} | {', '.join(g.repository_evidence)} | {'YES' if g.explicit_partnership_policy_available else 'NO'} | {'YES' if g.production_implementation_available else 'NO'} | {g.required_resolution.value} |")
lines += ["", "## S. Policy gaps", "",
    "Exact controls/distribution/optional-opening exceptions; first-seat/vulnerability scope and later-seat boundaries; nisim–nily activation; positive Pass approval; the precise application of the already-protected strong playing-trick alternative. Existing protective policy is known; the missing predicates are its affirmative resolution, not permission to discard it.", "",
    "## T. Source gaps", "",
    "Playing-trick concept lacks complete authoritative estimator/upper-bound support, including suit texture/fit/partner assumptions. Quick-trick tables cannot supply it. Qualitative opening exceptions lack exact claim-level bounds. Metadata such as Standard, bibliography links and canonical use do not supply authenticated claim coverage. No external source was acquired in this phase.", "",
    "## U. Engine gaps", "",
    "No current blocker is safely an engine-only task. PT/QT evaluator code is absent, but PT policy/authority is incomplete and QT opening use is unapproved. Implementing either now would choose policy implicitly. Existing Hand evaluation, Rule20 arithmetic, seat/history, vulnerability and system-option representations already suffice for the defined facts. ENGINE_HELPER_REQUIRED is reserved for a later fully specified policy with missing calculation code.", "",
    "## V. Coverage gaps", "",
    "11-HCP Rule20 arithmetic/strength policy and exact 5-5-major preference are defined, but production opening-family integration is absent. 5♠–5♥=>1♠ remains explicit partnership policy; it is not universal SAYC. Equal-minor and playing-trick domains still have substantive unresolved predicates and cannot be called coverage-only gaps. No coverage work is performed.", "",
    "## W. Exact human partnership decisions", "",
    "These questions are for review; no answer or approval is inferred. Each affects all 447 potentially, but approving one alone unlocks zero because the other dimensions remain unknown. A justified narrower domain is acceptable; maximizing coverage is not the objective.", ""]
for q in r.partnership_questions:
    lines += [f"### {q.question_id}", "", f"- Question: {q.question}", f"- Why: {q.why}",
        f"- Affected ordinary audit cases: {q.affected_cases}.", f"- Evidence: {', '.join(q.evidence)}.",
        f"- If unanswered: {q.unanswered_default}.", ""]
lines += ["## X. Is a positive Pass predicate sufficiently supported?", "", "NO. Repository/approved-policy evidence refines the unknowns and resolves the factual context, but does not supply any complete all-SAFE proof or an approved affirmative Pass domain.", "",
    "## Y. Exact proposed Phase29P", "",
    "Partnership decision and evidence-contract phase only: resolve W's minimum choices for a first-seat, explicitly activated, vulnerability-scoped subset; specify a sourced playing-trick exclusion proof and a closed exception contract; obtain explicit positive Pass approval. If an external source is required, acquire it only in a separately authorized later source phase. Then rerun the safety audit. NO production Pass implementation on the present evidence.", "",
    "## Z. Focused tests", "",
    "138 passed in 11.31s. Suites: Phase29O/N/M/L/K/J; SAYC openings, 2NT opening, strong2C, weak twos, three-level preempts; source-authority contract and registry audit; system profiles; route configuration. Tests cover tri-state conjunction/precedence, all original unknown dimensions, real context facts, known positive hazards, low-HCP Rule20 uncertainty, exact count migrations, deterministic registry/gaps/report, bounded representatives and unchanged routes. No full regression.", "",
    "## AA. Route count", "", "45 production SAYC routes. No opening rule added; existing opening rules unchanged.", "",
    "## AB. Git status/diff/whitespace", "",
    "Four untracked audit deliverables from C; no existing tracked modifications. `git diff --check` and `git diff --stat` empty. Separate trailing-whitespace/final-newline checks cover all four new files. Deterministic JSON verified and subset totals reconciled. HEAD unchanged. No commit or push.", "",
    "## AC. Semantic guards", "", "| Category changed? | YES/NO |", "|---|---|"]
for area in ("Production opening semantics", "Pass recommendations", "Bidding rules", "Opening rules", "Routes", "Route count", "ABSTAIN behavior", "UNKNOWN behavior", "System profiles/treatments", "Auction", "Deal generation", "Simulator", "GUI", "Contract extraction", "Play", "Double dummy"):
    lines.append(f"| {area} | NO |")
lines += ["", "## Required answers 1–20", ""]
answers = [
    "All 447 passed only the numerical/shape screen; Phase29N had no affirmative playing-trick exclusion, closed exception policy or approved context contract. Positive Pass approval is independently still missing.",
    "The three original dimensions tie: each blocks all 447. The additional positive-policy dimension also remains UNKNOWN for all 447.",
    "NO usable canonical playing-trick opening evaluator was located.",
    "Not applicable; the approximate source concept is not a complete authoritative safety predicate.",
    "NO usable canonical quick-trick evaluator was located. Reference tables exist; controls/HCP are not substitutes, and Rule22 is not adopted.",
    "Primarily SOURCE_GAP plus POLICY_GAP for exact partnership treatment/exclusion. It is not merely ENGINE_HELPER_REQUIRED.",
    "Concrete residuals are controls/suit-quality/distribution upgrades, optional opening adjustments and lack of a closed approved exception set. Existing scoped strength/length/equal-suit exclusions are already established for the 447; playing tricks and context are separately modeled.",
    "No exact approved seat-dependent nisim–nily Pass policy is defined. Repository guidance varies by opening position; compass seat is not opening position. All 447 are known first-seat dealer cases.",
    "No exact approved vulnerability-dependent Pass threshold is defined; reference guidance does change opening/preempt style. Current production opening predicates' lack of adjustment does not establish approved invariance.",
    "NO. Known context facts do not prove context irrelevant.",
    "0 of 447 become all-SAFE.",
    "447 remain UNKNOWN.",
    "0 of the target 447 are positively UNSAFE. Across all 616, 45 have approved normal/borderline strength barriers; 571 remain UNKNOWN.",
    "42 eleven-HCP qualifiers plus four lower-HCP qualifiers (three from old protected, one from old insufficient) equals46. Broader audit screening and precedence, not new opening authorization.",
    "65 minus three transferred low-HCP qualifiers plus 58 failed-screen eleven-HCP cases equals120: 51 long-suit +11 equal-suit +58 other.",
    "Correct documented refinements, not bugs. Exact migration assertions pass.",
    "Resolve the playing-trick definition/exclusion, closed opening exceptions, seat/vulnerability scope and partnership activation, then approve the affirmative positive Pass subset. Exact questions are in W.",
    "Each affects all447, but none alone unlocks a safe hand. All independent exclusions and positive approval must be satisfied; no claim that one answer guarantees coverage.",
    "NO. Phase29P cannot implement production Pass from the present evidence.",
    "Formalize those minimal partnership/evidence contracts for a narrow first-seat subset and rerun the safety audit; leave unanswered cases UNKNOWN/ABSTAIN.",
]
for i, answer in enumerate(answers, 1):
    lines.append(f"{i}. {answer}")
lines += ["", "## Reproduction", "", "```python", "from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation",
    "from bridge.opening_pass_safety_evidence_audit import build_pass_safety_audit_report",
    "report = build_pass_safety_audit_report(run_full_auction_simulation(SimulationConfig(100, 1000)))",
    "print(report.to_json())", "```", "", "Stop after reviewable audit delivery. No production integration authorized by this phase.", ""]
(OUT / (name + ".md")).write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"subset": r.subset_overall_counts, "full": r.full_population_overall_counts, "context": r.context_distribution}))
