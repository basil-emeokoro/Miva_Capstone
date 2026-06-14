from __future__ import annotations

import pandas as pd
import streamlit as st

from src.audio.audio_event_detector import create_background_speech_event
from src.enrolment.consent_manager import CONSENT_NOTICE, capture_consent
from src.enrolment.face_enrolment import (
    FACE_DIRECTIONS,
    captured_directions,
    is_face_enrolment_complete,
    record_face_sample,
)
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
from src.utils.file_utils import candidate_enrolment_dir, write_bytes
from src.vision.visual_event_detector import VISUAL_EVENT_PRESETS, create_demo_visual_event


st.set_page_config(page_title="Explainable Proctoring System", layout="wide")
initialize_database()

if "fusion_engine" not in st.session_state:
    st.session_state.fusion_engine = FusionEngine()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f3f7fb 0%, #eef4f8 42%, #ffffff 100%);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #e8eef5 0%, #f7fafc 100%);
            border-right: 1px solid #d6e0ea;
        }
        .hero {
            background: linear-gradient(135deg, #063b5c 0%, #075a75 52%, #0a7f78 100%);
            color: white;
            padding: 2.1rem 2.3rem;
            border-radius: 0 0 22px 22px;
            margin-bottom: 1.4rem;
            box-shadow: 0 18px 42px rgba(6, 59, 92, 0.18);
        }
        .hero h1 {
            margin: 0 0 .45rem 0;
            font-size: 2.2rem;
            letter-spacing: 0;
        }
        .hero p {
            margin: 0;
            color: #d7edf5;
            font-size: 1rem;
        }
        .notice {
            background: #fff8dc;
            color: #805700;
            border-left: 5px solid #f5b400;
            padding: 1rem 1.1rem;
            border-radius: 8px;
            margin-bottom: 1.2rem;
        }
        .status-card {
            background: #ffffff;
            border: 1px solid #d7e2eb;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stButton"] button,
        div[data-baseweb="select"],
        label[data-testid="stWidgetLabel"],
        input,
        textarea,
        .stTabs [role="tab"] {
            cursor: pointer !important;
        }
        div[data-testid="stButton"] button {
            border-radius: 8px;
            border: 1px solid #0b6b7a;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
        }
        div[data-testid="stButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(7, 90, 117, 0.18);
            border-color: #0a7f78;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: #0a7f78 !important;
            box-shadow: 0 0 0 1px rgba(10, 127, 120, .15);
        }
        .stTabs [role="tab"]:hover {
            color: #0a7f78;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Secure Remote-Proctored Assessment Console</h1>
            <p>Explainable multi-modal monitoring, identity assurance, event fusion, and human-supervised review.</p>
        </div>
        <div class="notice">
            Research prototype for academic demonstration. AI-generated alerts support human review and must not be treated as automatic misconduct decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    st.markdown("#### 1. Register candidate and capture consent")
    with st.form("candidate_form"):
        full_name = st.text_input("Full name", "Demo Candidate")
        exam_code = st.text_input("Exam code", "MIVA-CAPSTONE-001")
        institution = st.text_input("Institution", "Miva Open University")
        email = st.text_input("Email", "candidate@example.com")
        consent = st.checkbox(CONSENT_NOTICE)
        submitted = st.form_submit_button("Register candidate")

    if submitted:
        if not consent:
            st.error("Consent is required before enrolment.")
            return
        candidate_id = register_candidate(full_name, exam_code, institution, email)
        capture_consent(candidate_id)
        st.session_state.enrolment_candidate_id = candidate_id
        st.success(f"Candidate registered: {candidate_id}. Continue to guided face capture below.")

    guided_face_enrolment()


def guided_face_enrolment() -> None:
    candidates = list_candidates()
    st.markdown("#### 2. Guided facial enrolment")
    st.caption("Use the browser camera capture for each required direction. This creates real image evidence records for the prototype.")
    if not candidates:
        st.info("No registered candidates yet.")
        return

    candidate_options = {f"{c['full_name']} ({c['candidate_id']})": c for c in candidates}
    default_candidate_id = st.session_state.get("enrolment_candidate_id")
    labels = list(candidate_options)
    default_index = 0
    if default_candidate_id:
        for index, label in enumerate(labels):
            if str(default_candidate_id) in label:
                default_index = index
                break
    selected = st.selectbox("Candidate for face capture", labels, index=default_index)
    candidate = candidate_options[selected]
    candidate_id = str(candidate["candidate_id"])
    done = captured_directions(candidate_id)
    progress = len(done) / len(FACE_DIRECTIONS)
    st.progress(progress, text=f"{len(done)} of {len(FACE_DIRECTIONS)} directions captured")

    cols = st.columns(len(FACE_DIRECTIONS))
    for index, direction in enumerate(FACE_DIRECTIONS):
        with cols[index]:
            status = "Captured" if direction in done else "Pending"
            st.metric(direction.replace("_", " ").title(), status)

    remaining = [direction for direction in FACE_DIRECTIONS if direction not in done]
    direction = st.selectbox("Capture direction", remaining or FACE_DIRECTIONS)
    st.info(f"Position face for: {direction.replace('_', ' ').title()}")
    image = st.camera_input("Activate camera and capture face sample", key=f"camera_{candidate_id}_{direction}")

    if image and st.button("Save captured face sample"):
        file_path = candidate_enrolment_dir(candidate_id) / f"{direction}.jpg"
        write_bytes(file_path, image.getvalue())
        record_face_sample(candidate_id, direction, str(file_path), quality_score=0.85)
        if is_face_enrolment_complete(candidate_id):
            from src.storage.candidate_repository import update_enrolment_status

            update_enrolment_status(candidate_id, "face_enrolled")
            st.success("Guided facial enrolment completed for all required directions.")
        else:
            st.success(f"Saved {direction.replace('_', ' ')} face sample.")
        st.rerun()


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
    apply_theme()
    role = selected_role()
    render_hero()

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
