from src.security.access_control import has_permission


def test_admin_can_manage_config() -> None:
    assert has_permission("Admin", "manage_config")


def test_human_proctor_cannot_review_alerts() -> None:
    assert not has_permission("Human Proctor", "review_alerts")


def test_reviewer_can_review_alerts() -> None:
    assert has_permission("Reviewer", "review_alerts")
