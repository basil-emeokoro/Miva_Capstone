from __future__ import annotations

from src.fusion.event_schema import EvidenceEvent


VISUAL_EVENT_PRESETS = {
    "Brief look away": ("primary_camera", "brief_look_away", 0.2, 0.7, "primary", "Candidate briefly looked away."),
    "Repeated looking away": ("primary_camera", "repeated_looking_away", 0.45, 0.84, "primary", "Candidate repeatedly looked away from the screen."),
    "Mobile phone detected": ("secondary_camera", "mobile_phone_detected", 0.75, 0.88, "secondary", "Mobile phone detected in the environment view."),
    "Second person detected": ("secondary_camera", "second_person_detected", 0.8, 0.86, "secondary", "Additional person detected in the environment view."),
    "Candidate absent": ("primary_camera", "candidate_absent", 0.65, 0.82, "primary", "Candidate face was absent from primary camera view."),
    "Face mismatch": ("identity", "face_mismatch", 0.95, 0.9, "primary", "Current face confidence does not match enrolled identity."),
}


def create_demo_visual_event(session_id: str, candidate_id: str, preset_name: str) -> EvidenceEvent:
    source, event_type, weight, confidence, camera_id, description = VISUAL_EVENT_PRESETS[preset_name]
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module=source,
        event_type=event_type,
        risk_weight=weight,
        confidence=confidence,
        camera_id=camera_id,
        description=description,
    )
