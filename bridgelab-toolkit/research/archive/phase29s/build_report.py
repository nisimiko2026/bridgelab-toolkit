from pathlib import Path
from collections import Counter
import hashlib
import json
import sys

root = Path(r'C:\Users\nisim\Documents\BridgeLab-phase18b-worktree')
base = root/'bridgelab-toolkit'
out = Path(__file__).parent
sys.path.insert(0, str(base))
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.opening_policy_consolidation_audit import build_consolidation_audit, Classification, State

preserved = json.loads((out/'baseline.json').read_text())
for name, expected in preserved.items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest().upper() == expected
r = build_consolidation_audit(run_full_auction_simulation(SimulationConfig(100,1000)))
q = json.loads((base/'bridgelab_phase29q_nisim_nily_opening_pass_contract.json').read_text(encoding='utf-8'))
old = {row['deal_index']:row for row in q['cases']}
transitions = {}
for row in r.cases:
    key = (old[row.deal_index]['contract']['result'], row.assessment.classification.value)
    transitions.setdefault(key, []).append(row.deal_index)
interpretations = [
    'This latest consolidation specification supersedes earlier broader 11-HCP major and Strong2C approvals for this new overlay only. Earlier P/Q/R artifacts are preserved unchanged.',
    'Normal opening strength is 12+ OR Rule20>=20 in every seat. A positive strength result may leave the denomination unknown. Exact6-major+5-minor boundaries remain UNRESOLVED even with strength, as C expressly requests.',
    'The broader1NT wording does not unambiguously enumerate every shape. Canonical balanced shapes are a supported subset, including5332 five-card major; exactly nine major cards is excluded. Other shapes and >9-major interpretation remain unknown when in range.',
    'Weak two-suited candidates never gain a definite recommendation from incomplete honor quality.5-major+6-minor is directly covered; unapproved reverse6-5/6-6 orientations remain unknown rather than adopted. Relative range guidance is not turned into a suit-quality score.',
    'Multi weak uses only the current G examples for affirmative quality/strength: exact5HCP favorable with Q or K, or exact7HCP unfavorable with seven-card KJT/QJT. The corresponding unfavorable six-card examples are negative. Other valid-length combinations are unknown; no complete range or older generic quality table is silently imported.',
    'An explicitly allowed Multi weak branch is recorded as positive evidence, but Multi-versus-preempt level selection remains unresolved under K. A branch match is not an invented priority rule.',
    'Strong-minor unbalanced uses the canonical unbalanced category. Canonical6322 is semi-balanced, so its partnership applicability remains unknown rather than silently interpreting not-balanced as unbalanced.',
    'Seven-card strong-minor examples match named honor/intermediate patterns; unspecified low spots may include9 in KJT/QJT/AT/KT examples. Other patterns remain unknown.',
    '22-HCP strong-suit examples are sufficient patterns; because the list says include, unlisted honor combinations remain unknown. No five-card suit, or a five-card suit with no A/K/Q/J, excludes route2; ten alone is not an honor.',
    'Playing-trick table applies to named short honor holdings (up to3 cards) and exact six-card AKQxxx. No long-suit extrapolation, spot-only zero, void value, or unlisted honor value is added. An unapproved component makes a needed total unknown.',
    'Route3 Strong2C and strong-minor Multi can both fit a test hand; unlike the expressly stated22-HCP balanced priority, their mutual priority is not specified. That overlap remains unresolved.',
    'Preempt candidates conservatively include six-or-longer weak suits; numerical approximate ranges do not force a final level. No five-card preempt family is activated by this consolidation or retained earlier six/seven-card policy.',
    'Pass is only the complete conjunction of12 explicit negative family checks. The requested individual-review groups retain an UNKNOWN guard when opening strength has not independently resolved them. No old Pass signature is used as a blanket override.',
    'Review queues B/C include all requested shapes, even if an explicit approved rule already proves opening strength. Their tables retain classification and unresolved details for case-by-case review; queue A is restricted to unresolved11+HCP.',
]
payload = r.to_dict()
payload['baseline'] = dict(branch='codex/phase18b', head='c70c0f330d641964308e0e98500e8f47c29699a6', tracked_changes=0, preserved_phase29pqr_sha256=preserved)
payload['scope_interpretations'] = interpretations
payload['phase29q_transitions'] = [dict(before=a,after=b,count=len(ids),deal_indices=ids) for (a,b),ids in sorted(transitions.items())]
payload['approved_pt_table'] = {'A':1,'K alone':0,'Q alone':0,'AK':2,'AQ':1.5,'AJ':1,'AJ10':1.5,'KQ':1,'KQ10':1.5,'KQJ':2,'QJ':.25,'QJ10':1,'AKQ':3,'AKQxxx':6}
payload['validation'] = dict(focused_tests='39 passed in 16.39s',command='python -m pytest -q -p no:cacheprovider tests/test_bridge_phase29s_opening_policy_consolidation_audit.py',full_regression=False,committed=False,pushed=False)
(out/'bridgelab_phase29s_opening_policy_consolidation_audit.json').write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')

