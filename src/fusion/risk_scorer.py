from __future__ import annotations

from collections.abc import Iterable

from src.fusion.event_schema import EvidenceEvent, RiskLevel


class RiskScorer:
    def __init__(
        self,
        low_threshold: int = 25,
        medium_threshold: int = 50,
        high_threshold: int = 75,
        critical_threshold: int = 90,
    ) -> None:
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold

    def score(self, events: Iterable[EvidenceEvent]) -> int:
        event_list = list(events)
        if not event_list:
            return 0

        base_score = sum(event.risk_points() for event in event_list)
        source_diversity_bonus = max(0, len({event.source_module for event in event_list}) - 1) * 8
        identity_bonus = 20 if any(event.event_type in {"face_mismatch", "identity_substitution"} for event in event_list) else 0
        score = base_score + source_diversity_bonus + identity_bonus
        return min(100, score)

    def classify(self, score: int) -> RiskLevel:
        if score >= self.critical_threshold:
            return "Critical"
        if score >= self.high_threshold:
            return "High"
        if score >= self.medium_threshold:
            return "Medium"
        return "Low"
