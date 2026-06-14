from __future__ import annotations

import json
from uuid import uuid4

from src.session.environment_checker import DeviceCheckEvaluation
from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


def save_device_check(
    candidate_id: str,
    evaluation: DeviceCheckEvaluation,
    checked_by: str,
    staff_override: bool = False,
    override_reason: str = "",
) -> str:
    check_id = f"CHK-{uuid4().hex[:8].upper()}"
    statuses = evaluation.statuses
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO device_checks(
                check_id, candidate_id, monitoring_mode,
                primary_camera_status, secondary_camera_status, microphone_status,
                lighting_status, candidate_presence_status, environment_declaration_status,
                mirror_status, overall_status, staff_override, override_reason,
                checked_by, checked_at, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                check_id,
                candidate_id,
                evaluation.monitoring_mode,
                statuses["primary_camera"],
                statuses["secondary_camera"],
                statuses["microphone"],
                statuses["lighting"],
                statuses["candidate_presence"],
                statuses["environment_declaration"],
                statuses["mirror"],
                evaluation.overall_status,
                1 if staff_override else 0,
                override_reason.strip(),
                checked_by,
                utc_now_iso(),
                json.dumps(evaluation.details),
            ),
        )
    return check_id


def latest_device_check(candidate_id: str, monitoring_mode: str | None = None) -> dict[str, object] | None:
    query = "SELECT * FROM device_checks WHERE candidate_id = ?"
    params: list[object] = [candidate_id]
    if monitoring_mode:
        query += " AND monitoring_mode = ?"
        params.append(monitoring_mode.upper())
    query += " ORDER BY checked_at DESC LIMIT 1"
    with get_connection() as connection:
        row = connection.execute(query, tuple(params)).fetchone()
    return dict(row) if row else None
