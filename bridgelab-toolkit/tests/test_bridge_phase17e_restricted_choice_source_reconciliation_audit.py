from benchmarks.phase17e_restricted_choice_source_reconciliation_audit import (
    audit_phase17e,
)


def test_phase17e_candidate_and_classification_remain_source_partial():
    result = audit_phase17e()

    assert result.phase == "17E"
    assert result.candidate == "RESTRICTED_CHOICE"
    assert result.classification_before == "SOURCE_PARTIAL"
    assert result.classification_after == "SOURCE_PARTIAL"


def test_phase17e_untracked_source_history_is_not_resolved():
    result = audit_phase17e()

    assert result.provenance_history_found_for_untracked_sources is False


def test_phase17e_protected_sources_remain_unsafe_to_stage():
    result = audit_phase17e()

    protected = {
        record.logical_path: record
        for record in result.source_records
        if record.provenance_classification
        in {
            "UNTRACKED_PROVENANCE_UNRESOLVED",
            "TRACKED_MODIFIED_USER_OWNED",
        }
    }

    assert protected
    assert all(record.safe_to_modify is False for record in protected.values())
    assert all(record.safe_to_stage is False for record in protected.values())


def test_phase17e_source_contract_evidence_is_present_but_incomplete():
    result = audit_phase17e()

    assert result.vacant_places_source_contract_present is True
    assert result.restricted_choice_observation_contract_present is True
    assert result.explicit_precision_rounding_contract_present is False


def test_phase17e_probability_question_scaffolding_exists_and_is_tested():
    result = audit_phase17e()

    assert result.restricted_choice_question_exists is True
    assert result.vacant_places_question_exists is True
    assert result.question_scaffolding_tested is True


def test_phase17e_restricted_choice_and_vacant_places_engines_are_not_registered():
    result = audit_phase17e()

    assert result.restricted_choice_engine_registered is False
    assert result.vacant_places_engine_registered is False
    assert result.registered_probability_engines == 1


def test_phase17e_production_remains_blocked():
    result = audit_phase17e()

    assert result.source_executable is False
    assert result.production_implementation_authorized is False
    assert result.new_production_recommendations == 0


def test_phase17e_unresolved_dependencies_remain_explicit():
    result = audit_phase17e()

    assert set(result.unresolved_dependencies) == {
        "SOURCE_PROVENANCE",
        "VACANT_PLACES_INPUT_CONTRACT",
        "OBSERVATION_SEMANTICS",
        "PRECISION_AND_ROUNDING",
        "ARCHITECTURE_READINESS",
    }


def test_phase17e_gate_classifications_are_conservative():
    result = audit_phase17e()
    gates = {gate.name: gate for gate in result.gate_results}

    assert gates["source_provenance"].classification == "BLOCKED"
    assert gates["source_provenance"].production_gate_passed is False

    for name in (
        "vacant_places_input_contract",
        "observation_semantics",
        "precision_and_rounding",
        "architecture_readiness",
    ):
        assert gates[name].classification == "SOURCE_PARTIAL"
        assert gates[name].production_gate_passed is False

    assert gates["no_hidden_information"].production_gate_passed is True
    assert gates["no_formula_invention"].production_gate_passed is True


def test_phase17e_selects_contract_enrichment_not_implementation():
    result = audit_phase17e()

    assert result.phase17f_direction == "RESTRICTED_CHOICE_CONTRACT_ENRICHMENT"
