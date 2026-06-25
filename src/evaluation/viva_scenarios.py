from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.contextual_intelligence.contextual_intelligence_engine import ContextualIntelligenceEngine
from src.fusion.event_schema import EvidenceEvent, FusedAlert, RiskLevel
from src.orchestration.agentic_orchestrator import AgenticOrchestrator
from src.policy.incident_repository import (
    record_candidate_acknowledgement,
    record_reviewer_incident_decision,
    save_policy_decision,
)
from src.policy.policy_engine import evaluate_institutional_policy
from src.storage.database import get_connection
from src.storage.event_repository import save_alert, save_event
from src.utils.time_utils import utc_now_iso


RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


@dataclass(frozen=True)
class ScenarioEventDefinition:
    source_module: str
    event_type: str
    risk_weight: float
    confidence: float
    description: str
    camera_id: str | None = None
    count: int = 1


@dataclass(frozen=True)
class VivaScenario:
    scenario_id: str
    name: str
    description: str
    expected_risk_level: RiskLevel
    expected_policy_response: str
    reviewer_action: str
    final_outcome_status: str
    policy_profile: str = "Generic"
    notes: str = ""
    events: list[ScenarioEventDefinition] = field(default_factory=list)


@dataclass(frozen=True)
class VivaScenarioResult:
    run_id: str
    scenario_id: str
    scenario_name: str
    session_id: str
    candidate_id: str
    alert: FusedAlert
    policy_decision_id: str
    expected_risk_level: str
    actual_risk_level: str
    expected_policy_response: str
    actual_policy_response: str
    agent_recommendation: str
    acknowledgement_required: bool
    acknowledgement_recorded: bool
    reviewer_decision_recorded: bool
    final_outcome_status: str
    pass_status: str
    notes: str
    created_at: str
    generated_events: list[EvidenceEvent]

    def to_record(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "alert_id": self.alert.alert_id,
            "policy_decision_id": self.policy_decision_id,
            "expected_risk_level": self.expected_risk_level,
            "actual_risk_level": self.actual_risk_level,
            "expected_policy_response": self.expected_policy_response,
            "actual_policy_response": self.actual_policy_response,
            "agent_recommendation": self.agent_recommendation,
            "acknowledgement_required": self.acknowledgement_required,
            "acknowledgement_recorded": self.acknowledgement_recorded,
            "reviewer_decision_recorded": self.reviewer_decision_recorded,
            "final_outcome_status": self.final_outcome_status,
            "pass_status": self.pass_status,
            "notes": self.notes,
            "created_at": self.created_at,
        }


