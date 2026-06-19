import cv2
import numpy as np

from src.vision.face_detector import analyse_face_presence
from src.vision.visual_event_detector import (
    VISUAL_EVENT_DEFINITIONS,
    create_events_from_frame_analysis,
    create_event_from_face_detection,
    create_visual_event,
    is_visual_event,
)


def test_required_visual_events_are_defined() -> None:
    required = {
        "face_present",
        "face_absent",
        "face_obstructed",
        "camera_obstructed",
        "multiple_persons_detected",
        "looking_away",
        "head_movement_anomaly",
        "mobile_phone_detected",
        "unauthorised_object_detected",
    }

    assert required.issubset(VISUAL_EVENT_DEFINITIONS)


def test_visual_event_uses_common_evidence_schema() -> None:
    event = create_visual_event("SESSION-1", "CAND-1", "mobile_phone_detected")

    assert event.event_id.startswith("EVT-")
    assert event.session_id == "SESSION-1"
    assert event.candidate_id == "CAND-1"
    assert event.source_module == "secondary_camera"
    assert event.event_type == "mobile_phone_detected"
    assert event.camera_id == "secondary"
    assert event.risk_weight > 0
    assert event.confidence > 0
    assert is_visual_event(event.event_type)


def test_dark_image_generates_camera_obstructed_event() -> None:
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    result = analyse_face_presence(encoded.tobytes())
    event = create_event_from_face_detection("SESSION-1", "CAND-1", result)

    assert result.status == "camera_obstructed"
    assert event.event_type == "camera_obstructed"
    assert event.source_module == "primary_camera"


def test_frame_analysis_emits_structured_face_event() -> None:
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    result = analyse_face_presence(encoded.tobytes())
    analysis = create_events_from_frame_analysis("SESSION-1", "CAND-1", result, image_bytes=encoded.tobytes())

    assert analysis.events
    assert analysis.events[0].event_type == "camera_obstructed"
    assert analysis.events[0].session_id == "SESSION-1"
    assert analysis.events[0].candidate_id == "CAND-1"
    assert "OpenCV face detector" in analysis.detector_notes[0]
