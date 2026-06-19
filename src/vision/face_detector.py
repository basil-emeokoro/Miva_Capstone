from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class FaceDetectionResult:
    face_count: int
    brightness: float
    sharpness: float
    status: str
    confidence: float
    description: str
    face_box: tuple[int, int, int, int] | None = None
    frame_shape: tuple[int, int] | None = None


def analyse_face_presence(image_bytes: bytes) -> FaceDetectionResult:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return FaceDetectionResult(0, 0.0, 0.0, "camera_obstructed", 0.8, "Image could not be decoded.")
    return analyse_face_presence_frame(image)


def analyse_face_presence_frame(image: np.ndarray) -> FaceDetectionResult:
    """Analyse a decoded OpenCV frame without opening any camera device."""
    if image is None or image.size == 0:
        return FaceDetectionResult(0, 0.0, 0.0, "camera_obstructed", 0.8, "Image frame is empty.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    frame_shape = (int(image.shape[1]), int(image.shape[0]))
    if brightness < 25 or sharpness < 8:
        return FaceDetectionResult(
            0,
            brightness,
            sharpness,
            "camera_obstructed",
            0.78,
            "Camera view appears too dark, blurred, or obstructed for reliable monitoring.",
            frame_shape=frame_shape,
        )

    faces = _detect_faces(gray)
    if len(faces) == 0:
        return FaceDetectionResult(0, brightness, sharpness, "face_absent", 0.82, "No candidate face detected.", frame_shape=frame_shape)
    if len(faces) > 1:
        return FaceDetectionResult(
            len(faces),
            brightness,
            sharpness,
            "multiple_persons_detected",
            0.86,
            "More than one face was detected in the camera frame.",
            face_box=faces[0],
            frame_shape=frame_shape,
        )
    if sharpness < 20:
        return FaceDetectionResult(
            1,
            brightness,
            sharpness,
            "face_obstructed",
            0.7,
            "Candidate face is visible but partially blurred or obstructed.",
            face_box=faces[0],
            frame_shape=frame_shape,
        )
    return FaceDetectionResult(1, brightness, sharpness, "face_present", 0.9, "One candidate face is visible.", face_box=faces[0], frame_shape=frame_shape)


def _detect_faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.equalizeHist(gray)
    detected: list[tuple[int, int, int, int]] = []
    for cascade_name in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml"):
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_name)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(40, 40))
        detected.extend(tuple(map(int, face)) for face in faces)
    return _deduplicate_faces(detected)


def _deduplicate_faces(faces: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    if len(faces) <= 1:
        return faces
    selected: list[tuple[int, int, int, int]] = []
    for face in sorted(faces, key=lambda item: item[2] * item[3], reverse=True):
        if all(_overlap_ratio(face, existing) < 0.4 for existing in selected):
            selected.append(face)
    return selected


def _overlap_ratio(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x_left = max(ax, bx)
    y_top = max(ay, by)
    x_right = min(ax + aw, bx + bw)
    y_bottom = min(ay + ah, by + bh)
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
    intersection = (x_right - x_left) * (y_bottom - y_top)
    return intersection / float(min(aw * ah, bw * bh))
