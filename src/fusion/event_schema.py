from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

from src.utils.time_utils import utc_now_iso


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


@dataclass(frozen=True)
class EvidenceEvent:
    session_id: str
    candidate_id: str
    source_module: str
    event_type: str
    risk_weight: float
    confidence: float
    description: str
    camera_id: str | None = None
    evidence_path: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)
    event_id: str = field(default_factory=lambda: f"EVT-{uuid4().hex[:8].upper()}")

    def risk_points(self) -> int:
        return round(max(0.0, min(self.risk_weight, 1.0)) * max(0.0, min(self.confidence, 1.0)) * 100)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
            "event_type": self.event_type,
            "risk_weight": self.risk_weight,
            "confidence": self.confidence,
            "camera_id": self.camera_id,
            "evidence_path": self.evidence_path,
            "description": self.description,
        }


@dataclass(frozen=True)
class FusedAlert:
    session_id: str
    candidate_id: str
    start_time: str
    end_time: str
    risk_score: int
    risk_level: RiskLevel
    alert_type: str
    contributing_events: list[str]
    explanation: str
    recommended_action: str
    review_status: str = "pending"
    alert_id: str = field(default_factory=lambda: f"ALT-{uuid4().hex[:8].upper()}")

    def to_dict(self) -> dict[str, object]:
        return {
            "alert_id": self.alert_id,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "alert_type": self.alert_type,
            "contributing_events": self.contributing_events,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "review_status": self.review_status,
        }
