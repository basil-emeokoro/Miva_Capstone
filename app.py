from __future__ import annotations

import pandas as pd
import streamlit as st

from src.audio.audio_event_detector import create_background_speech_event
from src.enrolment.consent_manager import CONSENT_NOTICE, capture_consent
from src.enrolment.face_enrolment import complete_prototype_face_enrolment
from src.fusion.fusion_engine import FusionEngine
from src.reporting.session_report import export_session_report_json
from src.review import record_review
from src.security.access_control import Role, has_permission
from src.session.exam_controller import grade_answers, load_sample_questions
from src.session.monitoring_mode_controller import MonitoringModeController
from src.session.session_manager import list_sessions, start_session
from src.storage.candidate_repository import list_candidates, register_candidate
from src.storage.database import initialize_database
from src.storage.event_repository import list_alerts, list_events, save_alert, save_event
from src.vision.visual_event_detector import VISUAL_EVENT_PRESETS, create_demo_visual_event


st.set_page_config(page_title="Explainable Proctoring System", layout="wide")
initialize_database()

if "fusion_engine" not in st.session_state:
    st.session_state.fusion_engine = FusionEngine()


def selected_role() -> str:
    with st.sidebar:
        st.title("Proctoring Control")
        role = st.selectbox("Role", [role.value for role in Role])
        st.caption("Prototype RBAC. Not enterprise authentication.")
    return role


def candidate_management(role: str) -> None:
    st.subheader("Candidate Enrolment")
    if not has_permission(role, "register_candidate"):
        st.info("Your role can view monitoring data but cannot register candidates.")
        return

    with st.form("candidate_form"):
        full_name = st.text_input("Full name", "Demo Candidate")
        exam_code = st.text_input("Exam code", "MIVA-CAPSTONE-001")
        institution = st.text_input("Institution", "Miva Open University")
        email = st.text_input("Email", "candidate@example.com")
        consent = st.checkbox(CONSENT_NOTICE)
        submitted = st.form_submit_button("Register and enrol prototype candidate")

    if submitted:
        if not consent:
            st.error("Consent is required before enrolment.")
            return
        candidate_id = register_candidate(full_name, exam_code, institution, email)
        capture_consent(candidate_id)
        complete_prototype_face_enrolment(candidate_id)
        st.success(f"Candidate registered and prototype face enrolment completed: {candidate_id}")


def session_control(role: str) -> str | None:
    candidates = list_candidates()
    st.subheader("Session Control")
    if not candidates:
        st.warning("Register a candidate before starting a session.")
        return None

    candidate_options = {f"{c['full_name']} ({c['candidate_id']})": c for c in candidates}
    selected = st.selectbox("Candidate", list(candidate_options))
    candidate = candidate_options[selected]
    mode = st.selectbox("Monitoring mode", ["B", "A", "C"])
    plan = MonitoringModeController().configure(mode)
    st.caption(plan.confidence_note)

    if has_permission(role, "start_session") and st.button("Start prototype session"):
        session_id = start_session(str(candidate["candidate_id"]), str(candidate["exam_code"]), mode)
        st.session_state.active_session_id = session_id
        st.session_state.active_candidate_id = candidate["candidate_id"]
        st.success(f"Started session {session_id}")

    sessions = list_sessions()
    if sessions:
        session_labels = [f"{s['session_id']} - {s['candidate_id']} - {s['session_status']}" for s in sessions]
        chosen = st.selectbox("Active/reporting session", session_labels)
        session_id = chosen.split(" - ")[0]
        st.session_state.active_session_id = session_id
        st.session_state.active_candidate_id = next(s["candidate_id"] for s in sessions if s["session_id"] == session_id)
        return session_id
    return None


def mock_test_player() -> None:
    st.subheader("Prototype Test Player")
    questions = load_sample_questions()
    answers: dict[str, str] = {}
    with st.form("mock_test"):
        for question in questions:
            answers[question["question_id"]] = st.radio(
                question["prompt"],
                question["options"],
                key=f"question_{question['question_id']}",
            )
        submitted = st.form_submit_button("Submit mock assessment")
    if submitted:
        result = grade_answers(answers, questions)
        st.success(f"Score: {result['correct']}/{result['total']} ({result['percentage']}%)")


def monitoring_panel(role: str, session_id: str | None) -> None:
    st.subheader("Live Monitoring and Demo Events")
    if not session_id:
        st.info("Start or select a session to generate monitoring events.")
        return
    candidate_id = str(st.session_state.get("active_candidate_id"))

    if has_permission(role, "generate_demo_events"):
        col1, col2 = st.columns(2)
        with col1:
            preset = st.selectbox("Visual/identity event", list(VISUAL_EVENT_PRESETS))
            if st.button("Generate selected event"):
                event = create_demo_visual_event(session_id, candidate_id, preset)
                save_event(event)
                alert = st.session_state.fusion_engine.ingest(event)
                if alert:
                    save_alert(alert)
                st.success("Structured event generated and fused.")
        with col2:
            if st.button("Generate background speech event"):
                event = create_background_speech_event(session_id, candidate_id)
                save_event(event)
                alert = st.session_state.fusion_engine.ingest(event)
                if alert:
                    save_alert(alert)
                st.success("Audio event generated and fused.")
    else:
        st.info("Your role cannot generate demo monitoring events.")

    events = list_events(session_id)
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True)


def alert_review_panel(role: str, session_id: str | None) -> None:
    st.subheader("Fused Alerts and Human Review")
    if not session_id:
        st.info("Select a session to review alerts.")
        return

    alerts = list_alerts(session_id)
    if not alerts:
        st.info("No fused alerts yet.")
        return

    st.dataframe(pd.DataFrame(alerts), use_container_width=True)
    if has_permission(role, "review_alerts"):
        alert_ids = [str(alert["alert_id"]) for alert in alerts]
        alert_id = st.selectbox("Alert to review", alert_ids)
        decision = st.selectbox("Decision", ["accepted", "rejected", "escalated"])
        comment = st.text_area("Reviewer comment")
        if st.button("Submit reviewer decision"):
            record_review(alert_id, role, decision, comment)
            st.success("Reviewer decision recorded.")
    else:
        st.info("Only Admin or Reviewer roles can submit final alert decisions.")


def reports_panel(role: str, session_id: str | None) -> None:
    st.subheader("Reports")
    if not session_id:
        st.info("Select a session to export a report.")
        return
    if has_permission(role, "export_reports") and st.button("Export JSON session report"):
        path = export_session_report_json(session_id)
        st.success(f"Report exported to {path}")
    else:
        st.caption("Report export is available to Admin and Reviewer roles.")


def main() -> None:
    role = selected_role()
    st.title("Explainable Multi-Modal Proctoring Prototype")
    st.caption("Local-first capstone prototype. AI flags and explains; human reviewers decide.")

    tabs = st.tabs(["Enrolment", "Session", "Test Player", "Monitoring", "Review", "Reports"])
    with tabs[0]:
        candidate_management(role)
    with tabs[1]:
        session_id = session_control(role)
    with tabs[2]:
        mock_test_player()
    session_id = st.session_state.get("active_session_id")
    with tabs[3]:
        monitoring_panel(role, session_id)
    with tabs[4]:
        alert_review_panel(role, session_id)
    with tabs[5]:
        reports_panel(role, session_id)


if __name__ == "__main__":
    main()
