from __future__ import annotations

from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


def log_audit(actor: str, action: str, target: str, details: str = "") -> str:
    audit_id = f"AUD-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs(audit_id, actor, action, target, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (audit_id, actor, action, target, utc_now_iso(), details),
        )
    return audit_id
