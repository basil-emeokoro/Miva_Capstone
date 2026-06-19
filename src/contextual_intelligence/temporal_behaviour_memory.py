from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from src.fusion.event_schema import EvidenceEvent


@dataclass(frozen=True)
class TemporalBehaviourSummary:
    window_seconds: int
    total_events: int
    event_frequency: dict[str, int] = field(default_factory=dict)
    module_frequency: dict[str, int] = field(default_factory=dict)
    persistent_patterns: list[str] = field(default_factory=list)
    isolated_events: list[str] = field(default_factory=list)


class TemporalBehaviourMemory:
    def __init__(self, persistent_threshold: int = 3) -> None:
        self.persistent_threshold = persistent_threshold

    def summarise(self, events: list[EvidenceEvent], window_seconds: int) -> TemporalBehaviourSummary:
        event_counts = Counter(_normalize_event_type(event.event_type) for event in events)
        module_counts = Counter(event.source_module for event in events)
        persistent = [
            event_type
            for event_type, count in sorted(event_counts.items())
            if count >= self.persistent_threshold
        ]
        isolated = [
            event_type
            for event_type, count in sorted(event_counts.items())
            if count == 1
        ]
        return TemporalBehaviourSummary(
            window_seconds=window_seconds,
            total_events=len(events),
            event_frequency=dict(event_counts),
            module_frequency=dict(module_counts),
            persistent_patterns=persistent,
            isolated_events=isolated,
        )


def _normalize_event_type(event_type: str) -> str:
    aliases = {
        "candidate_absent": "face_absent",
        "repeated_looking_away": "looking_away",
        "camera_stream_ready": "camera_ready",
        "camera_stream_restored": "camera_ready",
        "camera_stream_disconnected": "camera_disconnected",
        "camera_stream_missing": "camera_missing",
    }
    return aliases.get(event_type, event_type)

