# Phase 29P — nisim–nily opening policy / real-hand classification audit

**Result: 17 / 616 are positive PASS_SUPPORTED under the explicit Phase 29P examples; 599 are not safe for a Pass rule.** Of those599,77 have affirmative opening/treatment evidence and522 remain unresolved. This is an audit overlay, not a production recommendation or deployment approval.

## A. Repository and scope

- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`; toolkit child `bridgelab-toolkit`.
- Branch `codex/phase18b`; local, tracking and live remote HEAD `c70c0f330d641964308e0e98500e8f47c29699a6`; ahead/behind `0/0`.
- Starting `git status --short`: empty. Git reports access warnings for existing ignored `.pytest_cache` directories; no source changes were present.
- No existing file was edited. No production bidding, route, auction, GUI or simulator behavior changed. No full regression, commit or push.
- Authority: user-supplied Phase29P sectionsC/D. Earlier29M–29O remain historical snapshots. No external source was fetched or authenticated.

## B. Existing implementation inventory

Paths below are toolkit-relative for Python and git-root-relative for `knowledge/`. All source citations are repository provenance, not external authority authentication. The introductory sayc.py docstring is stale about preempt/strong coverage; the executable classes/registry establish the inventory.

| Item | File and symbol | Current conditions | Recommendation | System/treatment gating | Source/provenance |
|---|---|---|---|---|---|
| Normal 1H/1S | `bridge/sayc.py` — `SaycOneHeartOpeningRule / SaycOneSpadeOpeningRule` | 12–21 HCP, >=5 in bid major, strictly longer than other major; reserve 22+ strong and 20–21 balanced 2NT | 1H / 1S | SAYC profile; unopened; no nisim-nily option | knowledge/bidding/systems/sayc.md#Five-Card Majors; natural-bids/opening-bids/1-heart.md and 1-spade.md |
| Normal 1C/1D | `bridge/sayc.py` — `SaycOneClubOpeningRule / SaycOneDiamondOpeningRule` | 12–21; no five-card major or covered NT/strong family; longer minor >=3; equal 3–3 -> C, equal 4–4 -> D; equal 5–5 not selected | 1C / 1D | SAYC profile; unopened | knowledge/bidding/systems/sayc.md#Better Minor |
| 1NT | `bridge/sayc.py` — `SaycOneNotrumpOpeningRule` | 15–17; canonical balanced shape; no five-card major | 1NT | SAYC profile; unopened; no optional adjustment enabled | knowledge/bidding/systems/sayc.md#Opening Bid Requirements; natural-bids/opening-bids/1nt-opening.md |
| Strong opening | `bridge/sayc.py` — `SaycStrongTwoClubOpeningRule` | 22+ HCP only; 9+ playing-trick branch explicitly unevaluated | 2C | SAYC profile; unopened | knowledge/bidding/systems/sayc.md#Strong 2♣ Opening |
| Rule20 | `bridge/nisim_nily_opening_policy.py` — `assess_rule_of_20 / build_nisim_nily_opening_policy` | Canonical HCP + two longest >=20; historical 29M approval primarily11; 29P C2 broadens audit entitlement | No production call; strength helper only | Declarative partnership knowledge, not router activated | User 29M E; user 29P C2; knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md |
| Weak Two / 2D | `bridge/sayc.py` — `SaycWeakTwoOpeningRule; sayc_opening_rules` | 6–10 HCP; exactly6 D/H/S; exactly one qualifying D/H/S; no seven-card suit; no quality or vulnerability test in this implementation | Natural 2D / 2H / 2S | SAYC profile; unopened; no Multi exclusion option | knowledge/bidding/systems/sayc.md#Weak Two Openings |
| Multi 2D | `knowledge/bidding/conventions/opening-bids/two-diamond-multi.md` — `Reference article only; no production class/route/option` | Reference normally six-card major, typical6–10, alternatives5–10/6–11, qualitative quality/vulnerability; optional strong variants | No implemented Multi call | User29P establishes partnership plays Multi; variant and qualifiers unresolved | Draft repository article; not a selected partnership contract |
| Partnership 2H / 2S | `bridge/nisim_nily_opening_policy.py; new bridge/opening_pass_nisim_nily_policy_audit.py` — `Historical policy versus classify_nisim_nily_hand audit overlay` | 29M prefers major with opening values; new29P C8 exact5H+5minor /5S+5minor below normal strength | Audit-only 2H / 2S | nisim-nily only, not generic SAYC; no production treatment activation | User29P C8/D |
| 2NT natural / weak two-suited | `bridge/sayc.py; new bridge/opening_pass_nisim_nily_policy_audit.py` — `SaycTwoNotrumpOpeningRule / classify_nisim_nily_hand` | Production20–21 balanced; audit C8 exact5D+5C below normal strength | Production natural2NT; partnership audit weak2NT | SAYC production vs nisim-nily audit only; no weak2NT option | knowledge/bidding/systems/sayc.md#2NT Opening; user29P C8/D |
| Three-level preempts | `bridge/sayc.py` — `SaycThreeLevelPreemptOpeningRule` | 6–10 HCP, exactly7 bid suit, single seven-card suit; reject any six-card D/H/S; no honor/vulnerability threshold | 3C / 3D / 3H / 3S | SAYC profile; unopened | knowledge/bidding/systems/sayc.md#Three-Level Openings |
| Third/fourth opening seat | `bridge/sayc.py; bridge/sayc_route_configuration.py; bridge/engine_router.py` — `_standard_gate / create_standard_sayc_router / auction_calls` | Raw rules accept all-pass histories with unchanged thresholds. Router opening route matches exactly empty auction; no after-P/P-P/P-P-P opening route | No seat-specific production opening policy; routed later-seat positions unsupported | No light-opening option; do not conflate raw rule eligibility and routing | knowledge/bidding/principles/bidding-fundamentals/seat-position.md is reference only; user29P C4/D supplies exact examples |
| System/partnership options | `bridge/bidding_rules.py; bridge/system_profiles.py; bridge/major_response_options.py` — `SystemContext / classify_system_profile / major_raise_style / forcing_one_notrump_treatment / two_over_one_treatment` | Opaque option tuples; recognized SAYC, TWO_OVER_ONE_GF, UNKNOWN; response options major_raise_style, forcing_one_notrump, two_over_one | No new opening recommendation | No nisim-nily profile, Multi or weak55 opening activation | Existing code contracts; response options do not authorize opening changes |
| nisim-nily historical evidence | `bridge/nisim_nily_opening_policy.py; bridge/opening_pass_positive_predicate_audit.py; bridge/opening_pass_safety_evidence_audit.py` — `build_nisim_nily_opening_policy / assess_positive_opening_pass_candidate / build_pass_safety_audit_report` | 29M.1 declarative policy; 29N proposed screen;29O decomposed UNKNOWN evidence; no positive Pass rule | Audit classifications only | Not production adopted | User29M–29O and repository reference evidence; new29P explicit approvals overlay rather than rewrite history |

SAYC natural Weak2D is not nisim–nily Multi2D. Existing 2H/2S weak-six-major meanings likewise cannot be reused for the new partnership 5–5 meanings without explicit activation and precedence design. Strong playing-trick evaluation remains absent; this phase adds no guessed formula.

## C–D. Current approvals and bounded interpretation

- Phase29P user C/D is current partnership evidence, not universal SAYC.
- Named HCP/shape Pass examples are literal approved signatures; no rank pattern is invented. Unnamed 4432 is shape-sorted; named majors are preserved.
- Pass signatures are limited to first/second seat; explicit case17/case18 govern later seats, other light/honor details remain UNKNOWN.
- C8 below normal strength is interpreted against C1 12+ as HCP<12, exact named5+5, no invented lower bound. Rule20/11-major overlap also says open; C8 supplies its explicit treatment call.
- Weak/Multi/preempt candidates identify shapes needing qualification; no implicit6–10 lower bound, quality test or exact call is imported from SAYC.
- The two six-card-minor Pass examples lack identifying cards/HCP/context in the supplied evidence; no blanket minor Pass policy is inferred.
- No vulnerability adjustment is added to the explicitly approved Pass signatures. Broader qualitative source exceptions remain unresolved outside them.

12+ HCP, Rule20>=20 at any HCP under current C2, and11HCP with a five-card major establish opening entitlement. Only exact normal-strength5S5H supplies1S here. Other OPEN_KNOWN hands have no invented denomination. Rule22 and a general Rule15/light-seat formula are not adopted.

The 17 Pass records are supported by four explicitly approved signatures. These direct approvals resolve the earlier broad UNKNOWN only for matching signatures; they do not prove a universal playing-trick exclusion or make every low hand Pass. First/second-seat scope is conservative for the9HCP and8HCP examples because unspecified later-seat light agreements persist.

Case17 and case18 are policy example labels, **not deterministic deal indices17/18**. Tests reuse real generated hands in explicitly counterfactual all-pass seat contexts. They are never reported as actual third/fourth-seat sample rows.

## E. Deterministic population and deliberate selection

`SimulationConfig(seed=100, deal_count=1000)` reproduces616 depth0 opening ABSTAINs, zero simulation errors, zero hand/route reproduction mismatches. Each dealer hand is regenerated with `generate_deal(100 + deal_index)` and compared with the saved simulator step. The existing root-cause auditor reruns all14 opening-rule traces for every one of the616.

The compact table selects **40 real records**, using the earliest three available records per requested stratum/classification, every distinct Pass signature, and notable strength/long-suit boundaries. Selected IDs are deterministic, unique, and all belong to the616. No hand is manufactured.

| Requested stratum | Available in616 |
|---|---:|
| 10-11-borderline | 170 |
| 5-5 | 32 |
| both-minors-5-5 | 5 |
| equal-five-majors | 11 |
| fourth-hand | 0 |
| low-hcp-apparent-pass | 320 |
| major-minor-5-5 | 16 |
| rule20 | 49 |
| seven-card | 10 |
| six-major | 21 |
| six-minor | 39 |
| strong-protected | 40 |
| third-hand | 0 |

**No actual third- or fourth-hand case exists in this population.** Every row is dealer acting first, with empty auction. No22+HCP strong hand occurs among616 (production covers that branch); normal-strength equal-major and protected distribution records supply the available exceptional cases.

## F–G. Compact real-hand table

Hand strings and lengths are S/H/D/C. `top2` lists the two longest lengths. Position1 means empty auction `[]`. Every row has current production result **ABSTAIN**, route `sayc.opening`; JSON stores its exact abstention code and all14 rejection explanations. `R` means existing root cause UNKNOWN/all controlled rules rejected; `E` means the diagnosed equal-major boundary. A dash in the call column means policy does not select a call.

| Deal | Dealer/actor | Vuln | Hand S.H.D.C | HCP | S/H/D/C | top2 | R20 | Position | Production/root | nisim–nily | Call |
|---:|---|---|---|---:|---|---|---:|---:|---|---|---|
| 1 | E/E | NS | `J987.962.94.J943` | 2 | 4/3/2/4 | 4+4 | 10 | 1 | ABSTAIN/R | UNKNOWN | — |
| 2 | S/S | EW | `974.KQT93.53.964` | 5 | 3/5/2/3 | 5+3 | 13 | 1 | ABSTAIN/R | UNKNOWN | — |
| 3 | W/W | Both | `KJT9874.A5.K2.96` | 11 | 7/2/2/2 | 7+2 | 20 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 4 | N/N | None | `854.A9853.J74.K4` | 8 | 3/5/3/2 | 5+3 | 16 | 1 | ABSTAIN/R | UNKNOWN | — |
| 9 | E/E | NS | `Q852.A2.J92.A642` | 11 | 4/2/3/4 | 4+4 | 19 | 1 | ABSTAIN/R | UNKNOWN | — |
| 23 | W/W | Both | `AK4.JT2.KT6.8754` | 11 | 3/3/3/4 | 4+3 | 18 | 1 | ABSTAIN/R | UNKNOWN | — |
| 32 | N/N | None | `KQJ76.AJ3.T3.T72` | 11 | 5/3/2/3 | 5+3 | 19 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 36 | N/N | None | `4.T6.QT98732.K98` | 5 | 1/2/7/3 | 7+3 | 15 | 1 | ABSTAIN/R | PREEMPT_CANDIDATE | — |
| 42 | S/S | EW | `AKJ954.QJ65.42.5` | 11 | 6/4/2/1 | 6+4 | 21 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 43 | W/W | Both | `85.Q72.43.KJT743` | 6 | 2/3/2/6 | 6+3 | 15 | 1 | ABSTAIN/R | PROTECTED_UNRESOLVED | — |
| 52 | N/N | None | `KT984.QJ986.9.42` | 6 | 5/5/1/2 | 5+5 | 16 | 1 | ABSTAIN/R | PROTECTED_UNRESOLVED | — |
| 57 | E/E | NS | `AJ543.AQJ63.74.2` | 12 | 5/5/2/1 | 5+5 | 22 | 1 | ABSTAIN/E | OPEN_KNOWN | 1S |
| 63 | W/W | Both | `72.KT75.QJ72.KJT` | 10 | 2/4/4/3 | 4+4 | 18 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |
| 64 | N/N | None | `98532.JT.QT743.T` | 3 | 5/2/5/1 | 5+5 | 13 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2S |
| 65 | E/E | NS | `43.JT8.QJ8652.87` | 4 | 2/3/6/2 | 6+3 | 13 | 1 | ABSTAIN/R | PROTECTED_UNRESOLVED | — |
| 70 | S/S | EW | `A9842.98732.K83.-` | 7 | 5/5/3/0 | 5+5 | 17 | 1 | ABSTAIN/R | PROTECTED_UNRESOLVED | — |
| 75 | W/W | Both | `J97.AQ874.54.A65` | 11 | 3/5/2/3 | 5+3 | 19 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 78 | S/S | EW | `Q9853.A98.K63.Q5` | 11 | 5/3/3/2 | 5+3 | 19 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 101 | E/E | NS | `KJ3.K973.K4.9743` | 10 | 3/4/2/4 | 4+4 | 18 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |
| 118 | S/S | EW | `T842.QJT9753.4.6` | 3 | 4/7/1/1 | 7+4 | 14 | 1 | ABSTAIN/R | PREEMPT_CANDIDATE | — |
| 119 | W/W | Both | `Q98763.963.T7.84` | 2 | 6/3/2/2 | 6+3 | 11 | 1 | ABSTAIN/R | WEAK_MULTI_CANDIDATE | — |
| 135 | W/W | Both | `94.8.J54.Q976543` | 3 | 2/1/3/7 | 7+3 | 13 | 1 | ABSTAIN/R | PREEMPT_CANDIDATE | — |
| 139 | W/W | Both | `T8.32.Q75.AJ9852` | 7 | 2/2/3/6 | 6+3 | 16 | 1 | ABSTAIN/R | PROTECTED_UNRESOLVED | — |
| 184 | N/N | None | `AKJT7.AKJ74.A54.-` | 20 | 5/5/3/0 | 5+5 | 30 | 1 | ABSTAIN/E | OPEN_KNOWN | 1S |
| 220 | N/N | None | `T.K5.T8752.AJ954` | 8 | 1/2/5/5 | 5+5 | 18 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2NT |
| 228 | N/N | None | `K765.AK9.43.T964` | 10 | 4/3/2/4 | 4+4 | 18 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |
| 235 | W/W | Both | `Q53.T7432.-.QJ532` | 5 | 3/5/0/5 | 5+5 | 15 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2H |
| 275 | W/W | Both | `JT972.93.Q9543.K` | 6 | 5/2/5/1 | 5+5 | 16 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2S |
| 295 | W/W | Both | `A7652.A2.QT.T963` | 10 | 5/2/2/4 | 5+4 | 19 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |
| 297 | E/E | NS | `J954.AQJT43.8.K5` | 11 | 4/6/1/2 | 6+4 | 21 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 299 | W/W | Both | `AKJ82.T.3.Q87543` | 10 | 5/1/1/6 | 6+5 | 21 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 310 | S/S | EW | `2.KT6432.963.865` | 3 | 1/6/3/3 | 6+3 | 12 | 1 | ABSTAIN/R | WEAK_MULTI_CANDIDATE | — |
| 317 | E/E | NS | `83.T87642.AT84.5` | 4 | 2/6/4/1 | 6+4 | 14 | 1 | ABSTAIN/R | WEAK_MULTI_CANDIDATE | — |
| 409 | E/E | NS | `Q.43.T7543.A7642` | 6 | 1/2/5/5 | 5+5 | 16 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2NT |
| 461 | E/E | NS | `94.7.AKQ9.J87543` | 10 | 2/1/4/6 | 6+4 | 20 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 477 | E/E | NS | `852.-.Q9852.KJT96` | 6 | 3/0/5/5 | 5+5 | 16 | 1 | ABSTAIN/R | PARTNERSHIP_TREATMENT | 2NT |
| 613 | E/E | NS | `AKQT8.87532.JT.Q` | 12 | 5/5/2/1 | 5+5 | 22 | 1 | ABSTAIN/E | OPEN_KNOWN | 1S |
| 735 | W/W | Both | `KJ876532.K.QT2.9` | 9 | 8/1/3/1 | 8+3 | 20 | 1 | ABSTAIN/R | OPEN_KNOWN | — |
| 888 | N/N | None | `JT753.K9742.6.AT` | 8 | 5/5/1/2 | 5+5 | 18 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |
| 955 | W/W | Both | `K8653.KQ43.J2.87` | 9 | 5/4/2/2 | 5+4 | 18 | 1 | ABSTAIN/R | PASS_SUPPORTED | P |

| Classification | All616 | Selected table |
|---|---:|---:|
| OPEN_KNOWN | 56 | 12 |
| WEAK_MULTI_CANDIDATE | 14 | 3 |
| PREEMPT_CANDIDATE | 6 | 3 |
| PASS_SUPPORTED | 17 | 6 |
| PARTNERSHIP_TREATMENT | 21 | 6 |
| PROTECTED_UNRESOLVED | 37 | 5 |
| UNKNOWN | 465 | 5 |

The JSON contains all616 rows, not just the table: exact cards, dealer/actor/vulnerability, canonical facts, actual context, production trace/root cause, previous29N class, new classification, provenance, unresolved reasons and supported call.

### Explicit identification by requested disposition

- **OPEN_KNOWN (56)** — deal indices: 3, 32, 42, 57, 66, 75, 77, 78, 91, 109, 111, 121, 180, 184, 246, 247, 277, 297, 299, 329, 346, 394, 403, 453, 461, 470, 488, 492, 504, 509, 540, 571, 601, 613, 623, 634, 645, 668, 703, 709, 719, 728, 735, 739, 748, 776, 832, 845, 864, 898, 925, 930, 970, 974, 992, 997.
- **WEAK_MULTI_CANDIDATE (14)** — deal indices: 119, 310, 317, 457, 500, 542, 607, 697, 743, 775, 795, 844, 862, 927.
- **PREEMPT_CANDIDATE (6)** — deal indices: 36, 118, 135, 148, 197, 480.
- **PASS_SUPPORTED (17)** — deal indices: 63, 101, 228, 295, 433, 456, 494, 616, 618, 628, 793, 825, 847, 882, 888, 904, 955.
- **PARTNERSHIP_TREATMENT (21)** — deal indices: 64, 220, 235, 275, 292, 319, 354, 409, 434, 477, 606, 626, 700, 736, 766, 778, 791, 842, 922, 983, 988.
- **PROTECTED_UNRESOLVED (37)** — deal indices: 43, 52, 65, 70, 139, 147, 195, 202, 227, 233, 245, 321, 361, 396, 401, 415, 471, 472, 484, 497, 506, 507, 563, 590, 599, 611, 621, 686, 729, 756, 867, 869, 890, 895, 919, 958, 985.
- **UNKNOWN (465)** — deal indices: 1, 2, 4, 5, 6, 7, 9, 10, 17, 19, 23, 24, 25, 26, 27, 28, 29, 30, 35, 38, 39, 44, 46, 48, 49, 50, 51, 53, 54, 56, 58, 60, 61, 62, 67, 68, 69, 72, 74, 76, 79, 83, 84, 85, 87, 89, 90, 92, 93, 98, 100, 102, 103, 106, 107, 108, 112, 113, 114, 115, 122, 127, 128, 131, 132, 134, 137, 138, 141, 143, 144, 145, 146, 149, 150, 154, 155, 158, 159, 160, 161, 163, 164, 165, 166, 167, 168, 171, 172, 173, 175, 178, 179, 182, 183, 185, 186, 187, 188, 189, 190, 192, 193, 194, 200, 204, 205, 206, 207, 209, 211, 213, 214, 216, 217, 221, 223, 230, 231, 232, 234, 239, 242, 243, 244, 252, 253, 255, 256, 258, 260, 261, 262, 263, 264, 265, 266, 267, 269, 270, 271, 276, 278, 281, 282, 284, 285, 286, 289, 290, 294, 303, 304, 305, 306, 307, 309, 312, 313, 314, 315, 316, 320, 322, 323, 324, 325, 327, 330, 331, 333, 335, 336, 337, 340, 341, 343, 344, 345, 348, 349, 351, 352, 355, 356, 357, 358, 359, 364, 365, 366, 368, 371, 372, 373, 374, 375, 377, 378, 382, 383, 385, 389, 400, 402, 404, 405, 406, 407, 408, 411, 412, 413, 417, 420, 425, 426, 427, 428, 430, 431, 436, 438, 439, 440, 441, 444, 445, 446, 447, 449, 451, 459, 460, 462, 463, 475, 478, 479, 481, 482, 489, 495, 499, 502, 503, 505, 508, 510, 511, 512, 517, 519, 520, 521, 524, 525, 526, 527, 528, 529, 533, 536, 537, 541, 547, 548, 550, 551, 553, 555, 564, 565, 566, 567, 568, 569, 570, 573, 574, 576, 577, 578, 581, 582, 587, 591, 592, 594, 595, 598, 600, 602, 603, 604, 605, 608, 609, 610, 614, 617, 619, 620, 629, 630, 631, 632, 636, 637, 638, 642, 646, 647, 648, 650, 651, 653, 654, 656, 661, 663, 664, 665, 666, 667, 670, 674, 675, 676, 677, 678, 681, 684, 685, 687, 689, 691, 693, 698, 706, 710, 711, 715, 716, 718, 721, 725, 727, 730, 731, 732, 733, 738, 745, 746, 751, 753, 754, 755, 757, 758, 759, 760, 762, 763, 765, 767, 768, 769, 770, 777, 780, 785, 786, 788, 794, 799, 801, 804, 805, 806, 813, 814, 815, 816, 817, 819, 820, 821, 822, 824, 827, 828, 829, 830, 833, 834, 837, 838, 839, 840, 843, 846, 848, 850, 852, 853, 854, 855, 856, 858, 860, 861, 863, 870, 873, 876, 877, 878, 880, 887, 893, 897, 899, 900, 901, 902, 903, 913, 914, 915, 916, 918, 923, 926, 928, 929, 931, 932, 934, 935, 940, 942, 943, 946, 951, 953, 956, 957, 959, 960, 965, 967, 969, 972, 975, 976, 978, 981, 982, 986, 993, 994, 998, 999.

OPEN_KNOWN56 plus PARTNERSHIP_TREATMENT21 identify the77 production abstentions with clear opening support. OPEN_KNOWN does not mean a complete production call is known. WEAK_MULTI_CANDIDATE14 and PREEMPT_CANDIDATE6 require qualification/treatment resolution, not an automatic2D or three-level bid. PROTECTED_UNRESOLVED37 are known difficult distributions; UNKNOWN465 lack affirmative policy evidence.

### Exact positive Pass evidence

| Approval | Count | Deal indices |
|---|---:|---|
| PHASE29P D: 10 HCP, 4-4-3-2 outside third/fourth seat | 13 | 63, 101, 228, 433, 456, 616, 618, 628, 793, 825, 847, 882, 904 |
| PHASE29P D: case17: 10 HCP, 5S-4-2-2 outside third/fourth seat | 2 | 295, 494 |
| PHASE29P D: 8 HCP, 5S-5H-2-1 | 1 | 888 |
| PHASE29P D: 9 HCP, 5S-4H-2-2 | 1 | 955 |

### Treatment and strength overlaps

Supported partnership calls: 2H: 5, 2NT: 5, 2S: 11. Exact5–5 only; no6–5 extrapolation.
Rule20/C8 overlap indices: 292, 626, 736, 922, 988. Both say open. C8 explicitly supplies the below12 treatment call; the report does not invent a competing one-level bid. Future contract review should state this precedence explicitly, including what “weak” means at the low end.
There are49 mathematical Rule20 qualifiers across616: the46 classified as Rule20 in29N plus3 normal-strength equal-major hands placed in29N’s higher-priority known-boundary group. This is the same population, not a changed simulation. Current C3 additionally opens11HCP five-major hands below20; old29M.1 retains its historical narrower text.

## H. Positive Pass safety answer

**17 positive Pass; 599 unsafe or unresolved for a Pass rule =77 affirmative opening/treatment +522 unresolved.** The522 consist of14 weak/Multi candidates,6 preempt candidates,37 protected unresolved and465UNKNOWN.

All17 matching approvals have HCP<11, Rule20<20, no six/seven/eight-card suit, and no named major-minor or minor-minor5–5 treatment. The8HCP equal-major Pass is explicitly approved; it is not normal-opening-strength5S5H. No unspecified minor example is included. No production ABSTAIN is converted to Pass; production remains ABSTAIN for all616.

These are positive **audit classifications** under the current literal user-approved signatures. They do not approve production activation, extend the scope to all vulnerabilities/seats/honor patterns beyond the supplied signatures, or resolve broader playing-trick/Multi/preempt contracts. No Pass implementation is proposed in this phase.

## I. Audit artifacts

- `bridge/opening_pass_nisim_nily_policy_audit.py`: separate policy overlay, canonical facts, actual-hand trace reuse, deterministic selection and report.
- `bridgelab_phase29p_nisim_nily_opening_policy_audit.json`: all616 records, inventory, scope and validation metadata.
- `bridgelab_phase29p_nisim_nily_opening_policy_audit.md`: this report and compact table.
- `tests/test_bridge_phase29p_nisim_nily_opening_policy_audit.py`: real-hand reproduction, approved signatures, positional boundaries, treatment separation, no-fallback, coverage and serialization tests.

## J. Validation and recommendation for Phase29Q

**Focused validation:172 passed in6.32s. Production route count:45.**

Command (using the bundled Python with workspace venv packages on PYTHONPATH):

```text
python -m pytest -q -p no:cacheprovider
  tests/test_bridge_phase29p_nisim_nily_opening_policy_audit.py
  tests/test_bridge_phase29m_nisim_nily_opening_policy.py
  tests/test_bridge_phase29n_positive_opening_pass_predicate_audit.py
  tests/test_bridge_phase29o_opening_pass_safety_evidence_audit.py
  tests/test_bridge_sayc_openings.py
  tests/test_bridge_sayc_2nt_opening.py
  tests/test_bridge_sayc_strong_two_club.py
  tests/test_bridge_sayc_weak_two_openings.py
  tests/test_bridge_sayc_three_level_preempts.py
  tests/test_bridge_auction.py
  tests/test_bridge_hand_evaluation.py
  tests/test_bridge_phase29f_deal_simulator.py
  tests/test_bridge_phase29g_full_auction_simulation.py
  tests/test_bridge_phase29h_full_auction_coverage_report.py
  tests/test_bridge_sayc_route_configuration.py
  tests/test_bridge_system_profiles.py
```

Final checks: `git diff --check` clean; `git diff --stat` empty because all four additions are untracked. `git status --short` contains only:

```text
?? bridgelab-toolkit/bridge/opening_pass_nisim_nily_policy_audit.py
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.json
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.md
?? bridgelab-toolkit/tests/test_bridge_phase29p_nisim_nily_opening_policy_audit.py
```

Untracked files additionally checked for trailing whitespace, final newlines and JSON consistency. HEAD unchanged; no full regression, commit or push.

**Recommend Phase29Q: a partnership-contract and real-hand review, still before production integration.** Use the17 supported Pass records and21 treatment records to state exact activation, seat/vulnerability and weak-range scope. Identify the missing six-minor examples; define Multi variants and quality/strength qualifiers separately from natural SAYC2D; state C8 versus Rule20/11-major precedence and the system-dependent case18 minor choice. Obtain actual later-seat evidence from a separately labeled dataset rather than relabeling these first-seat hands. Preserve all remaining unresolved hands as ABSTAIN. Coverage gain alone is not a reason to add a Pass rule.
