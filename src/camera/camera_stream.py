from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.fusion.event_schema import EvidenceEvent
from src.session.environment_checker import MODE_REQUIREMENTS
from src.utils.time_utils import utc_now_iso


CameraRole = Literal["primary", "secondary"]
StreamState = Literal["ready", "missing", "disconnected", "not_required"]


@dataclass(frozen=True)
class CameraDevice:
    device_id: str
    label: str
    role_hint: CameraRole
    browser_managed: bool = True


@dataclass(frozen=True)
class CameraStreamStatus:
    camera_id: CameraRole
    label: str
    required: bool
    state: StreamState
    monitoring_mode: str
    updated_at: str
    detail: str

    @property
    def display_state(self) -> str:
        return self.state.replace("_", " ").title()


def discover_camera_devices() -> list[CameraDevice]:
    """Return safe browser-camera slots without opening camera hardware."""
    return [
        CameraDevice("browser-primary", "Primary camera slot (browser default)", "primary"),
        CameraDevice("browser-secondary", "Secondary camera slot (USB/mobile environment view)", "secondary"),
    ]


def required_camera_roles(mode: str) -> set[CameraRole]:
    requirements = MODE_REQUIREMENTS.get(mode.upper(), set())
    roles: set[CameraRole] = set()
    if "primary_camera" in requirements:
        roles.add("primary")
    if "secondary_camera" in requirements:
        roles.add("secondary")
    return roles


def evaluate_camera_streams(
    mode: str,
    primary_connected: bool,
    secondary_connected: bool,
    primary_label: str = "Primary camera",
    secondary_label: str = "Secondary camera",
) -> list[CameraStreamStatus]:
    normalized_mode = mode.upper()
    required_roles = required_camera_roles(normalized_mode)
    timestamp = utc_now_iso()
    statuses = [
        _build_status("primary", primary_label, "primary" in required_roles, primary_connected, normalized_mode, timestamp),
        _build_status("secondary", secondary_label, "secondary" in required_roles, secondary_connected, normalized_mode, timestamp),
    ]
    return statuses


def _build_status(
    role: CameraRole,
    label: str,
    required: bool,
    connected: bool,
    mode: str,
    timestamp: str,
) -> CameraStreamStatus:
    if not required:
        state: StreamState = "not_required"
        detail = f"{label} is not required for Monitoring Mode {mode}."
    elif connected:
        state = "ready"
        detail = f"{label} is ready for Monitoring Mode {mode}."
    else:
        state = "missing"
        detail = f"{label} is required but not available for Monitoring Mode {mode}."
    return CameraStreamStatus(
        camera_id=role,
        label=label,
        required=required,
        state=state,
        monitoring_mode=mode,
        updated_at=timestamp,
        detail=detail,
    )


def camera_status_event(session_id: str, candidate_id: str, status: CameraStreamStatus) -> EvidenceEvent:
    event_type_by_state = {
        "ready": "camera_stream_ready",
        "missing": "camera_stream_missing",
        "disconnected": "camera_stream_disconnected",
        "not_required": "camera_stream_not_required",
    }
    risk_by_state = {
        "ready": 0.02,
        "missing": 0.5 if status.required else 0.02,
        "disconnected": 0.65 if status.required else 0.2,
        "not_required": 0.01,
    }
    source_module = f"{status.camera_id}_camera" if status.required or status.state != "not_required" else "system_health"
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module=source_module,
        event_type=event_type_by_state[status.state],
        risk_weight=risk_by_state[status.state],
        confidence=0.95,
        camera_id=status.camera_id,
        description=status.detail,
    )


def manual_camera_health_event(
    session_id: str,
    candidate_id: str,
    camera_id: CameraRole,
    event_type: str,
    description: str,
) -> EvidenceEvent:
    risk_weight = 0.65 if event_type in {"camera_stream_disconnected", "camera_stream_missing"} else 0.15
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module=f"{camera_id}_camera",
        event_type=event_type,
        risk_weight=risk_weight,
        confidence=0.9,
        camera_id=camera_id,
        description=description,
    )
