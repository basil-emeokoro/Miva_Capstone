from src.audio.audio_event_detector import (
    AUDIO_EVENT_DEFINITIONS,
    AudioFeatureSnapshot,
    AudioAnalysisResult,
    analyse_audio_features,
    create_audio_event,
    create_audio_event_from_analysis,
)


def test_audio_pipeline_defines_required_event_types() -> None:
    required = {
        "background_speech",
        "prolonged_speech",
        "abnormal_silence",
        "environmental_noise",
        "suspicious_audio_pattern",
        "voice_activity_detected",
    }

    assert required.issubset(AUDIO_EVENT_DEFINITIONS)


def test_audio_event_uses_common_evidence_schema() -> None:
    event = create_audio_event("SESSION-1", "CAND-1", "prolonged_speech")

    assert event.event_id.startswith("EVT-")
    assert event.session_id == "SESSION-1"
    assert event.candidate_id == "CAND-1"
    assert event.source_module == "audio"
    assert event.event_type == "prolonged_speech"
    assert event.camera_id is None
    assert event.risk_weight > 0
    assert event.confidence > 0


def test_audio_analysis_result_can_be_converted_to_evidence_event() -> None:
    result = AudioAnalysisResult(
        event_type="environmental_noise",
        confidence=0.73,
        description="Noise threshold exceeded.",
        detector_name="webrtc_vad_adapter",
    )

    event = create_audio_event_from_analysis("SESSION-1", "CAND-1", result)

    assert event.event_type == "environmental_noise"
    assert event.confidence == 0.73
    assert "webrtc_vad_adapter" in event.description


def test_audio_feature_snapshot_emits_structured_results() -> None:
    snapshot = AudioFeatureSnapshot(
        duration_seconds=30,
        voice_activity_ratio=0.65,
        speech_segments=3,
        rms_db=-18,
        noise_floor_db=-42,
        detector_name="silero_vad_adapter",
    )

    results = analyse_audio_features(snapshot)
    event_types = {result.event_type for result in results}

    assert "voice_activity_detected" in event_types
    assert "background_speech" in event_types
    assert "prolonged_speech" in event_types
    assert "environmental_noise" in event_types
    assert "suspicious_audio_pattern" in event_types
