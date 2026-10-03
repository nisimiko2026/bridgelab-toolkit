"""Print A8.12 production gap concentration without ranking semantics."""
from bridge.production_gap_concentration import analyze_production_gap_concentration


def show(title, groups):
    print(title)
    # Presentation may show largest concentrations first; this is descriptive
    # frequency display only and is not stored as a rank/priority.
    for x in sorted(groups, key=lambda g: (-g.count, g.key))[:20]:
        print(f"  {x.key}: {x.count} ({x.share_of_abstentions:.2%})")


def main():
    r=analyze_production_gap_concentration(start_seed=1,count=10000)
    print("=== A8.12 production gap concentration: 10,000 deals ===")
    print(f"completed: {r.source.completed}")
    print(f"abstained: {r.abstained}")
    print()
    show("BY REASON",r.by_reason)
    print()
    show("BY DEPTH",r.by_depth)
    print()
    show("BY ROUTE",r.by_route)
    print()
    show("BY EXACT AUCTION",r.by_auction)


if __name__=="__main__":
    main()