VIVA_SCENARIOS: dict[str, VivaScenario] = {
    "normal_candidate_behaviour": VivaScenario(
        scenario_id="normal_candidate_behaviour",
        name="Normal candidate behaviour",
        description="Candidate remains visible with healthy camera context and no suspicious multimodal evidence.",
        expected_risk_level="Low",
        expected_policy_response="Generic observation workflow",
        reviewer_action="Observe",
        final_outcome_status="low_risk_observation",
        notes="Low-risk CIE observation is persisted so the full governance path can be demonstrated without creating a misconduct finding.",
        events=[
            ScenarioEventDefinition("primary_camera", "face_present", 0.02, 0.95, "Candidate face is visible in the primary stream.", "primary"),
            ScenarioEventDefinition("primary_camera", "camera_ready", 0.02, 0.95, "Primary camera is ready.", "primary"),
        ],
    ),
    "brief_looking_away": VivaScenario(
        scenario_id="brief_looking_away",
        name="Brief looking away",
        description="A single gaze deviation is logged but should not trigger severe policy action.",
        expected_risk_level="Low",
        expected_policy_response="Generic observation workflow",
        reviewer_action="Observe",
        final_outcome_status="observe_only",
        events=[
            ScenarioEventDefinition("primary_camera", "looking_away", 0.24, 0.72, "Candidate briefly looked away once.", "primary"),
        ],
    ),
    "repeated_gaze_deviation": VivaScenario(
        scenario_id="repeated_gaze_deviation",
        name="Repeated gaze deviation",
        description="Repeated looking-away events demonstrate temporal behaviour memory and reviewer warning flow.",
        expected_risk_level="Medium",
        expected_policy_response="University warning and review workflow",
        reviewer_action="Issue Warning",
        final_outcome_status="warning_issued_for_review",
        policy_profile="Miva",
        events=[
            ScenarioEventDefinition("primary_camera", "looking_away", 0.55, 0.88, "Candidate repeatedly looked away from the screen.", "primary", count=4),
        ],
    ),
    "mobile_phone_detected": VivaScenario(
        scenario_id="mobile_phone_detected",
        name="Mobile phone detected",
        description="Object detection evidence produces a high-risk institutional incident acknowledgement workflow.",
        expected_risk_level="High",
        expected_policy_response="WAEC incident acknowledgement workflow",
        reviewer_action="Escalate",
        final_outcome_status="awaiting_reviewer_assessment",
        policy_profile="WAEC",
        events=[
            ScenarioEventDefinition("object_detection", "mobile_phone_detected", 0.86, 0.92, "A mobile phone-like object was detected near the candidate.", "primary"),
        ],
    ),
    "background_speech": VivaScenario(
        scenario_id="background_speech",
        name="Background speech during exam",
        description="Audio speech evidence alone should be reviewable but not automatically severe.",
        expected_risk_level="Medium",
        expected_policy_response="University warning and review workflow",
        reviewer_action="Continue Monitoring",
        final_outcome_status="flagged_for_later_review",
        policy_profile="Miva",
        events=[
            ScenarioEventDefinition("audio", "background_speech", 0.62, 0.88, "Background speech was detected by the audio pipeline."),
        ],
    ),
    "multiple_persons_detected": VivaScenario(
        scenario_id="multiple_persons_detected",
        name="Multiple persons detected",
        description="Visual evidence indicates another person may be present in the monitoring scene.",
        expected_risk_level="High",
        expected_policy_response="WAEC incident acknowledgement workflow",
        reviewer_action="Escalate",
        final_outcome_status="awaiting_reviewer_assessment",
        policy_profile="WAEC",
        events=[
            ScenarioEventDefinition("secondary_camera", "multiple_persons_detected", 0.88, 0.92, "Multiple persons were detected in the secondary camera context.", "secondary"),
        ],
    ),
    "repeated_face_absent": VivaScenario(
        scenario_id="repeated_face_absent",
        name="Candidate face absent repeatedly",
        description="Repeated face absence should raise risk through temporal memory while preserving human review.",
        expected_risk_level="Medium",
        expected_policy_response="University warning and review workflow",
        reviewer_action="Continue Monitoring",
        final_outcome_status="flagged_for_reviewer_attention",
        policy_profile="Miva",
        events=[
            ScenarioEventDefinition("primary_camera", "face_absent", 0.50, 0.86, "Candidate face was absent from the primary stream.", "primary", count=4),
        ],
    ),
    "identity_mismatch": VivaScenario(
        scenario_id="identity_mismatch",
        name="Candidate substitution / identity mismatch",
        description="Identity assurance reports a face mismatch and candidate substitution signal.",
        expected_risk_level="Critical",
        expected_policy_response="Generic critical-risk senior review workflow",
        reviewer_action="Refer to Senior Reviewer",
        final_outcome_status="senior_reviewer_required",
        policy_profile="Generic",
        events=[
            ScenarioEventDefinition("identity_assurance", "face_mismatch", 0.82, 0.93, "Periodic identity verification confidence dropped below the accepted threshold."),
            ScenarioEventDefinition("identity_assurance", "identity_substitution", 0.80, 0.90, "Identity assurance generated a candidate substitution signal."),
        ],
    ),
    "camera_disconnected_suspicious": VivaScenario(
        scenario_id="camera_disconnected_suspicious",
        name="Camera disconnected during suspicious activity",
        description="Camera health evidence combines with visual and audio evidence to demonstrate multimodal escalation.",
        expected_risk_level="High",
        expected_policy_response="WAEC incident acknowledgement workflow",
        reviewer_action="Escalate",
        final_outcome_status="awaiting_reviewer_assessment",
        policy_profile="WAEC",
        events=[
            ScenarioEventDefinition("primary_camera", "camera_disconnected", 0.66, 0.90, "Primary camera disconnected during monitoring.", "primary"),
            ScenarioEventDefinition("audio", "background_speech", 0.58, 0.86, "Background speech occurred during camera disruption."),
            ScenarioEventDefinition("primary_camera", "looking_away", 0.52, 0.84, "Candidate gaze deviated during camera disruption.", "primary"),
        ],
    ),
    "critical_combined": VivaScenario(
        scenario_id="critical_combined",
        name="Critical combined scenario",
        description="Phone, second person, background speech, face absence, and identity confidence drop occur in one window.",
        expected_risk_level="Critical",
        expected_policy_response="Generic critical-risk senior review workflow",
        reviewer_action="Refer to Senior Reviewer",
        final_outcome_status="senior_reviewer_required",
        policy_profile="Generic",
        events=[
            ScenarioEventDefinition("object_detection", "mobile_phone_detected", 0.86, 0.92, "Mobile phone-like object detected.", "primary"),
            ScenarioEventDefinition("secondary_camera", "multiple_persons_detected", 0.88, 0.91, "Second person detected in the room context.", "secondary"),
            ScenarioEventDefinition("audio", "background_speech", 0.64, 0.88, "Background speech detected."),
            ScenarioEventDefinition("primary_camera", "face_absent", 0.62, 0.88, "Candidate face absent from primary stream.", "primary"),
            ScenarioEventDefinition("identity_assurance", "face_mismatch", 0.78, 0.90, "Identity confidence dropped during the incident window."),
        ],
    ),
}


