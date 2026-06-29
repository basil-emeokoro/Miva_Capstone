from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from src.utils.config_loader import ROOT_DIR
from src.utils.time_utils import utc_now_iso


RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
SAFE_DUE_PROCESS_MESSAGE = (
    "A potential examination integrity concern has been detected. Please provide your explanation. "
    "Your response and the associated evidence will be reviewed by an authorised examination official "
    "before any determination is made."
)


@dataclass(frozen=True)
class InstitutionalPolicyRule:
    policy_id: str
    institution_profiles: list[str]
    min_risk_level: str
    workflow_label: str
    recommended_actions: list[str]
    pause_assessment: bool
    require_acknowledgement: bool
    notify_role: str
    preserve_evidence: bool
    candidate_message: str
    event_type_actions: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "InstitutionalPolicyRule":
        return cls(
            policy_id=str(data["policy_id"]),
            institution_profiles=[str(item) for item in data.get("institution_profiles", [])],
            min_risk_level=str(data.get("min_risk_level", "Low")),
            workflow_label=str(data.get("workflow_label", "Institutional incident workflow")),
            recommended_actions=[str(item) for item in data.get("recommended_actions", [])],
            pause_assessment=bool(data.get("pause_assessment", False)),
            require_acknowledgement=bool(data.get("require_acknowledgement", False)),
            notify_role=str(data.get("notify_role", "Reviewer")),
            preserve_evidence=bool(data.get("preserve_evidence", True)),
            candidate_message=_safe_candidate_message(str(data.get("candidate_message", SAFE_DUE_PROCESS_MESSAGE))),
            event_type_actions={
                str(event_type): [str(action) for action in actions]
                for event_type, actions in dict(data.get("event_type_actions", {})).items()
            },
        )


@dataclass(frozen=True)
class PolicyDecision:
    policy_id: str
    institution_profile: str
    alert_id: str
    session_id: str
    candidate_id: str
    risk_level: str
    agent_priority: str
    agent_actions: list[str]
    recommended_actions: list[str]
    pause_assessment: bool
    require_acknowledgement: bool
    notify_role: str
    preserve_evidence: bool
    candidate_message: str
    workflow_label: str
    status: str
    created_at: str = field(default_factory=utc_now_iso)
    decision_id: str = field(default_factory=lambda: f"POL-{uuid4().hex[:8].upper()}")

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "policy_id": self.policy_id,
            "institution_profile": self.institution_profile,
            "alert_id": self.alert_id,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "risk_level": self.risk_level,
            "agent_priority": self.agent_priority,
            "agent_actions": self.agent_actions,
            "recommended_actions": self.recommended_actions,
            "pause_assessment": self.pause_assessment,
            "require_acknowledgement": self.require_acknowledgement,
            "notify_role": self.notify_role,
            "preserve_evidence": self.preserve_evidence,
            "candidate_message": self.candidate_message,
            "workflow_label": self.workflow_label,
            "status": self.status,
            "created_at": self.created_at,
        }


def load_policy_rules(path: str | Path | None = None) -> list[InstitutionalPolicyRule]:
    policy_path = Path(path) if path else ROOT_DIR / "config" / "institutional_policies.json"
    with policy_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [InstitutionalPolicyRule.from_dict(item) for item in payload.get("policies", [])]


def evaluate_institutional_policy(
    alert: dict[str, object],
    institution_profile: str,
    agent_actions: list[str] | None = None,
    agent_priority: str = "normal",
    rules: list[InstitutionalPolicyRule] | None = None,
) -> PolicyDecision:
    resolved_profile = normalize_institution_profile(institution_profile)
    risk_level = str(alert.get("risk_level") or "Low")
    selected_rule = select_policy_rule(resolved_profile, risk_level, rules or load_policy_rules())
    recommended_actions = _merge_policy_event_actions(selected_rule, _extract_event_types(alert))
    pause_assessment = selected_rule.pause_assessment or "pause_exam_timer" in recommended_actions
    require_acknowledgement = selected_rule.require_acknowledgement or "require_candidate_acknowledgement" in recommended_actions
    candidate_message = _candidate_message_for_actions(selected_rule.candidate_message, recommended_actions)
    status = "awaiting_candidate_acknowledgement" if require_acknowledgement else "policy_action_recorded"
    return PolicyDecision(
        policy_id=selected_rule.policy_id,
        institution_profile=resolved_profile,
        alert_id=str(alert["alert_id"]),
        session_id=str(alert["session_id"]),
        candidate_id=str(alert["candidate_id"]),
        risk_level=risk_level,
        agent_priority=agent_priority,
        agent_actions=agent_actions or [],
        recommended_actions=recommended_actions,
        pause_assessment=pause_assessment,
        require_acknowledgement=require_acknowledgement,
        notify_role=selected_rule.notify_role,
        preserve_evidence=selected_rule.preserve_evidence,
        candidate_message=candidate_message,
        workflow_label=selected_rule.workflow_label,
        status=status,
    )


def select_policy_rule(
    institution_profile: str,
    risk_level: str,
    rules: list[InstitutionalPolicyRule],
) -> InstitutionalPolicyRule:
    risk_rank = RISK_ORDER.get(risk_level, RISK_ORDER["Low"])
    profile_candidates = [institution_profile, "Generic"]
    matches = [
        rule
        for rule in rules
        if any(profile in rule.institution_profiles for profile in profile_candidates)
        and RISK_ORDER.get(rule.min_risk_level, RISK_ORDER["Low"]) <= risk_rank
    ]
    if not matches:
        raise ValueError(f"No institutional policy rule matched {institution_profile} at {risk_level}.")

    def sort_key(rule: InstitutionalPolicyRule) -> tuple[int, int]:
        specificity = 2 if institution_profile in rule.institution_profiles else 1
        threshold = RISK_ORDER.get(rule.min_risk_level, RISK_ORDER["Low"])
        return specificity, threshold

    return sorted(matches, key=sort_key, reverse=True)[0]


def normalize_institution_profile(value: str | None) -> str:
    profile = (value or "Generic").strip()
    if profile.lower() in {"miva", "miva open university", "university"}:
        return "University"
    if profile.upper() == "WAEC":
        return "WAEC"
    return "Generic" if not profile else profile


def _safe_candidate_message(message: str) -> str:
    forbidden = ["you have committed malpractice", "candidate cheated", "you cheated"]
    lowered = message.lower()
    if any(phrase in lowered for phrase in forbidden):
        return SAFE_DUE_PROCESS_MESSAGE
    return message


def _extract_event_types(alert: dict[str, object]) -> list[str]:
    value = alert.get("contributing_event_types") or alert.get("event_types")
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        if isinstance(decoded, list):
            return [str(item) for item in decoded]
    return []


def _merge_policy_event_actions(rule: InstitutionalPolicyRule, event_types: list[str]) -> list[str]:
    actions = list(rule.recommended_actions)
    for event_type in event_types:
        for action in rule.event_type_actions.get(event_type, []):
            if action not in actions:
                actions.append(action)
    return actions


def _candidate_message_for_actions(base_message: str, actions: list[str]) -> str:
    if "activate_temporary_screen_shield" not in actions:
        return base_message
    return _safe_candidate_message(
        "A potential examination integrity concern has been detected. Exam content is temporarily protected "
        "while the system records the event for authorised review. Please provide your explanation if requested "
        "by institutional policy."
    )
