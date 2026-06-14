from __future__ import annotations

from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


VALID_DECISIONS = {"accepted", "rejected", "escalated"}


def record_review(alert_id: str, reviewer_id: str, decision: str, comment: str = "") -> str:
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Unsupported reviewer decision: {decision}")

    review_id = f"REV-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reviewer_decisions(review_id, alert_id, reviewer_id, decision, reviewer_comment, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review_id, alert_id, reviewer_id, decision, comment, utc_now_iso()),
        )
        connection.execute(
            "UPDATE fused_alerts SET review_status = ? WHERE alert_id = ?",
            (decision, alert_id),
        )
    return review_id
