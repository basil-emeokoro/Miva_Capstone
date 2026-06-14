from __future__ import annotations

from src.fusion.event_schema import EvidenceEvent


def create_background_speech_event(session_id: str, candidate_id: str) -> EvidenceEvent:
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module="audio",
        event_type="background_speech",
        risk_weight=0.55,
        confidence=0.78,
        camera_id=None,
        description="Background speech was detected by the microphone.",
    )
