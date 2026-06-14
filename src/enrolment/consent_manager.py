from __future__ import annotations

from uuid import uuid4

from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


CONSENT_NOTICE = """
I acknowledge that this prototype may process webcam, microphone, identity, and session
event metadata for remote-proctoring demonstration. AI-generated alerts are reviewed by a
human reviewer before any final decision.
""".strip()


def capture_consent(candidate_id: str, consent_status: str = "accepted") -> str:
    consent_id = f"CON-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO consent(consent_id, candidate_id, consent_text_version, consent_status, consent_timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (consent_id, candidate_id, "prototype-v1", consent_status, utc_now_iso()),
        )
    return consent_id
