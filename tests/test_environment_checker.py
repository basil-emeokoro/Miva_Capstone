from src.session.environment_checker import (
    FAIL,
    NOT_REQUIRED,
    OVERRIDE,
    PASS,
    device_check_allows_session_start,
    evaluate_device_checks,
    required_checks_for_mode,
)


def test_mode_a_does_not_require_secondary_camera() -> None:
    evaluation = evaluate_device_checks(
        "A",
        {
            "primary_camera": True,
            "microphone": True,
            "lighting": True,
            "candidate_presence": True,
            "environment_declaration": True,
        },
    )

    assert evaluation.overall_status == PASS
    assert evaluation.statuses["secondary_camera"] == NOT_REQUIRED


def test_mode_b_requires_secondary_camera() -> None:
    evaluation = evaluate_device_checks(
        "B",
        {
            "primary_camera": True,
            "microphone": True,
            "lighting": True,
            "candidate_presence": True,
            "environment_declaration": True,
        },
    )

    assert evaluation.overall_status == FAIL
    assert evaluation.statuses["secondary_camera"] == FAIL


def test_mode_c_requires_mirror() -> None:
    assert "mirror" in required_checks_for_mode("C")
    evaluation = evaluate_device_checks(
        "C",
        {
            "primary_camera": True,
            "microphone": True,
            "lighting": True,
            "candidate_presence": True,
            "environment_declaration": True,
            "mirror": True,
        },
    )

    assert evaluation.overall_status == PASS
    assert evaluation.statuses["secondary_camera"] == NOT_REQUIRED


def test_staff_override_allows_session_start_when_reason_is_recorded() -> None:
    evaluation = evaluate_device_checks("B", {}, staff_override=True, override_reason="Secondary camera unavailable.")

    assert evaluation.overall_status == OVERRIDE
    assert device_check_allows_session_start({"overall_status": OVERRIDE})
