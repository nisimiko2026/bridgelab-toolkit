"""A9.1 contract smoke check."""
from bridge.evidence_review_contract import (
    EvidenceReference,
    ReviewClassification,
    ReviewDisposition,
    review,
)


def main():
    x = review(
        replay_key="sayc-production@1:seed:2",
        classification=ReviewClassification.INSUFFICIENT_EVIDENCE,
        disposition=ReviewDisposition.NEEDS_MORE_EVIDENCE,
        rationale=(
            "A8 classified this case for opening-Pass review; A9.1 does not "
            "infer the required opening action."
        ),
        evidence=(
            EvidenceReference(
                "A8.13",
                "The case belongs to opening-pass-review, not a proven policy gap.",
            ),
        ),
    )
    print("=== A9.1 EVIDENCE REVIEW CONTRACT ===")
    print("replay:", x.replay_key)
    print("classification:", x.classification.value)
    print("disposition:", x.disposition.value)
    print("evidence:", len(x.evidence))
    print("policy change: none")


if __name__ == "__main__":
    main()
