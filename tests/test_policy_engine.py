from src.policy.policy_engine import evaluate_institutional_policy


def _alert(risk_level: str) -> dict[str, object]:
    return {
        "alert_id": f"ALT-{risk_level}",
        "session_id": "SESSION-POLICY",
        "candidate_id": "CAND-POLICY",
        "risk_level": risk_level,
    }


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
