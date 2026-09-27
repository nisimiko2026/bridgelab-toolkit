# BridgeLab PT-1B — matched shortness effect validation

## A. Repository state and interrupted-run recovery

Branch `codex/phase18b`; HEAD `a3007ee510c2bf8aceea4dd72895a95b3fa12994`. No tracked files changed; PT-1/PT-1A and PT-1B artifacts remain untracked. No commit or push was made. `git diff --check` is clean.

The interrupted run had already completed its main study. The gzip CRC and every JSON row were verified: 14,000 unique source IDs, 11 × 1,000 ordinary matched pairs, and 6 × 500 reciprocal comparisons. All 2,500 feasible four-corner records retained both steps on both paths. No main cohort was rerun. The original sensitivity aggregates lacked individual exchange outcomes. Only that 220-source subset was replayed to write complete per-exchange DDS provenance; its recomputed statistics matched all saved source summaries exactly.

## B. Transformation and preservation contract

For a singleton in hand H and side suit X, one rank-2–10 card of X moves from partner to H while a rank-2–10 card of another nontrump suit moves from H to partner. Two successive swaps make a three-card control when possible. Candidate paths are enumerated in stable suit/rank order, then selected by a seeded uniform index. The audit verifies every move forward and backward to the identical deal.

Exactly preserved: all 52 unique cards, both defender hands, HCP and every J-or-higher honor by partnership hand, all trump cards and their allocation, side aces/entry indicators, declarer North, spade strain, and actual defender trump split. Necessarily changed: studied-suit and compensation-suit lengths and spot-card locations. The source's opposite studied-suit length, natural top winners, and ruffable-loser proxy are recorded for stratification; they are not claimed constant after the exchange. Other source shortness, if present, remains unchanged within a pair and is reported separately.

Reciprocal cases use a commuting four-corner design: reciprocal R, North singleton removed N, South singleton removed S, and neither 0. Standalone `effect_N = DD(S) − DD(0)` and `effect_S = DD(N) − DD(0)`; `reciprocal_effect = DD(R) − DD(0)`; `interaction = DD(R) − DD(N) − DD(S) + DD(0)`. The two conditional removal contrasts `DD(R) − DD(N)` and `DD(R) − DD(S)` are also reported. All DDS results are reference measurements, never NPT or APT coefficients.

## C. Acceptance and structural limits

| Family | Generated | Accepted | Rejected for legal exchange | Solver rejection |
|---|---:|---:|---:|---:|
| Ordinary singleton (11 cohorts) | 14476 | 11000 | 3476 | 0 |
| Reciprocal (five squares + 7–3 direct) | 7631 | 3000 | 4631 | 0 |

Among 11,000 accepted ordinary sources, 5575 also supported exact three-card controls; the remainder were explicitly unavailable. No impossible transformation was forced.

For 7–3 reciprocal deals, the long-trump hand has only six side cards and cannot support a clean four-corner square without creating another singleton. Its 500 observations are direct reciprocal-to-neither controls only; interaction is unavailable. For 7–3 short-hand singleton controls, all 1,000 accepted sources have preserved additional shortness in the seven-trump hand. Their estimate is conditional on that context, not an isolated-singleton estimate.

