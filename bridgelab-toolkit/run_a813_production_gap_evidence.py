from bridge.production_gap_evidence import classify_production_gap_evidence

def main():
    r=classify_production_gap_evidence(start_seed=1,count=10000)
    print("=== A8.13 production gap evidence: 10,000 deals ===")
    print(f"completed: {r.completed}")
    print(f"abstained: {r.abstained}")
    for g in r.groups:
        print(f"{g.evidence_class.value}: {g.count} ({g.share_of_abstentions:.2%})")
    print()
    print("NOTE: these are evidence classes, not policy-gap or engine-defect findings.")

if __name__=="__main__":
    main()
