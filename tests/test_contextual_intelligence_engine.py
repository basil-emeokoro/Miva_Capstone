from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine
from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourMemory
from src.fusion.event_schema import EvidenceEvent


def test_contextual_engine_wraps_event_fusion_with_temporal_reasoning() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    events = [
        EvidenceEvent(
            session_id="SESSION-CIE-1",
            candidate_id="CAND-CIE-1",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Candidate looked away.",
        ),
        EvidenceEvent(
            session_id="SESSION-CIE-1",
            candidate_id="CAND-CIE-1",
            source_module="audio",
            event_type="background_speech",
            risk_weight=0.55,
            confidence=0.78,
            description="Background speech detected.",
        ),
    ]

    alert = engine.fuse(events)

    assert alert is not None
    assert alert.alert_type == "possible_third_party_assistance"
    assert "Contextual Intelligence Engine" in " ".join(alert.reasoning_trace)
    assert "Temporal Behaviour Memory" in alert.explanation
    assert set(alert.contributing_modules) == {"audio", "primary_camera"}


def test_temporal_memory_identifies_persistent_patterns() -> None:
    memory = TemporalBehaviourMemory(persistent_threshold=3)
    events = [
        EvidenceEvent(
            session_id="SESSION-CIE-2",
            candidate_id="CAND-CIE-2",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Candidate looked away.",
        )
        for _ in range(3)
    ]

    summary = memory.summarise(events, window_seconds=90)

    assert summary.total_events == 3
    assert summary.event_frequency["looking_away"] == 3
    assert summary.persistent_patterns == ["looking_away"]
