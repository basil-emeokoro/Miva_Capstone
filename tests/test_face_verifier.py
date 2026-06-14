import pytest

from src.authentication.face_verifier import verify_face_against_enrolment


def test_face_verifier_rejects_invalid_image_bytes() -> None:
    with pytest.raises(ValueError):
        verify_face_against_enrolment("CAND-UNKNOWN", b"not-an-image")
