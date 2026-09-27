# PT-1B matched shortness validation

This experiment compares actual DDS declarer tricks from physical 52-card deals. It does not assign Playing-Trick coefficients, infer natural playing tricks, or alter bidding behavior.

For an ordinary singleton in hand H and side suit X, the doubleton control moves one spot card (rank 2–10) of X from partner to H and sends one spot card of a different side suit from H to partner. The three-card control applies two such swaps. Each candidate leaves at least two cards in the depleted side holdings, so it does not create a new singleton. All candidate paths are enumerated in stable suit/rank order; a seeded uniform index chooses the recorded control. Every accepted swap is reversed and checked against the exact original serialized deal.

For reciprocal singletons (North short in X, South short in Y), the four-corner design uses the third side suit Z as compensation. One swap removes North's singleton, another removes South's, and the two swaps commute. The source, North-removed, South-removed, and neither variants are all solved. If `R`, `N`, `S`, and `0` denote their DDS tricks, the combined contrast is `R − 0`, conditional singleton contrasts are `R − N` and `R − S`, standalone singleton contrasts are `S − 0` and `N − 0`, and the additive interaction is `R − N − S + 0`. A positive interaction indicates value beyond the sum of standalone effects. For 7–3, the long trump hand has only six side cards and cannot support a clean four-corner design without introducing another singleton. A direct X/Y spot-card exchange compares reciprocal shortness with neither studied singleton there, but it cannot identify an interaction.

The defender hands, partnership HCP, trump cards and allocation, all honors by hand, side-ace entries, declarer, strain, and defender trump split remain exact. Studied and compensation suit lengths and spot-card locations necessarily change. The source's opposite length, natural top winners, and ruffable-loser proxy are retained as stratification features; they are not assumed invariant after the intervention. Trump Honor Control is fixed before measurement: A=2, K=1, Q=1, J=0; weak score 0–1, medium 2–3, strong 4.

The conditioned PT-1 sampler can produce other side-suit singletons or voids in a source. They remain unchanged by the studied-suit exchange, so the paired contrast is conditional on that source context. The summary separately reports sources with no other side shortness and sources with additional shortness. In particular, a valid 7–3 short-trump-hand singleton-to-doubleton control requires another short side suit in the long-trump hand; it cannot be interpreted as an isolated one-singleton hand.

Run the DDS validation in the Python 3.12 environment with `endplay==0.5.12`:

```powershell
& 'C:\Users\nisim\OneDrive\BridgeLab\.pt1a_env\Scripts\python.exe' -m benchmarks.pt1b_shortness_validation --seed 2901 --primary-target 1000 --reciprocal-target 500 --sensitivity-sources 20
```

Run focused solver tests in that environment:

```powershell
& 'C:\Users\nisim\OneDrive\BridgeLab\.pt1a_env\Scripts\python.exe' -m pytest tests\test_bridge_pt1a_solver.py tests\test_bridge_pt1b_shortness.py -q
```

Run the historical suite in the project Python 3.14 environment:

```powershell
& 'C:\Users\nisim\Documents\BridgeLab\.venv\Scripts\python.exe' -m pytest -q
```

The Python 3.14 environment does not have a supported endplay wheel; solver-specific tests skip there. Three existing PT-1 probability tests encounter a `VacantPlacesQuestion` dataclass `super()` issue on Python 3.12, so the historical suite is validated under the project's Python 3.14 interpreter. Use the separate solver environment for the DDS tests and study. Solver failures remain null and are excluded from matched statistics.

The output contains `pt1b_summary.json`, `pt1b_cases.jsonl.gz`, and `pt1b_exchange_sensitivity.jsonl.gz`. The case file records source cases, physical control deals, card moves with before/after shapes, candidate counts and selected indices, and full solver provenance. Exchange sensitivity solves every valid one-step spot-card control for the first 20 accepted source deals in each ordinary singleton cohort. Its separate case file records every alternative exchange and DDS result; the summary reports main-study and provenance-replay solver calls separately.

Verify all saved transformations and solver/deal IDs without rerunning DDS:

```powershell
& 'C:\Users\nisim\OneDrive\BridgeLab\.pt1a_env\Scripts\python.exe' -m benchmarks.pt1b_output_audit
```
