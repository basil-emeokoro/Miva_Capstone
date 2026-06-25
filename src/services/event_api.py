from __future__ import annotations

import base64

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.audio.audio_event_detector import AudioFeatureSnapshot, analyse_audio_features, create_audio_event_from_analysis
from src.authentication.identity_event_detector import analyse_identity_confidence, create_identity_event_from_analysis
from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine
from src.fusion.event_schema import EvidenceEvent
from src.storage.event_repository import save_alert, save_event
from src.vision.face_detector import analyse_face_presence
from src.vision.visual_event_detector import create_events_from_frame_analysis


class EvidenceEventPayload(BaseModel):
    session_id: str
    candidate_id: str
    source_module: str
    event_type: str
    risk_weight: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    description: str
    camera_id: str | None = None
    evidence_path: str | None = None
    timestamp: str | None = None


class VisionFramePayload(BaseModel):
    session_id: str
    candidate_id: str
    image_base64: str
    camera_id: str = "primary"
    evidence_path: str | None = None
    run_object_detection: bool = False


class AudioFeaturePayload(BaseModel):
    session_id: str
    candidate_id: str
    duration_seconds: float = Field(ge=0)
    voice_activity_ratio: float = Field(default=0.0, ge=0, le=1)
    speech_segments: int = Field(default=0, ge=0)
    silence_seconds: float = Field(default=0.0, ge=0)
    rms_db: float | None = None
    noise_floor_db: float | None = None
    detector_name: str = "feature_audio_pipeline"


class IdentityConfidencePayload(BaseModel):
    session_id: str
    candidate_id: str
    confidence: float = Field(ge=0, le=1)
    threshold: float = Field(default=0.65, ge=0, le=1)
    substitution_threshold: float = Field(default=0.35, ge=0, le=1)
    unknown_face: bool = False
    detector_name: str = "periodic_face_verifier"
    evidence_path: str | None = None


def create_app(engine: ContextualIntelligenceEngine | None = None) -> FastAPI:
    app = FastAPI(title="SERPS Structured Event API")
    cie = engine or ContextualIntelligenceEngine()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "component": "structured-event-api"}

    @app.post("/events")
    def ingest_event(payload: EvidenceEventPayload) -> dict[str, object]:
        event_kwargs = payload.model_dump(exclude_none=True)
        event = EvidenceEvent(**event_kwargs)
        save_event(event)
        alert = cie.ingest(event)
        if alert:
            save_alert(alert)
        return {
            "event_id": event.event_id,
            "alert_id": alert.alert_id if alert else None,
            "message": "Structured evidence event accepted. CIE alert generated only when contextual evidence warrants it.",
        }

    @app.post("/vision/analyse-frame")
    def analyse_vision_frame(payload: VisionFramePayload) -> dict[str, object]:
        image_bytes = base64.b64decode(payload.image_base64)
        face_result = analyse_face_presence(image_bytes)
        analysis = create_events_from_frame_analysis(
            session_id=payload.session_id,
            candidate_id=payload.candidate_id,
            face_result=face_result,
            camera_id=payload.camera_id,
            evidence_path=payload.evidence_path,
            image_bytes=image_bytes,
            run_object_detection=payload.run_object_detection,
        )
        return _persist_and_ingest(analysis.events, cie, analysis.detector_notes)

    @app.post("/audio/analyse-features")
    def analyse_audio(payload: AudioFeaturePayload) -> dict[str, object]:
        snapshot = AudioFeatureSnapshot(
            duration_seconds=payload.duration_seconds,
            voice_activity_ratio=payload.voice_activity_ratio,
            speech_segments=payload.speech_segments,
            silence_seconds=payload.silence_seconds,
            rms_db=payload.rms_db,
            noise_floor_db=payload.noise_floor_db,
            detector_name=payload.detector_name,
        )
        events = [
            create_audio_event_from_analysis(payload.session_id, payload.candidate_id, result)
            for result in analyse_audio_features(snapshot)
        ]
        return _persist_and_ingest(events, cie, [f"{len(events)} audio evidence event(s) generated."])

    @app.post("/identity/analyse-confidence")
    def analyse_identity(payload: IdentityConfidencePayload) -> dict[str, object]:
        result = analyse_identity_confidence(
            confidence=payload.confidence,
            threshold=payload.threshold,
            substitution_threshold=payload.substitution_threshold,
            unknown_face=payload.unknown_face,
            detector_name=payload.detector_name,
        )
        event = create_identity_event_from_analysis(
            payload.session_id,
            payload.candidate_id,
            result,
            evidence_path=payload.evidence_path,
        )
        return _persist_and_ingest([event], cie, [result.description])

    return app


def _persist_and_ingest(
    events: list[EvidenceEvent],
    cie: ContextualIntelligenceEngine,
    notes: list[str] | None = None,
) -> dict[str, object]:
    alerts = []
    for event in events:
        save_event(event)
        alert = cie.ingest(event)
        if alert:
            save_alert(alert)
            alerts.append(alert.alert_id)
    return {
        "event_ids": [event.event_id for event in events],
        "alert_ids": alerts,
        "notes": notes or [],
        "message": "Detector output accepted as structured evidence. CIE remains responsible for contextual reasoning.",
    }


app = create_app()
