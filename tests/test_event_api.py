import base64

import cv2
import numpy as np
from fastapi.testclient import TestClient

from src.services.event_api import create_app
from src.storage.database import initialize_database
from src.storage.event_repository import list_events


def test_structured_event_api_persists_evidence_event(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_event_api.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    client = TestClient(create_app())

    response = client.post(
        "/events",
        json={
            "session_id": "SESSION-API-1",
            "candidate_id": "CAND-API-1",
            "source_module": "audio",
            "event_type": "background_speech",
            "risk_weight": 0.55,
            "confidence": 0.78,
            "description": "Background speech event from external detector.",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_id"].startswith("EVT-")
    events = list_events("SESSION-API-1")
    assert len(events) == 1
    assert events[0]["event_type"] == "background_speech"


def test_vision_frame_api_persists_detector_events(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_vision_api.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    client = TestClient(create_app())
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    response = client.post(
        "/vision/analyse-frame",
        json={
            "session_id": "SESSION-API-VISION",
            "candidate_id": "CAND-API-1",
            "image_base64": base64.b64encode(encoded.tobytes()).decode("ascii"),
            "camera_id": "primary",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_ids"]
    events = list_events("SESSION-API-VISION")
    assert events[0]["event_type"] == "camera_obstructed"


def test_audio_feature_api_persists_detector_events(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_audio_api.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    client = TestClient(create_app())

    response = client.post(
        "/audio/analyse-features",
        json={
            "session_id": "SESSION-API-AUDIO",
            "candidate_id": "CAND-API-1",
            "duration_seconds": 30,
            "voice_activity_ratio": 0.65,
            "speech_segments": 3,
            "rms_db": -18,
            "noise_floor_db": -42,
            "detector_name": "webrtc_vad_adapter",
        },
    )

    assert response.status_code == 200
    events = list_events("SESSION-API-AUDIO")
    event_types = {event["event_type"] for event in events}
    assert "background_speech" in event_types
    assert "prolonged_speech" in event_types


def test_identity_confidence_api_persists_detector_event(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_identity_api.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    client = TestClient(create_app())

    response = client.post(
        "/identity/analyse-confidence",
        json={
            "session_id": "SESSION-API-IDENTITY",
            "candidate_id": "CAND-API-1",
            "confidence": 0.22,
            "threshold": 0.65,
            "substitution_threshold": 0.35,
        },
    )

    assert response.status_code == 200
    events = list_events("SESSION-API-IDENTITY")
    assert events[0]["event_type"] == "candidate_substitution_suspected"
