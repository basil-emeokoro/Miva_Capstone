from __future__ import annotations

from datetime import datetime

from src.fusion.event_schema import EvidenceEvent


class EventBuffer:
    def __init__(self) -> None:
        self._events: list[EvidenceEvent] = []

    def add(self, event: EvidenceEvent) -> None:
        self._events.append(event)

    def all(self) -> list[EvidenceEvent]:
        return list(self._events)

    def for_session(self, session_id: str) -> list[EvidenceEvent]:
        return [event for event in self._events if event.session_id == session_id]

    def within_window(self, session_id: str, anchor: EvidenceEvent, seconds: int) -> list[EvidenceEvent]:
        anchor_time = datetime.fromisoformat(anchor.timestamp)
        window: list[EvidenceEvent] = []
        for event in self.for_session(session_id):
            event_time = datetime.fromisoformat(event.timestamp)
            if abs((anchor_time - event_time).total_seconds()) <= seconds:
                window.append(event)
        return window