def list_viva_scenarios() -> list[VivaScenario]:
    return list(VIVA_SCENARIOS.values())


def get_viva_scenario(scenario_id: str) -> VivaScenario:
    try:
        return VIVA_SCENARIOS[scenario_id]
    except KeyError as exc:
        raise ValueError(f"Unknown viva scenario: {scenario_id}") from exc


def execute_viva_scenario(
    scenario_id: str,
    session_id: str,
    candidate_id: str,
    *,
    policy_profile: str | None = None,
    window_seconds: int = 300,
    cie: ContextualIntelligenceEngine | None = None,
) -> VivaScenarioResult:
    scenario = get_viva_scenario(scenario_id)
    generated_events = build_scenario_events(scenario, session_id, candidate_id)
    for event in generated_events:
        save_event(event)

    engine = cie or ContextualIntelligenceEngine(time_window_seconds=window_seconds)
    alert = engine.fuse(generated_events, rolling_events=generated_events)
    if alert is None:
        alert = low_observation_alert(scenario, generated_events, session_id, candidate_id)
    save_alert(alert)

    orchestrated = AgenticOrchestrator().plan_actions(alert)
    decision = evaluate_institutional_policy(
        alert.to_dict(),
        policy_profile or scenario.policy_profile,
        agent_actions=orchestrated.actions,
        agent_priority=orchestrated.priority,
    )
    decision_id = save_policy_decision(decision)

    result = VivaScenarioResult(
        run_id=f"VIVA-{uuid4().hex[:8].upper()}",
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        session_id=session_id,
        candidate_id=candidate_id,
        alert=alert,
        policy_decision_id=decision_id,
        expected_risk_level=scenario.expected_risk_level,
        actual_risk_level=alert.risk_level,
        expected_policy_response=scenario.expected_policy_response,
        actual_policy_response=decision.workflow_label,
        agent_recommendation=orchestrated.priority,
        acknowledgement_required=decision.require_acknowledgement,
        acknowledgement_recorded=False,
        reviewer_decision_recorded=False,
        final_outcome_status="awaiting_candidate_acknowledgement"
        if decision.require_acknowledgement
        else "awaiting_human_review",
        pass_status=validation_status(scenario.expected_risk_level, alert.risk_level, scenario.expected_policy_response, decision.workflow_label),
        notes=scenario.notes or "Controlled viva scenario. Output is a validation trace, not a cheating label.",
        created_at=utc_now_iso(),
        generated_events=generated_events,
    )
    save_viva_scenario_run(result)
    return result


def build_scenario_events(scenario: VivaScenario, session_id: str, candidate_id: str) -> list[EvidenceEvent]:
    base_time = datetime.now(timezone.utc).replace(microsecond=0)
    events: list[EvidenceEvent] = []
    offset = 0
    for definition in scenario.events:
        for index in range(definition.count):
            event_time = base_time + timedelta(seconds=offset)
            suffix = f" ({index + 1}/{definition.count})" if definition.count > 1 else ""
            events.append(
                EvidenceEvent(
                    session_id=session_id,
                    candidate_id=candidate_id,
                    source_module=definition.source_module,
                    event_type=definition.event_type,
                    risk_weight=definition.risk_weight,
                    confidence=definition.confidence,
                    description=f"{definition.description}{suffix}",
                    camera_id=definition.camera_id,
                    timestamp=event_time.isoformat(),
                )
            )
            offset += 2
    return events


