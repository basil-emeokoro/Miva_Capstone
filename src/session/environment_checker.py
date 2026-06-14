from __future__ import annotations

from dataclasses import dataclass

from src.session.monitoring_mode_controller import MonitoringModeController


PASS = "passed"
FAIL = "failed"
NOT_REQUIRED = "not_required"
OVERRIDE = "override"

CHECK_LABELS = {
    "primary_camera": "Primary camera",
    "secondary_camera": "Secondary camera",
    "microphone": "Microphone",
    "lighting": "Lighting",
    "candidate_presence": "Candidate presence",
    "environment_declaration": "Environment declaration",
    "mirror": "Mirror",
}

MODE_REQUIREMENTS = {
    "A": {"primary_camera", "microphone", "lighting", "candidate_presence", "environment_declaration"},
    "B": {"primary_camera", "secondary_camera", "microphone", "lighting", "candidate_presence", "environment_declaration"},
    "C": {"primary_camera", "microphone", "lighting", "candidate_presence", "environment_declaration", "mirror"},
}


@dataclass(frozen=True)
class DeviceCheckEvaluation:
    monitoring_mode: str
    statuses: dict[str, str]
    required_checks: list[str]
    overall_status: str
    details: dict[str, object]


def required_checks_for_mode(mode: str) -> list[str]:
    normalized_mode = mode.upper()
    if normalized_mode not in MODE_REQUIREMENTS:
        raise ValueError(f"Unsupported monitoring mode: {mode}")
    return [check for check in CHECK_LABELS if check in MODE_REQUIREMENTS[normalized_mode]]


def evaluate_device_checks(
    mode: str,
    checks: dict[str, bool],
    staff_override: bool = False,
    override_reason: str = "",
) -> DeviceCheckEvaluation:
    normalized_mode = mode.upper()
    required = set(required_checks_for_mode(normalized_mode))
    statuses: dict[str, str] = {}
    for check_name in CHECK_LABELS:
        if check_name not in required:
            statuses[check_name] = NOT_REQUIRED
        elif checks.get(check_name, False):
            statuses[check_name] = PASS
        else:
            statuses[check_name] = FAIL

    failed_required = [check for check in required if statuses[check] != PASS]
    if not failed_required:
        overall_status = PASS
    elif staff_override and override_reason.strip():
        overall_status = OVERRIDE
    else:
        overall_status = FAIL

    plan = MonitoringModeController().configure(normalized_mode)
    return DeviceCheckEvaluation(
        monitoring_mode=normalized_mode,
        statuses=statuses,
        required_checks=required_checks_for_mode(normalized_mode),
        overall_status=overall_status,
        details={
            "enabled_modules": plan.enabled_modules,
            "disabled_modules": plan.disabled_modules,
            "confidence_note": plan.confidence_note,
            "failed_required_checks": sorted(failed_required),
            "override_reason": override_reason.strip(),
        },
    )


def device_check_allows_session_start(check: dict[str, object] | None) -> bool:
    if not check:
        return False
    return str(check.get("overall_status")) in {PASS, OVERRIDE}
