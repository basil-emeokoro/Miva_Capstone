from __future__ import annotations

from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourSummary
from src.contextual_intelligence.risk_scoring_engine import ContextualRiskResult
from src.fusion.event_schema import FusedAlert


class ContextualReasoningModule:
    def build_trace(
        self,
        alert: FusedAlert,
        memory: TemporalBehaviourSummary,
        risk_result: ContextualRiskResult,
    ) -> list[str]:
        trace = list(alert.reasoning_trace)
        trace.append("Contextual Intelligence Engine evaluated the fused alert with temporal behaviour memory.")
        trace.append(
            f"Temporal window={memory.window_seconds}s; total events={memory.total_events}; "
            f"persistent patterns={', '.join(memory.persistent_patterns) if memory.persistent_patterns else 'none'}."
        )
        trace.extend(risk_result.reasons)
        trace.append(
            f"CIE contextual adjustment={risk_result.adjustment}; "
            f"contextual current score={risk_result.current_risk_score}; "
            f"contextual rolling score={risk_result.rolling_risk_score}."
        )
        trace.append("Agentic AI receives CIE output for workflow coordination; human reviewer remains final decision-maker.")
        return trace

