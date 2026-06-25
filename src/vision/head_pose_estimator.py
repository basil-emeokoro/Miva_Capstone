from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeadPoseSignal:
    event_type: str
    confidence: float
    description: str
    direction: str = "centre"
    horizontal_ratio: float = 0.5
    vertical_ratio: float = 0.5


def estimate_head_pose_from_position(face_center_x_ratio: float, face_center_y_ratio: float) -> HeadPoseSignal:
    """Estimate coarse gaze/head-position evidence from detected face location.

    This is a lightweight service-ready signal, not a final behavioural
    judgement. Production-grade gaze should later use MediaPipe face landmarks
    or a dedicated WebRTC/OpenCV service.
    """
    x_ratio = max(0.0, min(float(face_center_x_ratio), 1.0))
    y_ratio = max(0.0, min(float(face_center_y_ratio), 1.0))
    direction = _direction_from_position(x_ratio, y_ratio)
    if x_ratio < 0.32 or x_ratio > 0.68:
        return HeadPoseSignal(
            "looking_away",
            0.72,
            f"Face position is biased {direction}, suggesting the candidate may be looking away from the screen.",
            direction,
            x_ratio,
            y_ratio,
        )
    if y_ratio < 0.22 or y_ratio > 0.78:
        return HeadPoseSignal(
            "head_movement_anomaly",
            0.68,
            f"Head position is biased {direction}, outside the expected monitoring zone.",
            direction,
            x_ratio,
            y_ratio,
        )
    return HeadPoseSignal(
        "face_present",
        0.55,
        "Head position appears within the expected monitoring zone.",
        direction,
        x_ratio,
        y_ratio,
    )


def _direction_from_position(x_ratio: float, y_ratio: float) -> str:
    horizontal = "centre"
    vertical = "centre"
    if x_ratio < 0.32:
        horizontal = "left"
    elif x_ratio > 0.68:
        horizontal = "right"
    if y_ratio < 0.22:
        vertical = "up"
    elif y_ratio > 0.78:
        vertical = "down"
    if horizontal == "centre":
        return vertical
    if vertical == "centre":
        return horizontal
    return f"{vertical}-{horizontal}"
