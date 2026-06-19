from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import FusedAlert, RiskLevel
from src.fusion.risk_scorer import RiskScorer
from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourSummary


@dataclass(frozen=True)
class ContextualRiskResult:
    current_risk_score: int
    rolling_risk_score: int
    risk_level: RiskLevel
    adjustment: int
    reasons: list[str]


class ContextualRiskScoringEngine:
    def __init__(self, scorer: RiskScorer | None = None) -> None:
        self.scorer = scorer or RiskScorer()

    def apply_context(self, alert: FusedAlert, memory: TemporalBehaviourSummary) -> ContextualRiskResult:
        adjustment = 0
        reasons: list[str] = []
        if memory.persistent_patterns:
            adjustment += min(12, len(memory.persistent_patterns) * 6)
            reasons.append(
                "Temporal behaviour memory found persistent pattern(s): "
                + ", ".join(memory.persistent_patterns)
                + "."
            )
        if len(memory.module_frequency) >= 3:
            adjustment += 4
            reasons.append("Evidence came from three or more independent modules.")
        if memory.total_events >= 5:
            adjustment += 4
            reasons.append("Event frequency is elevated within the temporal window.")
        reasons.append("Reviewer feedback weighting is reserved as a future supervised-learning input.")

        current = min(100, int(alert.current_risk_score or alert.risk_score) + adjustment)
        rolling = min(100, max(current, int(alert.rolling_risk_score or alert.risk_score) + adjustment))
        return ContextualRiskResult(
            current_risk_score=current,
            rolling_risk_score=rolling,
            risk_level=self.scorer.classify(rolling),
            adjustment=adjustment,
            reasons=reasons,
        )

