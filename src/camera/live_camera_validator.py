from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from typing import Callable, Literal

import cv2
import numpy as np

from src.fusion.event_schema import EvidenceEvent


CameraRole = Literal["primary", "secondary"]
CaptureFactory = Callable[[int, int], object]


@dataclass(frozen=True)
class LiveCameraDevice:
    index: int
    label: str
    width: int
    height: int
    fps: float
    available: bool = True

    @property
    def display_label(self) -> str:
        resolution = f"{self.width}x{self.height}" if self.width and self.height else "resolution unknown"
        fps_label = f"{self.fps:.1f} FPS" if self.fps > 0 else "FPS unknown"
        return f"Camera {self.index} - {resolution} - {fps_label}"


@dataclass(frozen=True)
class LiveCameraSample:
    role: CameraRole
    index: int
    connected: bool
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_rgb: np.ndarray | None = None
    message: str = ""

    @property
    def status_label(self) -> str:
        return "Connected" if self.connected else "Disconnected"

    @property
    def resolution_label(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unavailable"


def discover_physical_cameras(max_index: int = 8, capture_factory: CaptureFactory | None = None) -> list[LiveCameraDevice]:
    """Probe local OpenCV camera indices only when explicitly called by the UI."""

    factory = capture_factory or _open_capture
    devices: list[LiveCameraDevice] = []
    for index in range(max_index):
        capture = factory(index, _preferred_backend())
        try:
            if not _capture_is_opened(capture):
                continue
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            height, width = frame.shape[:2]
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
            devices.append(LiveCameraDevice(index=index, label=f"Camera {index}", width=width, height=height, fps=fps))
        finally:
            _release_capture(capture)
    return devices


def capture_live_camera_sample(
    index: int,
    role: CameraRole,
    sample_frames: int = 12,
    capture_factory: CaptureFactory | None = None,
) -> LiveCameraSample:
    """Open one camera briefly, sample frames, then release the device."""

    factory = capture_factory or _open_capture
    capture = factory(index, _preferred_backend())
    started_at = time.perf_counter()
    frames_read = 0
    last_frame: np.ndarray | None = None
    try:
        if not _capture_is_opened(capture):
            return LiveCameraSample(role=role, index=index, connected=False, message=f"Camera {index} could not be opened.")

        for _ in range(max(1, sample_frames)):
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            frames_read += 1
            last_frame = frame

        if last_frame is None:
            return LiveCameraSample(role=role, index=index, connected=False, message=f"Camera {index} opened but produced no frame.")

        elapsed = max(time.perf_counter() - started_at, 0.001)
        measured_fps = frames_read / elapsed
        device_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        height, width = last_frame.shape[:2]
        frame_rgb = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)
        return LiveCameraSample(
            role=role,
            index=index,
            connected=True,
            width=width,
            height=height,
            fps=device_fps if device_fps > 1 else measured_fps,
            frame_rgb=frame_rgb,
            message=f"{role.title()} camera {index} produced live frames.",
        )
    finally:
        _release_capture(capture)


def live_camera_event(session_id: str, candidate_id: str, sample: LiveCameraSample) -> EvidenceEvent:
    if sample.connected:
        event_type = "camera_stream_ready"
        risk_weight = 0.02
        confidence = 0.95
        description = (
            f"{sample.role.title()} physical camera {sample.index} validated at "
            f"{sample.resolution_label}, {sample.fps:.1f} FPS."
        )
    else:
        event_type = "camera_stream_disconnected"
        risk_weight = 0.65
        confidence = 0.9
        description = sample.message or f"{sample.role.title()} physical camera {sample.index} is disconnected or unavailable."
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module=f"{sample.role}_camera",
        event_type=event_type,
        risk_weight=risk_weight,
        confidence=confidence,
        camera_id=sample.role,
        description=description,
    )


def sample_frame_to_jpeg_bytes(sample: LiveCameraSample) -> bytes | None:
    """Encode a captured RGB sample frame for downstream detector modules."""

    if sample.frame_rgb is None:
        return None
    bgr_frame = cv2.cvtColor(sample.frame_rgb, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", bgr_frame)
    if not ok:
        return None
    return encoded.tobytes()


def _preferred_backend() -> int:
    if platform.system().lower() == "windows":
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


def _open_capture(index: int, backend: int) -> cv2.VideoCapture:
    return cv2.VideoCapture(index, backend)


def _capture_is_opened(capture: object) -> bool:
    return bool(getattr(capture, "isOpened")())


def _release_capture(capture: object) -> None:
    release = getattr(capture, "release", None)
    if callable(release):
        release()