### D. Singleton versus doubleton by structure and location

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 5-3 long-hand-singleton | 1000 | 0.441 | 0.000 | 0.679 | [0.399, 0.483] | 0.459 | 0.480 | 0.061 | 0.459 | 0.061 |
| 5-3 short-hand-singleton | 1000 | 0.434 | 0.000 | 0.736 | [0.388, 0.480] | 0.450 | 0.478 | 0.072 | 0.450 | 0.072 |
| 5-4 long-hand-singleton | 1000 | 0.702 | 1.000 | 0.737 | [0.656, 0.748] | 0.605 | 0.364 | 0.031 | 0.605 | 0.031 |
| 5-4 short-hand-singleton | 1000 | 0.868 | 1.000 | 0.741 | [0.822, 0.914] | 0.685 | 0.303 | 0.012 | 0.685 | 0.012 |
| 5-5 equal-hand-singleton | 1000 | 0.970 | 1.000 | 0.751 | [0.923, 1.017] | 0.732 | 0.258 | 0.010 | 0.732 | 0.010 |
| 6-3 long-hand-singleton | 1000 | 0.550 | 1.000 | 0.674 | [0.508, 0.592] | 0.526 | 0.435 | 0.039 | 0.526 | 0.039 |
| 6-3 short-hand-singleton | 1000 | 0.644 | 1.000 | 0.732 | [0.599, 0.689] | 0.570 | 0.396 | 0.034 | 0.570 | 0.034 |
| 6-4 long-hand-singleton | 1000 | 0.741 | 1.000 | 0.737 | [0.695, 0.787] | 0.642 | 0.322 | 0.036 | 0.642 | 0.036 |
| 6-4 short-hand-singleton | 1000 | 1.018 | 1.000 | 0.742 | [0.972, 1.064] | 0.755 | 0.239 | 0.006 | 0.755 | 0.006 |
| 7-3 long-hand-singleton | 1000 | 0.499 | 0.000 | 0.686 | [0.456, 0.542] | 0.498 | 0.452 | 0.050 | 0.498 | 0.050 |
| 7-3 short-hand-singleton | 1000 | 0.876 | 1.000 | 0.744 | [0.830, 0.922] | 0.680 | 0.310 | 0.010 | 0.680 | 0.010 |

### E. Singleton versus three-card controls, where feasible

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 5-3 long-hand-singleton | 672 | 0.612 | 1.000 | 0.851 | [0.547, 0.676] | 0.536 | 0.391 | 0.073 | 0.536 | 0.073 |
| 5-3 short-hand-singleton | 574 | 0.681 | 1.000 | 0.918 | [0.606, 0.756] | 0.577 | 0.348 | 0.075 | 0.577 | 0.075 |
| 5-4 long-hand-singleton | 622 | 0.958 | 1.000 | 0.909 | [0.887, 1.030] | 0.680 | 0.296 | 0.024 | 0.680 | 0.024 |
| 5-4 short-hand-singleton | 523 | 1.233 | 1.000 | 0.972 | [1.150, 1.317] | 0.763 | 0.224 | 0.013 | 0.763 | 0.013 |
| 5-5 equal-hand-singleton | 511 | 1.409 | 1.000 | 0.998 | [1.323, 1.495] | 0.810 | 0.174 | 0.016 | 0.810 | 0.016 |
| 6-3 long-hand-singleton | 665 | 0.609 | 1.000 | 0.897 | [0.541, 0.677] | 0.529 | 0.383 | 0.087 | 0.529 | 0.087 |
| 6-3 short-hand-singleton | 469 | 0.962 | 1.000 | 0.917 | [0.879, 1.045] | 0.697 | 0.258 | 0.045 | 0.697 | 0.045 |
| 6-4 long-hand-singleton | 559 | 0.857 | 1.000 | 0.934 | [0.779, 0.934] | 0.631 | 0.320 | 0.048 | 0.631 | 0.048 |
| 6-4 short-hand-singleton | 446 | 1.453 | 1.000 | 0.963 | [1.364, 1.542] | 0.830 | 0.166 | 0.004 | 0.830 | 0.004 |
| 7-3 long-hand-singleton | 208 | 0.779 | 1.000 | 0.839 | [0.665, 0.893] | 0.615 | 0.346 | 0.038 | 0.615 | 0.038 |
| 7-3 short-hand-singleton | 326 | 1.218 | 1.000 | 0.840 | [1.127, 1.309] | 0.804 | 0.187 | 0.009 | 0.804 | 0.009 |

