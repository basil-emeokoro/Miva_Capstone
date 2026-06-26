from src.evaluation.viva_scenarios import execute_viva_scenario
from src.reporting.session_report import build_session_report
from src.storage.database import get_connection, initialize_database


def _seed_candidate_session(tmp_path, monkeypatch) -> tuple[str, str]:
    db_path = tmp_path / "serps_report.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO candidates(candidate_id, full_name, exam_code, institution, email, institution_type, enrolment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "CAND-REPORT",
                "Report Candidate",
                "CAND-REPORT",
                "Miva Open University",
                "report@example.com",
                "Miva",
                "face_enrolled",
                "2026-06-26T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO sessions(session_id, candidate_id, exam_code, monitoring_mode, start_time, authentication_status, session_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "SESSION-REPORT",
                "CAND-REPORT",
                "CAND-REPORT",
                "B",
                "2026-06-26T00:00:00+00:00",
                "prototype_authenticated",
                "active",
            ),
        )
    return "SESSION-REPORT", "CAND-REPORT"


def test_session_report_includes_governance_and_due_process_sections(tmp_path, monkeypatch) -> None:
    session_id, candidate_id = _seed_candidate_session(tmp_path, monkeypatch)
    execute_viva_scenario("mobile_phone_detected", session_id, candidate_id)

    report = build_session_report(session_id)

    assert report["session_id"] == session_id
    assert report["event_count"] > 0
    assert report["alert_count"] > 0
    assert report["policy_decision_count"] == 1
    assert report["viva_scenario_run_count"] == 1
    assert "institutional_policy_decisions" in report["report_sections"]
    assert "viva_scenario_validation" in report["report_sections"]
    assert report["policy_decisions"][0]["candidate_id"] == candidate_id
    assert report["viva_scenario_validation"][0]["scenario_name"] == "Mobile phone detected"
    assert report["evidence_pack_manifest"][0]["acknowledgement_required"] is True
    assert "do not declare misconduct" in report["prototype_note"]
    assert "does not declare misconduct" in report["due_process_note"]
