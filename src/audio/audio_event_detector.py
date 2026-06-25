from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import EvidenceEvent


@dataclass(frozen=True)
class AudioEventDefinition:
    label: str
    event_type: str
    risk_weight: float
    confidence: float
    description: str


@dataclass(frozen=True)
class AudioAnalysisResult:
    event_type: str
    confidence: float
    description: str
    detector_name: str = "prototype_audio_pipeline"


@dataclass(frozen=True)
class AudioFeatureSnapshot:
    duration_seconds: float
    voice_activity_ratio: float = 0.0
    speech_segments: int = 0
    silence_seconds: float = 0.0
    rms_db: float | None = None
    noise_floor_db: float | None = None
    detector_name: str = "feature_audio_pipeline"


AUDIO_EVENT_DEFINITIONS: dict[str, AudioEventDefinition] = {
    "voice_activity_detected": AudioEventDefinition(
        "Voice activity detected",
        "voice_activity_detected",
        0.18,
        0.7,
        "Voice activity was detected by the audio pipeline.",
    ),
    "background_speech": AudioEventDefinition(
        "Background speech",
        "background_speech",
        0.55,
        0.78,
        "Background speech was detected by the microphone.",
    ),
    "prolonged_speech": AudioEventDefinition(
        "Prolonged speech",
        "prolonged_speech",
        0.62,
        0.76,
        "Sustained speech activity was detected during the assessment.",
    ),
    "abnormal_silence": AudioEventDefinition(
        "Abnormal silence",
        "abnormal_silence",
        0.25,
        0.68,
        "Microphone activity was unexpectedly silent for the configured interval.",
    ),
    "environmental_noise": AudioEventDefinition(
        "Environmental noise",
        "environmental_noise",
        0.32,
        0.7,
        "Environmental noise exceeded the prototype monitoring threshold.",
    ),
    "suspicious_audio_pattern": AudioEventDefinition(
        "Suspicious audio pattern",
        "suspicious_audio_pattern",
        0.68,
        0.74,
        "Audio pattern may require human review when correlated with other evidence.",
    ),
}


def analyse_audio_features(snapshot: AudioFeatureSnapshot) -> list[AudioAnalysisResult]:
    """Convert detector features into structured audio signals.

    This function is intentionally feature-based so Whisper, WebRTC VAD,
    Silero VAD, or another local service can be substituted without affecting
    the CIE or persistence layer.
    """
    duration = max(float(snapshot.duration_seconds), 0.0)
    voice_ratio = max(0.0, min(float(snapshot.voice_activity_ratio), 1.0))
    silence_seconds = max(float(snapshot.silence_seconds), 0.0)
    speech_segments = max(int(snapshot.speech_segments), 0)
    results: list[AudioAnalysisResult] = []

    if voice_ratio >= 0.08:
        results.append(
            AudioAnalysisResult(
                "voice_activity_detected",
                min(0.95, 0.55 + voice_ratio),
                f"Voice activity ratio {voice_ratio:.2f} over {duration:.1f} seconds.",
                snapshot.detector_name,
            )
        )
    if speech_segments >= 2 or voice_ratio >= 0.18:
        results.append(
            AudioAnalysisResult(
                "background_speech",
                min(0.95, 0.64 + voice_ratio / 2),
                f"Background speech pattern detected: {speech_segments} segment(s), voice ratio {voice_ratio:.2f}.",
                snapshot.detector_name,
            )
        )
    if duration >= 20 and voice_ratio >= 0.55:
        results.append(
            AudioAnalysisResult(
                "prolonged_speech",
                min(0.95, 0.7 + voice_ratio / 4),
                f"Prolonged speech-like activity covered {voice_ratio:.2f} of a {duration:.1f}s window.",
                snapshot.detector_name,
            )
        )
    if duration >= 20 and silence_seconds >= duration * 0.9:
        results.append(
            AudioAnalysisResult(
                "abnormal_silence",
                0.72,
                f"Audio was silent for {silence_seconds:.1f}s in a {duration:.1f}s window.",
                snapshot.detector_name,
            )
        )
    if snapshot.rms_db is not None and snapshot.noise_floor_db is not None:
        if snapshot.rms_db - snapshot.noise_floor_db >= 18:
            results.append(
                AudioAnalysisResult(
                    "environmental_noise",
                    0.73,
                    f"Audio level exceeded baseline by {snapshot.rms_db - snapshot.noise_floor_db:.1f} dB.",
                    snapshot.detector_name,
                )
            )
    if len({result.event_type for result in results if result.event_type != "voice_activity_detected"}) >= 2:
        results.append(
            AudioAnalysisResult(
                "suspicious_audio_pattern",
                0.78,
                "Multiple audio indicators occurred in the same analysis window.",
                snapshot.detector_name,
            )
        )
    return results


def create_audio_event(
    session_id: str,
    candidate_id: str,
    event_type: str,
    confidence: float | None = None,
    description: str | None = None,
) -> EvidenceEvent:
    try:
        definition = AUDIO_EVENT_DEFINITIONS[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported audio event type: {event_type}") from exc
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module="audio",
        event_type=definition.event_type,
        risk_weight=definition.risk_weight,
        confidence=confidence if confidence is not None else definition.confidence,
        camera_id=None,
        description=description or definition.description,
    )


def create_audio_event_from_analysis(session_id: str, candidate_id: str, result: AudioAnalysisResult) -> EvidenceEvent:
    return create_audio_event(
        session_id=session_id,
        candidate_id=candidate_id,
        event_type=result.event_type,
        confidence=result.confidence,
        description=f"{result.detector_name}: {result.description}",
    )


def create_background_speech_event(session_id: str, candidate_id: str) -> EvidenceEvent:
    return create_audio_event(session_id, candidate_id, "background_speech")