### F. Pooled location strata (descriptive across structures)

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| equal | 1000 | 0.970 | 1.000 | 0.751 | [0.923, 1.017] | 0.732 | 0.258 | 0.010 | 0.732 | 0.010 |
| long | 5000 | 0.587 | 1.000 | 0.712 | [0.567, 0.606] | 0.546 | 0.411 | 0.043 | 0.546 | 0.043 |
| short | 5000 | 0.768 | 1.000 | 0.767 | [0.747, 0.789] | 0.628 | 0.345 | 0.027 | 0.628 | 0.027 |

Short-hand and long-hand source populations are distinct; the pooled location difference is descriptive, not a within-deal causal contrast. The per-structure rows above are the primary location evidence.

### G. Studied-suit ruffable-loser groups

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0 | 218 | 0.298 | 0.000 | 0.606 | [0.218, 0.379] | 0.317 | 0.638 | 0.046 | 0.317 | 0.046 |
| 1 | 1206 | 0.595 | 0.500 | 0.726 | [0.554, 0.636] | 0.500 | 0.478 | 0.022 | 0.500 | 0.022 |
| 2 | 4778 | 0.776 | 1.000 | 0.746 | [0.755, 0.797] | 0.648 | 0.324 | 0.028 | 0.648 | 0.028 |
| 3+ | 4798 | 0.678 | 1.000 | 0.757 | [0.656, 0.699] | 0.590 | 0.370 | 0.040 | 0.590 | 0.040 |

### H1. Opposite studied-suit length

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 3 | 4723 | 0.780 | 1.000 | 0.754 | [0.758, 0.801] | 0.642 | 0.331 | 0.026 | 0.642 | 0.026 |
| 4 | 3902 | 0.659 | 1.000 | 0.741 | [0.636, 0.683] | 0.579 | 0.384 | 0.037 | 0.579 | 0.037 |
| 5 | 1780 | 0.626 | 1.000 | 0.737 | [0.592, 0.661] | 0.557 | 0.404 | 0.039 | 0.557 | 0.039 |
| 6 | 504 | 0.609 | 1.000 | 0.743 | [0.544, 0.674] | 0.518 | 0.450 | 0.032 | 0.518 | 0.032 |
| 7 | 87 | 0.690 | 1.000 | 0.919 | [0.497, 0.883] | 0.609 | 0.299 | 0.092 | 0.609 | 0.092 |
| 8 | 4 | 1.250 | 1.500 | 0.957 | [0.312, 2.188] | 0.750 | 0.250 | 0.000 | 0.750 | 0.000 |

### H2. Natural top winners in the studied suit

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0 | 7774 | 0.736 | 1.000 | 0.761 | [0.719, 0.753] | 0.626 | 0.338 | 0.036 | 0.626 | 0.036 |
| 1 | 2436 | 0.733 | 1.000 | 0.725 | [0.704, 0.762] | 0.610 | 0.370 | 0.019 | 0.610 | 0.019 |
| 2 | 621 | 0.306 | 0.000 | 0.590 | [0.260, 0.352] | 0.320 | 0.639 | 0.040 | 0.320 | 0.040 |
| 3 | 140 | 0.221 | 0.000 | 0.563 | [0.128, 0.315] | 0.250 | 0.700 | 0.050 | 0.250 | 0.050 |
| 4 | 24 | 0.458 | 0.500 | 0.588 | [0.223, 0.694] | 0.500 | 0.458 | 0.042 | 0.500 | 0.042 |
| 5 | 5 | 0.200 | 0.000 | 0.447 | [-0.192, 0.592] | 0.200 | 0.800 | 0.000 | 0.200 | 0.000 |

### I1. Predefined Trump Honor Control category

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| medium | 5988 | 0.710 | 1.000 | 0.754 | [0.691, 0.729] | 0.606 | 0.360 | 0.034 | 0.606 | 0.034 |
| strong | 3624 | 0.763 | 1.000 | 0.730 | [0.739, 0.787] | 0.632 | 0.349 | 0.020 | 0.632 | 0.020 |
| weak | 1388 | 0.523 | 0.000 | 0.760 | [0.483, 0.563] | 0.494 | 0.444 | 0.062 | 0.494 | 0.062 |

