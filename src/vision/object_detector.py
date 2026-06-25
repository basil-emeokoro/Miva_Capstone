from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np


@dataclass(frozen=True)
class ObjectDetectionHook:
    event_type: str
    confidence: float
    description: str


@dataclass(frozen=True)
class ObjectDetectionResult:
    event_type: str
    confidence: float
    description: str
    model_name: str
    available: bool = True


@dataclass(frozen=True)
class ObjectDetectionConfig:
    model_name: str = "yolov8n.pt"
    confidence_threshold: float = 0.35


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
    "laptop_or_tablet_detected": ObjectDetectionHook(
        "laptop_or_tablet_detected",
        0.72,
        "Prototype hook: laptop or tablet detected in the monitoring area.",
    ),
    "book_or_document_detected": ObjectDetectionHook(
        "book_or_document_detected",
        0.7,
        "Prototype hook: book or document detected in the monitoring area.",
    ),
    "headphones_or_earpiece_detected": ObjectDetectionHook(
        "headphones_or_earpiece_detected",
        0.7,
        "Prototype hook: headphones or earpiece detected during monitoring.",
    ),
    "suspicious_handheld_object_detected": ObjectDetectionHook(
        "suspicious_handheld_object_detected",
        0.74,
        "Prototype hook: suspicious handheld object detected near the candidate.",
    ),
}


PHONE_LABELS = {"cell phone", "mobile phone", "phone", "smartphone"}
LAPTOP_TABLET_LABELS = {"laptop", "tablet", "ipad", "notebook computer"}
BOOK_DOCUMENT_LABELS = {"book", "notebook", "paper", "document", "binder"}
HEADPHONE_LABELS = {"headphones", "earphones", "earpiece", "headset"}
HANDHELD_OBJECT_LABELS = {"remote", "keyboard", "mouse", "tv", "scissors", "knife"}
UNAUTHORISED_LABELS = PHONE_LABELS | LAPTOP_TABLET_LABELS | BOOK_DOCUMENT_LABELS | HEADPHONE_LABELS | HANDHELD_OBJECT_LABELS


def prototype_object_detection_event(event_type: str) -> ObjectDetectionHook:
    try:
        return OBJECT_DETECTION_HOOKS[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported object detection hook: {event_type}") from exc


def analyse_objects_with_yolo(
    image_bytes: bytes,
    confidence_threshold: float = 0.35,
    config: ObjectDetectionConfig | None = None,
) -> list[ObjectDetectionResult]:
    """Run optional YOLO object analysis without making any misconduct decision.

    The model is loaded lazily only when this function is explicitly called. If
    ultralytics or a local YOLO model is unavailable, the function returns a
    non-event diagnostic result so callers can degrade to prototype hooks.
    """
    config = config or ObjectDetectionConfig(confidence_threshold=confidence_threshold)
    model = _load_yolo_model(config.model_name)
    if model is None:
        return [
            ObjectDetectionResult(
                "object_detector_unavailable",
                0.0,
                "YOLO object detector is not available in this local environment.",
                "ultralytics-yolo",
                available=False,
            )
        ]
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return [
            ObjectDetectionResult(
                "camera_obstructed",
                0.8,
                "Image could not be decoded for object analysis.",
                "ultralytics-yolo",
            )
        ]
    detections: list[ObjectDetectionResult] = []
    results = model(image, verbose=False)
    names = getattr(model, "names", {})
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        for box in boxes:
            confidence = float(box.conf[0]) if getattr(box, "conf", None) is not None else 0.0
            if confidence < config.confidence_threshold:
                continue
            class_id = int(box.cls[0]) if getattr(box, "cls", None) is not None else -1
            label = str(names.get(class_id, class_id)).lower()
            if label in PHONE_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "mobile_phone_detected",
                        confidence,
                        f"YOLO detected a possible mobile phone ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
            elif label in LAPTOP_TABLET_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "laptop_or_tablet_detected",
                        confidence,
                        f"YOLO detected a possible laptop or tablet ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
            elif label in BOOK_DOCUMENT_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "book_or_document_detected",
                        confidence,
                        f"YOLO detected a possible book or document ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
            elif label in HEADPHONE_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "headphones_or_earpiece_detected",
                        confidence,
                        f"YOLO detected possible headphones or earpiece ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
            elif label in HANDHELD_OBJECT_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "suspicious_handheld_object_detected",
                        confidence,
                        f"YOLO detected a suspicious handheld object ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
            elif label in UNAUTHORISED_LABELS:
                detections.append(
                    ObjectDetectionResult(
                        "unauthorised_object_detected",
                        confidence,
                        f"YOLO detected a possible unauthorised object ({label}) in the monitoring frame.",
                        "ultralytics-yolo",
                    )
                )
    return detections


@lru_cache(maxsize=4)
def _load_yolo_model(model_name: str = "yolov8n.pt") -> object | None:
    try:
        from ultralytics import YOLO
    except Exception:
        return None
    try:
        return YOLO(model_name)
    except Exception:
        return None
