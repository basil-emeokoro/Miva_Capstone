from __future__ import annotations

from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


def register_candidate(full_name: str, exam_code: str, institution: str, email: str) -> str:
    candidate_id = f"CAND-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO candidates(candidate_id, full_name, exam_code, institution, email, enrolment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (candidate_id, full_name, exam_code, institution, email, "registered", utc_now_iso()),
        )
    return candidate_id


def save_candidate_custom_fields(candidate_id: str, fields: dict[str, str]) -> None:
    with get_connection() as connection:
        for field_name, field_value in fields.items():
            if not field_name.strip() or not field_value.strip():
                continue
            connection.execute(
                """
                INSERT INTO candidate_custom_fields(field_id, candidate_id, field_name, field_value, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"FLD-{uuid4().hex[:8].upper()}", candidate_id, field_name.strip(), field_value.strip(), utc_now_iso()),
            )


def list_candidate_custom_fields(candidate_id: str) -> list[dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM candidate_custom_fields
            WHERE candidate_id = ?
            ORDER BY created_at
            """,
            (candidate_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_candidates() -> list[dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def update_enrolment_status(candidate_id: str, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE candidates SET enrolment_status = ? WHERE candidate_id = ?",
            (status, candidate_id),
        )
