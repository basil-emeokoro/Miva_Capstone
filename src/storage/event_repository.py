from __future__ import annotations

import json

from src.fusion.event_schema import EvidenceEvent, FusedAlert
from src.storage.database import get_connection


def save_event(event: EvidenceEvent) -> None:
    data = event.to_dict()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO events(event_id, session_id, candidate_id, timestamp, source_module, event_type,
            risk_weight, confidence, camera_id, evidence_path, description)
            VALUES (:event_id, :session_id, :candidate_id, :timestamp, :source_module, :event_type,
            :risk_weight, :confidence, :camera_id, :evidence_path, :description)
            """,
            data,
        )


def save_alert(alert: FusedAlert) -> None:
    data = alert.to_dict()
    data["contributing_events"] = json.dumps(data["contributing_events"])
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO fused_alerts(alert_id, session_id, candidate_id, start_time, end_time,
            risk_score, risk_level, alert_type, contributing_events, explanation, recommended_action, review_status)
            VALUES (:alert_id, :session_id, :candidate_id, :start_time, :end_time, :risk_score,
            :risk_level, :alert_type, :contributing_events, :explanation, :recommended_action, :review_status)
            """,
            data,
        )


def list_events(session_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM events"
    params: tuple[object, ...] = ()
    if session_id:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY timestamp DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def list_alerts(session_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM fused_alerts"
    params: tuple[object, ...] = ()
    if session_id:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY start_time DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]
