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


AUDIO_EVENT_DEFINITIONS: dict[str, AudioEventDefinition] = {
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
