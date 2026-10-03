"""A8.15 consolidated 10,000-deal production benchmark report."""
from bridge.production_benchmark_report import build_consolidated_production_benchmark_report


def main():
    r=build_consolidated_production_benchmark_report(
        start_seed=1,count=10000,per_class_limit=5
    )
    s=r.summary
    print("=== A8.15 CONSOLIDATED PRODUCTION BENCHMARK ===")
    print(f"seed window: {s.start_seed}-{s.start_seed+s.runs-1}")
    print(f"runs: {s.runs}")
    print(f"production_calls: {s.production_calls}")
    print(f"fixture_calls: {s.fixture_calls}")
    print(f"completed: {s.completed} ({s.completion_rate:.2%})")
    print(f"abstained: {s.abstained} ({s.abstention_rate:.2%})")

    print("\nEVIDENCE CLASSIFICATION")
    for g in r.evidence.groups:
        print(f"  {g.evidence_class.value}: {g.count} ({g.share_of_abstentions:.2%})")

    print("\nABSTENTION DEPTH")
    for g in sorted(r.concentration.by_depth,key=lambda x:int(x.key)):
        print(f"  depth {g.key}: {g.count} ({g.share_of_abstentions:.2%})")

    print("\nREPRESENTATIVE REPLAY CASES")
    for g in r.representatives.groups:
        seeds=", ".join(str(c.seed) for c in g.cases)
        print(f"  {g.evidence_class.value}: available={g.available_count}; sample seeds={seeds}")

    print("\nInterpretation guard: descriptive benchmark evidence only; no ranking, correctness, policy-gap, or engine-defect conclusion.")


if __name__=="__main__":
    main()
