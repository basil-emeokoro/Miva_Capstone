from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectDetectionHook:
    event_type: str
    confidence: float
    description: str


OBJECT_DETECTION_HOOKS = {
    "mobile_phone_detected": ObjectDetectionHook(
        "mobile_phone_detected",
        0.88,
        "Prototype hook: mobile phone detected in the environment view.",
    ),
    "unauthorised_object_detected": ObjectDetectionHook(
        "unauthorised_object_detected",
        0.82,
        "Prototype hook: unauthorised object detected in the monitoring area.",
    ),
}


def prototype_object_detection_event(event_type: str) -> ObjectDetectionHook:
    try:
        return OBJECT_DETECTION_HOOKS[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported object detection hook: {event_type}") from exc
