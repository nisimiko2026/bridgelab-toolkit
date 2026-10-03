from collections import Counter, defaultdict

from bridge.missing_route_structural_classification import (
    classify_missing_route_structure,
)


def main():
    r = classify_missing_route_structure(start_seed=1, count=10000)
    print("A9.6.1 Missing-Route Structural Classification")
    print("runs", r.runs)
    print("missing_route_population", r.missing_route_population)
    print()

    for g in r.groups:
        print(g.family.value, g.count, f"{g.share:.2%}")

    print()
    print("top exact auctions by family")
    by_family = defaultdict(Counter)
    for x in r.cases:
        by_family[x.family.value][x.auction] += 1

    for family in sorted(by_family):
        print()
        print(f"[{family}]")
        for auction, n in by_family[family].most_common(15):
            print(n, auction or "<empty>")


if __name__ == "__main__":
    main()
