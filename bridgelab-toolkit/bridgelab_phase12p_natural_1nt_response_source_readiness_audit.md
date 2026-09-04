# Phase 12P — Natural 1NT Response Source-Readiness Audit

## Deterministic sample

- Seeds: 1–10,000
- Auction prefix: `1NT-P`
- Phase 12M abstentions: 271
- Jacoby five-plus-major exclusions: 5
- Stayman exactly-four-major exclusions: 142
- Natural candidate population: 124

## Source-certainty matrix

| Family | Count | HCP | Candidate calls | Classification | Executable? | Policy? | Architecture? | Blocker | Action |
|---|---:|---|---|---|---|---|---|---|---|
| natural.pass.balanced-0-7 | 41 | 0-7 | P | SOURCE_PARTIAL | NO | NO | NO | No exact HCP-to-Pass contract or complete convention/minor exception boundary. | defer |
| natural.2nt.balanced-8-9 | 9 | 8-9 | 2NT | SOURCE_PARTIAL | NO | NO | NO | Approximate range and unresolved long-minor/partnership alternatives. | defer |
| natural.3nt.balanced-10-15 | 27 | 10-15 | 3NT | SOURCE_PARTIAL | NO | NO | NO | Typical range rather than exact mapping; minor and slam precedence unresolved. | defer |
| natural.minor-oriented.unbalanced | 45 | 0-16 | 2S, 2NT, 3C, 3D | PARTNERSHIP_DEPENDENT | NO | YES | NO | Call selection is explicitly method/partnership dependent. | defer |
| natural.balanced-slam-interest-16-plus | 2 | 17-17 | 4NT, 4C, 6NT | SOURCE_PARTIAL | NO | NO | NO | No exact call mapping among quantitative, Gerber, and direct slam actions. | defer |

Exact HCP distributions, shape partitions, route fields, and all twelve source-audit answers are preserved per family in the JSON artifact.

## Ranked candidates

1. `natural.2nt.balanced-8-9` — SOURCE_PARTIAL
2. `natural.3nt.balanced-10-15` — SOURCE_PARTIAL
3. `natural.pass.balanced-0-7` — SOURCE_PARTIAL
4. `natural.minor-oriented.unbalanced` — PARTNERSHIP_DEPENDENT
5. `natural.balanced-slam-interest-16-plus` — SOURCE_PARTIAL

No source-safe subset exists. The source uses “typical” or “approximately” for numeric ranges, says distribution can alter them, leaves long-minor methods to partnership agreement, and does not provide complete precedence among natural, minor, or slam responses.

## Complete position inventory and router status

Every included position reaches `sayc.response.1nt.jacoby`; that rule checks and abstains. No route is missing.

