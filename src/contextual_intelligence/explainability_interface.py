from __future__ import annotations

from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourSummary
from src.contextual_intelligence.risk_scoring_engine import ContextualRiskResult
from src.fusion.event_schema import FusedAlert


class ExplainabilityInterface:
    def build_explanation(
        self,
        alert: FusedAlert,
        memory: TemporalBehaviourSummary,
        risk_result: ContextualRiskResult,
    ) -> str:
        explanation = alert.explanation
        if memory.persistent_patterns:
            explanation += (
                " Temporal Behaviour Memory elevated context because repeated pattern(s) were observed: "
                + ", ".join(memory.persistent_patterns)
                + "."
            )
        else:
            explanation += " Temporal Behaviour Memory treated the contributing evidence as non-persistent in the selected window."
        explanation += (
            f" The Contextual Intelligence Engine assigned {risk_result.risk_level} Risk "
            f"with contextual rolling score {risk_result.rolling_risk_score}."
        )
        return explanation

