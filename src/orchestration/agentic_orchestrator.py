from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import FusedAlert


@dataclass(frozen=True)
class OrchestratedAction:
    alert_id: str
    priority: str
    actions: list[str]
    reviewer_summary: str


class AgenticOrchestrator:
    def plan_actions(self, alert: FusedAlert) -> OrchestratedAction:
        if alert.risk_level == "Critical":
            actions = [
                "pause session for reviewer attention",
                "trigger immediate re-authentication",
                "capture evidence screenshots",
                "send alert to escalation queue",
            ]
            priority = "urgent"
        elif alert.risk_level == "High":
            actions = [
                "trigger re-authentication",
                "capture evidence screenshots",
                "move session to high-priority reviewer queue",
            ]
            priority = "high"
        elif alert.risk_level == "Medium":
            actions = ["flag for reviewer inspection", "continue monitoring"]
            priority = "normal"
        else:
            actions = ["log alert", "continue monitoring"]
            priority = "low"

        return OrchestratedAction(
            alert_id=alert.alert_id,
            priority=priority,
            actions=actions,
            reviewer_summary=f"{alert.risk_level} alert: {alert.explanation}",
        )
