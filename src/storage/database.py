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


def fetch_all(query: str, params: Iterable[object] = ()) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return list(connection.execute(query, tuple(params)))
