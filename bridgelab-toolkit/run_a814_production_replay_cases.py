"""Print A8.14 deterministic representative/replay cases."""
from bridge.production_replay_cases import build_representative_replay_report


def main():
    r = build_representative_replay_report(
        start_seed=1, count=10000, per_class_limit=5
    )
    print("=== A8.14 representative replay cases: 10,000 deals ===")
    print(f"abstained: {r.abstained}")
    print(f"selected: {r.selected_count}")
    for g in r.groups:
        print()
        print(f"{g.evidence_class.value}: available={g.available_count}")
        for c in g.cases:
            route = c.route_id if c.route_id is not None else "<NO_ROUTE>"
            auction = c.auction if c.auction else "<OPENING>"
            print(
                f"  seed={c.seed} depth={c.depth} seat={c.stopped_seat} "
                f"route={route} auction={auction} replay={c.replay_key}"
            )


if __name__ == "__main__":
    main()
