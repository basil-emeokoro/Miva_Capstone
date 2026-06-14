from __future__ import annotations

import re
from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


def register_candidate(
    full_name: str,
    candidate_id: str,
    institution: str,
    email: str,
    institution_type: str = "Generic",
    waec_registration_number: str | None = None,
    matric_number: str | None = None,
    gender: str | None = None,
    date_of_birth: str | None = None,
    country: str | None = None,
    state: str | None = None,
    local_government_area: str | None = None,
    postal_code: str | None = None,
    street_address: str | None = None,
) -> str:
    resolved_candidate_id = normalize_candidate_id(candidate_id, institution_type)
    centre_number = resolved_candidate_id[:7] if institution_type == "WAEC" else None
    candidate_number = resolved_candidate_id[-3:] if institution_type == "WAEC" else None
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO candidates(
                candidate_id, full_name, exam_code, institution, email, institution_type,
                waec_registration_number, centre_number, candidate_number, matric_number,
                gender, date_of_birth, country, state, local_government_area, postal_code, street_address,
                enrolment_status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_candidate_id,
                full_name,
                resolved_candidate_id,
                institution,
                email,
                institution_type,
                waec_registration_number,
                centre_number,
                candidate_number,
                matric_number,
                gender,
                date_of_birth,
                country,
                state,
                local_government_area,
                postal_code,
                street_address,
                "registered",
                utc_now_iso(),
            ),
        )
    return resolved_candidate_id


def normalize_candidate_id(candidate_id: str, institution_type: str) -> str:
    value = candidate_id.strip().upper()
    if not value:
        raise ValueError("Candidate ID is required.")
    if institution_type == "WAEC":
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("WAEC Candidate ID must be exactly 10 digits.")
        return value
    if institution_type == "Miva":
        if not re.fullmatch(r"\d+", value):
            raise ValueError("Miva Candidate ID must contain digits only.")
        return value
    return value


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
