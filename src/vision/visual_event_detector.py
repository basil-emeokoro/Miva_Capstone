from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import EvidenceEvent
from src.vision.face_detector import FaceDetectionResult
from src.vision.head_pose_estimator import estimate_head_pose_from_position
from src.vision.object_detector import analyse_objects_with_yolo


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


@dataclass(frozen=True)
class VisualFrameAnalysis:
    events: list[EvidenceEvent]
    detector_notes: list[str]


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
    "laptop_or_tablet_detected": VisualEventDefinition(
        "Laptop or tablet detected",
        "secondary_camera",
        "laptop_or_tablet_detected",
        0.62,
        0.78,
        "secondary",
        "Laptop or tablet detected in the monitoring area.",
    ),
    "book_or_document_detected": VisualEventDefinition(
        "Book or document detected",
        "secondary_camera",
        "book_or_document_detected",
        0.58,
        0.76,
        "secondary",
        "Book or document detected in the monitoring area.",
    ),
    "headphones_or_earpiece_detected": VisualEventDefinition(
        "Headphones or earpiece detected",
        "secondary_camera",
        "headphones_or_earpiece_detected",
        0.64,
        0.76,
        "secondary",
        "Headphones or earpiece detected during monitoring.",
    ),
    "suspicious_handheld_object_detected": VisualEventDefinition(
        "Suspicious handheld object detected",
        "secondary_camera",
        "suspicious_handheld_object_detected",
        0.66,
        0.76,
        "secondary",
        "Suspicious handheld object detected near the candidate.",
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


def create_events_from_frame_analysis(
    session_id: str,
    candidate_id: str,
    face_result: FaceDetectionResult,
    camera_id: str = "primary",
    evidence_path: str | None = None,
    image_bytes: bytes | None = None,
    run_object_detection: bool = False,
) -> VisualFrameAnalysis:
    events = [
        create_event_from_face_detection(
            session_id=session_id,
            candidate_id=candidate_id,
            result=face_result,
            camera_id=camera_id,
            evidence_path=evidence_path,
        )
    ]
    notes = [
        f"OpenCV face detector: {face_result.status}; faces={face_result.face_count}; "
        f"brightness={face_result.brightness:.1f}; sharpness={face_result.sharpness:.1f}"
    ]
    pose_event = _head_pose_event(session_id, candidate_id, face_result, camera_id, evidence_path)
    if pose_event:
        events.append(pose_event)
        notes.append("Head-pose prototype emitted gaze/head-position evidence from face location.")
    if run_object_detection and image_bytes:
        for result in analyse_objects_with_yolo(image_bytes):
            if not result.available:
                notes.append(result.description)
                continue
            if result.event_type in VISUAL_EVENT_DEFINITIONS:
                events.append(
                    create_visual_event(
                        session_id=session_id,
                        candidate_id=candidate_id,
                        event_type=result.event_type,
                        camera_id=camera_id,
                        confidence=result.confidence,
                        description=result.description,
                        evidence_path=evidence_path,
                    )
                )
                notes.append(f"{result.model_name}: {result.description}")
    return VisualFrameAnalysis(events=events, detector_notes=notes)


def _head_pose_event(
    session_id: str,
    candidate_id: str,
    face_result: FaceDetectionResult,
    camera_id: str,
    evidence_path: str | None,
) -> EvidenceEvent | None:
    if not face_result.face_box or not face_result.frame_shape or face_result.face_count != 1:
        return None
    x, y, width, height = face_result.face_box
    frame_width, frame_height = face_result.frame_shape
    if frame_width <= 0 or frame_height <= 0:
        return None
    face_center_x_ratio = (x + width / 2) / frame_width
    face_center_y_ratio = (y + height / 2) / frame_height
    pose = estimate_head_pose_from_position(face_center_x_ratio, face_center_y_ratio)
    if pose.event_type == "face_present":
        return None
    return create_visual_event(
        session_id=session_id,
        candidate_id=candidate_id,
        event_type=pose.event_type,
        camera_id=camera_id,
        confidence=pose.confidence,
        description=pose.description,
        evidence_path=evidence_path,
    )


def visual_event_types() -> list[str]:
    return list(VISUAL_EVENT_DEFINITIONS)


def is_visual_event(event_type: str) -> bool:
    return event_type in VISUAL_EVENT_DEFINITIONS
