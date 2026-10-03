"""Print A9.2 review of A8.14 opening representative seeds."""
from bridge.opening_pass_review import review_opening_pass_cases


def main():
    r = review_opening_pass_cases(
        start_seed=1, count=10000, seeds=(2, 6, 9, 10, 11)
    )
    print("=== A9.2 OPENING-PASS REVIEW ===")
    print(f"opening-pass-review population: {r.population}")
    for x in r.cases:
        print()
        print(f"seed={x.seed} replay={x.replay_key}")
        print(f"hand={x.hand}")
        print(f"HCP={x.hcp} shape(S/H/D/C)={'-'.join(map(str,x.shape))}")
        print(f"rejected opening rules={len(x.rejected_rules)}")
        for rule, reason in x.rejected_rules:
            print(f"  {rule}: {reason}")
    print()
    print("A9.2 conclusion: diagnostic evidence only; no Pass/opening policy decision.")


if __name__ == "__main__":
    main()
