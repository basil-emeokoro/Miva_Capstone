from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import EvidenceEvent
from src.vision.face_detector import FaceDetectionResult


@dataclass(frozen=True)
class VisualEventDefinition:
    label: str
    source_module: str
    event_type: str
    risk_weight: float
    confidence: float
    camera_id: str
    description: str
    prototype_only: bool = True


VISUAL_EVENT_DEFINITIONS: dict[str, VisualEventDefinition] = {
    "face_present": VisualEventDefinition(
        "Face present",
        "primary_camera",
        "face_present",
        0.02,
        0.9,
        "primary",
        "Candidate face is visible in the primary camera.",
        prototype_only=False,
    ),
    "face_absent": VisualEventDefinition(
        "Face absent",
        "primary_camera",
        "face_absent",
        0.65,
        0.82,
        "primary",
        "Candidate face is absent from the primary camera.",
    ),
    "face_obstructed": VisualEventDefinition(
        "Face obstructed",
        "primary_camera",
        "face_obstructed",
        0.55,
        0.74,
        "primary",
        "Candidate face appears obstructed or unclear.",
    ),
    "camera_obstructed": VisualEventDefinition(
        "Camera obstructed",
        "primary_camera",
        "camera_obstructed",
        0.7,
        0.78,
        "primary",
        "Camera view appears blocked, dark, or unusable.",
    ),
    "multiple_persons_detected": VisualEventDefinition(
        "Multiple persons detected",
        "secondary_camera",
        "multiple_persons_detected",
        0.8,
        0.86,
        "secondary",
        "More than one person appears in the monitored environment.",
    ),
    "looking_away": VisualEventDefinition(
        "Looking away",
        "primary_camera",
        "looking_away",
        0.35,
        0.76,
        "primary",
        "Candidate appears to be looking away from the screen.",
    ),
    "head_movement_anomaly": VisualEventDefinition(
        "Head movement anomaly",
        "primary_camera",
        "head_movement_anomaly",
        0.42,
        0.72,
        "primary",
        "Candidate head movement is outside the expected monitoring range.",
    ),
    "mobile_phone_detected": VisualEventDefinition(
        "Mobile phone detected",
        "secondary_camera",
        "mobile_phone_detected",
        0.75,
        0.88,
        "secondary",
        "Mobile phone detected in the environment view.",
    ),
    "unauthorised_object_detected": VisualEventDefinition(
        "Unauthorised object detected",
        "secondary_camera",
        "unauthorised_object_detected",
        0.72,
        0.82,
        "secondary",
        "Unauthorised object detected in the monitoring area.",
    ),
}


VISUAL_EVENT_PRESETS = {definition.label: definition for definition in VISUAL_EVENT_DEFINITIONS.values()}


def create_visual_event(
    session_id: str,
    candidate_id: str,
    event_type: str,
    camera_id: str | None = None,
    confidence: float | None = None,
    description: str | None = None,
    evidence_path: str | None = None,
) -> EvidenceEvent:
    try:
        definition = VISUAL_EVENT_DEFINITIONS[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported visual event type: {event_type}") from exc
    resolved_camera_id = camera_id or definition.camera_id
    source_module = f"{resolved_camera_id}_camera" if resolved_camera_id in {"primary", "secondary"} else definition.source_module
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module=source_module,
        event_type=definition.event_type,
        risk_weight=definition.risk_weight,
        confidence=confidence if confidence is not None else definition.confidence,
        camera_id=resolved_camera_id,
        evidence_path=evidence_path,
        description=description or definition.description,
    )


def create_demo_visual_event(session_id: str, candidate_id: str, preset_name: str) -> EvidenceEvent:
    definition = VISUAL_EVENT_PRESETS[preset_name]
    return create_visual_event(session_id, candidate_id, definition.event_type)


def create_event_from_face_detection(
    session_id: str,
    candidate_id: str,
    result: FaceDetectionResult,
    camera_id: str = "primary",
    evidence_path: str | None = None,
) -> EvidenceEvent:
    return create_visual_event(
        session_id=session_id,
        candidate_id=candidate_id,
        event_type=result.status,
        camera_id=camera_id,
        confidence=result.confidence,
        description=result.description,
        evidence_path=evidence_path,
    )


def visual_event_types() -> list[str]:
    return list(VISUAL_EVENT_DEFINITIONS)


def is_visual_event(event_type: str) -> bool:
    return event_type in VISUAL_EVENT_DEFINITIONS
