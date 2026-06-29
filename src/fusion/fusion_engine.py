from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from src.explainability.explanation_generator import ExplanationGenerator
from src.fusion.event_buffer import EventBuffer
from src.fusion.event_schema import EvidenceEvent, FusedAlert
from src.fusion.risk_scorer import RiskScorer
from src.storage.event_repository import list_events


@dataclass(frozen=True)
class FusionRule:
    name: str
    alert_type: str
    risk_boost: int
    explanation: str
    recommended_action: str
    predicate: Callable[[list[EvidenceEvent]], bool]


class FusionEngine:
    """Rule-based multi-modal event fusion independent of Streamlit UI code."""

    def __init__(self, time_window_seconds: int = 20, scorer: RiskScorer | None = None) -> None:
        self.time_window_seconds = time_window_seconds
        self.buffer = EventBuffer()
        self.scorer = scorer or RiskScorer()
        self.explainer = ExplanationGenerator()
        self.rules = self._build_rules()

    def ingest(self, event: EvidenceEvent) -> FusedAlert | None:
        self.buffer.add(event)
        current_events = self.buffer.within_window(event.session_id, event, self.time_window_seconds)
        rolling_events = self.buffer.within_window(event.session_id, event, self.time_window_seconds * 3)
        return self.fuse(current_events, rolling_events=rolling_events)

    def load_events_for_window(self, session_id: str, window_seconds: int | None = None) -> list[EvidenceEvent]:
        """Load persisted events for a session using the latest event as the anchor."""
        seconds = window_seconds or self.time_window_seconds
        events = [event_from_row(row) for row in list_events(session_id)]
        if not events:
            return []

        anchor_time = max(_parse_timestamp(event.timestamp) for event in events)
        start_time = anchor_time - timedelta(seconds=seconds)
        return [
            event
            for event in events
            if start_time <= _parse_timestamp(event.timestamp) <= anchor_time
        ]

    def fuse_recent(self, session_id: str, window_seconds: int | None = None) -> FusedAlert | None:
        seconds = window_seconds or self.time_window_seconds
        current_events = self.load_events_for_window(session_id, seconds)
        rolling_events = self.load_events_for_window(session_id, seconds * 3)
        return self.fuse(current_events, rolling_events=rolling_events)

    def fuse(
        self,
        events: list[EvidenceEvent],
        rolling_events: list[EvidenceEvent] | None = None,
    ) -> FusedAlert | None:
        if not events:
            return None

        deduplicated_events = self._deduplicate_events(events)
        if not deduplicated_events:
            return None

        matched_rule = self._match_rule(deduplicated_events)
        current_score = self.scorer.score(deduplicated_events)
        if matched_rule:
            current_score = min(100, current_score + matched_rule.risk_boost)

        # Low/noise-only events stay as raw evidence unless a cross-modal rule matched.
        if current_score < self.scorer.low_threshold and not matched_rule:
            return None

        rolling_source = self._deduplicate_events(rolling_events or deduplicated_events)
        previous_score = self._previous_score(rolling_source, {event.event_id for event in deduplicated_events})
        rolling_score = max(current_score, min(100, round((current_score * 0.7) + (previous_score * 0.3))))
        risk_trend = self._risk_trend(current_score, previous_score)
        risk_level = self.scorer.classify(rolling_score)
        alert_type = matched_rule.alert_type if matched_rule else self._classify_alert_type(deduplicated_events)
        confidence = self._aggregate_confidence(deduplicated_events)
        contributing_modules = sorted({event.source_module for event in deduplicated_events})
        explanation = self._explain(
            deduplicated_events,
            risk_level,
            matched_rule,
            current_score,
            rolling_score,
            risk_trend,
        )
        action = matched_rule.recommended_action if matched_rule else self.explainer.recommended_action(risk_level)
        reasoning_trace = self._reasoning_trace(
            source_count=len(events),
            deduplicated_count=len(deduplicated_events),
            matched_rule=matched_rule,
            current_score=current_score,
            previous_score=previous_score,
            rolling_score=rolling_score,
            risk_trend=risk_trend,
            contributing_modules=contributing_modules,
        )

        return FusedAlert(
            session_id=deduplicated_events[0].session_id,
            candidate_id=deduplicated_events[0].candidate_id,
            start_time=min(event.timestamp for event in deduplicated_events),
            end_time=max(event.timestamp for event in deduplicated_events),
            risk_score=rolling_score,
            risk_level=risk_level,
            alert_type=alert_type,
            contributing_events=[event.event_id for event in deduplicated_events],
            explanation=explanation,
            recommended_action=action,
            confidence=confidence,
            current_risk_score=current_score,
            rolling_risk_score=rolling_score,
            risk_trend=risk_trend,
            contributing_modules=contributing_modules,
            reasoning_trace=reasoning_trace,
        )

    def _build_rules(self) -> list[FusionRule]:
        return [
            FusionRule(
                name="primary_absent_secondary_present",
                alert_type="possible_primary_camera_avoidance",
                risk_boost=12,
                explanation=(
                    "Primary camera face absence was correlated with secondary-camera candidate presence, "
                    "suggesting possible primary camera avoidance rather than full candidate absence."
                ),
                recommended_action="Reviewer should inspect primary and secondary camera evidence before deciding.",
                predicate=lambda events: _has(events, "face_absent", camera_id="primary")
                and (_has(events, "candidate_present", camera_id="secondary") or _has(events, "face_present", camera_id="secondary")),
            ),
            FusionRule(
                name="speech_lookaway_after_identity",
                alert_type="possible_third_party_assistance",
                risk_boost=16,
                explanation=(
                    "Background speech and looking-away behaviour occurred inside the same event window after session authentication, "
                    "which may indicate third-party assistance."
                ),
                recommended_action="Reviewer should inspect the audio/visual timeline and consider re-authentication.",
                predicate=lambda events: _has(events, "background_speech") and _has(events, "looking_away"),
            ),
            FusionRule(
                name="silence_multiple_persons",
                alert_type="possible_unauthorised_presence",
                risk_boost=14,
                explanation=(
                    "Audio silence was correlated with multiple-person visual evidence, suggesting possible unauthorised presence."
                ),
                recommended_action="Reviewer should inspect the secondary-camera evidence and continue monitoring.",
                predicate=lambda events: _has(events, "silence") and _has(events, "multiple_persons_detected"),
            ),
            FusionRule(
                name="primary_disconnected_secondary_ready",
                alert_type="reduced_monitoring_confidence",
                risk_boost=6,
                explanation=(
                    "Primary camera disconnection was correlated with a ready secondary camera, reducing monitoring confidence "
                    "while preserving some environmental visibility."
                ),
                recommended_action="Continue monitoring through the available stream and request primary-camera restoration.",
                predicate=lambda events: _has(events, "camera_disconnected", camera_id="primary")
                and _has(events, "camera_ready", camera_id="secondary"),
            ),
            FusionRule(
                name="absent_phone_lookaway_pattern",
                alert_type="high_risk_behavioural_pattern",
                risk_boost=24,
                explanation=(
                    "Face absence, mobile-phone evidence, and looking-away behaviour were correlated in the same window, "
                    "forming a high-risk behavioural pattern."
                ),
                recommended_action="Immediate reviewer inspection and candidate re-authentication recommended.",
                predicate=lambda events: _has(events, "face_absent")
                and _has(events, "mobile_phone_detected")
                and _has(events, "looking_away"),
            ),
        ]

    def _match_rule(self, events: list[EvidenceEvent]) -> FusionRule | None:
        for rule in self.rules:
            if rule.predicate(events):
                return rule
        return None

    def _deduplicate_events(self, events: list[EvidenceEvent]) -> list[EvidenceEvent]:
        latest_by_signature: dict[tuple[str, str, str | None], EvidenceEvent] = {}
        for event in sorted(events, key=lambda item: _parse_timestamp(item.timestamp)):
            signature = (event.source_module, _normalize_event_type(event.event_type), event.camera_id)
            latest_by_signature[signature] = event
        return sorted(latest_by_signature.values(), key=lambda item: _parse_timestamp(item.timestamp))

    def _previous_score(self, rolling_events: list[EvidenceEvent], current_event_ids: set[str]) -> int:
        previous_events = [event for event in rolling_events if event.event_id not in current_event_ids]
        return self.scorer.score(previous_events)

    def _risk_trend(self, current_score: int, previous_score: int) -> str:
        if current_score >= previous_score + 10:
            return "increasing"
        if current_score <= previous_score - 10:
            return "decreasing"
        return "stable"

    def _aggregate_confidence(self, events: list[EvidenceEvent]) -> float:
        total_weight = sum(max(0.01, event.risk_weight) for event in events)
        if total_weight <= 0:
            return 0.0
        weighted = sum(max(0.0, min(event.confidence, 1.0)) * max(0.01, event.risk_weight) for event in events)
        return round(weighted / total_weight, 3)

    def _explain(
        self,
        events: list[EvidenceEvent],
        risk_level: str,
        matched_rule: FusionRule | None,
        current_score: int,
        rolling_score: int,
        risk_trend: str,
    ) -> str:
        source_explanation = self.explainer.generate(events, risk_level)
        score_context = (
            f" Current risk score is {current_score}; rolling risk score is {rolling_score}; "
            f"risk trend is {risk_trend}."
        )
        if matched_rule:
            return f"{matched_rule.explanation} {source_explanation}{score_context}"
        return f"{source_explanation}{score_context}"

    def _reasoning_trace(
        self,
        source_count: int,
        deduplicated_count: int,
        matched_rule: FusionRule | None,
        current_score: int,
        previous_score: int,
        rolling_score: int,
        risk_trend: str,
        contributing_modules: list[str],
    ) -> list[str]:
        trace = [
            f"Loaded {source_count} evidence event(s) from the configured time window.",
            f"Duplicate suppression retained {deduplicated_count} event signature(s).",
            f"Contributing modules: {', '.join(contributing_modules) if contributing_modules else 'none'}.",
            f"Current score={current_score}; previous rolling-window score={previous_score}; rolling score={rolling_score}.",
            f"Risk trend classified as {risk_trend}.",
            "Fusion output is advisory; human reviewer remains responsible for final decision.",
        ]
        if matched_rule:
            trace.insert(2, f"Matched prototype fusion rule: {matched_rule.name}.")
        else:
            trace.insert(2, "No named prototype fusion rule matched; score derived from weighted evidence.")
        return trace

    def _classify_alert_type(self, events: list[EvidenceEvent]) -> str:
        types = {_normalize_event_type(event.event_type) for event in events}
        if {"face_mismatch", "identity_substitution"} & types and "background_speech" in types:
            return "possible_identity_substitution"
        if "mobile_phone_detected" in types or "unauthorised_object_detected" in types:
            return "possible_external_assistance"
        if "face_absent" in types:
            return "candidate_absence"
        if "looking_away" in types:
            return "behavioural_anomaly"
        if "camera_disconnected" in types or "camera_missing" in types:
            return "stream_health_alert"
        return "monitoring_alert"


