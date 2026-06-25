from __future__ import annotations

import json
from uuid import uuid4

from src.policy.policy_engine import PolicyDecision
from src.storage.candidate_repository import get_candidate
from src.storage.database import get_connection
from src.storage.event_repository import list_alerts, list_events
from src.session.session_manager import list_sessions
from src.utils.time_utils import utc_now_iso


REVIEWER_INCIDENT_ACTIONS = [
    "Observe",
    "Continue Monitoring",
    "Issue Warning",
    "Escalate",
    "Refer to Senior Reviewer",
    "Close Incident",
]


def save_policy_decision(decision: PolicyDecision) -> str:
    existing = get_policy_decision_for_alert(decision.alert_id)
    if existing:
        return str(existing["decision_id"])
    data = decision.to_dict()
    data["agent_actions"] = json.dumps(data["agent_actions"])
    data["recommended_actions"] = json.dumps(data["recommended_actions"])
    data["pause_assessment"] = int(bool(data["pause_assessment"]))
    data["require_acknowledgement"] = int(bool(data["require_acknowledgement"]))
    data["preserve_evidence"] = int(bool(data["preserve_evidence"]))
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO policy_decisions(
                decision_id, policy_id, institution_profile, alert_id, session_id, candidate_id,
                risk_level, agent_priority, agent_actions, recommended_actions, pause_assessment,
                require_acknowledgement, notify_role, preserve_evidence, candidate_message,
                workflow_label, status, created_at
            )
            VALUES (
                :decision_id, :policy_id, :institution_profile, :alert_id, :session_id, :candidate_id,
                :risk_level, :agent_priority, :agent_actions, :recommended_actions, :pause_assessment,
                :require_acknowledgement, :notify_role, :preserve_evidence, :candidate_message,
                :workflow_label, :status, :created_at
            )
            """,
            data,
        )
    return decision.decision_id


def list_policy_decisions(session_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM policy_decisions"
    params: tuple[object, ...] = ()
    if session_id:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_decode_decision(dict(row)) for row in rows]


def get_policy_decision(decision_id: str) -> dict[str, object] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM policy_decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    return _decode_decision(dict(row)) if row else None


def get_policy_decision_for_alert(alert_id: str) -> dict[str, object] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM policy_decisions WHERE alert_id = ? ORDER BY created_at DESC LIMIT 1", (alert_id,)).fetchone()
    return _decode_decision(dict(row)) if row else None


def record_candidate_acknowledgement(
    decision_id: str,
    candidate_id: str,
    candidate_explanation: str,
    acknowledged: bool,
) -> str:
    acknowledgement_id = f"ACK-{uuid4().hex[:8].upper()}"
    status = "candidate_acknowledged" if acknowledged else "candidate_response_recorded"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO incident_acknowledgements(
                acknowledgement_id, decision_id, candidate_id, candidate_explanation, acknowledged, acknowledged_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (acknowledgement_id, decision_id, candidate_id, candidate_explanation.strip(), int(acknowledged), utc_now_iso()),
        )
        connection.execute("UPDATE policy_decisions SET status = ? WHERE decision_id = ?", (status, decision_id))
    return acknowledgement_id


def list_candidate_acknowledgements(decision_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM incident_acknowledgements"
    params: tuple[object, ...] = ()
    if decision_id:
        query += " WHERE decision_id = ?"
        params = (decision_id,)
    query += " ORDER BY acknowledged_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def record_reviewer_incident_decision(
    decision_id: str,
    reviewer_id: str,
    reviewer_action: str,
    rationale: str,
) -> str:
    if reviewer_action not in REVIEWER_INCIDENT_ACTIONS:
        raise ValueError(f"Unsupported incident reviewer action: {reviewer_action}")
    incident_review_id = f"IRD-{uuid4().hex[:8].upper()}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reviewer_incident_decisions(
                incident_review_id, decision_id, reviewer_id, reviewer_action, rationale, reviewed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (incident_review_id, decision_id, reviewer_id, reviewer_action, rationale.strip(), utc_now_iso()),
        )
        connection.execute("UPDATE policy_decisions SET status = ? WHERE decision_id = ?", (reviewer_action.lower().replace(" ", "_"), decision_id))
    return incident_review_id


def list_reviewer_incident_decisions(decision_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM reviewer_incident_decisions"
    params: tuple[object, ...] = ()
    if decision_id:
        query += " WHERE decision_id = ?"
        params = (decision_id,)
    query += " ORDER BY reviewed_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def build_evidence_package(decision_id: str) -> dict[str, object]:
    decision = get_policy_decision(decision_id)
    if not decision:
        raise ValueError(f"Policy decision not found: {decision_id}")
    alert = next((item for item in list_alerts(str(decision["session_id"])) if str(item.get("alert_id")) == str(decision["alert_id"])), None)
    event_ids = set(_ensure_list(alert.get("contributing_events")) if alert else [])
    contributing_events = [
        event for event in list_events(str(decision["session_id"])) if not event_ids or str(event.get("event_id")) in event_ids
    ]
    session = next((item for item in list_sessions() if str(item.get("session_id")) == str(decision["session_id"])), None)
    return {
        "package_id": f"EPK-{decision_id}",
        "generated_at": utc_now_iso(),
        "candidate_profile": get_candidate(str(decision["candidate_id"])),
        "session_metadata": session,
        "policy_decision": decision,
        "contextual_risk_assessment": alert,
        "contributing_evidence": contributing_events,
        "candidate_acknowledgements": list_candidate_acknowledgements(decision_id),
        "reviewer_incident_decisions": list_reviewer_incident_decisions(decision_id),
        "audit_trail_note": "Full audit trail is stored separately in audit_logs; this package references the policy decision, alert, acknowledgement, and reviewer action records.",
    }


def _decode_decision(row: dict[str, object]) -> dict[str, object]:
    for field in ("agent_actions", "recommended_actions"):
        value = row.get(field)
        if isinstance(value, str):
            try:
                row[field] = json.loads(value)
            except json.JSONDecodeError:
                row[field] = []
    for field in ("pause_assessment", "require_acknowledgement", "preserve_evidence"):
        row[field] = bool(row.get(field))
    return row


def _ensure_list(value: object) -> list[str]:
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