### I2. Actual defender trump split

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0-3 | 1106 | 0.735 | 1.000 | 0.762 | [0.690, 0.780] | 0.618 | 0.349 | 0.033 | 0.618 | 0.033 |
| 0-4 | 379 | 0.641 | 1.000 | 0.744 | [0.566, 0.716] | 0.580 | 0.377 | 0.042 | 0.580 | 0.042 |
| 0-5 | 90 | 0.400 | 0.000 | 0.731 | [0.249, 0.551] | 0.433 | 0.478 | 0.089 | 0.433 | 0.089 |
| 1-2 | 3894 | 0.845 | 1.000 | 0.752 | [0.822, 0.869] | 0.674 | 0.307 | 0.020 | 0.674 | 0.020 |
| 1-3 | 1984 | 0.647 | 1.000 | 0.716 | [0.615, 0.678] | 0.575 | 0.392 | 0.033 | 0.575 | 0.033 |
| 1-4 | 570 | 0.419 | 0.000 | 0.685 | [0.363, 0.476] | 0.433 | 0.507 | 0.060 | 0.433 | 0.060 |
| 2-2 | 1637 | 0.756 | 1.000 | 0.740 | [0.720, 0.792] | 0.626 | 0.352 | 0.021 | 0.626 | 0.021 |
| 2-3 | 1340 | 0.448 | 0.000 | 0.716 | [0.409, 0.486] | 0.465 | 0.467 | 0.068 | 0.465 | 0.068 |

Trump Honor Control was fixed before looking at outcomes: A=2, K=1, Q=1, J=0; weak 0–1, medium 2–3, strong 4. These are observed defender splits, not unconditional break probabilities. `pt1b_summary.json` additionally gives every split, quality, length, winner, and loser stratum within each cohort and reciprocal comparison.

### J. Other side shortness in ordinary source deals

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| additional_side_shortness | 6179 | 0.767 | 1.000 | 0.757 | [0.748, 0.786] | 0.633 | 0.341 | 0.027 | 0.633 | 0.027 |
| no_other_side_shortness | 4821 | 0.623 | 1.000 | 0.735 | [0.602, 0.643] | 0.559 | 0.401 | 0.041 | 0.559 | 0.041 |

## K. Exchange sensitivity

All legal one-step low-card exchanges were solved for 220 deterministic sources (2793 candidate records; candidate count 2–40). 220 sources had every candidate solved. The mean within-source range was 0.368 tricks and the mean within-source SD was 0.181. A different legal exchange changed Δ for 0.345 of sources: 144 ranges were 0, 71 were 1, and 5 were 2 tricks. The seeded selected-exchange Δ minus the all-exchange mean averaged -0.018 tricks (approximate 95% CI [-0.058, 0.022]); no systematic selection shift is evident in this subset, but individual spot-card choice sometimes matters.

### L. Reciprocal singleton effects and interaction

