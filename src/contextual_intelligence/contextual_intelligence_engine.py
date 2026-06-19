from __future__ import annotations

from dataclasses import replace

from src.contextual_intelligence.contextual_reasoning_module import ContextualReasoningModule
from src.contextual_intelligence.event_fusion_module import EventFusionModule
from src.contextual_intelligence.explainability_interface import ExplainabilityInterface
from src.contextual_intelligence.risk_scoring_engine import ContextualRiskScoringEngine
from src.contextual_intelligence.temporal_behaviour_memory import TemporalBehaviourMemory
from src.fusion.event_schema import EvidenceEvent, FusedAlert


class ContextualIntelligenceEngine:
    """Central SERPS reasoning layer.

    The CIE encapsulates Event Fusion as a submodule and adds temporal behaviour memory,
    contextual scoring, reasoning trace enrichment, and explainability handoff.
    """

    def __init__(self, time_window_seconds: int = 20) -> None:
        self.time_window_seconds = time_window_seconds
        self.event_fusion = EventFusionModule(time_window_seconds=time_window_seconds)
        self.temporal_memory = TemporalBehaviourMemory()
        self.risk_scoring = ContextualRiskScoringEngine()
        self.contextual_reasoning = ContextualReasoningModule()
        self.explainability = ExplainabilityInterface()

    def ingest(self, event: EvidenceEvent) -> FusedAlert | None:
        self.event_fusion.buffer.add(event)
        current_events = self.event_fusion.buffer.within_window(event.session_id, event, self.time_window_seconds)
        rolling_events = self.event_fusion.buffer.within_window(event.session_id, event, self.time_window_seconds * 3)
        alert = self.event_fusion.fuse(current_events, rolling_events=rolling_events)
        return self._contextualise(alert, rolling_events or current_events, self.time_window_seconds * 3)

    def fuse_recent(self, session_id: str, window_seconds: int | None = None) -> FusedAlert | None:
        seconds = window_seconds or self.time_window_seconds
        current_events = self.event_fusion.load_events_for_window(session_id, seconds)
        rolling_events = self.event_fusion.load_events_for_window(session_id, seconds * 3)
        alert = self.event_fusion.fuse(current_events, rolling_events=rolling_events)
        return self._contextualise(alert, rolling_events or current_events, seconds * 3)

    def fuse(
        self,
        events: list[EvidenceEvent],
        rolling_events: list[EvidenceEvent] | None = None,
    ) -> FusedAlert | None:
        alert = self.event_fusion.fuse(events, rolling_events=rolling_events)
        return self._contextualise(alert, rolling_events or events, self.time_window_seconds * 3)

    def load_events_for_window(self, session_id: str, window_seconds: int | None = None) -> list[EvidenceEvent]:
        return self.event_fusion.load_events_for_window(session_id, window_seconds)

    def _contextualise(
        self,
        alert: FusedAlert | None,
        memory_events: list[EvidenceEvent],
        memory_window_seconds: int,
    ) -> FusedAlert | None:
        if not alert:
            return None

        memory = self.temporal_memory.summarise(memory_events, memory_window_seconds)
        risk_result = self.risk_scoring.apply_context(alert, memory)
        explanation = self.explainability.build_explanation(alert, memory, risk_result)
        reasoning_trace = self.contextual_reasoning.build_trace(alert, memory, risk_result)
        modules = sorted(set(alert.contributing_modules) | set(memory.module_frequency))
        trend = alert.risk_trend
        if risk_result.adjustment > 0 and trend == "stable":
            trend = "increasing"

        return replace(
            alert,
            risk_score=risk_result.rolling_risk_score,
            risk_level=risk_result.risk_level,
            explanation=explanation,
            current_risk_score=risk_result.current_risk_score,
            rolling_risk_score=risk_result.rolling_risk_score,
            risk_trend=trend,
            contributing_modules=modules,
            reasoning_trace=reasoning_trace,
        )

