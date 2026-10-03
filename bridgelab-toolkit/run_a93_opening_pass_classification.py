"""A9.3 classify the full 10,000-deal opening-review population."""
from bridge.opening_pass_classification import classify_opening_pass_population


def main():
    r = classify_opening_pass_population(start_seed=1, count=10000)
    print("=== A9.3 OPENING-PASS CLASSIFICATION ===")
    print(f"opening-review population: {r.population}")

    print("\nSTRENGTH CLASSES")
    for g in r.groups:
        print(f"  {g.review_class.value}: {g.count} ({g.share_of_population:.2%})")

    print("\nHCP DISTRIBUTION")
    for hcp, n in r.hcp_counts:
        print(f"  {hcp}: {n}")

    print("\nUNRESOLVED 12+ HCP CASES")
    strong = [x for x in r.cases if x.case.hcp >= 12]
    for x in strong:
        c = x.case
        print(
            f"  seed={c.seed} HCP={c.hcp} "
            f"shape(S/H/D/C)={'-'.join(map(str,c.shape))} "
            f"hand={c.hand} class={x.review_class.value}"
        )

    print("\nInterpretation guard: below 12 HCP is not automatically Pass; "
          "12+ unresolved is not automatically a policy gap.")


if __name__ == "__main__":
    main()
