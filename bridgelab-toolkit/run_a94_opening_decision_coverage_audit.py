"""A9.4 full 10,000-deal opening decision coverage audit."""
from bridge.opening_decision_coverage_audit import (
    OpeningCoverageFamily,
    audit_opening_decision_coverage,
)


def main():
    r = audit_opening_decision_coverage(start_seed=1, count=10000)
    print("=== A9.4 OPENING DECISION COVERAGE AUDIT ===")
    print(f"opening-review population: {r.population}")

    print("\nCOVERAGE FAMILIES")
    for g in r.groups:
        print(f"  {g.family.value}: {g.count} ({g.share_of_population:.2%})")

    print("\nNORMAL-STRENGTH SHAPES")
    for shape, n in r.normal_strength_shape_counts:
        print(f"  {'-'.join(map(str, shape))}: {n}")

    print("\nNORMAL-STRENGTH FAMILY SEEDS")
    for family in (
        OpeningCoverageFamily.EQUAL_FIVE_PLUS_MAJORS,
        OpeningCoverageFamily.EQUAL_FIVE_MINORS,
        OpeningCoverageFamily.OTHER_NORMAL_STRENGTH_UNRESOLVED,
    ):
        group = next((g for g in r.groups if g.family is family), None)
        print(f"  {family.value}: {'' if group is None else ','.join(map(str, group.seeds))}")

    print("\nInterpretation guard: equal-major/equal-minor families explain the "
          "normal-strength abstentions; they do not authorize a tie-break. "
          "Below-normal-strength cases remain unresolved review evidence, not Pass.")


if __name__ == "__main__":
    main()
