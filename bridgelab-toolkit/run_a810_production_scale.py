"""Run and print the A8.10 production SAYC scale benchmark."""
from bridge.production_scale_benchmark import run_production_scale_benchmark

def main():
    for count in (1000,10000):
        r=run_production_scale_benchmark(start_seed=1,count=count)
        m=r.coverage.metrics
        print(f"=== A8.10 production SAYC: {count:,} deals ===")
        print(f"seeds: 1-{count}")
        print(f"production_calls: {m.production_calls}")
        print(f"fixture_calls: {m.fixture_calls}")
        print(f"opened: {m.opened} ({m.opening_rate:.2%})")
        print(f"responder_reached: {m.responder_reached}")
        print(f"responder_bid: {m.responder_bid} ({m.responder_bid_rate:.2%})")
        print(f"opener_rebid: {m.opener_rebid} ({m.opener_rebid_rate:.2%})")
        print(f"completed: {m.completed}")
        print(f"abstained: {m.abstained}")
        print(f"depth_counts: {m.depth_counts}")
        print(f"replay_records: {len(r.replay_records)}")
        print()

if __name__=="__main__":
    main()
