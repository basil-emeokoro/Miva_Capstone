from __future__ import annotations

import time

import cv2

from src.vision.face_quality import assess_face_capture


def ai_auto_capture(camera_index: int = 0, direction: str = "front", timeout_seconds: int = 8) -> dict[str, object]:
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        return {
            "accepted": False,
            "image_bytes": None,
            "message": "Could not open the local webcam for AI auto-capture.",
        }

    deadline = time.time() + timeout_seconds
    best_message = "No valid frame was captured."
    try:
        while time.time() < deadline:
            ok, frame = capture.read()
            if not ok:
                continue
            encoded_ok, encoded = cv2.imencode(".jpg", frame)
            if not encoded_ok:
                continue
            image_bytes = encoded.tobytes()
            assessment = assess_face_capture(image_bytes, direction)
            best_message = str(assessment["message"])
            if assessment["accepted"]:
                return {
                    "accepted": True,
                    "image_bytes": image_bytes,
                    "assessment": assessment,
                    "message": "AI auto-capture accepted a valid face frame.",
                }
            time.sleep(0.15)
    finally:
        capture.release()

    return {
        "accepted": False,
        "image_bytes": None,
        "message": best_message,
    }
