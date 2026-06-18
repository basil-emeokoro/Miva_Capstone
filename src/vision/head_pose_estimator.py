from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeadPoseSignal:
    event_type: str
    confidence: float
    description: str


def estimate_head_pose_from_position(face_center_x_ratio: float, face_center_y_ratio: float) -> HeadPoseSignal:
    if face_center_x_ratio < 0.32 or face_center_x_ratio > 0.68:
        return HeadPoseSignal("looking_away", 0.72, "Face position suggests the candidate is looking away from the screen.")
    if face_center_y_ratio < 0.22 or face_center_y_ratio > 0.78:
        return HeadPoseSignal("head_movement_anomaly", 0.68, "Head position is outside the expected monitoring zone.")
    return HeadPoseSignal("face_present", 0.55, "Head position appears within the expected monitoring zone.")
