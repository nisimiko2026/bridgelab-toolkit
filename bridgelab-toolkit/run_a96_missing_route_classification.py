from collections import Counter

from bridge.missing_route_classification import classify_missing_routes


def main():
    r = classify_missing_routes(start_seed=1, count=10000)
    print("A9.6 Missing-Route Classification")
    print("runs", r.runs)
    print("abstained", r.abstained)
    print("missing_route_population", r.missing_route_population)
    print()
    for g in r.groups:
        print(g.family.value, g.classification.value, g.count)

    print()
    print("top exact auctions")
    c = Counter(x.auction for x in r.cases)
    for auction, n in c.most_common(25):
        print(n, auction or "<empty>")


if __name__ == "__main__":
    main()