| Comparison | N | Mean Δ | Median | SD | 95% CI | P(>0) | P(=0) | P(<0) | P(≥1) | P(≤−1) |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 5-3_reciprocal: combined | 500 | 0.628 | 1.000 | 0.739 | [0.563, 0.693] | 0.564 | 0.394 | 0.042 | 0.564 | 0.042 |
| 5-3_reciprocal: interaction | 500 | -0.112 | 0.000 | 0.780 | [-0.180, -0.044] | 0.184 | 0.560 | 0.256 | 0.184 | 0.256 |
| 5-3_reciprocal: n_alone | 500 | 0.394 | 0.000 | 0.648 | [0.337, 0.451] | 0.410 | 0.540 | 0.050 | 0.410 | 0.050 |
| 5-3_reciprocal: remove_n_conditional | 500 | 0.282 | 0.000 | 0.675 | [0.223, 0.341] | 0.336 | 0.586 | 0.078 | 0.336 | 0.078 |
| 5-3_reciprocal: remove_s_conditional | 500 | 0.234 | 0.000 | 0.663 | [0.176, 0.292] | 0.326 | 0.566 | 0.108 | 0.326 | 0.108 |
| 5-3_reciprocal: s_alone | 500 | 0.346 | 0.000 | 0.692 | [0.285, 0.407] | 0.390 | 0.528 | 0.082 | 0.390 | 0.082 |
| 5-4_reciprocal: combined | 500 | 1.222 | 1.000 | 0.703 | [1.160, 1.284] | 0.856 | 0.144 | 0.000 | 0.856 | 0.000 |
| 5-4_reciprocal: interaction | 500 | -0.464 | 0.000 | 0.705 | [-0.526, -0.402] | 0.042 | 0.532 | 0.426 | 0.042 | 0.426 |
| 5-4_reciprocal: n_alone | 500 | 0.764 | 1.000 | 0.636 | [0.708, 0.820] | 0.666 | 0.328 | 0.006 | 0.666 | 0.006 |
| 5-4_reciprocal: remove_n_conditional | 500 | 0.300 | 0.000 | 0.625 | [0.245, 0.355] | 0.366 | 0.556 | 0.078 | 0.366 | 0.078 |
| 5-4_reciprocal: remove_s_conditional | 500 | 0.458 | 0.000 | 0.649 | [0.401, 0.515] | 0.486 | 0.458 | 0.056 | 0.486 | 0.056 |
| 5-4_reciprocal: s_alone | 500 | 0.922 | 1.000 | 0.670 | [0.863, 0.981] | 0.748 | 0.248 | 0.004 | 0.748 | 0.004 |
| 5-5_reciprocal: combined | 500 | 1.436 | 1.000 | 0.653 | [1.379, 1.493] | 0.928 | 0.072 | 0.000 | 0.928 | 0.000 |
| 5-5_reciprocal: interaction | 500 | -0.638 | 0.000 | 0.775 | [-0.706, -0.570] | 0.008 | 0.512 | 0.480 | 0.008 | 0.480 |
| 5-5_reciprocal: n_alone | 500 | 1.030 | 1.000 | 0.640 | [0.974, 1.086] | 0.816 | 0.184 | 0.000 | 0.816 | 0.000 |
| 5-5_reciprocal: remove_n_conditional | 500 | 0.392 | 0.000 | 0.641 | [0.336, 0.448] | 0.446 | 0.484 | 0.070 | 0.446 | 0.070 |
| 5-5_reciprocal: remove_s_conditional | 500 | 0.406 | 0.000 | 0.608 | [0.353, 0.459] | 0.454 | 0.490 | 0.056 | 0.454 | 0.056 |
| 5-5_reciprocal: s_alone | 500 | 1.044 | 1.000 | 0.683 | [0.984, 1.104] | 0.800 | 0.198 | 0.002 | 0.800 | 0.002 |
| 6-3_reciprocal: combined | 500 | 1.002 | 1.000 | 0.766 | [0.935, 1.069] | 0.756 | 0.224 | 0.020 | 0.756 | 0.020 |
| 6-3_reciprocal: interaction | 500 | -0.284 | 0.000 | 0.719 | [-0.347, -0.221] | 0.094 | 0.572 | 0.334 | 0.094 | 0.334 |
| 6-3_reciprocal: n_alone | 500 | 0.528 | 1.000 | 0.659 | [0.470, 0.586] | 0.524 | 0.432 | 0.044 | 0.524 | 0.044 |
| 6-3_reciprocal: remove_n_conditional | 500 | 0.244 | 0.000 | 0.649 | [0.187, 0.301] | 0.320 | 0.586 | 0.094 | 0.320 | 0.094 |
| 6-3_reciprocal: remove_s_conditional | 500 | 0.474 | 0.000 | 0.694 | [0.413, 0.535] | 0.498 | 0.442 | 0.060 | 0.498 | 0.060 |
| 6-3_reciprocal: s_alone | 500 | 0.758 | 1.000 | 0.724 | [0.695, 0.821] | 0.660 | 0.310 | 0.030 | 0.660 | 0.030 |
| 6-4_reciprocal: combined | 500 | 1.364 | 1.000 | 0.699 | [1.303, 1.425] | 0.896 | 0.104 | 0.000 | 0.896 | 0.000 |
| 6-4_reciprocal: interaction | 500 | -0.570 | 0.000 | 0.801 | [-0.640, -0.500] | 0.042 | 0.500 | 0.458 | 0.042 | 0.458 |
| 6-4_reciprocal: n_alone | 500 | 0.788 | 1.000 | 0.678 | [0.729, 0.847] | 0.668 | 0.320 | 0.012 | 0.668 | 0.012 |
| 6-4_reciprocal: remove_n_conditional | 500 | 0.218 | 0.000 | 0.626 | [0.163, 0.273] | 0.320 | 0.574 | 0.106 | 0.320 | 0.106 |
| 6-4_reciprocal: remove_s_conditional | 500 | 0.576 | 1.000 | 0.636 | [0.520, 0.632] | 0.574 | 0.388 | 0.038 | 0.574 | 0.038 |
| 6-4_reciprocal: s_alone | 500 | 1.146 | 1.000 | 0.697 | [1.085, 1.207] | 0.830 | 0.170 | 0.000 | 0.830 | 0.000 |
| 7-3_reciprocal: combined_direct | 500 | 0.920 | 1.000 | 0.720 | [0.857, 0.983] | 0.716 | 0.278 | 0.006 | 0.716 | 0.006 |

