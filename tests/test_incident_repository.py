from src.fusion.event_schema import EvidenceEvent, FusedAlert
from src.policy.incident_repository import (
    build_evidence_package,
    get_policy_decision_for_alert,
    list_candidate_acknowledgements,
    list_reviewer_incident_decisions,
    record_candidate_acknowledgement,
    record_reviewer_incident_decision,
    save_policy_decision,
)
from src.policy.policy_engine import evaluate_institutional_policy
from src.storage.database import get_connection, initialize_database
from src.storage.event_repository import save_alert, save_event


def test_incident_records_acknowledgement_reviewer_action_and_package(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_incidents.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO candidates(candidate_id, full_name, exam_code, institution, email, institution_type, enrolment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "CAND-IPIME",
                "Policy Candidate",
                "CAND-IPIME",
                "WAEC",
                "candidate@waec.org.ng",
                "WAEC",
                "face_enrolled",
                "2026-06-25T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO sessions(session_id, candidate_id, exam_code, monitoring_mode, start_time, authentication_status, session_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("SESSION-IPIME", "CAND-IPIME", "CAND-IPIME", "B", "2026-06-25T00:00:00+00:00", "prototype_authenticated", "active"),
        )
    event = EvidenceEvent(
        session_id="SESSION-IPIME",
        candidate_id="CAND-IPIME",
        source_module="primary_camera",
        event_type="looking_away",
        risk_weight=0.6,
        confidence=0.9,
        description="Candidate repeatedly looked away.",
    )
    save_event(event)
    alert = FusedAlert(
        session_id="SESSION-IPIME",
        candidate_id="CAND-IPIME",
        start_time=event.timestamp,
        end_time=event.timestamp,
        risk_score=72,
        risk_level="High",
        alert_type="monitoring_alert",
        contributing_events=[event.event_id],
        explanation="Looking away pattern produced a high contextual risk.",
        recommended_action="Escalate",
        confidence=0.9,
    )
    save_alert(alert)

    decision = evaluate_institutional_policy(alert.to_dict(), "WAEC")
    decision_id = save_policy_decision(decision)

    assert get_policy_decision_for_alert(alert.alert_id)["decision_id"] == decision_id
    ack_id = record_candidate_acknowledgement(decision_id, "CAND-IPIME", "I was checking the screen instruction.", True)
    reviewer_action_id = record_reviewer_incident_decision(decision_id, "Reviewer", "Continue Monitoring", "Explanation accepted for now.")

    acknowledgements = list_candidate_acknowledgements(decision_id)
    reviewer_actions = list_reviewer_incident_decisions(decision_id)
    package = build_evidence_package(decision_id)

    assert acknowledgements[0]["acknowledgement_id"] == ack_id
    assert reviewer_actions[0]["incident_review_id"] == reviewer_action_id
    assert package["candidate_profile"]["candidate_id"] == "CAND-IPIME"
    assert package["contextual_risk_assessment"]["alert_id"] == alert.alert_id
    assert package["contributing_evidence"][0]["event_id"] == event.event_id
