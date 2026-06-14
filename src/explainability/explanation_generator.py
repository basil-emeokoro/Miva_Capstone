from __future__ import annotations

from collections import defaultdict

from src.fusion.event_schema import EvidenceEvent


class ExplanationGenerator:
    def generate(self, events: list[EvidenceEvent], risk_level: str) -> str:
        if not events:
            return "No contributing events were available."

        grouped: dict[str, list[EvidenceEvent]] = defaultdict(list)
        for event in events:
            grouped[event.source_module].append(event)

        parts: list[str] = []
        for source, source_events in grouped.items():
            labels = ", ".join(event.event_type.replace("_", " ") for event in source_events)
            confidence = max(event.confidence for event in source_events)
            parts.append(f"{source} reported {labels} with confidence up to {confidence:.2f}")

        return f"{risk_level}-risk alert generated because " + "; ".join(parts) + "."

    def recommended_action(self, risk_level: str) -> str:
        if risk_level == "Critical":
            return "Immediate reviewer inspection, candidate re-authentication, and escalation recommended."
        if risk_level == "High":
            return "Reviewer inspection and candidate re-authentication recommended."
        if risk_level == "Medium":
            return "Reviewer should inspect the event timeline and continue monitoring."
        return "Continue monitoring; no immediate escalation is required."
