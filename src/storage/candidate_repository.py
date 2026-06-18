from __future__ import annotations

import sqlite3
import re
from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
INSTITUTION_EMAIL_DEFAULTS = {
    "Miva": "candidate@miva.edu.ng",
    "WAEC": "candidate@waec.org.ng",
    "Generic": "candidate@example.com",
}


class CandidateDuplicateError(ValueError):
    def __init__(self, message: str, existing_candidate_id: str):
        super().__init__(message)
        self.existing_candidate_id = existing_candidate_id


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
    enrolment_status: str = "registered_pending_face_capture",
) -> str:
    resolved_candidate_id = normalize_candidate_id(candidate_id, institution_type)
    resolved_email = validate_email(email)
    centre_number = resolved_candidate_id[:7] if institution_type == "WAEC" else None
    candidate_number = resolved_candidate_id[-3:] if institution_type == "WAEC" else None
    duplicate = find_duplicate_candidate(
        candidate_id=resolved_candidate_id,
        email=resolved_email,
        waec_registration_number=waec_registration_number,
        matric_number=matric_number,
    )
    if duplicate:
        raise CandidateDuplicateError(_duplicate_message(duplicate), str(duplicate["candidate_id"]))
    with get_connection() as connection:
        try:
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
                    full_name.strip(),
                    resolved_candidate_id,
                    institution.strip(),
                    resolved_email,
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
                    enrolment_status,
                    utc_now_iso(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise CandidateDuplicateError(
                "This candidate identifier already exists. Open the existing candidate profile or use a different ID.",
                resolved_candidate_id,
            ) from exc
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
            raise ValueError("Miva Student ID must contain digits only.")
        return value
    return value


def validate_email(email: str) -> str:
    value = email.strip().lower()
    if not value:
        raise ValueError("Email address is required.")
    if not EMAIL_PATTERN.fullmatch(value):
        raise ValueError("Enter a valid email address.")
    return value


def default_email_for_institution(institution_type: str) -> str:
    return INSTITUTION_EMAIL_DEFAULTS.get(institution_type, INSTITUTION_EMAIL_DEFAULTS["Generic"])


def generate_candidate_id(institution_type: str) -> str:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT candidate_id FROM candidates WHERE institution_type = ?",
            (institution_type,),
        ).fetchall()
    values = [str(row["candidate_id"]) for row in rows]
    if institution_type == "WAEC":
        numeric_values = [int(value) for value in values if re.fullmatch(r"\d{10}", value)]
        return str((max(numeric_values) if numeric_values else 1234567000) + 1).zfill(10)
    if institution_type == "Miva":
        numeric_values = [int(value) for value in values if re.fullmatch(r"\d+", value)]
        return str((max(numeric_values) if numeric_values else 10000000) + 1)
    suffixes = [int(value.rsplit("-", 1)[-1]) for value in values if re.fullmatch(r"CAND-DEMO-\d{3,}", value)]
    return f"CAND-DEMO-{(max(suffixes) if suffixes else 0) + 1:03d}"


def find_duplicate_candidate(
    candidate_id: str | None = None,
    email: str | None = None,
    waec_registration_number: str | None = None,
    matric_number: str | None = None,
    exclude_candidate_id: str | None = None,
) -> dict[str, object] | None:
    clauses: list[str] = []
    params: list[str] = []
    if candidate_id:
        clauses.append("UPPER(candidate_id) = UPPER(?)")
        params.append(candidate_id.strip())
    if email:
        clauses.append("LOWER(email) = LOWER(?)")
        params.append(email.strip())
    if waec_registration_number:
        clauses.append("UPPER(waec_registration_number) = UPPER(?)")
        params.append(waec_registration_number.strip())
    if matric_number:
        clauses.append("UPPER(matric_number) = UPPER(?)")
        params.append(matric_number.strip())
    if not clauses:
        return None
    where_sql = f"({' OR '.join(clauses)})"
    if exclude_candidate_id:
        where_sql = f"{where_sql} AND candidate_id <> ?"
        params.append(exclude_candidate_id)
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM candidates WHERE {where_sql} LIMIT 1",
            tuple(params),
        ).fetchone()
    return dict(row) if row else None


def _duplicate_message(candidate: dict[str, object]) -> str:
    institution_type = candidate.get("institution_type")
    id_label = "Student ID" if institution_type == "Miva" else "Candidate ID"
    return (
        f"A candidate already exists with this {id_label}, email, matric number, or registration number: "
        f"{candidate.get('full_name')} ({candidate.get('candidate_id')}). Open the existing profile or use different details."
    )


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


def get_candidate(candidate_id: str) -> dict[str, object] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)).fetchone()
    return dict(row) if row else None


def update_enrolment_status(candidate_id: str, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE candidates SET enrolment_status = ? WHERE candidate_id = ?",
            (status, candidate_id),
        )


def update_candidate_biodata(
    candidate_id: str,
    full_name: str,
    institution: str,
    email: str,
    waec_registration_number: str | None = None,
    matric_number: str | None = None,
    gender: str | None = None,
    date_of_birth: str | None = None,
    country: str | None = None,
    state: str | None = None,
    local_government_area: str | None = None,
    postal_code: str | None = None,
    street_address: str | None = None,
) -> None:
    resolved_email = validate_email(email)
    duplicate = find_duplicate_candidate(
        email=resolved_email,
        waec_registration_number=waec_registration_number,
        matric_number=matric_number,
        exclude_candidate_id=candidate_id,
    )
    if duplicate:
        raise CandidateDuplicateError(_duplicate_message(duplicate), str(duplicate["candidate_id"]))
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE candidates
            SET full_name = ?, institution = ?, email = ?, waec_registration_number = ?,
                matric_number = ?, gender = ?, date_of_birth = ?, country = ?, state = ?,
                local_government_area = ?, postal_code = ?, street_address = ?
            WHERE candidate_id = ?
            """,
            (
                full_name.strip(),
                institution.strip(),
                resolved_email,
                waec_registration_number,
                matric_number,
                gender,
                date_of_birth,
                country,
                state,
                local_government_area,
                postal_code,
                street_address,
                candidate_id,
            ),
        )