| Seed | Responder hand | HCP | S-H-D-C shape | Family | Route | Action |
|---:|---|---:|---|---|---|---|
| 33 | `96.42.Q98754.J63` | 3 | 2-2-6-3 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 197 | `J32.Q92.86432.J8` | 4 | 3-3-5-2 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 234 | `753.J93.K96.J632` | 5 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 296 | `Q54.K72.8432.J72` | 6 | 3-3-4-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 413 | `Q72.T43.KJ864.85` | 6 | 3-3-5-2 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 581 | `T94.94.9654.7543` | 0 | 3-2-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 687 | `T4.9.QJ96.AQJ975` | 10 | 2-1-4-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 865 | `972.K62.T43.A976` | 7 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 947 | `932.32.QT32.JT42` | 3 | 3-2-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 949 | `J7.T2.K32.JT9732` | 5 | 2-2-3-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 1239 | `A32.K72.AQT43.42` | 13 | 3-3-5-2 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 1312 | `2.972.A952.T7653` | 4 | 1-3-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 1314 | `T32.AQ4.KT985.83` | 9 | 3-3-5-2 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 1375 | `QJ4.AT8.94.KJ642` | 11 | 3-3-2-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 1381 | `JT6.T95.854.AT64` | 5 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 1400 | `J94.Q82.32.86532` | 3 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 1434 | `843.K98.AK64.A86` | 14 | 3-3-4-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 1485 | `AK8.5.QT8742.Q43` | 11 | 3-1-6-3 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 1563 | `7.Q54.J65.AJT985` | 8 | 1-3-3-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 1600 | `T53.976.9876542.-` | 0 | 3-3-7-0 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 1856 | `KQ5.AT9.Q87.AT74` | 15 | 3-3-3-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 1881 | `Q53.J42.7.KJT943` | 7 | 3-3-1-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2096 | `AQ6.A7.QT942.T65` | 12 | 3-2-5-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 2124 | `A83.J96.A75.9643` | 9 | 3-3-3-4 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 2127 | `4.AT6.K976543.87` | 7 | 1-3-7-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2150 | `K8.Q5.Q742.QT764` | 9 | 2-2-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2176 | `K6.A4.8642.KJT52` | 11 | 2-2-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2202 | `6.A5.KQJ874.KQ84` | 15 | 1-2-6-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2214 | `98.AQJ.JT982.742` | 8 | 2-3-5-3 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 2232 | `95.873.Q83.A8765` | 6 | 2-3-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 2258 | `QT7.T96.875.A842` | 6 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 2267 | `87.K2.AJT9752.54` | 8 | 2-2-7-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2401 | `754.654.Q53.AK32` | 9 | 3-3-3-4 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 2441 | `Q75.JT9.T932.A97` | 7 | 3-3-4-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 2462 | `T65.J.AQT83.8762` | 7 | 3-1-5-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2620 | `A6.T3.QJ952.AQ53` | 13 | 2-2-5-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 2660 | `T42.A43.KQT.K975` | 12 | 3-3-3-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 2977 | `Q7.J.QJT952.8752` | 6 | 2-1-6-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 3015 | `QT2.QJ9.AT752.86` | 9 | 3-3-5-2 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 3070 | `J9.J98.A76432.AK` | 13 | 2-3-6-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 3150 | `K96.Q3.987.T8742` | 5 | 3-2-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 3170 | `K7.874.A63.KT982` | 10 | 2-3-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 3323 | `J5.983.K965.QT92` | 6 | 2-3-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 3395 | `T73.KJ.K83.KQJ54` | 13 | 3-2-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 3436 | `Q74.J95.Q3.98754` | 5 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 3818 | `98.762.863.KT963` | 3 | 2-3-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 3853 | `KQ3.J64.9872.763` | 6 | 3-3-4-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 3857 | `K.T72.97.QT87532` | 5 | 1-3-2-7 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 3914 | `T83.7.AQ9854.864` | 6 | 3-1-6-3 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 3942 | `A5.Q96.A7432.652` | 10 | 2-3-5-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 4021 | `Q82.A3.K972.JT87` | 10 | 3-2-4-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 4093 | `73.T32.T942.AQ32` | 6 | 2-3-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 4478 | `87.A53.KQ65.T642` | 9 | 2-3-4-4 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 4481 | `987.KT8.K9843.65` | 6 | 3-3-5-2 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 4592 | `AT6.65.KQ32.KQ82` | 14 | 3-2-4-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 4746 | `Q52.983.KJ86.AT4` | 10 | 3-3-4-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 4863 | `J76.Q.8654.KT854` | 6 | 3-1-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 4929 | `T94.Q43.AKT76.75` | 9 | 3-3-5-2 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 4974 | `K84.KT.Q63.QJ985` | 11 | 3-2-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 4982 | `96.65.T943.AT985` | 4 | 2-2-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 4995 | `85.J42.842.JT865` | 2 | 2-3-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 5071 | `9.T.AT543.JT9732` | 5 | 1-1-5-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5347 | `AQ4.K.K9854.QT95` | 14 | 3-1-5-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5392 | `J92.854.654.T942` | 1 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 5393 | `52.8.Q765.QT7432` | 4 | 2-1-4-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5435 | `K.63.AK854.AQT63` | 16 | 1-2-5-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5442 | `764.A95.J5.T8742` | 5 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 5582 | `J82.A7.Q53.KT985` | 10 | 3-2-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 5613 | `T94.862.T975.J82` | 1 | 3-3-4-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 5754 | `JT.QT9.K9532.JT9` | 7 | 2-3-5-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 5772 | `4.T74.AQ975.A542` | 10 | 1-3-5-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5837 | `Q74.J98.2.AJ9652` | 8 | 3-3-1-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 5863 | `982.K7.AJ94.KQJ3` | 14 | 3-2-4-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 5879 | `T5.K32.KJ8653.J8` | 8 | 2-3-6-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 6108 | `A74.Q98.KJ52.A75` | 14 | 3-3-4-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 6292 | `Q62.Q42.QJ5.AT64` | 11 | 3-3-3-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 6307 | `T94.KJ6.K75.T743` | 7 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 6517 | `A8.Q2.QT9654.Q63` | 10 | 2-2-6-3 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 6555 | `862.643.T92.K532` | 3 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 6680 | `63.T87.KJ543.AT8` | 8 | 2-3-5-3 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 6840 | `J3.K3.AKT7.85432` | 11 | 2-2-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 6921 | `A6.J94.AK2.KT763` | 15 | 2-3-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7017 | `T8.T98.K8754.874` | 3 | 2-3-5-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7093 | `72.K84.986543.83` | 3 | 2-3-6-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7116 | `JT6.T63.T4.T9876` | 1 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7241 | `Q54.754.72.AJT86` | 7 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7259 | `AT9.42.KJ86.A642` | 12 | 3-2-4-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7338 | `AT8.2.T982.QT973` | 6 | 3-1-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7356 | `A86.KT5.T975.854` | 7 | 3-3-4-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7427 | `J62.Q4.T7.QJ8642` | 6 | 3-2-2-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7469 | `Q93.96.A85432.93` | 6 | 3-2-6-2 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7486 | `AT.JT6.QT94.T763` | 7 | 2-3-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7558 | `A73.J83.AK98.JT6` | 13 | 3-3-4-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7561 | `Q5.AK5.62.KT9653` | 12 | 2-3-2-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7582 | `J8.J52.K52.J9764` | 6 | 2-3-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7610 | `T75.432.Q2.QJ763` | 5 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7660 | `T4.J82.AQT94.752` | 7 | 2-3-5-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 7686 | `KJ6.JT6.A.T98752` | 9 | 3-3-1-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7707 | `974.Q85.T97643.3` | 2 | 3-3-6-1 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7714 | `983.K.KJ763.T752` | 7 | 3-1-5-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 7717 | `A9.AT8.T52.KQT72` | 13 | 2-3-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7787 | `A82.Q9.K9543.QJ8` | 12 | 3-2-5-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7792 | `Q86.AT4.K752.AT2` | 13 | 3-3-4-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 7963 | `AT4.83.9763.QT75` | 6 | 3-2-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 8085 | `T.T4.K5432.87654` | 3 | 1-2-5-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 8108 | `KQ6.A3.KT74.AJT9` | 17 | 3-2-4-4 | natural.balanced-slam-interest-16-plus | sayc.response.1nt.jacoby | ABSTAIN |
| 8335 | `6.T6.AT9632.T953` | 4 | 1-2-6-4 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 8483 | `JT9.A62.T97653.2` | 5 | 3-3-6-1 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 8585 | `T97.KT.AQ73.K876` | 12 | 3-2-4-4 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 8628 | `984.62.T42.97432` | 0 | 3-2-3-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 8740 | `JT5.Q32.AKJ86.J4` | 12 | 3-3-5-2 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 8947 | `A8.A64.JT2.QJT87` | 12 | 2-3-3-5 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 9003 | `64.A53.AJT85.KQ7` | 14 | 2-3-5-3 | natural.3nt.balanced-10-15 | sayc.response.1nt.jacoby | ABSTAIN |
| 9171 | `Q75.64.KQJ9632.4` | 8 | 3-2-7-1 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 9195 | `J9.875.Q954.AT75` | 7 | 2-3-4-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 9272 | `K86.5.753.AT7632` | 7 | 3-1-3-6 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 9533 | `Q95.T42.T6.98654` | 2 | 3-3-2-5 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 9606 | `J52.J63.QT3.JT84` | 5 | 3-3-3-4 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 9662 | `Q83.4.K954.T9765` | 5 | 3-1-4-5 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 9694 | `972.J5.Q9654.Q54` | 5 | 3-2-5-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |
| 9758 | `K8.Q75.AQJ3.AJ87` | 17 | 2-3-4-4 | natural.balanced-slam-interest-16-plus | sayc.response.1nt.jacoby | ABSTAIN |
| 9762 | `3.732.AKJT63.AJ3` | 13 | 1-3-6-3 | natural.minor-oriented.unbalanced | sayc.response.1nt.jacoby | ABSTAIN |
| 9914 | `J8.JT4.Q9863.AT7` | 8 | 2-3-5-3 | natural.2nt.balanced-8-9 | sayc.response.1nt.jacoby | ABSTAIN |
| 9984 | `JT6.73.KT752.J86` | 5 | 3-2-5-3 | natural.pass.balanced-0-7 | sayc.response.1nt.jacoby | ABSTAIN |

## Decision and Phase 12Q

**E. DEFER NATURAL 1NT RESPONSE FAMILY.**

Phase 12Q — Responder Rebid Source-Readiness Audit: return to the next Phase 12M ranked family, responder.rebid-after-opener-rebid, and inventory narrow exact-auction decision points before selecting any implementation.

Guards: routes=45; Phase 12N=24; Phase 12O=23; Phase 12G={'4H': 17, '4S': 21}; Phase 12H=197; Phase 12L={'HEARTS': 5, 'SPADES': 7}; Jacoby={'heart_transfer': 62, 'spade_transfer': 61, 'total': 123}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12P
