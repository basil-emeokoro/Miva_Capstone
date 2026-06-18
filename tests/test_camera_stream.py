from src.camera.camera_stream import camera_status_event, evaluate_camera_streams, required_camera_roles


def test_mode_a_requires_only_primary_camera() -> None:
    statuses = evaluate_camera_streams("A", primary_connected=True, secondary_connected=False)

    assert required_camera_roles("A") == {"primary"}
    assert statuses[0].camera_id == "primary"
    assert statuses[0].state == "ready"
    assert statuses[1].camera_id == "secondary"
    assert statuses[1].state == "not_required"


def test_mode_b_missing_secondary_camera_creates_common_schema_event() -> None:
    statuses = evaluate_camera_streams("B", primary_connected=True, secondary_connected=False)
    secondary_status = next(status for status in statuses if status.camera_id == "secondary")

    event = camera_status_event("SESSION-1", "CAND-1", secondary_status)

    assert secondary_status.required is True
    assert secondary_status.state == "missing"
    assert event.source_module == "secondary_camera"
    assert event.event_type == "camera_stream_missing"
    assert event.camera_id == "secondary"
    assert event.risk_weight > 0


def test_mode_c_secondary_camera_is_not_required() -> None:
    statuses = evaluate_camera_streams("C", primary_connected=True, secondary_connected=False)
    secondary_status = next(status for status in statuses if status.camera_id == "secondary")
    event = camera_status_event("SESSION-1", "CAND-1", secondary_status)

    assert required_camera_roles("C") == {"primary"}
    assert secondary_status.state == "not_required"
    assert event.source_module == "system_health"
    assert event.event_type == "camera_stream_not_required"
