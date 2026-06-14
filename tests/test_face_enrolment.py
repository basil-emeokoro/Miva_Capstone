from src.enrolment.face_enrolment import FACE_DIRECTIONS


def test_face_enrolment_requires_six_directional_samples() -> None:
    assert FACE_DIRECTIONS == ["front", "left", "right", "slight_up", "slight_down", "centre"]
