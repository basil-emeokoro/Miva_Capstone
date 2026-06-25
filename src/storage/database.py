from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from src.utils.config_loader import load_config, resolve_project_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    exam_code TEXT NOT NULL,
    institution TEXT NOT NULL,
    email TEXT NOT NULL,
    institution_type TEXT DEFAULT 'Generic',
    waec_registration_number TEXT,
    centre_number TEXT,
    candidate_number TEXT,
    matric_number TEXT,
    gender TEXT,
    date_of_birth TEXT,
    country TEXT,
    state TEXT,
    local_government_area TEXT,
    postal_code TEXT,
    street_address TEXT,
    enrolment_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consent (
    consent_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    consent_text_version TEXT NOT NULL,
    consent_status TEXT NOT NULL,
    consent_timestamp TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS face_enrolment (
    face_record_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    capture_direction TEXT NOT NULL,
    image_path TEXT,
    embedding_path TEXT,
    quality_score REAL NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS candidate_custom_fields (
    field_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS voice_enrolment (
    voice_record_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    phrase_used TEXT NOT NULL,
    audio_path TEXT,
    quality_score REAL NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    exam_code TEXT NOT NULL,
    monitoring_mode TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    authentication_status TEXT NOT NULL,
    session_status TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS device_checks (
    check_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    monitoring_mode TEXT NOT NULL,
    primary_camera_status TEXT NOT NULL,
    secondary_camera_status TEXT NOT NULL,
    microphone_status TEXT NOT NULL,
    lighting_status TEXT NOT NULL,
    candidate_presence_status TEXT NOT NULL,
    environment_declaration_status TEXT NOT NULL,
    mirror_status TEXT NOT NULL,
    overall_status TEXT NOT NULL,
    staff_override INTEGER NOT NULL DEFAULT 0,
    override_reason TEXT,
    checked_by TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source_module TEXT NOT NULL,
    event_type TEXT NOT NULL,
    risk_weight REAL NOT NULL,
    confidence REAL NOT NULL,
    camera_id TEXT,
    evidence_path TEXT,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fused_alerts (
    alert_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    contributing_events TEXT NOT NULL,
    explanation TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    current_risk_score INTEGER NOT NULL DEFAULT 0,
    rolling_risk_score INTEGER NOT NULL DEFAULT 0,
    risk_trend TEXT NOT NULL DEFAULT 'stable',
    contributing_modules TEXT NOT NULL DEFAULT '[]',
    reasoning_trace TEXT NOT NULL DEFAULT '[]',
    review_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviewer_decisions (
    review_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer_comment TEXT,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES fused_alerts(alert_id)
);

CREATE TABLE IF NOT EXISTS policy_decisions (
    decision_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    institution_profile TEXT NOT NULL,
    alert_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    agent_priority TEXT,
    agent_actions TEXT NOT NULL,
    recommended_actions TEXT NOT NULL,
    pause_assessment INTEGER NOT NULL DEFAULT 0,
    require_acknowledgement INTEGER NOT NULL DEFAULT 0,
    notify_role TEXT NOT NULL,
    preserve_evidence INTEGER NOT NULL DEFAULT 1,
    candidate_message TEXT NOT NULL,
    workflow_label TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incident_acknowledgements (
    acknowledgement_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    candidate_explanation TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    acknowledged_at TEXT NOT NULL,
    FOREIGN KEY(decision_id) REFERENCES policy_decisions(decision_id)
);

CREATE TABLE IF NOT EXISTS reviewer_incident_decisions (
    incident_review_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    reviewer_action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(decision_id) REFERENCES policy_decisions(decision_id)
);

CREATE TABLE IF NOT EXISTS viva_scenario_runs (
    run_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    session_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    alert_id TEXT,
    policy_decision_id TEXT,
    expected_risk_level TEXT NOT NULL,
    actual_risk_level TEXT NOT NULL,
    expected_policy_response TEXT NOT NULL,
    actual_policy_response TEXT NOT NULL,
    agent_recommendation TEXT NOT NULL,
    acknowledgement_required INTEGER NOT NULL DEFAULT 0,
    acknowledgement_recorded INTEGER NOT NULL DEFAULT 0,
    reviewer_decision_recorded INTEGER NOT NULL DEFAULT 0,
    final_outcome_status TEXT NOT NULL,
    pass_status TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT
);
"""


def database_path() -> Path:
    config = load_config()
    return resolve_project_path(config["storage"]["database_path"])


def get_connection(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path else database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(path: str | Path | None = None) -> None:
    with get_connection(path) as connection:
        connection.executescript(SCHEMA)
        _ensure_candidate_columns(connection)
        _ensure_fused_alert_columns(connection)
        _ensure_policy_decision_columns(connection)
        _ensure_viva_scenario_columns(connection)


def fetch_all(query: str, params: Iterable[object] = ()) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return list(connection.execute(query, tuple(params)))


def _ensure_candidate_columns(connection: sqlite3.Connection) -> None:
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(candidates)").fetchall()}
    required_columns = {
        "institution_type": "TEXT DEFAULT 'Generic'",
        "waec_registration_number": "TEXT",
        "centre_number": "TEXT",
        "candidate_number": "TEXT",
        "matric_number": "TEXT",
        "gender": "TEXT",
        "date_of_birth": "TEXT",
        "country": "TEXT",
        "state": "TEXT",
        "local_government_area": "TEXT",
        "postal_code": "TEXT",
        "street_address": "TEXT",
    }
    for column, definition in required_columns.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE candidates ADD COLUMN {column} {definition}")


def _ensure_fused_alert_columns(connection: sqlite3.Connection) -> None:
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(fused_alerts)").fetchall()}
    required_columns = {
        "confidence": "REAL NOT NULL DEFAULT 0",
        "current_risk_score": "INTEGER NOT NULL DEFAULT 0",
        "rolling_risk_score": "INTEGER NOT NULL DEFAULT 0",
        "risk_trend": "TEXT NOT NULL DEFAULT 'stable'",
        "contributing_modules": "TEXT NOT NULL DEFAULT '[]'",
        "reasoning_trace": "TEXT NOT NULL DEFAULT '[]'",
    }
    for column, definition in required_columns.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE fused_alerts ADD COLUMN {column} {definition}")


def _ensure_policy_decision_columns(connection: sqlite3.Connection) -> None:
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(policy_decisions)").fetchall()}
    required_columns = {
        "agent_priority": "TEXT",
        "agent_actions": "TEXT NOT NULL DEFAULT '[]'",
        "workflow_label": "TEXT NOT NULL DEFAULT 'Institutional incident workflow'",
    }
    for column, definition in required_columns.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE policy_decisions ADD COLUMN {column} {definition}")


def _ensure_viva_scenario_columns(connection: sqlite3.Connection) -> None:
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(viva_scenario_runs)").fetchall()}
    required_columns = {
        "agent_recommendation": "TEXT NOT NULL DEFAULT ''",
        "acknowledgement_required": "INTEGER NOT NULL DEFAULT 0",
        "acknowledgement_recorded": "INTEGER NOT NULL DEFAULT 0",
        "reviewer_decision_recorded": "INTEGER NOT NULL DEFAULT 0",
        "final_outcome_status": "TEXT NOT NULL DEFAULT 'pending_human_review'",
        "notes": "TEXT",
    }
    for column, definition in required_columns.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE viva_scenario_runs ADD COLUMN {column} {definition}")