lines = ['# Phase 29S — nisim–nily opening policy consolidation audit','',
    '**616 real production opening abstentions: 48 OPENING_SUPPORTED, 0 PARTNERSHIP_TREATMENT_SUPPORTED, 440 PASS_SUPPORTED, 128 UNRESOLVED.** These are audit classifications only. Production remains ABSTAIN for every record; no production rule, route or bidding behavior changed.','',
    '## Baseline and scope','',
    '- Repository: `C:\\Users\\nisim\\Documents\\BridgeLab-phase18b-worktree\\bridgelab-toolkit`.',
    '- Branch `codex/phase18b`; committed HEAD `c70c0f330d641964308e0e98500e8f47c29699a6`.',
    '- Initial status: exactly the 12 expected Phase29P/Q/R files untracked, no tracked modifications. No earlier Phase29S file existed.',
    '- All 12 existing artifacts preserved byte-for-byte; SHA256 before/after values are in JSON baseline metadata.',
    '- Current authority is the latest user attachment, “PHASE29S — NISIM–NILY OPENING POLICY CONSOLIDATION AUDIT,” sections B–M. Earlier incompatible approvals are not mass-replaced; this is a new versioned overlay.',
    '- Simulation: seed100, deal_count1000. The previous audit regenerates each dealer hand from seed+deal index and verifies production route/rejection traces. Population616; simulation errors0; no reproduction mismatch.','',
    '## Consolidated policy and explicit limits','',
    '| Family | Current approved rule | Remaining judgment / audit treatment |','|---|---|---|',
    '| Natural strength | 12+ HCP OR Rule20>=20, all four seats | Strength alone does not always choose denomination |',
    '| 11-HCP exceptions | Five-major or six-minor concentration may support opening | No concentration score invented; independent Rule20 takes precedence |',
    '| Natural suit choice | Equal5/6 majors1S;5-major+5/6-minor major;equal5/6 minors1D | 6-major+5-minor remains separately unresolved |',
    '| 1NT | 15–17;14 in third/fourth seat;five-major/six-minor possible;exactly9 major cards excluded | Broader shape scope not replaced by SAYC; unenumerated cases unknown |',
    '| Weak two-suited | 2S major+minor,2H major+minor,2NT minors;6–10 base, relative-vulnerability guidance;5–5/5–6 structures | No complete honor-quality test; natural/Rule20 priority; third-seat3–4 only favorable |',
    '| Multi weak | Single6/7 major;8 not Multi;side5+ excluded;exact unfavorable7-HCP KJT/QJT examples and favorable5-HCP Q/K guidance | Remaining range/quality and Multi/preempt priority unknown |',
    '| Multi strong minor | 20–21,unbalanced,6+minor,side suits<4;listed six/seven-card qualities | Unlisted qualities/6322 semi-balanced interpretation unresolved |',
    '| Multi balanced | 20–22,4333/4432/5332,includingfive-major/minor | 5422 not assumed;22 strong2C priority respected |',
    '| Strong2C | 23+;or22 with5+strong suit;or17–21 closed6+AKQ suit,side<4,approvedPT>=8.5 | Partial PT table only; no circular forcing-property criterion |',
    '| Preempts | Approximately6–10,good long suit;vulnerability and Rule2/3/4 guideline | No deterministic level inferred; candidate stays unresolved |',
    '| Later seats | Approved light-opening guidance | Quality/concentration unspecified; no Rule15 introduced |',
    '| Pass | Every applicable family explicitly negative | Missing/duplicate/UNKNOWN checks cannot establish Pass; explicit review guard retained |','']
