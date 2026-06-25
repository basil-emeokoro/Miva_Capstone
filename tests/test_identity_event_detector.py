from src.authentication.identity_event_detector import (
    IDENTITY_EVENT_DEFINITIONS,
    analyse_identity_confidence,
    create_identity_event,
    create_identity_event_from_analysis,
)


def test_identity_pipeline_defines_required_event_types() -> None:
    required = {
        "identity_verified",
        "identity_confidence_low",
        "face_mismatch_detected",
        "candidate_substitution_suspected",
        "unknown_face_detected",
    }

    assert required.issubset(IDENTITY_EVENT_DEFINITIONS)


def test_identity_event_uses_common_evidence_schema() -> None:
    event = create_identity_event("SESSION-1", "CAND-1", "face_mismatch_detected")

    assert event.event_id.startswith("EVT-")
    assert event.session_id == "SESSION-1"
    assert event.candidate_id == "CAND-1"
    assert event.source_module == "identity"
    assert event.event_type == "face_mismatch_detected"
    assert event.camera_id == "primary"
    assert event.risk_weight > 0
    assert event.confidence > 0


def test_identity_confidence_maps_to_verification_event() -> None:
    result = analyse_identity_confidence(0.82, threshold=0.65)
    event = create_identity_event_from_analysis("SESSION-1", "CAND-1", result)

    assert event.event_type == "identity_verified"
    assert event.confidence == 0.82
    assert "periodic_face_verifier" in event.description


def test_low_identity_confidence_maps_to_substitution_signal() -> None:
    result = analyse_identity_confidence(0.2, threshold=0.65, substitution_threshold=0.35)

    assert result.event_type == "candidate_substitution_suspected"


def test_unknown_face_maps_to_unknown_face_signal() -> None:
    result = analyse_identity_confidence(0.4, unknown_face=True)

    assert result.event_type == "unknown_face_detected"
