from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine
from src.fusion.event_schema import EvidenceEvent
from src.storage.event_repository import save_alert, save_event


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

    return app


app = create_app()
