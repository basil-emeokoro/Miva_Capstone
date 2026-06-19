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
            f" The Contextual Intelligence Engine evaluated {memory.total_events} contributing event(s) "
            f"inside a {memory.window_seconds}-second temporal window and assigned {risk_result.risk_level} Risk "
            f"with current risk score {risk_result.current_risk_score}, contextual rolling score {risk_result.rolling_risk_score}, "
            f"and confidence {alert.confidence:.2f}. Recommended reviewer action: {alert.recommended_action}"
        )
        return explanation
