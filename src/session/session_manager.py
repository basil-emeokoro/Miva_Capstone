from __future__ import annotations

from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


def start_session(candidate_id: str, exam_code: str, monitoring_mode: str = "B") -> str:
    session_id = f"SESSION-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO sessions(session_id, candidate_id, exam_code, monitoring_mode, start_time, authentication_status, session_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, candidate_id, exam_code, monitoring_mode, utc_now_iso(), "prototype_authenticated", "active"),
        )
    return session_id


def end_session(session_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE sessions SET end_time = ?, session_status = ? WHERE session_id = ?",
            (utc_now_iso(), "ended", session_id),
        )


def list_sessions() -> list[dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM sessions ORDER BY start_time DESC").fetchall()
    return [dict(row) for row in rows]
