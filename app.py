from __future__ import annotations

import pandas as pd
import streamlit as st
import numpy as np

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
from src.storage.candidate_repository import list_candidates, register_candidate, save_candidate_custom_fields
from src.storage.database import initialize_database
from src.storage.event_repository import list_alerts, list_events, save_alert, save_event
from src.utils.file_utils import candidate_enrolment_dir, write_bytes
from src.vision.face_quality import assess_face_capture, extract_face_embedding
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
        div[data-baseweb="select"] *,
        div[data-baseweb="select"] svg,
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
        div[data-baseweb="select"] > div:hover svg {
            color: #0a7f78 !important;
            fill: #0a7f78 !important;
            transform: scale(1.18);
            transition: transform .12s ease, fill .12s ease;
        }
        .stTabs [role="tab"]:hover {
            color: #0a7f78;
        }
        .wizard-step {
            display: inline-flex;
            align-items: center;
            gap: .55rem;
            margin: .2rem .55rem 1rem 0;
            padding: .55rem .85rem;
            border-radius: 999px;
            background: #e9f2f7;
            border: 1px solid #cfe0ea;
            font-weight: 600;
            color: #355064;
        }
        .wizard-step.active {
            background: #0a7f78;
            border-color: #0a7f78;
            color: #ffffff;
        }
        .capture-guide {
            border: 1px solid #cfe0ea;
            background: linear-gradient(180deg, #ffffff 0%, #f5fbfd 100%);
            border-radius: 8px;
            padding: 1.2rem;
            margin: 1rem 0;
        }
        .face-orb {
            width: 190px;
            height: 190px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: .6rem auto;
            background: radial-gradient(circle, #dff7f4 0%, #c7e9f2 62%, #0a7f78 64%, #063b5c 100%);
            color: #063b5c;
            font-size: 3rem;
            font-weight: 800;
            box-shadow: inset 0 0 0 10px rgba(255,255,255,.65), 0 12px 30px rgba(6,59,92,.18);
        }
        .stCameraInput video,
        .stCameraInput img {
            cursor: crosshair !important;
        }
        .camera-circular .stCameraInput video,
        .camera-circular .stCameraInput img,
        div[data-testid="stCameraInput"] video,
        div[data-testid="stCameraInput"] img {
            max-width: 280px !important;
            border-radius: 999px !important;
            aspect-ratio: 1 / 1 !important;
            object-fit: cover !important;
            border: 4px solid #0a7f78 !important;
            box-shadow: 0 10px 30px rgba(6,59,92,.18);
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

    if "enrolment_step" not in st.session_state:
        st.session_state.enrolment_step = "register"
    if "custom_fields" not in st.session_state:
        st.session_state.custom_fields = [{"label": "Department", "value": ""}]

    render_enrolment_steps()
    if st.session_state.enrolment_step == "register":
        registration_wizard(role)
    else:
        guided_face_enrolment()


def render_enrolment_steps() -> None:
    register_state = "active" if st.session_state.enrolment_step == "register" else ""
    face_state = "active" if st.session_state.enrolment_step == "face" else ""
    st.markdown(
        f"""
        <div>
            <span class="wizard-step {register_state}">1. Registration + Consent</span>
            <span class="wizard-step {face_state}">2. Guided Face Capture</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def registration_wizard(role: str) -> None:
    st.markdown("#### Register candidate and capture consent")
    with st.expander("Admin field customization", expanded=False):
        st.caption("Prototype custom fields apply to this registration form submission.")
        field_count = st.number_input("Number of additional fields", min_value=0, max_value=8, value=len(st.session_state.custom_fields))
        current_fields = st.session_state.custom_fields[: int(field_count)]
        while len(current_fields) < int(field_count):
            current_fields.append({"label": f"Custom field {len(current_fields) + 1}", "value": ""})
        st.session_state.custom_fields = current_fields
        for index, field in enumerate(st.session_state.custom_fields):
            field["label"] = st.text_input(f"Field {index + 1} label", field["label"], key=f"custom_label_{index}")

    with st.form("candidate_form"):
        full_name = st.text_input("Full name", "Demo Candidate")
        exam_code = st.text_input("Exam code", "MIVA-CAPSTONE-001")
        institution = st.text_input("Institution", "Miva Open University")
        email = st.text_input("Email", "candidate@example.com")
        custom_values: dict[str, str] = {}
        for index, field in enumerate(st.session_state.custom_fields):
            label = field["label"].strip()
            if label:
                custom_values[label] = st.text_input(label, field.get("value", ""), key=f"custom_value_{index}")
        consent = st.checkbox(CONSENT_NOTICE)
        submitted = st.form_submit_button("Register candidate and continue")

    if submitted:
        if not consent:
            st.error("Consent is required before enrolment.")
            return
        candidate_id = register_candidate(full_name, exam_code, institution, email)
        save_candidate_custom_fields(candidate_id, custom_values)
        capture_consent(candidate_id)
        st.session_state.enrolment_candidate_id = candidate_id
        st.session_state.enrolment_step = "face"
        st.success(f"Candidate registered: {candidate_id}. Proceeding to guided face capture.")
        st.rerun()


def guided_face_enrolment() -> None:
    candidates = list_candidates()
    st.markdown("#### Guided facial enrolment")
    st.caption("AI validation checks that a single face is visible before each sample is saved.")
    if not candidates:
        st.info("No registered candidates yet.")
        if st.button("Back to registration"):
            st.session_state.enrolment_step = "register"
            st.rerun()
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

    remaining = [direction for direction in FACE_DIRECTIONS if direction not in done]
    if not remaining:
        st.success("Guided facial enrolment is complete for this candidate.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Register another candidate"):
                st.session_state.enrolment_step = "register"
                st.session_state.pop("enrolment_candidate_id", None)
                st.rerun()
        with col_b:
            st.caption("Next workflow: authenticate candidate and start session monitoring.")
        return

    direction = remaining[0]
    direction_label = direction.replace("_", " ").title()
    st.markdown(f"### Capture {len(done) + 1} of {len(FACE_DIRECTIONS)}: {direction_label}")
    render_capture_indicator(direction)
    frame_shape = st.radio("Camera frame", ["Circular guide", "Original rectangle"], horizontal=True, index=0)
    if frame_shape == "Original rectangle":
        st.markdown(
            """
            <style>
            div[data-testid="stCameraInput"] video,
            div[data-testid="stCameraInput"] img {
                max-width: 100% !important;
                border-radius: 8px !important;
                aspect-ratio: auto !important;
                object-fit: contain !important;
                border: 2px solid #cfe0ea !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    if frame_shape == "Circular guide":
        st.markdown('<div class="camera-circular">', unsafe_allow_html=True)
    image = st.camera_input(f"Activate camera and capture {direction_label} face sample", key=f"camera_{candidate_id}_{direction}")
    if frame_shape == "Circular guide":
        st.markdown("</div>", unsafe_allow_html=True)

    if image and st.button("Save captured face sample"):
        assessment = assess_face_capture(image.getvalue())
        if not assessment["accepted"]:
            st.error(str(assessment["message"]))
            return
        file_path = candidate_enrolment_dir(candidate_id) / f"{direction}.jpg"
        embedding_path = candidate_enrolment_dir(candidate_id) / f"{direction}_embedding.npy"
        write_bytes(file_path, image.getvalue())
        embedding = extract_face_embedding(image.getvalue())
        np.save(embedding_path, embedding)
        record_face_sample(
            candidate_id,
            direction,
            str(file_path),
            quality_score=float(assessment["quality_score"]),
            embedding_path=str(embedding_path),
        )
        if is_face_enrolment_complete(candidate_id):
            from src.storage.candidate_repository import update_enrolment_status

            update_enrolment_status(candidate_id, "face_enrolled")
            st.success("Guided facial enrolment completed for all required directions.")
        else:
            st.success(f"Saved {direction_label} face sample. The next capture will load automatically.")
        st.rerun()

    if st.button("Back to registration"):
        st.session_state.enrolment_step = "register"
        st.rerun()


def render_capture_indicator(direction: str) -> None:
    arrows = {
        "front": "CENTER",
        "left": "<",
        "right": ">",
        "slight_up": "^",
        "slight_down": "v",
        "centre": "CENTER",
    }
    notes = {
        "front": "Look directly into the camera with the full face inside the circle.",
        "left": "Turn your face slightly to your left while keeping both eyes visible.",
        "right": "Turn your face slightly to your right while keeping both eyes visible.",
        "slight_up": "Tilt your face slightly upward while remaining visible.",
        "slight_down": "Tilt your face slightly downward while remaining visible.",
        "centre": "Return to a neutral centre-facing posture for confirmation.",
    }
    st.markdown(
        f"""
        <div class="capture-guide">
            <div class="face-orb">{arrows[direction]}</div>
            <strong>{notes[direction]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
