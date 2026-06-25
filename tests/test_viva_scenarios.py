from src.evaluation.viva_scenarios import (
    execute_viva_scenario,
    get_viva_scenario_run,
    list_viva_scenario_runs,
    record_viva_candidate_acknowledgement,
    record_viva_reviewer_decision,
)
from src.policy.incident_repository import (
    build_evidence_package,
    list_candidate_acknowledgements,
    list_reviewer_incident_decisions,
)
from src.storage.database import get_connection, initialize_database
from src.storage.event_repository import list_alerts, list_events


def _seed_candidate_session(tmp_path, monkeypatch, candidate_id: str = "CAND-VIVA") -> tuple[str, str]:
    db_path = tmp_path / "serps_viva.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO candidates(candidate_id, full_name, exam_code, institution, email, institution_type, enrolment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                "Viva Candidate",
                candidate_id,
                "Miva Open University",
                "viva@example.com",
                "Miva",
                "face_enrolled",
                "2026-06-25T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO sessions(session_id, candidate_id, exam_code, monitoring_mode, start_time, authentication_status, session_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "SESSION-VIVA",
                candidate_id,
                candidate_id,
                "B",
                "2026-06-25T00:00:00+00:00",
                "prototype_authenticated",
                "active",
            ),
        )
    return "SESSION-VIVA", candidate_id


def test_normal_scenario_remains_low_risk(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("normal_candidate_behaviour", session_id, candidate_id)

    assert result.actual_risk_level == "Low"
    assert result.pass_status == "Pass"
    assert result.acknowledgement_required is False
    assert "committed malpractice" not in result.alert.explanation.lower()
    assert list_events(session_id)
    assert list_alerts(session_id)


def test_isolated_event_does_not_trigger_severe_policy_action(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("brief_looking_away", session_id, candidate_id)

    assert result.actual_risk_level == "Low"
    assert result.acknowledgement_required is False
    assert result.actual_policy_response == "Generic observation workflow"


def test_repeated_events_increase_risk(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("repeated_gaze_deviation", session_id, candidate_id)

    assert result.actual_risk_level in {"Medium", "High", "Critical"}
    assert result.actual_policy_response == "University warning and review workflow"
    assert result.alert.risk_score >= 50


def test_multimodal_events_escalate_risk(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("camera_disconnected_suspicious", session_id, candidate_id)

    assert result.actual_risk_level in {"High", "Critical"}
    assert result.acknowledgement_required is True
    assert "WAEC incident acknowledgement workflow" == result.actual_policy_response


def test_critical_scenario_triggers_incident_acknowledgement(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("critical_combined", session_id, candidate_id)

    assert result.actual_risk_level == "Critical"
    assert result.acknowledgement_required is True
    assert result.actual_policy_response == "Generic critical-risk senior review workflow"
    assert result.final_outcome_status == "awaiting_candidate_acknowledgement"


def test_ipime_does_not_bypass_human_review(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)

    result = execute_viva_scenario("mobile_phone_detected", session_id, candidate_id)
    stored_run = get_viva_scenario_run(result.run_id)

    assert stored_run is not None
    assert stored_run["reviewer_decision_recorded"] is False
    assert stored_run["final_outcome_status"] in {"awaiting_candidate_acknowledgement", "awaiting_human_review"}
    assert "committed malpractice" not in result.alert.explanation.lower()


def test_candidate_acknowledgement_and_reviewer_decision_are_traceable(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)
    result = execute_viva_scenario("critical_combined", session_id, candidate_id)

    ack_id = record_viva_candidate_acknowledgement(
        result.run_id,
        "I acknowledge the concern and request human review.",
        True,
    )
    review_id = record_viva_reviewer_decision(
        result.run_id,
        "Reviewer",
        "Refer to Senior Reviewer",
        "Critical validation scenario requires senior review.",
    )

    stored_run = get_viva_scenario_run(result.run_id)
    package = build_evidence_package(result.policy_decision_id)

    assert stored_run is not None
    assert stored_run["acknowledgement_recorded"] is True
    assert stored_run["reviewer_decision_recorded"] is True
    assert stored_run["final_outcome_status"] == "refer_to_senior_reviewer"
    assert list_candidate_acknowledgements(result.policy_decision_id)[0]["acknowledgement_id"] == ack_id
    assert list_reviewer_incident_decisions(result.policy_decision_id)[0]["incident_review_id"] == review_id
    assert package["contextual_risk_assessment"]["alert_id"] == result.alert.alert_id
    assert package["contributing_evidence"]


def test_viva_scenario_summary_is_persisted(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)
    result = execute_viva_scenario("background_speech", session_id, candidate_id)

    runs = list_viva_scenario_runs(session_id)

    assert runs[0]["run_id"] == result.run_id
    assert runs[0]["scenario_name"] == "Background speech during exam"
    assert runs[0]["pass_status"] in {"Pass", "Needs Review"}
