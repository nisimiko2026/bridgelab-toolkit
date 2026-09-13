from benchmarks.source_authority_registry_audit import (
    run_source_authority_registry_audit,
)


def test_source_authority_registry_audit_passes_current_bidding_inventory():
    audit = run_source_authority_registry_audit()

    assert audit.audit_status == "PASS"
    assert len(audit.article_ids) == 16
    assert audit.missing_articles == ()
    assert audit.unexpected_authority == ()
    assert audit.unexpected_coverage == ()