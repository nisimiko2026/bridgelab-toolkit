"""Print the A8.11 production abstention extraction."""
from bridge.abstention_diagnostics import AbstentionReason
from bridge.production_gap_extraction import extract_production_abstentions


def main():
    for count in (1000, 10000):
        r = extract_production_abstentions(start_seed=1, count=count)
        print(f"=== A8.11 production abstentions: {count:,} deals ===")
        print(f"completed: {r.completed}")
        print(f"abstained: {r.abstained}")
        print(f"no_route: {r.count(AbstentionReason.NO_ROUTE)}")
        print(
            "routed_no_applicable_rule: "
            f"{r.count(AbstentionReason.ROUTED_NO_APPLICABLE_RULE)}"
        )
        print(f"groups: {len(r.groups)}")
        print()


if __name__ == "__main__":
    main()
