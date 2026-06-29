import numpy as np

from src.camera.live_camera_validator import (
    capture_live_camera_sample,
    discover_physical_cameras,
    live_camera_event,
)
from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine


class FakeCapture:
    def __init__(self, opened=True, frame=None, fps=24.0):
        self.opened = opened
        self.frame = frame
        self.fps = fps
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if not self.opened or self.frame is None:
            return False, None
        return True, self.frame.copy()

    def get(self, prop):
        return self.fps

    def release(self):
        self.released = True


def test_discover_physical_cameras_probes_only_when_called() -> None:
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    def factory(index, backend):
        return FakeCapture(opened=index in {0, 2}, frame=frame, fps=30.0)

    devices = discover_physical_cameras(max_index=4, capture_factory=factory)

    assert [device.index for device in devices] == [0, 2]
    assert devices[0].width == 320
    assert devices[0].height == 240
    assert "Camera 0" in devices[0].display_label


def test_capture_live_camera_sample_returns_rgb_frame_and_metadata() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    frame[:, :, 2] = 255

    def factory(index, backend):
        return FakeCapture(opened=True, frame=frame, fps=25.0)

    sample = capture_live_camera_sample(0, "primary", sample_frames=3, capture_factory=factory)

    assert sample.connected is True
    assert sample.width == 160
    assert sample.height == 120
    assert sample.fps == 25.0
    assert sample.frame_rgb is not None
    assert sample.frame_rgb[0, 0, 0] == 255


def test_live_camera_event_uses_common_evidence_schema() -> None:
    sample = capture_live_camera_sample(
        1,
        "secondary",
        sample_frames=1,
        capture_factory=lambda index, backend: FakeCapture(opened=False, frame=None),
    )

    event = live_camera_event("SESSION-1", "CAND-1", sample)

    assert event.source_module == "secondary_camera"
    assert event.event_type == "camera_stream_disconnected"
    assert event.camera_id == "secondary"
    assert event.risk_weight > 0.5
    assert event.to_dict()["session_id"] == "SESSION-1"


def test_live_camera_event_can_enter_cie_pipeline() -> None:
    sample = capture_live_camera_sample(
        1,
        "primary",
        sample_frames=1,
        capture_factory=lambda index, backend: FakeCapture(opened=False, frame=None),
    )
    event = live_camera_event("SESSION-1", "CAND-1", sample)

    alert = ContextualIntelligenceEngine().ingest(event)

    assert alert is not None
    assert event.event_id in alert.contributing_events
    assert "primary_camera" in alert.contributing_modules