def low_observation_alert(
    scenario: VivaScenario,
    events: list[EvidenceEvent],
    session_id: str,
    candidate_id: str,
) -> FusedAlert:
    start_time = min((event.timestamp for event in events), default=utc_now_iso())
    end_time = max((event.timestamp for event in events), default=start_time)
    confidence = round(sum(event.confidence for event in events) / len(events), 3) if events else 0.0
    return FusedAlert(
        session_id=session_id,
        candidate_id=candidate_id,
        start_time=start_time,
        end_time=end_time,
        risk_score=0,
        risk_level="Low",
        alert_type="viva_low_risk_observation",
        contributing_events=[event.event_id for event in events],
        explanation=(
            f"CIE validation observation for '{scenario.name}': no severe contextual pattern was found. "
            "This low-risk record exists to demonstrate the governance pipeline while preserving human review."
        ),
        recommended_action="Observe and continue monitoring.",
        confidence=confidence,
        current_risk_score=0,
        rolling_risk_score=0,
        risk_trend="stable",
        contributing_modules=sorted({event.source_module for event in events}),
        reasoning_trace=[
            "CIE received scenario evidence and found no severe contextual pattern.",
            "Low-risk observation was persisted for end-to-end viva validation.",
            "Human reviewer remains responsible for final decision.",
        ],
    )


def validation_status(
    expected_risk: str,
    actual_risk: str,
    expected_policy_response: str,
    actual_policy_response: str,
) -> str:
    expected_rank = RISK_ORDER.get(expected_risk, 1)
    actual_rank = RISK_ORDER.get(actual_risk, 1)
    risk_ok = actual_rank >= expected_rank if expected_rank >= RISK_ORDER["Medium"] else actual_rank == expected_rank
    policy_ok = expected_policy_response == actual_policy_response
    return "Pass" if risk_ok and policy_ok else "Needs Review"


def save_viva_scenario_run(result: VivaScenarioResult) -> str:
    record = result.to_record()
    record["acknowledgement_required"] = int(bool(record["acknowledgement_required"]))
    record["acknowledgement_recorded"] = int(bool(record["acknowledgement_recorded"]))
    record["reviewer_decision_recorded"] = int(bool(record["reviewer_decision_recorded"]))
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO viva_scenario_runs(
                run_id, scenario_id, scenario_name, session_id, candidate_id, alert_id, policy_decision_id,
                expected_risk_level, actual_risk_level, expected_policy_response, actual_policy_response,
                agent_recommendation, acknowledgement_required, acknowledgement_recorded,
                reviewer_decision_recorded, final_outcome_status, pass_status, notes, created_at
            )
            VALUES (
                :run_id, :scenario_id, :scenario_name, :session_id, :candidate_id, :alert_id, :policy_decision_id,
                :expected_risk_level, :actual_risk_level, :expected_policy_response, :actual_policy_response,
                :agent_recommendation, :acknowledgement_required, :acknowledgement_recorded,
                :reviewer_decision_recorded, :final_outcome_status, :pass_status, :notes, :created_at
            )
            """,
            record,
        )
    return result.run_id


def list_viva_scenario_runs(session_id: str | None = None) -> list[dict[str, object]]:
    query = "SELECT * FROM viva_scenario_runs"
    params: tuple[object, ...] = ()
    if session_id:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_decode_run(dict(row)) for row in rows]


def get_viva_scenario_run(run_id: str) -> dict[str, object] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM viva_scenario_runs WHERE run_id = ?", (run_id,)).fetchone()
    return _decode_run(dict(row)) if row else None


def record_viva_candidate_acknowledgement(
    run_id: str,
    candidate_explanation: str,
    acknowledged: bool = True,
) -> str:
    run = get_viva_scenario_run(run_id)
    if not run or not run.get("policy_decision_id"):
        raise ValueError(f"Viva scenario run has no policy decision: {run_id}")
    acknowledgement_id = record_candidate_acknowledgement(
        str(run["policy_decision_id"]),
        str(run["candidate_id"]),
        candidate_explanation,
        acknowledged,
    )
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE viva_scenario_runs
            SET acknowledgement_recorded = ?, final_outcome_status = ?
            WHERE run_id = ?
            """,
            (int(bool(acknowledged)), "awaiting_human_review", run_id),
        )
    return acknowledgement_id


def record_viva_reviewer_decision(
    run_id: str,
    reviewer_id: str,
    reviewer_action: str,
    rationale: str,
) -> str:
    run = get_viva_scenario_run(run_id)
    if not run or not run.get("policy_decision_id"):
        raise ValueError(f"Viva scenario run has no policy decision: {run_id}")
    review_id = record_reviewer_incident_decision(
        str(run["policy_decision_id"]),
        reviewer_id,
        reviewer_action,
        rationale,
    )
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE viva_scenario_runs
            SET reviewer_decision_recorded = 1, final_outcome_status = ?
            WHERE run_id = ?
            """,
            (reviewer_action.lower().replace(" ", "_"), run_id),
        )
    return review_id


def _decode_run(row: dict[str, object]) -> dict[str, object]:
    for field in ("acknowledgement_required", "acknowledgement_recorded", "reviewer_decision_recorded"):
        row[field] = bool(row.get(field))
    return row