def event_from_row(row: dict[str, object]) -> EvidenceEvent:
    return EvidenceEvent(
        session_id=str(row["session_id"]),
        candidate_id=str(row["candidate_id"]),
        source_module=str(row["source_module"]),
        event_type=str(row["event_type"]),
        risk_weight=float(row["risk_weight"]),
        confidence=float(row["confidence"]),
        camera_id=str(row["camera_id"]) if row.get("camera_id") else None,
        evidence_path=str(row["evidence_path"]) if row.get("evidence_path") else None,
        description=str(row["description"]),
        timestamp=str(row["timestamp"]),
        event_id=str(row["event_id"]),
    )


def _has(events: list[EvidenceEvent], event_type: str, camera_id: str | None = None) -> bool:
    normalized = _normalize_event_type(event_type)
    return any(
        _normalize_event_type(event.event_type) == normalized
        and (camera_id is None or event.camera_id == camera_id)
        for event in events
    )


def _normalize_event_type(event_type: str) -> str:
    aliases = {
        "candidate_absent": "face_absent",
        "candidate_present": "candidate_present",
        "repeated_looking_away": "looking_away",
        "camera_stream_ready": "camera_ready",
        "camera_stream_restored": "camera_ready",
        "camera_stream_disconnected": "camera_disconnected",
        "camera_stream_missing": "camera_missing",
        "candidate_facing_phone_detected": "mobile_phone_detected",
        "phone_towards_screen_detected": "mobile_phone_detected",
        "possible_screen_capture_attempt": "mobile_phone_detected",
        "repeated_phone_visibility": "mobile_phone_detected",
    }
    return aliases.get(event_type, event_type)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)
