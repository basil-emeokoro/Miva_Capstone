from __future__ import annotations

from src.explainability.explanation_generator import ExplanationGenerator
from src.fusion.event_buffer import EventBuffer
from src.fusion.event_schema import EvidenceEvent, FusedAlert
from src.fusion.risk_scorer import RiskScorer


class FusionEngine:
    def __init__(self, time_window_seconds: int = 20, scorer: RiskScorer | None = None) -> None:
        self.time_window_seconds = time_window_seconds
        self.buffer = EventBuffer()
        self.scorer = scorer or RiskScorer()
        self.explainer = ExplanationGenerator()

    def ingest(self, event: EvidenceEvent) -> FusedAlert | None:
        self.buffer.add(event)
        events = self.buffer.within_window(event.session_id, event, self.time_window_seconds)
        return self.fuse(events)

    def fuse(self, events: list[EvidenceEvent]) -> FusedAlert | None:
        if not events:
            return None

        score = self.scorer.score(events)
        risk_level = self.scorer.classify(score)
        alert_type = self._classify_alert_type(events)
        explanation = self.explainer.generate(events, risk_level)
        action = self.explainer.recommended_action(risk_level)

        return FusedAlert(
            session_id=events[0].session_id,
            candidate_id=events[0].candidate_id,
            start_time=min(event.timestamp for event in events),
            end_time=max(event.timestamp for event in events),
            risk_score=score,
            risk_level=risk_level,
            alert_type=alert_type,
            contributing_events=[event.event_id for event in events],
            explanation=explanation,
            recommended_action=action,
        )

    def _classify_alert_type(self, events: list[EvidenceEvent]) -> str:
        types = {event.event_type for event in events}
        if {"face_mismatch", "second_person_detected"} & types and "background_speech" in types:
            return "possible_identity_substitution"
        if "mobile_phone_detected" in types or "unauthorised_object_detected" in types:
            return "possible_external_assistance"
        if "candidate_absent" in types:
            return "candidate_absence"
        if "repeated_looking_away" in types:
            return "behavioural_anomaly"
        return "monitoring_alert"
