from src.session.monitoring_mode_controller import MonitoringModeController


def test_mode_b_enables_secondary_camera() -> None:
    plan = MonitoringModeController().configure("B")
    assert "secondary_camera" in plan.enabled_modules
    assert plan.disabled_modules == []


def test_mode_c_reduces_reflected_object_confidence() -> None:
    plan = MonitoringModeController().configure("C")
    assert "high_confidence_reflected_object_detection" in plan.disabled_modules
