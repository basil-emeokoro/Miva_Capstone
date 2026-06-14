from __future__ import annotations

import cv2
import numpy as np


def mirror_image_bytes(image_bytes: bytes) -> bytes:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image could not be decoded.")
    flipped = cv2.flip(image, 1)
    ok, encoded = cv2.imencode(".jpg", flipped)
    if not ok:
        raise ValueError("Image could not be encoded after mirror correction.")
    return encoded.tobytes()


def assess_face_capture(image_bytes: bytes, direction: str = "front") -> dict[str, object]:
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
    gray = cv2.equalizeHist(gray)
    detection = _detect_faces(gray, direction)
    faces = detection["faces"]
    orientation = detection["orientation"]
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
    if direction in {"left", "right"} and orientation == "front":
        return {
            "accepted": False,
            "face_count": 1,
            "quality_score": 0.5,
            "message": f"Face is still too front-facing. Turn slightly to your {direction} and retake.",
        }

    quality = min(0.98, 0.55 + min(brightness / 255, 0.25) + min(sharpness / 600, 0.18))
    return {
        "accepted": True,
        "face_count": 1,
        "orientation": orientation,
        "quality_score": round(float(quality), 2),
        "message": "Face detected. Capture quality is acceptable for prototype enrolment.",
    }


def extract_face_embedding(image_bytes: bytes, direction: str = "front") -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image could not be decoded.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = _detect_faces(gray, direction)["faces"]
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


def _detect_faces(gray: np.ndarray, direction: str) -> dict[str, object]:
    cascade_names = [
        "haarcascade_frontalface_default.xml",
        "haarcascade_frontalface_alt2.xml",
    ]
    if direction in {"left", "right"}:
        cascade_names.insert(0, "haarcascade_profileface.xml")

    detected: list[tuple[int, int, int, int]] = []
    for cascade_name in cascade_names:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_name)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.06, minNeighbors=3, minSize=(40, 40))
        detected.extend(tuple(map(int, face)) for face in faces)
        if detected:
            orientation = "profile" if cascade_name == "haarcascade_profileface.xml" else "front"
            return {"faces": _deduplicate_faces(detected), "orientation": orientation}

        if direction in {"left", "right"} and cascade_name == "haarcascade_profileface.xml":
            flipped = cv2.flip(gray, 1)
            faces = cascade.detectMultiScale(flipped, scaleFactor=1.06, minNeighbors=3, minSize=(40, 40))
            width = gray.shape[1]
            detected.extend((int(width - x - w), int(y), int(w), int(h)) for x, y, w, h in faces)
            if detected:
                return {"faces": _deduplicate_faces(detected), "orientation": "profile"}
    return {"faces": [], "orientation": "unknown"}


def _deduplicate_faces(faces: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    if len(faces) <= 1:
        return faces
    faces_sorted = sorted(faces, key=lambda face: face[2] * face[3], reverse=True)
    return [faces_sorted[0]]
