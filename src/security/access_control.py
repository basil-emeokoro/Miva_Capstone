from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "Admin"
    HUMAN_PROCTOR = "Human Proctor"
    REVIEWER = "Reviewer"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "register_candidate",
        "capture_enrolment",
        "start_session",
        "view_live_monitoring",
        "generate_demo_events",
        "review_alerts",
        "export_reports",
        "manage_config",
    },
    Role.HUMAN_PROCTOR: {
        "register_candidate",
        "capture_enrolment",
        "start_session",
        "view_live_monitoring",
        "generate_demo_events",
    },
    Role.REVIEWER: {
        "view_live_monitoring",
        "review_alerts",
        "export_reports",
    },
}


def has_permission(role: str, permission: str) -> bool:
    try:
        resolved_role = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS[resolved_role]