lines += ['- '+x for x in interpretations]
lines += ['', 'Canonical balanced shapes come from `bridge/evaluation.py`:4333,4432,5332. Canonical semi-balanced shapes are5422 and6322. Existing `bridge/sayc.py` 2NT is20–21 balanced and permits a five-card major; current partnership Multi balanced changes both call meaning and upper range. Existing production Strong2C still uses22+HCP; the new23+/conditional22 audit does not alter it.','',
    'The approved PT table is stored in JSON. QJ is exactly0.25. Values are used only when the hand needs route3 and every required holding is covered. Low-HCP ordinary hands exclude all three new Strong2C routes by their explicit gates; this resolves the old blanket strong-family UNKNOWN without estimating their tricks.','',
    '## Population classifications and provenance','',
    '| Classification | Count |','|---|---:|']
lines += [f'| {name} | {count} |' for name,count in r.counts]
lines += ['', 'All616 records are in JSON, with actual hand, dealer/actor, absolute and relative vulnerability, HCP, shape class, S/H/D/C lengths and holdings, named honors, production ABSTAIN/code, all12 family checks and their provenance/reason, matched families, unresolved blockers and supported call where known.','',
    'All decisions are actual first-seat dealer decisions with empty auction. There are no actual later-seat cases in this population; later-seat boundary tests use synthetic unit-test fixtures, never invented population records. No20+HCP Multi/Strong2C test fixture is added to the616.','',
    'There are49 affirmative normal-strength hands. Deal739 (`AK8532.-.A8632.92`,11HCP,6S+5D) remains UNRESOLVED because sectionC explicitly leaves that suit-choice boundary to judgment. The other48 have opening entitlement; only the explicit covered selectors receive a concrete call. A null call is intentionally not an invented denomination.','',
    'The440 Pass results each have all12 checks NEGATIVE. None has an UNKNOWN check or a review dependency. This is a bounded audit proof against the currently specified families, not a production fallback rule. The128 unresolved records retain their blockers; none is converted to Pass because production failed to match.','',
    '## Review queues','',
    'Queues overlap. A is unresolved11+HCP only; B/C list every hand in the requested numeric/shape group, including explicitly supported opening cases. D–H record unresolved family dependencies even where independent opening strength is known. The tables support individual review and do not choose an unsupported call.','',
    '| Queue | Count |','|---|---:|']
lines += [f'| {name} | {len(ids)} |' for name,ids in r.queues]
by_id={row.deal_index:row for row in r.cases}
for name,ids in r.queues:
    lines += ['', '### '+name, '']
    if not ids:
        lines.append('No real cases in this population. This does not establish that the family is globally complete.')
    elif name[0] in 'ABC':
        lines += ['S/H/D/C order. Every row is first seat; production ABSTAIN. “—” means no supported call.','',
            '| Deal | Dealer/actor | Vuln / relative | Hand | HCP | S/H/D/C | R20 | Audit result / call | Unresolved questions |',
            '|---:|---|---|---|---:|---|---:|---|---|']
        for index in ids:
            a=by_id[index].assessment
            lines.append(f'| {index} | {a.dealer}/{a.seat} | {a.vulnerability} / {a.relative_vulnerability} | `{a.hand}` | {a.hcp} | {"/".join(map(str,a.suit_lengths))} | {a.rule20} | {a.classification.value} / {a.supported_call or "—"} | {", ".join(a.unresolved_blockers) or "None under explicit approvals; review entry retained as requested"} |')
    else:
        lines.append('Deal indices: '+', '.join(map(str,ids))+'. Full cards, context, holdings and question reasons are in JSON.')
lines += ['', '## Family states — overlaps are retained','',
    '| Family | POSITIVE | NEGATIVE | UNKNOWN |','|---|---:|---:|---:|']
family_counts={(f,s):n for f,s,n in r.family_counts}
for f in dict.fromkeys(f for f,_,_ in r.family_counts):
    lines.append(f'| {f} | {family_counts[f,"POSITIVE"]} | {family_counts[f,"NEGATIVE"]} | {family_counts[f,"UNKNOWN"]} |')
