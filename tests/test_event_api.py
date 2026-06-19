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
