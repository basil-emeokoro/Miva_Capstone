from src.fusion.event_schema import EvidenceEvent
from src.fusion.fusion_engine import FusionEngine


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
