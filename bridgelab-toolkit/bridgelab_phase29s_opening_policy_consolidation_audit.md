# Phase 29S — nisim–nily opening policy consolidation audit

**616 real production opening abstentions: 48 OPENING_SUPPORTED, 0 PARTNERSHIP_TREATMENT_SUPPORTED, 440 PASS_SUPPORTED, 128 UNRESOLVED.** These are audit classifications only. Production remains ABSTAIN for every record; no production rule, route or bidding behavior changed.

## Baseline and scope

- Repository: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree\bridgelab-toolkit`.
- Branch `codex/phase18b`; committed HEAD `c70c0f330d641964308e0e98500e8f47c29699a6`.
- Initial status: exactly the 12 expected Phase 29P/Q/R files untracked, no tracked modifications. No earlier Phase 29S file existed.
- All 12 existing artifacts preserved byte-for-byte; SHA256 before/after values are in JSON baseline metadata.
- Current authority is the latest user attachment, “PHASE29S — NISIM–NILY OPENING POLICY CONSOLIDATION AUDIT,” sections B–M. Earlier incompatible approvals are not mass-replaced; this is a new versioned overlay.
- Simulation: seed100, deal_count1000. The previous audit regenerates each dealer hand from seed+deal index and verifies production route/rejection traces. Population616; simulation errors0; no reproduction mismatch.

## Consolidated policy and explicit limits

| Family | Current approved rule | Remaining judgment / audit treatment |
|---|---|---|
| Natural strength | 12+ HCP OR Rule20>=20, all four seats | Strength alone does not always choose denomination |
| 11-HCP exceptions | Five-major or six-minor concentration may support opening | No concentration score invented; independent Rule20 takes precedence |
| Natural suit choice | Equal5/6 majors1S;5-major+5/6-minor major;equal5/6 minors1D | 6-major+5-minor remains separately unresolved |
| 1NT | 15–17;14 in third/fourth seat;five-major/six-minor possible;exactly9 major cards excluded | Broader shape scope not replaced by SAYC; unenumerated cases unknown |
| Weak two-suited | 2S major+minor,2H major+minor,2NT minors;6–10 base, relative-vulnerability guidance;5–5/5–6 structures | No complete honor-quality test; natural/Rule20 priority; third-seat3–4 only favorable |
| Multi weak | Single6/7 major;8 not Multi;side5+ excluded;exact unfavorable7-HCP KJT/QJT examples and favorable5-HCP Q/K guidance | Remaining range/quality and Multi/preempt priority unknown |
| Multi strong minor | 20–21,unbalanced,6+minor,side suits<4;listed six/seven-card qualities | Unlisted qualities/6322 semi-balanced interpretation unresolved |
| Multi balanced | 20–22,4333/4432/5332,includingfive-major/minor | 5422 not assumed;22 strong2C priority respected |
| Strong2C | 23+;or22 with5+strong suit;or17–21 closed6+AKQ suit,side<4,approvedPT>=8.5 | Partial PT table only; no circular forcing-property criterion |
| Preempts | Approximately6–10,good long suit;vulnerability and Rule2/3/4 guideline | No deterministic level inferred; candidate stays unresolved |
| Later seats | Approved light-opening guidance | Quality/concentration unspecified; no Rule15 introduced |
| Pass | Every applicable family explicitly negative | Missing/duplicate/UNKNOWN checks cannot establish Pass; explicit review guard retained |

- This latest consolidation specification supersedes earlier broader 11-HCP major and Strong2C approvals for this new overlay only. Earlier P/Q/R artifacts are preserved unchanged.
- Normal opening strength is 12+ OR Rule20>=20 in every seat. A positive strength result may leave the denomination unknown. Exact6-major+5-minor boundaries remain UNRESOLVED even with strength, as C expressly requests.
- The broader1NT wording does not unambiguously enumerate every shape. Canonical balanced shapes are a supported subset, including5332 five-card major; exactly nine major cards is excluded. Other shapes and >9-major interpretation remain unknown when in range.
- Weak two-suited candidates never gain a definite recommendation from incomplete honor quality.5-major+6-minor is directly covered; unapproved reverse6-5/6-6 orientations remain unknown rather than adopted. Relative range guidance is not turned into a suit-quality score.
- Multi weak uses only the current G examples for affirmative quality/strength: exact5HCP favorable with Q or K, or exact7HCP unfavorable with seven-card KJT/QJT. The corresponding unfavorable six-card examples are negative. Other valid-length combinations are unknown; no complete range or older generic quality table is silently imported.
- An explicitly allowed Multi weak branch is recorded as positive evidence, but Multi-versus-preempt level selection remains unresolved under K. A branch match is not an invented priority rule.
- Strong-minor unbalanced uses the canonical unbalanced category. Canonical6322 is semi-balanced, so its partnership applicability remains unknown rather than silently interpreting not-balanced as unbalanced.
- Seven-card strong-minor examples match named honor/intermediate patterns; unspecified low spots may include9 in KJT/QJT/AT/KT examples. Other patterns remain unknown.
- 22-HCP strong-suit examples are sufficient patterns; because the list says include, unlisted honor combinations remain unknown. No five-card suit, or a five-card suit with no A/K/Q/J, excludes route2; ten alone is not an honor.
- Playing-trick table applies to named short honor holdings (up to3 cards) and exact six-card AKQxxx. No long-suit extrapolation, spot-only zero, void value, or unlisted honor value is added. An unapproved component makes a needed total unknown.
- Route3 Strong2C and strong-minor Multi can both fit a test hand; unlike the expressly stated22-HCP balanced priority, their mutual priority is not specified. That overlap remains unresolved.
- Preempt candidates conservatively include six-or-longer weak suits; numerical approximate ranges do not force a final level. No five-card preempt family is activated by this consolidation or retained earlier six/seven-card policy.
- Pass is only the complete conjunction of12 explicit negative family checks. The requested individual-review groups retain an UNKNOWN guard when opening strength has not independently resolved them. No old Pass signature is used as a blanket override.
- Review queues B/C include all requested shapes, even if an explicit approved rule already proves opening strength. Their tables retain classification and unresolved details for case-by-case review; queue A is restricted to unresolved11+HCP.

Canonical balanced shapes come from `bridge/evaluation.py`:4333,4432,5332. Canonical semi-balanced shapes are5422 and6322. Existing `bridge/sayc.py` 2NT is20–21 balanced and permits a five-card major; current partnership Multi balanced changes both call meaning and upper range. Existing production Strong2C still uses22+HCP; the new23+/conditional22 audit does not alter it.

The approved PT table is stored in JSON. QJ is exactly0.25. Values are used only when the hand needs route3 and every required holding is covered. Low-HCP ordinary hands exclude all three new Strong2C routes by their explicit gates; this resolves the old blanket strong-family UNKNOWN without estimating their tricks.

## Population classifications and provenance

| Classification | Count |
|---|---:|
| OPENING_SUPPORTED | 48 |
| PARTNERSHIP_TREATMENT_SUPPORTED | 0 |
| PASS_SUPPORTED | 440 |
| UNRESOLVED | 128 |

All616 records are in JSON, with actual hand, dealer/actor, absolute and relative vulnerability, HCP, shape class, S/H/D/C lengths and holdings, named honors, production ABSTAIN/code, all 12 family checks and their provenance/reason, matched families, unresolved blockers and supported call where known.

All decisions are actual first-seat dealer decisions with empty auction. There are no actual later-seat cases in this population; later-seat boundary tests use synthetic unit-test fixtures, never invented population records. No20+HCP Multi/Strong2C test fixture is added to the616.

There are 49 affirmative normal-strength hands. Deal739 (`AK8532.-.A8632.92`,11HCP,6S+5D) remains UNRESOLVED because sectionC explicitly leaves that suit-choice boundary to judgment. The other 48 have opening entitlement; only the explicit covered selectors receive a concrete call. A null call is intentionally not an invented denomination.

The 440 Pass results each have all 12 checks NEGATIVE. None has an UNKNOWN check or a review dependency. This is a bounded audit proof against the currently specified families, not a production fallback rule. The 128 unresolved records retain their blockers; none is converted to Pass because production failed to match.

## Review queues

Queues overlap. A is unresolved11+HCP only; B/C list every hand in the requested numeric/shape group, including explicitly supported opening cases. D–H record unresolved family dependencies even where independent opening strength is known. The tables support individual review and do not choose an unsupported call.

| Queue | Count |
|---|---:|
| A_11plus_unresolved | 59 |
| B_5to10_two_fives | 19 |
| C_above5_six_cards | 36 |
| D_weak_two_suited_quality | 13 |
| E_multi_weak | 23 |
| F_preempt | 51 |
| G_strong_2c_playing_tricks | 0 |
| H_later_seat | 0 |

### A_11plus_unresolved

S/H/D/C order. Every row is first seat; production ABSTAIN. “—” means no supported call.

| Deal | Dealer/actor | Vuln / relative | Hand | HCP | S/H/D/C | R20 | Audit result / call | Unresolved questions |
|---:|---|---|---|---:|---|---:|---|---|
| 9 | E/E | NS / favorable | `Q852.A2.J92.A642` | 11 | 4/2/3/4 | 19 | UNRESOLVED / — | individual_review |
| 23 | W/W | Both / equal-vulnerable | `AK4.JT2.KT6.8754` | 11 | 3/3/3/4 | 18 | UNRESOLVED / — | individual_review |
| 26 | S/S | EW / favorable | `J.T874.AJ72.AJ73` | 11 | 1/4/4/4 | 19 | UNRESOLVED / — | individual_review |
| 30 | S/S | EW / favorable | `AJ62.62.K32.K862` | 11 | 4/2/3/4 | 19 | UNRESOLVED / — | individual_review |
| 32 | N/N | None / equal-nonvulnerable | `KQJ76.AJ3.T3.T72` | 11 | 5/3/2/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 53 | E/E | NS / favorable | `J53.T5.KJ7.KQJ73` | 11 | 3/2/3/5 | 19 | UNRESOLVED / — | individual_review |
| 69 | E/E | NS / favorable | `T964.A52.74.AQJ7` | 11 | 4/3/2/4 | 19 | UNRESOLVED / — | individual_review |
| 72 | N/N | None / equal-nonvulnerable | `K86.AT6.KT76.J74` | 11 | 3/3/4/3 | 18 | UNRESOLVED / — | individual_review |
| 75 | W/W | Both / equal-vulnerable | `J97.AQ874.54.A65` | 11 | 3/5/2/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 78 | S/S | EW / favorable | `Q9853.A98.K63.Q5` | 11 | 5/3/3/2 | 19 | UNRESOLVED / — | concentration, individual_review |
| 84 | N/N | None / equal-nonvulnerable | `Q5.972.KQ7.A9873` | 11 | 2/3/3/5 | 19 | UNRESOLVED / — | individual_review |
| 107 | W/W | Both / equal-vulnerable | `K65.A87.J3.QJ753` | 11 | 3/3/2/5 | 19 | UNRESOLVED / — | individual_review |
| 109 | E/E | NS / favorable | `QT.A9864.A65.J95` | 11 | 2/5/3/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 113 | E/E | NS / favorable | `Q862.AQ74.96.K82` | 11 | 4/4/2/3 | 19 | UNRESOLVED / — | individual_review |
| 163 | W/W | Both / equal-vulnerable | `KJT3.A543.KT5.T2` | 11 | 4/4/3/2 | 19 | UNRESOLVED / — | individual_review |
| 168 | N/N | None / equal-nonvulnerable | `K62.A873.Q87.Q73` | 11 | 3/4/3/3 | 18 | UNRESOLVED / — | individual_review |
| 171 | W/W | Both / equal-vulnerable | `A654.J96.QJT.K86` | 11 | 4/3/3/3 | 18 | UNRESOLVED / — | individual_review |
| 182 | S/S | EW / favorable | `J2.Q874.AQT7.QT7` | 11 | 2/4/4/3 | 19 | UNRESOLVED / — | individual_review |
| 189 | E/E | NS / favorable | `KT95.KJ5.8532.AT` | 11 | 4/3/4/2 | 19 | UNRESOLVED / — | individual_review |
| 216 | N/N | None / equal-nonvulnerable | `962.Q43.AKQ6.975` | 11 | 3/3/4/3 | 18 | UNRESOLVED / — | individual_review |
| 255 | W/W | Both / equal-vulnerable | `82.AJT.KT2.QJ985` | 11 | 2/3/3/5 | 19 | UNRESOLVED / — | individual_review |
| 260 | N/N | None / equal-nonvulnerable | `43.A93.QJT75.A32` | 11 | 2/3/5/3 | 19 | UNRESOLVED / — | individual_review |
| 286 | S/S | EW / favorable | `A84.Q63.JT97.KJ2` | 11 | 3/3/4/3 | 18 | UNRESOLVED / — | individual_review |
| 320 | N/N | None / equal-nonvulnerable | `T2.K86.J7532.AK4` | 11 | 2/3/5/3 | 19 | UNRESOLVED / — | individual_review |
| 329 | E/E | NS / favorable | `AJ832.63.Q94.AT6` | 11 | 5/2/3/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 344 | N/N | None / equal-nonvulnerable | `965.QJ3.K43.AJT5` | 11 | 3/3/3/4 | 18 | UNRESOLVED / — | individual_review |
| 351 | W/W | Both / equal-vulnerable | `AT5.K6.QT8.QT984` | 11 | 3/2/3/5 | 19 | UNRESOLVED / — | individual_review |
| 359 | W/W | Both / equal-vulnerable | `QT74.4.AJT8.KJ73` | 11 | 4/1/4/4 | 19 | UNRESOLVED / — | individual_review |
| 364 | N/N | None / equal-nonvulnerable | `9876.AQT.A7.JT63` | 11 | 4/3/2/4 | 19 | UNRESOLVED / — | individual_review |
| 366 | S/S | EW / favorable | `AKQ3.QT74.65.863` | 11 | 4/4/2/3 | 19 | UNRESOLVED / — | individual_review |
| 405 | E/E | NS / favorable | `KJ92.974.K2.A743` | 11 | 4/3/2/4 | 19 | UNRESOLVED / — | individual_review |
| 444 | N/N | None / equal-nonvulnerable | `KT8.KT95.QJ7.QT9` | 11 | 3/4/3/3 | 18 | UNRESOLVED / — | individual_review |
| 488 | N/N | None / equal-nonvulnerable | `J62.A7652.Q6.A72` | 11 | 3/5/2/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 489 | E/E | NS / favorable | `KQ6.AJT5.65.JT32` | 11 | 3/4/2/4 | 19 | UNRESOLVED / — | individual_review |
| 509 | E/E | NS / favorable | `T5.AK742.AT7.T93` | 11 | 2/5/3/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 528 | N/N | None / equal-nonvulnerable | `AT75.AK87.T964.6` | 11 | 4/4/4/1 | 19 | UNRESOLVED / — | individual_review |
| 551 | W/W | Both / equal-vulnerable | `AT97.Q.J742.AT94` | 11 | 4/1/4/4 | 19 | UNRESOLVED / — | individual_review |
| 591 | W/W | Both / equal-vulnerable | `743.A4.Q987.AJT8` | 11 | 3/2/4/4 | 19 | UNRESOLVED / — | individual_review |
| 601 | E/E | NS / favorable | `KQJ54.983.AJ5.75` | 11 | 5/3/3/2 | 19 | UNRESOLVED / — | concentration, individual_review |
| 638 | S/S | EW / favorable | `K5.JT2.T86.AK853` | 11 | 2/3/3/5 | 19 | UNRESOLVED / — | individual_review |
| 650 | S/S | EW / favorable | `K76.QT72.K52.K75` | 11 | 3/4/3/3 | 18 | UNRESOLVED / — | individual_review |
| 668 | N/N | None / equal-nonvulnerable | `T98.AKQT6.94.Q63` | 11 | 3/5/2/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 674 | S/S | EW / favorable | `J73.J98.A97.AJ84` | 11 | 3/3/3/4 | 18 | UNRESOLVED / — | individual_review |
| 678 | S/S | EW / favorable | `A74.JT5.AT63.Q97` | 11 | 3/3/4/3 | 18 | UNRESOLVED / — | individual_review |
| 728 | N/N | None / equal-nonvulnerable | `JT532.76.AK5.K82` | 11 | 5/2/3/3 | 19 | UNRESOLVED / — | concentration, individual_review |
| 739 | W/W | Both / equal-vulnerable | `AK8532.-.A8632.92` | 11 | 6/0/5/2 | 22 | UNRESOLVED / — | natural_choice |
| 746 | S/S | EW / favorable | `654.KQ3.Q96.A654` | 11 | 3/3/3/4 | 18 | UNRESOLVED / — | individual_review |
| 751 | W/W | Both / equal-vulnerable | `9764.KQ52.A83.Q5` | 11 | 4/4/3/2 | 19 | UNRESOLVED / — | individual_review |
| 758 | S/S | EW / favorable | `43.J72.AKQ3.J963` | 11 | 2/3/4/4 | 19 | UNRESOLVED / — | individual_review |
| 786 | S/S | EW / favorable | `QJ32.QT52.K.K732` | 11 | 4/4/1/4 | 19 | UNRESOLVED / — | individual_review |
| 804 | N/N | None / equal-nonvulnerable | `Q962.943.T32.AKQ` | 11 | 4/3/3/3 | 18 | UNRESOLVED / — | individual_review |
| 815 | W/W | Both / equal-vulnerable | `KJT9.863.A986.K5` | 11 | 4/3/4/2 | 19 | UNRESOLVED / — | individual_review |
| 852 | N/N | None / equal-nonvulnerable | `QT82.KQJT.T73.K8` | 11 | 4/4/3/2 | 19 | UNRESOLVED / — | individual_review |
| 858 | S/S | EW / favorable | `AK95.94.T842.KJ9` | 11 | 4/2/4/3 | 19 | UNRESOLVED / — | individual_review |
| 959 | W/W | Both / equal-vulnerable | `KJ64.AK2.54.8542` | 11 | 4/3/2/4 | 19 | UNRESOLVED / — | individual_review |
| 970 | S/S | EW / favorable | `J74.AQJ52.K52.84` | 11 | 3/5/3/2 | 19 | UNRESOLVED / — | concentration, individual_review |
| 976 | N/N | None / equal-nonvulnerable | `865.Q3.K9743.AQ9` | 11 | 3/2/5/3 | 19 | UNRESOLVED / — | individual_review |
| 978 | S/S | EW / favorable | `Q73.53.A92.KQ943` | 11 | 3/2/3/5 | 19 | UNRESOLVED / — | individual_review |
| 992 | N/N | None / equal-nonvulnerable | `T5.J7543.AK7.K82` | 11 | 2/5/3/3 | 19 | UNRESOLVED / — | concentration, individual_review |

### B_5to10_two_fives

S/H/D/C order. Every row is first seat; production ABSTAIN. “—” means no supported call.

| Deal | Dealer/actor | Vuln / relative | Hand | HCP | S/H/D/C | R20 | Audit result / call | Unresolved questions |
|---:|---|---|---|---:|---|---:|---|---|
| 52 | N/N | None / equal-nonvulnerable | `KT984.QJ986.9.42` | 6 | 5/5/1/2 | 16 | UNRESOLVED / — | individual_review |
| 70 | S/S | EW / favorable | `A9842.98732.K83.-` | 7 | 5/5/3/0 | 17 | UNRESOLVED / — | individual_review |
| 220 | N/N | None / equal-nonvulnerable | `T.K5.T8752.AJ954` | 8 | 1/2/5/5 | 18 | UNRESOLVED / — | weak_two_suited, individual_review |
| 235 | W/W | Both / equal-vulnerable | `Q53.T7432.-.QJ532` | 5 | 3/5/0/5 | 15 | UNRESOLVED / — | individual_review |
| 275 | W/W | Both / equal-vulnerable | `JT972.93.Q9543.K` | 6 | 5/2/5/1 | 16 | UNRESOLVED / — | weak_two_suited, individual_review |
| 319 | W/W | Both / equal-vulnerable | `J9762.9.Q7.QT762` | 5 | 5/1/2/5 | 15 | UNRESOLVED / — | individual_review |
| 409 | E/E | NS / favorable | `Q.43.T7543.A7642` | 6 | 1/2/5/5 | 16 | UNRESOLVED / — | weak_two_suited, individual_review |
| 434 | S/S | EW / favorable | `98732.8.AQ862.97` | 6 | 5/1/5/2 | 16 | UNRESOLVED / — | weak_two_suited, individual_review |
| 477 | E/E | NS / favorable | `852.-.Q9852.KJT96` | 6 | 3/0/5/5 | 16 | UNRESOLVED / — | weak_two_suited, individual_review |
| 606 | S/S | EW / favorable | `A.52.Q9643.JT543` | 7 | 1/2/5/5 | 17 | UNRESOLVED / — | weak_two_suited, individual_review |
| 700 | N/N | None / equal-nonvulnerable | `T9763.5.KQT64.A8` | 9 | 5/1/5/2 | 19 | UNRESOLVED / — | weak_two_suited, individual_review |
| 736 | N/N | None / equal-nonvulnerable | `Q8642.Q.Q8532.AT` | 10 | 5/1/5/2 | 20 | OPENING_SUPPORTED / 1S | None under explicit approvals; review entry retained as requested |
| 766 | S/S | EW / favorable | `QJ653.QT5.QT976.-` | 7 | 5/3/5/0 | 17 | UNRESOLVED / — | weak_two_suited, individual_review |
| 778 | S/S | EW / favorable | `JT974.9.Q6.AJ943` | 8 | 5/1/2/5 | 18 | UNRESOLVED / — | weak_two_suited, individual_review |
| 791 | W/W | Both / equal-vulnerable | `T3.A9642.AJ642.5` | 9 | 2/5/5/1 | 19 | UNRESOLVED / — | weak_two_suited, individual_review |
| 842 | S/S | EW / favorable | `7.QJT84.KT876.J7` | 7 | 1/5/5/2 | 17 | UNRESOLVED / — | weak_two_suited, individual_review |
| 888 | N/N | None / equal-nonvulnerable | `JT753.K9742.6.AT` | 8 | 5/5/1/2 | 18 | UNRESOLVED / — | individual_review |
| 890 | S/S | EW / favorable | `Q8654.QJ964.4.A2` | 9 | 5/5/1/2 | 19 | UNRESOLVED / — | individual_review |
| 983 | W/W | Both / equal-vulnerable | `AQ962.6.J9872.Q6` | 9 | 5/1/5/2 | 19 | UNRESOLVED / — | weak_two_suited, individual_review |

### C_above5_six_cards

S/H/D/C order. Every row is first seat; production ABSTAIN. “—” means no supported call.

| Deal | Dealer/actor | Vuln / relative | Hand | HCP | S/H/D/C | R20 | Audit result / call | Unresolved questions |
|---:|---|---|---|---:|---|---:|---|---|
| 42 | S/S | EW / favorable | `AKJ954.QJ65.42.5` | 11 | 6/4/2/1 | 21 | OPENING_SUPPORTED / — | multi_weak |
| 43 | W/W | Both / equal-vulnerable | `85.Q72.43.KJT743` | 6 | 2/3/2/6 | 15 | UNRESOLVED / — | preempt, individual_review |
| 139 | W/W | Both / equal-vulnerable | `T8.32.Q75.AJ9852` | 7 | 2/2/3/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 147 | W/W | Both / equal-vulnerable | `J2.653.JT.AQT532` | 8 | 2/3/2/6 | 17 | UNRESOLVED / — | preempt, individual_review |
| 202 | S/S | EW / favorable | `K754.3.43.KT9653` | 6 | 4/1/2/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 227 | W/W | Both / equal-vulnerable | `97.974.92.KQJT95` | 6 | 2/3/2/6 | 15 | UNRESOLVED / — | preempt, individual_review |
| 233 | E/E | NS / favorable | `-.K64.Q963.JT9843` | 6 | 0/3/4/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 246 | S/S | EW / favorable | `K72.KQ3.T.KT8763` | 11 | 3/3/1/6 | 20 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 297 | E/E | NS / favorable | `J954.AQJT43.8.K5` | 11 | 4/6/1/2 | 21 | OPENING_SUPPORTED / — | multi_weak |
| 299 | W/W | Both / equal-vulnerable | `AKJ82.T.3.Q87543` | 10 | 5/1/1/6 | 21 | OPENING_SUPPORTED / 1S | None under explicit approvals; review entry retained as requested |
| 321 | E/E | NS / favorable | `A93.6.832.QJT852` | 7 | 3/1/3/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 361 | E/E | NS / favorable | `74.5.K752.QJT432` | 6 | 2/1/4/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 394 | S/S | EW / favorable | `K2.JT9542.43.AK4` | 11 | 2/6/2/3 | 20 | OPENING_SUPPORTED / — | multi_weak |
| 396 | N/N | None / equal-nonvulnerable | `86.T97.Q2.AQ6532` | 8 | 2/3/2/6 | 17 | UNRESOLVED / — | preempt, individual_review |
| 401 | E/E | NS / favorable | `-.T8632.86.AK9854` | 7 | 0/5/2/6 | 18 | UNRESOLVED / — | weak_two_suited, preempt, individual_review |
| 415 | W/W | Both / equal-vulnerable | `AK8.85.76.QT8432` | 9 | 3/2/2/6 | 18 | UNRESOLVED / — | preempt, individual_review |
| 453 | E/E | NS / favorable | `-.KJ7.AQJ972.9876` | 11 | 0/3/6/4 | 21 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 461 | E/E | NS / favorable | `94.7.AKQ9.J87543` | 10 | 2/1/4/6 | 20 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 471 | W/W | Both / equal-vulnerable | `952.K92.5.KQJT95` | 9 | 3/3/1/6 | 18 | UNRESOLVED / — | preempt, individual_review |
| 472 | N/N | None / equal-nonvulnerable | `J4.KJ52.7.AT8643` | 9 | 2/4/1/6 | 19 | UNRESOLVED / — | preempt, individual_review |
| 492 | N/N | None / equal-nonvulnerable | `KQ932.KJT743.Q4.-` | 11 | 5/6/2/0 | 22 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 497 | E/E | NS / favorable | `K43.2.J73.A97542` | 8 | 3/1/3/6 | 17 | UNRESOLVED / — | preempt, individual_review |
| 507 | W/W | Both / equal-vulnerable | `AQJ7.8.94.QT9742` | 9 | 4/1/2/6 | 19 | UNRESOLVED / — | preempt, individual_review |
| 540 | N/N | None / equal-nonvulnerable | `Q42.AQ8632.7.QJ6` | 11 | 3/6/1/3 | 20 | OPENING_SUPPORTED / — | multi_weak |
| 590 | S/S | EW / favorable | `T82.72.A2.Q98532` | 6 | 3/2/2/6 | 15 | UNRESOLVED / — | preempt, individual_review |
| 621 | E/E | NS / favorable | `75.Q97.Q2.Q97653` | 6 | 2/3/2/6 | 15 | UNRESOLVED / — | preempt, individual_review |
| 686 | S/S | EW / favorable | `T765.J9.8.AKT963` | 8 | 4/2/1/6 | 18 | UNRESOLVED / — | preempt, individual_review |
| 719 | W/W | Both / equal-vulnerable | `QJ76.K.QJT876.QT` | 11 | 4/1/6/2 | 21 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 739 | W/W | Both / equal-vulnerable | `AK8532.-.A8632.92` | 11 | 6/0/5/2 | 22 | UNRESOLVED / — | natural_choice |
| 756 | N/N | None / equal-nonvulnerable | `92.953.T4.AK8532` | 7 | 2/3/2/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 845 | E/E | NS / favorable | `Q865.A82.-.KQ8754` | 11 | 4/3/0/6 | 21 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 864 | N/N | None / equal-nonvulnerable | `52.Q6.AKQT97.T75` | 11 | 2/2/6/3 | 20 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 867 | W/W | Both / equal-vulnerable | `A.J93.A72.T98643` | 9 | 1/3/3/6 | 18 | UNRESOLVED / — | preempt, individual_review |
| 869 | E/E | NS / favorable | `T3.Q6.J92.AT9863` | 7 | 2/2/3/6 | 16 | UNRESOLVED / — | preempt, individual_review |
| 898 | S/S | EW / favorable | `A.9874.AQJ765.52` | 11 | 1/4/6/2 | 21 | OPENING_SUPPORTED / — | None under explicit approvals; review entry retained as requested |
| 974 | S/S | EW / favorable | `QJT962.JT3.AJ4.Q` | 11 | 6/3/3/1 | 20 | OPENING_SUPPORTED / — | multi_weak |

### D_weak_two_suited_quality

Deal indices: 220, 275, 401, 409, 434, 477, 606, 700, 766, 778, 791, 842, 983. Full cards, context, holdings and question reasons are in JSON.

### E_multi_weak

Deal indices: 3, 42, 118, 119, 197, 297, 310, 317, 394, 457, 500, 540, 542, 607, 645, 697, 709, 743, 775, 795, 844, 862, 974. Full cards, context, holdings and question reasons are in JSON.

### F_preempt

Deal indices: 36, 43, 65, 118, 119, 135, 139, 147, 148, 195, 197, 202, 227, 233, 245, 310, 317, 321, 361, 396, 401, 415, 457, 471, 472, 480, 497, 500, 506, 507, 542, 590, 599, 607, 611, 621, 686, 697, 729, 743, 756, 775, 795, 844, 862, 867, 869, 895, 919, 927, 985. Full cards, context, holdings and question reasons are in JSON.

### G_strong_2c_playing_tricks

No real cases in this population. This does not establish that the family is globally complete.

### H_later_seat

No real cases in this population. This does not establish that the family is globally complete.

## Family states — overlaps are retained

| Family | POSITIVE | NEGATIVE | UNKNOWN |
|---|---:|---:|---:|
| natural_strength | 49 | 567 | 0 |
| natural_choice | 10 | 605 | 1 |
| concentration | 0 | 604 | 12 |
| one_nt | 0 | 616 | 0 |
| weak_two_suited | 0 | 603 | 13 |
| multi_weak | 0 | 593 | 23 |
| multi_minor | 0 | 616 | 0 |
| multi_nt | 0 | 616 | 0 |
| strong_2c | 0 | 616 | 0 |
| preempt | 0 | 565 | 51 |
| later_seat | 0 | 616 | 0 |
| individual_review | 0 | 519 | 97 |

## Comparison with unchanged Phase 29Q

| Previous classification | Current classification | Count |
|---|---|---:|
| OPEN_SUPPORTED | OPENING_SUPPORTED | 48 |
| OPEN_SUPPORTED | UNRESOLVED | 13 |
| OTHER_UNRESOLVED | PASS_SUPPORTED | 419 |
| OTHER_UNRESOLVED | UNRESOLVED | 46 |
| PARTNERSHIP_TREATMENT | PASS_SUPPORTED | 2 |
| PARTNERSHIP_TREATMENT | UNRESOLVED | 14 |
| PASS_SUPPORTED | PASS_SUPPORTED | 16 |
| PASS_SUPPORTED | UNRESOLVED | 1 |
| PREEMPT_UNRESOLVED | UNRESOLVED | 6 |
| PROTECTED_UNRESOLVED | PASS_SUPPORTED | 3 |
| PROTECTED_UNRESOLVED | UNRESOLVED | 35 |
| WEAK_MULTI_UNRESOLVED | UNRESOLVED | 13 |

Changes come from the explicit latest policy: bounded Strong2C routes; 11-HCP concentration now unresolved unless Rule20 independently proves strength; weak-treatment ranges/quality no longer presumed from every below12 exact5–5 shape; individual review for specified boundary groups. Previous P/Q/R data and decisions remain historical evidence, not edited facts. Every transition includes its actual deal indices in JSON.

## Remaining partnership questions

1. Define concentration for 11-HCP major/minor exceptions and later-seat openings, and resolve the6-major+5-minor selector.
2. Enumerate the broader1NT shapes and whether the nine-major exclusion means exactly9 or9+. Clarify6322 for strong-minor Multi and5422 for balanced Multi.
3. Define weak two-suited suit quality, exact range boundaries by relative vulnerability, and uncovered6–5/6–6 orientations. The current statements permit candidates but do not decide every hand.
4. Complete Multi weak strength/quality cases outside the explicit examples and select Multi versus3M/preempt level where both are possible.
5. Supply missing PT holding values and clarify route3 Strong2C versus strong-minor Multi priority. Do not infer values for unlisted holdings.
6. Review the A–C tables case-by-case. No production integration is performed or recommended by this audit.

## Validation and final repository state

**Focused Phase 29S tests: 39 passed in 16.39s. Production route count: 45.**

```text
python -m pytest -q -p no:cacheprovider tests/test_bridge_phase29s_opening_policy_consolidation_audit.py
```

Tests cover deterministic616, every-seat Rule20, natural priority, exact natural suit choices, weak two-suited unknown quality and third-seat exception, Multi weak boundaries, strong-minor seven-card examples and side-suit exclusions,20–22 balanced branch,22-HCP2C priority,1NT shape ambiguity,QJ PT0.25, missing PT values, complete-negative Pass evidence and every review queue. Synthetic boundary fixtures are not represented as real sample hands.

Files created (no pre-existing file modified):

- `bridge/opening_policy_consolidation_audit.py`
- `bridgelab_phase29s_opening_policy_consolidation_audit.json`
- `bridgelab_phase29s_opening_policy_consolidation_audit.md`
- `tests/test_bridge_phase29s_opening_policy_consolidation_audit.py`

`git diff --check`: clean. `git diff --stat`: empty because all 16 audit additions are untracked. Explicit trailing-whitespace/final-newline checks cover the four new files. `git status --short`:

```text
?? bridgelab-toolkit/bridge/nisim_nily_opening_pass_contract.py
?? bridgelab-toolkit/bridge/opening_pass_nisim_nily_policy_audit.py
?? bridgelab-toolkit/bridge/opening_policy_consolidation_audit.py
?? bridgelab-toolkit/bridge/strong_two_club_policy_audit.py
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.json
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.md
?? bridgelab-toolkit/bridgelab_phase29q_nisim_nily_opening_pass_contract.json
?? bridgelab-toolkit/bridgelab_phase29q_nisim_nily_opening_pass_contract.md
?? bridgelab-toolkit/bridgelab_phase29r_strong_two_club_policy_audit.json
?? bridgelab-toolkit/bridgelab_phase29r_strong_two_club_policy_audit.md
?? bridgelab-toolkit/bridgelab_phase29s_opening_policy_consolidation_audit.json
?? bridgelab-toolkit/bridgelab_phase29s_opening_policy_consolidation_audit.md
?? bridgelab-toolkit/tests/test_bridge_phase29p_nisim_nily_opening_policy_audit.py
?? bridgelab-toolkit/tests/test_bridge_phase29q_nisim_nily_opening_pass_contract.py
?? bridgelab-toolkit/tests/test_bridge_phase29r_strong_two_club_policy_audit.py
?? bridgelab-toolkit/tests/test_bridge_phase29s_opening_policy_consolidation_audit.py
```

Existing ignored `.pytest_cache` access warnings remain. No tracked/production file changed; all 12 P/Q/R hashes match. No full regression, commit or push. Stopped after the Phase 29S audit.