The 7–3 direct row has no effect_N, effect_S, or interaction. Across the five feasible four-corner structures, interaction means are all negative; this does not justify a positive crossruff bonus or a final Playing-Trick coefficient.

## M. Tests, runtime, and production safety

- PT-1 under project Python 3.14: **14 passed**.
- PT-1A under solver Python 3.12: **17 passed**.
- PT-1B under solver Python 3.12: **16 passed**.
- Relevant hand evaluation, structured hand, probability, Strong-2C, and Playing-Trick dependency tests under Python 3.14: **105 passed**.
- Historical suite under Python 3.14: **2,672 passed, 9 solver-dependent skipped, 143 subtests passed** in 1,201.44 s. Later PT-1B test, reporting, and output-audit additions passed their focused tests and complete output audit; production code remained unchanged.
- The three pre-existing `VacantPlacesQuestion` dataclass `super()` tests fail only under Python 3.12; they pass in the project Python 3.14 environment. Production code was not changed to address an environment-only issue.
- Main DDS run: **41,148 calls**, all successful, 1072.66 s wall time. Sensitivity provenance recovery: **2,793 calls**, all successful, 9.12 s. Total executed calls: **43,941**. Solver: endplay/DDS 0.5.12.
- Full output audit: **14,000** main sources, **32,650** main forward/reverse card moves, and **2,793** sensitivity exchanges verified; gzip/JSON integrity passed.
- `production_changed = False`; production routes **45 before / 45 after**. No tracked diff, bidding rule, or route changed. No commit or push.

## N. Recommendation

**Another methodological revision required.** The matched DDS data show a measurable studied-singleton contribution and consistent negative reciprocal interaction, but the necessary compensation-suit shape change, spot-exchange sensitivity in 34.5% of tested sources, and 7–3's unavoidable additional-shortness context limit a single transportable coefficient. The next revision should predefine how compensation-suit effects and source-context interactions enter calibration. PT-2 and final Playing-Trick coefficients remain deferred.

## Files

- `pt1b_summary.json`: full comparison statistics and within-cohort strata.
- `pt1b_cases.jsonl.gz`: all main source/control deals, selected exchanges, and DDS provenance.
- `pt1b_exchange_sensitivity.jsonl.gz`: every sensitivity exchange, delta, and DDS result.
- `pt1b_integrity_audit.json`: case-file integrity and reverse-replay counts.
