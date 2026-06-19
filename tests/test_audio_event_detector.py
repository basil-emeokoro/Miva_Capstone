from src.audio.audio_event_detector import (
    AUDIO_EVENT_DEFINITIONS,
    AudioAnalysisResult,
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
