from __future__ import annotations

from pathlib import Path

import numpy as np

from src.enrolment.face_enrolment import list_face_samples
from src.vision.face_quality import extract_face_embedding


def verify_face_against_enrolment(candidate_id: str, image_bytes: bytes, threshold: float = 0.65) -> dict[str, object]:
    probe = extract_face_embedding(image_bytes)
    templates = _load_templates(candidate_id)
    if not templates:
        return {
            "matched": False,
            "confidence": 0.0,
            "message": "No enrolled face templates are available for this candidate.",
        }

    best_score = max(_cosine_similarity(probe, template) for template in templates)
    return {
        "matched": best_score >= threshold,
        "confidence": round(float(best_score), 3),
        "message": "Face matched enrolled template." if best_score >= threshold else "Face did not match enrolled template.",
    }


def _load_templates(candidate_id: str) -> list[np.ndarray]:
    templates: list[np.ndarray] = []
    for sample in list_face_samples(candidate_id):
        embedding_path = sample.get("embedding_path")
        if not embedding_path:
            continue
        path = Path(str(embedding_path))
        if path.exists():
            templates.append(np.load(path))
    return templates


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0:
        return 0.0
    return float(np.dot(left, right) / denominator)
