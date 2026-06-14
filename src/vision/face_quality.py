from __future__ import annotations

import cv2
import numpy as np


def assess_face_capture(image_bytes: bytes) -> dict[str, object]:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return {
            "accepted": False,
            "face_count": 0,
            "quality_score": 0.0,
            "message": "Image could not be decoded. Retake the capture.",
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if len(faces) == 0:
        return {
            "accepted": False,
            "face_count": 0,
            "quality_score": 0.0,
            "message": "No face was detected. Centre the face inside the guide and retake.",
        }
    if len(faces) > 1:
        return {
            "accepted": False,
            "face_count": int(len(faces)),
            "quality_score": 0.0,
            "message": "Multiple faces were detected. Only the candidate should be visible.",
        }
    if brightness < 45:
        return {
            "accepted": False,
            "face_count": 1,
            "quality_score": 0.35,
            "message": "Lighting is too low. Improve lighting and retake.",
        }
    if sharpness < 25:
        return {
            "accepted": False,
            "face_count": 1,
            "quality_score": 0.4,
            "message": "Capture appears blurred. Hold still and retake.",
        }

    quality = min(0.98, 0.55 + min(brightness / 255, 0.25) + min(sharpness / 600, 0.18))
    return {
        "accepted": True,
        "face_count": 1,
        "quality_score": round(float(quality), 2),
        "message": "Face detected. Capture quality is acceptable for prototype enrolment.",
    }


def extract_face_embedding(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image could not be decoded.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) != 1:
        raise ValueError("Exactly one face is required to generate a face template.")

    x, y, width, height = faces[0]
    face = gray[y : y + height, x : x + width]
    resized = cv2.resize(face, (64, 64), interpolation=cv2.INTER_AREA)
    normalized = resized.astype("float32") / 255.0
    embedding = normalized.flatten()
    norm = np.linalg.norm(embedding)
    if norm == 0:
        raise ValueError("Invalid face template.")
    return embedding / norm