lines += ['', '## Comparison with unchanged Phase29Q','',
    '| Previous classification | Current classification | Count |','|---|---|---:|']
lines += [f'| {before} | {after} | {len(ids)} |' for (before,after),ids in sorted(transitions.items())]
lines += ['', 'Changes come from the explicit latest policy: bounded Strong2C routes; 11-HCP concentration now unresolved unless Rule20 independently proves strength; weak-treatment ranges/quality no longer presumed from every below12 exact5–5 shape; individual review for specified boundary groups. Previous P/Q/R data and decisions remain historical evidence, not edited facts. Every transition includes its actual deal indices in JSON.','',
    '## Remaining partnership questions','',
    '1. Define concentration for 11-HCP major/minor exceptions and later-seat openings, and resolve the6-major+5-minor selector.',
    '2. Enumerate the broader1NT shapes and whether the nine-major exclusion means exactly9 or9+. Clarify6322 for strong-minor Multi and5422 for balanced Multi.',
    '3. Define weak two-suited suit quality, exact range boundaries by relative vulnerability, and uncovered6–5/6–6 orientations. The current statements permit candidates but do not decide every hand.',
    '4. Complete Multi weak strength/quality cases outside the explicit examples and select Multi versus3M/preempt level where both are possible.',
    '5. Supply missing PT holding values and clarify route3 Strong2C versus strong-minor Multi priority. Do not infer values for unlisted holdings.',
    '6. Review the A–C tables case-by-case. No production integration is performed or recommended by this audit.','',
    '## Validation and final repository state','',
    '**Focused Phase29S tests:39 passed in16.39s. Production route count:45.**','',
    '```text',payload['validation']['command'],'```','',
    'Tests cover deterministic616, every-seat Rule20, natural priority, exact natural suit choices, weak two-suited unknown quality and third-seat exception, Multi weak boundaries, strong-minor seven-card examples and side-suit exclusions,20–22 balanced branch,22-HCP2C priority,1NT shape ambiguity,QJ PT0.25, missing PT values, complete-negative Pass evidence and every review queue. Synthetic boundary fixtures are not represented as real sample hands.','',
    'Files created (no pre-existing file modified):','',
    '- `bridge/opening_policy_consolidation_audit.py`',
    '- `bridgelab_phase29s_opening_policy_consolidation_audit.json`',
    '- `bridgelab_phase29s_opening_policy_consolidation_audit.md`',
    '- `tests/test_bridge_phase29s_opening_policy_consolidation_audit.py`','',
    '`git diff --check`: clean. `git diff --stat`: empty because all16 audit additions are untracked. Explicit trailing-whitespace/final-newline checks cover the four new files. `git status --short`:','', '```text']
names=list(preserved)+['bridge/opening_policy_consolidation_audit.py','tests/test_bridge_phase29s_opening_policy_consolidation_audit.py','bridgelab_phase29s_opening_policy_consolidation_audit.json','bridgelab_phase29s_opening_policy_consolidation_audit.md']
lines += ['?? bridgelab-toolkit/'+name for name in sorted(names)]
lines += ['```','','Existing ignored `.pytest_cache` access warnings remain. No tracked/production file changed; all12 P/Q/R hashes match. No full regression, commit or push. Stopped after the Phase29S audit.','']
text='\n'.join(lines)
for oldtext,newtext in {'Phase29':'Phase 29','all616':'all 616','all12':'all 12','all16':'all 16','the440':'the 440','The440':'The 440','the128':'the 128','The128':'The 128','There are49':'There are 49','other48':'other 48','tests:39 passed in16.39s':'tests: 39 passed in 16.39s','count:45':'count: 45'}.items():
    text=text.replace(oldtext,newtext)
(out/'bridgelab_phase29s_opening_policy_consolidation_audit.md').write_text(text,encoding='utf-8')
print(json.dumps({'counts':dict(r.counts),'queues':{name:len(ids) for name,ids in r.queues},'preserved':len(preserved),'transitions':[(a,b,len(ids)) for (a,b),ids in sorted(transitions.items())]},indent=2))
