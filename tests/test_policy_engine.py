from src.policy.policy_engine import evaluate_institutional_policy


def _alert(risk_level: str) -> dict[str, object]:
    return {
        "alert_id": f"ALT-{risk_level}",
        "session_id": "SESSION-POLICY",
        "candidate_id": "CAND-POLICY",
        "risk_level": risk_level,
    }


def _alert_with_event(risk_level: str, event_type: str) -> dict[str, object]:
    alert = _alert(risk_level)
    alert["contributing_event_types"] = [event_type]
    return alert


def test_waec_high_risk_requires_acknowledgement_and_reviewer_notice() -> None:
    decision = evaluate_institutional_policy(
        _alert("High"),
        "WAEC",
        agent_actions=["move session to high-priority reviewer queue"],
        agent_priority="high",
    )

    assert decision.policy_id == "waec_high_risk_incident_acknowledgement"
    assert decision.pause_assessment is True
    assert decision.require_acknowledgement is True
    assert decision.notify_role == "Reviewer"
    assert "potential examination integrity concern" in decision.candidate_message.lower()
    assert "committed malpractice" not in decision.candidate_message.lower()


def test_university_medium_risk_warns_without_pausing() -> None:
    decision = evaluate_institutional_policy(_alert("Medium"), "Miva")

    assert decision.policy_id == "university_medium_risk_warning_review"
    assert decision.pause_assessment is False
    assert decision.require_acknowledgement is False
    assert "display_warning" in decision.recommended_actions
    assert "flag_for_later_review" in decision.recommended_actions


def test_generic_critical_risk_preserves_evidence_for_senior_review() -> None:
    decision = evaluate_institutional_policy(_alert("Critical"), "Generic")

    assert decision.policy_id == "generic_critical_risk_senior_review"
    assert decision.pause_assessment is True
    assert decision.notify_role == "Senior Reviewer"
    assert "recommend_suspension" in decision.recommended_actions
    assert decision.preserve_evidence is True


def test_candidate_facing_phone_policy_can_activate_screen_shield() -> None:
    decision = evaluate_institutional_policy(
        _alert_with_event("High", "candidate_facing_phone_detected"),
        "WAEC",
        agent_actions=["escalate"],
        agent_priority="high",
    )

    assert "activate_temporary_screen_shield" in decision.recommended_actions
    assert "require_candidate_acknowledgement" in decision.recommended_actions
    assert decision.require_acknowledgement is True
    assert decision.pause_assessment is True
    assert "temporarily protected" in decision.candidate_message.lower()


def test_university_candidate_facing_phone_can_warn_without_screen_shield() -> None:
    decision = evaluate_institutional_policy(
        _alert_with_event("Medium", "candidate_facing_phone_detected"),
        "Miva",
    )

    assert "display_warning" in decision.recommended_actions
    assert "activate_temporary_screen_shield" not in decision.recommended_actions
    assert decision.pause_assessment is False
