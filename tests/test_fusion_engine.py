from src.fusion.event_schema import EvidenceEvent
from src.fusion.fusion_engine import FusionEngine
from src.storage.database import initialize_database
from src.storage.event_repository import save_event


def test_fusion_generates_high_risk_for_cross_modal_evidence() -> None:
    engine = FusionEngine()
    event_one = EvidenceEvent(
        session_id="SESSION-1",
        candidate_id="CAND-1",
        source_module="primary_camera",
        event_type="repeated_looking_away",
        risk_weight=0.45,
        confidence=0.84,
        camera_id="primary",
        description="Repeated looking away.",
    )
    event_two = EvidenceEvent(
        session_id="SESSION-1",
        candidate_id="CAND-1",
        source_module="secondary_camera",
        event_type="mobile_phone_detected",
        risk_weight=0.75,
        confidence=0.88,
        camera_id="secondary",
        description="Phone detected.",
    )

    engine.ingest(event_one)
    alert = engine.ingest(event_two)

    assert alert is not None
    assert alert.risk_level in {"High", "Critical"}
    assert alert.alert_type == "possible_external_assistance"
    assert set(alert.contributing_events) == {event_one.event_id, event_two.event_id}


def test_fusion_matches_high_risk_absent_phone_lookaway_pattern() -> None:
    engine = FusionEngine(time_window_seconds=30)
    events = [
        EvidenceEvent(
            session_id="SESSION-2",
            candidate_id="CAND-2",
            source_module="primary_camera",
            event_type="face_absent",
            risk_weight=0.65,
            confidence=0.82,
            camera_id="primary",
            description="Face absent.",
        ),
        EvidenceEvent(
            session_id="SESSION-2",
            candidate_id="CAND-2",
            source_module="secondary_camera",
            event_type="mobile_phone_detected",
            risk_weight=0.75,
            confidence=0.88,
            camera_id="secondary",
            description="Phone detected.",
        ),
        EvidenceEvent(
            session_id="SESSION-2",
            candidate_id="CAND-2",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Looking away.",
        ),
    ]

    alert = engine.fuse(events)

    assert alert is not None
    assert alert.alert_type == "high_risk_behavioural_pattern"
    assert alert.risk_level in {"High", "Critical"}
    assert alert.confidence > 0
    assert "Matched prototype fusion rule" in " ".join(alert.reasoning_trace)


def test_fusion_correlates_primary_disconnect_with_secondary_ready() -> None:
    engine = FusionEngine(time_window_seconds=30)
    events = [
        EvidenceEvent(
            session_id="SESSION-3",
            candidate_id="CAND-3",
            source_module="primary_camera",
            event_type="camera_stream_disconnected",
            risk_weight=0.65,
            confidence=0.9,
            camera_id="primary",
            description="Primary camera disconnected.",
        ),
        EvidenceEvent(
            session_id="SESSION-3",
            candidate_id="CAND-3",
            source_module="secondary_camera",
            event_type="camera_stream_ready",
            risk_weight=0.02,
            confidence=0.95,
            camera_id="secondary",
            description="Secondary camera ready.",
        ),
    ]

    alert = engine.fuse(events)

    assert alert is not None
    assert alert.alert_type == "reduced_monitoring_confidence"
    assert "secondary camera" in alert.explanation.lower()
    assert set(alert.contributing_modules) == {"primary_camera", "secondary_camera"}


def test_fusion_loads_recent_events_from_sqlite(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_test.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    engine = FusionEngine(time_window_seconds=30)
    speech = EvidenceEvent(
        session_id="SESSION-4",
        candidate_id="CAND-4",
        source_module="audio",
        event_type="background_speech",
        risk_weight=0.55,
        confidence=0.78,
        description="Background speech detected.",
    )
    lookaway = EvidenceEvent(
        session_id="SESSION-4",
        candidate_id="CAND-4",
        source_module="primary_camera",
        event_type="looking_away",
        risk_weight=0.35,
        confidence=0.76,
        camera_id="primary",
        description="Candidate looking away.",
    )
    save_event(speech)
    save_event(lookaway)

    alert = engine.fuse_recent("SESSION-4", 30)

    assert alert is not None
    assert alert.alert_type == "possible_third_party_assistance"
    assert set(alert.contributing_events) == {speech.event_id, lookaway.event_id}
