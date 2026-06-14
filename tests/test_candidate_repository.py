import pytest

from src.storage.candidate_repository import normalize_candidate_id


def test_waec_candidate_id_must_be_ten_digits() -> None:
    assert normalize_candidate_id("1234567001", "WAEC") == "1234567001"
    with pytest.raises(ValueError):
        normalize_candidate_id("1234567ABC", "WAEC")


def test_miva_candidate_id_must_be_digits_only() -> None:
    assert normalize_candidate_id("10000001", "Miva") == "10000001"
    with pytest.raises(ValueError):
        normalize_candidate_id("MIVA/001", "Miva")
