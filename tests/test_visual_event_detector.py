import cv2
import numpy as np

from src.vision.face_detector import FaceDetectionResult
from src.vision.face_detector import analyse_face_presence
from src.vision.object_detector import ObjectDetectionResult
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
        "laptop_or_tablet_detected",
        "book_or_document_detected",
        "headphones_or_earpiece_detected",
        "suspicious_handheld_object_detected",
        "candidate_facing_phone_detected",
        "phone_towards_screen_detected",
        "possible_screen_capture_attempt",
        "repeated_phone_visibility",
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


def test_primary_camera_phone_detection_maps_to_candidate_facing_event(monkeypatch) -> None:
    def fake_yolo(_image_bytes: bytes) -> list[ObjectDetectionResult]:
        return [
            ObjectDetectionResult(
                "mobile_phone_detected",
                0.91,
                "YOLO detected a possible mobile phone.",
                "test-yolo",
            )
        ]

    monkeypatch.setattr("src.vision.visual_event_detector.analyse_objects_with_yolo", fake_yolo)
    face_result = FaceDetectionResult(
        face_count=1,
        brightness=120.0,
        sharpness=50.0,
        status="face_present",
        confidence=0.9,
        description="One candidate face is visible.",
        frame_shape=(160, 120),
    )

    analysis = create_events_from_frame_analysis(
        "SESSION-1",
        "CAND-1",
        face_result,
        camera_id="primary",
        image_bytes=b"frame",
        run_object_detection=True,
    )

    event_types = {event.event_type for event in analysis.events}
    candidate_phone = next(event for event in analysis.events if event.event_type == "candidate_facing_phone_detected")
    assert "candidate_facing_phone_detected" in event_types
    assert candidate_phone.camera_id == "primary"
    assert candidate_phone.source_module == "primary_camera"


def test_secondary_camera_phone_detection_remains_room_facing_event(monkeypatch) -> None:
    def fake_yolo(_image_bytes: bytes) -> list[ObjectDetectionResult]:
        return [
            ObjectDetectionResult(
                "mobile_phone_detected",
                0.91,
                "YOLO detected a possible mobile phone.",
                "test-yolo",
            )
        ]

    monkeypatch.setattr("src.vision.visual_event_detector.analyse_objects_with_yolo", fake_yolo)
    face_result = FaceDetectionResult(
        face_count=0,
        brightness=120.0,
        sharpness=50.0,
        status="face_absent",
        confidence=0.82,
        description="No candidate face detected.",
        frame_shape=(160, 120),
    )

    analysis = create_events_from_frame_analysis(
        "SESSION-1",
        "CAND-1",
        face_result,
        camera_id="secondary",
        image_bytes=b"frame",
        run_object_detection=True,
    )

    phone_event = next(event for event in analysis.events if event.event_type == "mobile_phone_detected")
    assert phone_event.camera_id == "secondary"
    assert phone_event.source_module == "secondary_camera"
