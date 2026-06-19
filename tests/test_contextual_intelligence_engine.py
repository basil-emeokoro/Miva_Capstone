from datetime import datetime, timedelta

from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine
from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourMemory
from src.fusion.event_schema import EvidenceEvent
from src.storage.database import initialize_database
from src.storage.event_repository import list_events, save_alert, save_event


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


def test_isolated_event_does_not_become_critical() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    event = EvidenceEvent(
        session_id="SESSION-CIE-3",
        candidate_id="CAND-CIE-3",
        source_module="secondary_camera",
        event_type="mobile_phone_detected",
        risk_weight=0.75,
        confidence=0.88,
        camera_id="secondary",
        description="Single mobile phone detection.",
    )

    alert = engine.fuse([event])

    assert alert is not None
    assert alert.risk_level != "Critical"


def test_repeated_events_increase_contextual_risk() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    single = [
        EvidenceEvent(
            session_id="SESSION-CIE-4",
            candidate_id="CAND-CIE-4",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Single looking away.",
        )
    ]
    repeated = [
        EvidenceEvent(
            session_id="SESSION-CIE-4",
            candidate_id="CAND-CIE-4",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Repeated looking away.",
        )
        for _ in range(3)
    ]

    single_alert = engine.fuse(single)
    repeated_alert = engine.fuse(repeated, rolling_events=repeated)

    assert single_alert is not None
    assert repeated_alert is not None
    assert repeated_alert.current_risk_score > single_alert.current_risk_score
    assert "looking_away" in " ".join(repeated_alert.reasoning_trace)


def test_multimodal_events_elevate_risk() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    isolated = [
        EvidenceEvent(
            session_id="SESSION-CIE-5",
            candidate_id="CAND-CIE-5",
            source_module="audio",
            event_type="background_speech",
            risk_weight=0.55,
            confidence=0.78,
            description="Background speech.",
        )
    ]
    multimodal = isolated + [
        EvidenceEvent(
            session_id="SESSION-CIE-5",
            candidate_id="CAND-CIE-5",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Looking away.",
        )
    ]

    isolated_alert = engine.fuse(isolated)
    multimodal_alert = engine.fuse(multimodal)

    assert isolated_alert is not None
    assert multimodal_alert is not None
    assert multimodal_alert.risk_score > isolated_alert.risk_score
    assert multimodal_alert.alert_type == "possible_third_party_assistance"


def test_duplicate_suppression_prevents_unfair_critical_risk() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    events = [
        EvidenceEvent(
            session_id="SESSION-CIE-6",
            candidate_id="CAND-CIE-6",
            source_module="secondary_camera",
            event_type="mobile_phone_detected",
            risk_weight=0.75,
            confidence=0.88,
            camera_id="secondary",
            description=f"Duplicate phone detection {index}.",
        )
        for index in range(10)
    ]

    alert = engine.fuse(events, rolling_events=events)

    assert alert is not None
    assert alert.risk_level != "Critical"
    assert len(alert.contributing_events) == 1
    assert "Duplicate suppression retained 1 event signature" in " ".join(alert.reasoning_trace)


def test_temporal_window_affects_correlation(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_cie_window.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    now = datetime.now().astimezone().replace(microsecond=0)
    for offset in (-180, -150, -5):
        save_event(
            EvidenceEvent(
                session_id="SESSION-CIE-7",
                candidate_id="CAND-CIE-7",
                source_module="primary_camera",
                event_type="looking_away",
                risk_weight=0.35,
                confidence=0.76,
                camera_id="primary",
                description="Temporal window looking-away event.",
                timestamp=(now + timedelta(seconds=offset)).isoformat(),
            )
        )
    engine = ContextualIntelligenceEngine(time_window_seconds=30)

    short_window = engine.fuse_recent("SESSION-CIE-7", 30)
    long_window = engine.fuse_recent("SESSION-CIE-7", 300)

    assert short_window is not None
    assert long_window is not None
    assert long_window.current_risk_score > short_window.current_risk_score
    assert "repeated pattern" in long_window.explanation


def test_explanation_and_recommendation_include_reviewer_context() -> None:
    engine = ContextualIntelligenceEngine(time_window_seconds=30)
    events = [
        EvidenceEvent(
            session_id="SESSION-CIE-8",
            candidate_id="CAND-CIE-8",
            source_module="primary_camera",
            event_type="looking_away",
            risk_weight=0.35,
            confidence=0.76,
            camera_id="primary",
            description="Looking away.",
        ),
        EvidenceEvent(
            session_id="SESSION-CIE-8",
            candidate_id="CAND-CIE-8",
            source_module="audio",
            event_type="background_speech",
            risk_weight=0.55,
            confidence=0.78,
            description="Background speech.",
        ),
    ]

    alert = engine.fuse(events)

    assert alert is not None
    explanation = alert.explanation.lower()
    assert "contributing event" in explanation
    assert "temporal window" in explanation
    assert "risk score" in explanation
    assert "confidence" in explanation
    assert alert.recommended_action
    assert "human reviewer remains final decision-maker" in " ".join(alert.reasoning_trace).lower()


def test_raw_events_remain_immutable_when_contextual_alert_is_saved(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "serps_cie_immutable.db"
    monkeypatch.setattr("src.storage.database.database_path", lambda: db_path)
    initialize_database(db_path)
    event_one = EvidenceEvent(
        session_id="SESSION-CIE-9",
        candidate_id="CAND-CIE-9",
        source_module="audio",
        event_type="background_speech",
        risk_weight=0.55,
        confidence=0.78,
        description="Background speech.",
    )
    event_two = EvidenceEvent(
        session_id="SESSION-CIE-9",
        candidate_id="CAND-CIE-9",
        source_module="primary_camera",
        event_type="looking_away",
        risk_weight=0.35,
        confidence=0.76,
        camera_id="primary",
        description="Looking away.",
    )
    save_event(event_one)
    save_event(event_two)
    before = list_events("SESSION-CIE-9")

    alert = ContextualIntelligenceEngine(time_window_seconds=30).fuse_recent("SESSION-CIE-9", 30)
    assert alert is not None
    save_alert(alert)
    after = list_events("SESSION-CIE-9")

    assert before == after
