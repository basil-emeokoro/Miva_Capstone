from __future__ import annotations

from uuid import uuid4

from src.storage.candidate_repository import update_enrolment_status
from src.storage.database import get_connection
from src.utils.time_utils import utc_now_iso


FACE_DIRECTIONS = ["front", "left", "right", "slight_up", "slight_down", "centre"]


def record_face_sample(candidate_id: str, capture_direction: str, image_path: str | None = None, quality_score: float = 0.8) -> str:
    if capture_direction not in FACE_DIRECTIONS:
        raise ValueError(f"Unsupported face direction: {capture_direction}")

    face_record_id = f"FACE-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO face_enrolment(face_record_id, candidate_id, capture_direction, image_path, embedding_path, quality_score, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (face_record_id, candidate_id, capture_direction, image_path, None, quality_score, utc_now_iso()),
        )
    return face_record_id


def complete_prototype_face_enrolment(candidate_id: str) -> list[str]:
    records = [record_face_sample(candidate_id, direction, quality_score=0.85) for direction in FACE_DIRECTIONS]
    update_enrolment_status(candidate_id, "face_enrolled")
    return records


def list_face_samples(candidate_id: str) -> list[dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM face_enrolment
            WHERE candidate_id = ?
            ORDER BY captured_at DESC
            """,
            (candidate_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def captured_directions(candidate_id: str) -> set[str]:
    return {
        str(sample["capture_direction"])
        for sample in list_face_samples(candidate_id)
        if sample.get("image_path")
    }


def is_face_enrolment_complete(candidate_id: str) -> bool:
    return set(FACE_DIRECTIONS).issubset(captured_directions(candidate_id))
