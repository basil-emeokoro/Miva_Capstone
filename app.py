from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
import numpy as np

from src.audio.audio_event_detector import create_background_speech_event
from src.camera.camera_stream import (
    camera_status_event,
    discover_camera_devices,
    evaluate_camera_streams,
    manual_camera_health_event,
    required_camera_roles,
)
from src.enrolment.consent_manager import CONSENT_NOTICE, capture_consent
from src.enrolment.face_enrolment import (
    FACE_DIRECTIONS,
    captured_directions,
    is_face_enrolment_complete,
    list_face_samples,
    record_face_sample,
)
from src.fusion.fusion_engine import FusionEngine
from src.reporting.session_report import export_session_report_json
from src.review import record_review
from src.security.access_control import Role, has_permission
from src.security.audit_logger import list_recent_audit_logs, log_audit
from src.session.environment_checker import CHECK_LABELS, MODE_REQUIREMENTS, device_check_allows_session_start, evaluate_device_checks
from src.session.exam_controller import grade_answers, load_sample_questions
from src.session.monitoring_mode_controller import MonitoringModeController
from src.session.session_manager import end_session, list_sessions, start_session
from src.storage.candidate_repository import (
    CandidateDuplicateError,
    default_email_for_institution,
    generate_candidate_id,
    get_candidate,
    list_candidate_custom_fields,
    list_candidates,
    register_candidate,
    save_candidate_custom_fields,
    update_candidate_biodata,
)
from src.storage.database import fetch_all, initialize_database
from src.storage.device_check_repository import latest_device_check, save_device_check
from src.storage.event_repository import list_alerts, list_events, save_alert, save_event
from src.utils.file_utils import candidate_enrolment_dir, write_bytes
from src.utils.geodata import COUNTRIES, NIGERIA_LGAS, NIGERIA_STATES
from src.vision.visual_event_detector import VISUAL_EVENT_PRESETS, create_demo_visual_event


APP_ROOT = Path(__file__).resolve().parent
SERPS_LOGO_PATH = APP_ROOT / "assets" / "SERPS_Logo.png"
PAGES = ["Home", "Enrolment", "Candidate Profiles", "Session", "Test Player", "Monitoring", "Review", "Reports"]
PAGE_SLUGS = {
    "Home": "home",
    "Enrolment": "enrolment",
    "Candidate Profiles": "candidate-profiles",
    "Session": "session",
    "Test Player": "test-player",
    "Monitoring": "monitoring",
    "Review": "review",
    "Reports": "reports",
}


st.set_page_config(
    page_title="SERPS - Explainable Proctoring System",
    page_icon=str(SERPS_LOGO_PATH) if SERPS_LOGO_PATH.exists() else None,
    layout="wide",
)
initialize_database()

if "fusion_engine" not in st.session_state:
    st.session_state.fusion_engine = FusionEngine()


@st.cache_data(show_spinner=False)
def logo_data_uri() -> str:
    if not SERPS_LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(SERPS_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@st.cache_data(ttl=5, show_spinner=False)
def cached_candidates() -> list[dict[str, object]]:
    return list_candidates()


@st.cache_data(ttl=5, show_spinner=False)
def cached_sessions() -> list[dict[str, object]]:
    return list_sessions()


@st.cache_data(ttl=5, show_spinner=False)
def cached_events(session_id: str | None = None) -> list[dict[str, object]]:
    return list_events(session_id)


@st.cache_data(ttl=5, show_spinner=False)
def cached_alerts(session_id: str | None = None) -> list[dict[str, object]]:
    return list_alerts(session_id)


@st.cache_data(ttl=5, show_spinner=False)
def cached_audit_logs(limit: int = 30) -> list[dict[str, object]]:
    return list_recent_audit_logs(limit)


def clear_app_caches() -> None:
    cached_candidates.clear()
    cached_sessions.clear()
    cached_events.clear()
    cached_alerts.clear()
    cached_audit_logs.clear()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f3f7fb 0%, #eef4f8 42%, #ffffff 100%);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #e0edf2 0%, #eef6f7 48%, #f8fbfc 100%);
            border-right: 1px solid #c8dce4;
        }
        .block-container {
            padding-top: 2.2rem;
        }
        .hero {
            background: linear-gradient(135deg, #063b5c 0%, #075a75 52%, #0a7f78 100%);
            color: white;
            padding: 2.1rem 2.3rem;
            border-radius: 0 0 22px 22px;
            margin-bottom: 1.4rem;
            box-shadow: 0 18px 42px rgba(6, 59, 92, 0.18);
        }
        .hero-identity {
            display: flex;
            align-items: center;
            gap: 1.2rem;
        }
        .hero-logo {
            width: 76px;
            height: 76px;
            border-radius: 16px;
            object-fit: contain;
            background: rgba(255,255,255,.94);
            padding: .45rem;
            box-shadow: 0 10px 24px rgba(2, 18, 33, .18);
            flex: 0 0 auto;
        }
        .hero-copy {
            min-width: 0;
        }
        .hero .brand {
            display: block;
            margin: 0 0 .45rem 0;
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: .16rem;
            color: #b9f4ef;
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
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: .75rem;
            margin: .2rem 0 1.2rem 0;
        }
        .sidebar-brand img {
            width: 46px;
            height: 46px;
            border-radius: 10px;
            object-fit: contain;
            background: #ffffff;
            padding: .25rem;
            border: 1px solid #d7e2eb;
        }
        .sidebar-brand strong {
            display: block;
            color: #0f172a;
            font-size: 1.05rem;
            line-height: 1.1;
        }
        .sidebar-brand span {
            display: block;
            color: #64748b;
            font-size: .76rem;
        }
        @media (max-width: 720px) {
            .hero-identity {
                align-items: flex-start;
            }
            .hero-logo {
                width: 58px;
                height: 58px;
                border-radius: 12px;
            }
            .hero h1 {
                font-size: 1.65rem;
            }
            .module-grid {
                grid-template-columns: 1fr;
            }
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
        .module-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(150px, 1fr));
            gap: .8rem;
            margin: 1rem 0;
        }
        .module-card {
            background: #ffffff;
            border: 1px solid #d7e2eb;
            border-radius: 8px;
            padding: 1rem;
            min-height: 112px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        }
        .module-card strong {
            display: block;
            margin-bottom: .35rem;
            color: #0f172a;
        }
        .module-card span {
            color: #64748b;
            font-size: .88rem;
        }
        .footer {
            margin-top: 2.4rem;
            padding: 1.15rem 0 .8rem 0;
            border-top: 1px solid #b8d5df;
            color: #31566a;
            font-size: .86rem;
            line-height: 1.55;
            text-align: center;
            font-weight: 500;
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
        .capture-shell {
            background: #ffffff;
            border: 1px solid #cfe0ea;
            border-radius: 10px;
            padding: .85rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, .06);
            max-width: 720px;
            margin: 0 auto;
        }
        .ai-status {
            display: flex;
            gap: .55rem;
            align-items: center;
            padding: .7rem .85rem;
            border-radius: 8px;
            background: #e8f7f5;
            color: #075a75;
            border: 1px solid #b9e4de;
            margin: .65rem 0;
        }
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(140px, 1fr));
            gap: .75rem;
            margin: .85rem 0;
        }
        .profile-card {
            background: #ffffff;
            border: 1px solid #d7e2eb;
            border-radius: 8px;
            padding: .85rem;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        }
        .profile-card span {
            display: block;
            color: #64748b;
            font-size: .8rem;
            margin-bottom: .25rem;
        }
        .profile-card strong {
            color: #0f172a;
        }
        .stCameraInput video,
        .stCameraInput img {
            cursor: crosshair !important;
        }
        .camera-circular .stCameraInput video,
        .camera-circular .stCameraInput img,
        div[data-testid="stCameraInput"] video,
        div[data-testid="stCameraInput"] img {
            width: 280px !important;
            height: 280px !important;
            max-width: 280px !important;
            max-height: 280px !important;
            border-radius: 999px !important;
            aspect-ratio: 1 / 1 !important;
            object-fit: cover !important;
            border: 4px solid #0a7f78 !important;
            box-shadow: 0 10px 30px rgba(6,59,92,.18);
            display: block !important;
            margin: 0 auto !important;
        }
        div[data-testid="stCameraInput"] {
            max-width: 360px !important;
            margin: 0 auto !important;
            position: relative !important;
        }
        div[data-testid="stCameraInput"]::before {
            content: var(--capture-guide-text, "Face guide");
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 5;
            padding: .35rem .7rem;
            border-radius: 999px;
            background: rgba(6, 59, 92, .86);
            color: #ffffff;
            font-weight: 700;
            font-size: .82rem;
            text-align: center;
            pointer-events: none;
            white-space: nowrap;
        }
        div[data-testid="stCameraInput"]::after {
            content: var(--capture-guide-arrow, "CENTER");
            position: absolute;
            top: 42px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 5;
            color: #ffffff;
            background: rgba(10, 127, 120, .9);
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            pointer-events: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    if st.session_state.get("enrolment_step") == "face":
        st.markdown(
            """
            <div class="notice">
                Guided enrolment is active. Follow the in-frame arrow and use AI auto-capture where available.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    logo_src = logo_data_uri()
    logo_markup = f'<img class="hero-logo" src="{logo_src}" alt="SERPS logo">' if logo_src else ""
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-identity">
                {logo_markup}
                <div class="hero-copy">
                    <span class="brand">SERPS</span>
                    <h1>Secure Remote-Proctored Assessment Console</h1>
                    <p>Explainable multi-modal monitoring, identity assurance, event fusion, and human-supervised review.</p>
                </div>
            </div>
        </div>
        <div class="notice">
            Research prototype for academic demonstration. AI-generated alerts support human review and must not be treated as automatic misconduct decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


def home_page() -> None:
    logo_src = logo_data_uri()
    logo_markup = f'<img class="hero-logo" src="{logo_src}" alt="SERPS logo">' if logo_src else ""
    modules = [
        ("Enrolment", "Register candidates, capture consent, and complete guided facial enrolment."),
        ("Candidate Profiles", "Search and inspect enrolled candidate records with role-aware visibility."),
        ("Session Control", "Run mode selection, device checks, authentication, and session start gates."),
        ("Test Player", "Demonstrate assessment delivery with proctoring-focused sample questions."),
        ("Monitoring", "Generate structured demo events for visual, identity, and audio intelligence."),
        ("Review", "Inspect explainable fused alerts and record human-supervised decisions."),
        ("Reports", "Filter session data and export JSON evidence reports."),
    ]
    cards = "".join(f'<div class="module-card"><strong>{title}</strong><span>{body}</span></div>' for title, body in modules)
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-identity">
                {logo_markup}
                <div class="hero-copy">
                    <span class="brand">SERPS</span>
                    <h1>Secure Remote-Proctored Assessment Console</h1>
                    <p>Secure Explainable Remote Proctoring System for identity assurance, multi-modal monitoring, event fusion, and human-supervised review.</p>
                </div>
            </div>
        </div>
        <div class="module-grid">{cards}</div>
        <div class="notice">
            Academic research prototype for MSc/MIT capstone demonstration. AI-generated alerts support human review and must not be treated as automatic misconduct decisions.
        </div>
        <div class="status-card">
            <strong>Human-in-the-loop decision reminder</strong><br>
            Detection modules generate evidence and explanations. Staff reviewers remain responsible for final review outcomes.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer">
            <strong>SERPS - Secure Explainable Remote Proctoring System</strong><br>
            Miva Open University MIT Capstone Research Prototype<br>
            AI-generated alerts support human review and must not be treated as automatic misconduct decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


def return_to_top() -> None:
    st.markdown('<a href="#top">Return to Top</a>', unsafe_allow_html=True)


def selected_role_and_page() -> tuple[str, str]:
    with st.sidebar:
        slug_to_page = {slug: page_name for page_name, slug in PAGE_SLUGS.items()}
        requested_page = str(st.query_params.get("page", "home"))
        page = slug_to_page.get(requested_page, "Home")
        logo_src = logo_data_uri()
        if logo_src:
            st.markdown(
                f"""
                <div class="sidebar-brand">
                    <img src="{logo_src}" alt="SERPS logo">
                    <div>
                        <strong>SERPS</strong>
                        <span>Proctoring Control</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.title("Proctoring Control")
        st.caption("Navigation")
        for page_name in PAGES:
            active_class = "font-weight: 800; color: #075a75;" if page == page_name else "color: #0f172a;"
            st.markdown(
                f'<a href="?page={PAGE_SLUGS[page_name]}" target="_self" style="display:block; padding:.42rem .2rem; text-decoration:none; {active_class}">{page_name}</a>',
                unsafe_allow_html=True,
            )
        role = st.selectbox("Prototype Role Simulator", [role.value for role in Role])
        st.caption(
            "In production, roles would be assigned after secure staff login. "
            "Candidates would not access the SERPS dashboard."
        )
    return role, page


def candidate_management(role: str) -> None:
    st.subheader("Candidate Enrolment")
    if not has_permission(role, "register_candidate"):
        st.info("Your role can view monitoring data but cannot register candidates.")
        return

    if "enrolment_step" not in st.session_state:
        st.session_state.enrolment_step = "dashboard"
    if "custom_fields" not in st.session_state:
        st.session_state.custom_fields = [{"label": "Custom Reference", "type": "Text", "applies_to": "Generic", "value": ""}]
    active_enrolment_candidate = st.session_state.get("enrolment_candidate_id")
    if st.session_state.enrolment_step == "profile" and not _candidate_face_complete(active_enrolment_candidate):
        st.session_state.enrolment_step = "dashboard"

    if st.session_state.enrolment_step == "dashboard":
        enrolment_dashboard()
    elif st.session_state.enrolment_step == "register":
        render_enrolment_steps()
        registration_wizard(role)
    elif st.session_state.enrolment_step == "face":
        render_enrolment_steps()
        guided_face_enrolment()
    else:
        render_enrolment_steps()
        profile_candidate_id = st.session_state.get("profile_candidate_id") or st.session_state.get("enrolment_candidate_id")
        candidate_profile_browser(str(profile_candidate_id) if profile_candidate_id else None)
    return_to_top()


def enrolment_dashboard() -> None:
    st.markdown("#### Enrolment Dashboard")
    st.caption("Choose the next enrolment action. Candidate registration fields remain hidden until a new registration is started.")
    candidates = cached_candidates()
    eligible_face_candidates = face_capture_eligible_candidates(candidates)
    if st.session_state.get("face_gate_message"):
        st.warning(str(st.session_state.pop("face_gate_message")))
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Register New Candidate", key="start_new_registration", use_container_width=True):
            st.session_state.enrolment_step = "register"
            st.session_state.pop("enrolment_candidate_id", None)
            st.rerun()
    with col2:
        disabled = not candidates
        if st.button("Continue Face Capture", key="continue_face_capture", disabled=disabled, use_container_width=True):
            if not eligible_face_candidates:
                st.session_state.face_gate_message = "Please register or save candidate biodata before guided face capture."
            else:
                st.session_state.enrolment_step = "face"
            st.rerun()
    with col3:
        if st.button("View My Profile / View Candidate Profile", key="open_enrolment_profile", disabled=not candidates, use_container_width=True):
            st.session_state.enrolment_step = "profile"
            st.rerun()


def candidate_profile_browser(default_candidate_id: str | None = None) -> None:
    candidates = cached_candidates()
    st.markdown("#### Enrolled candidates")
    if not candidates:
        st.info("No enrolled candidates are available yet.")
        return
    search = st.text_input("Search candidate", key="enrolment_profile_search", placeholder="Type name, Student ID, or Candidate ID")
    filtered_candidates = _filter_candidates(candidates, search)
    if not filtered_candidates:
        st.warning("No candidate matches your search.")
        return
    labels = [f"{candidate['full_name']} ({candidate['candidate_id']})" for candidate in filtered_candidates]
    default_index = 0
    if default_candidate_id:
        for index, label in enumerate(labels):
            if default_candidate_id in label:
                default_index = index
                break
    selected = st.selectbox("Select candidate profile", labels, index=default_index, key="enrolment_profile_select")
    candidate_id = selected.split("(")[-1].rstrip(")")
    render_candidate_profile(candidate_id, include_images=True, allow_biodata_edit=True)


def candidate_profiles_page(role: str) -> None:
    st.subheader("Candidate Profiles")
    candidates = cached_candidates()
    if not candidates:
        st.info("No candidate profiles are available yet.")
        return

    if role == Role.ADMIN.value:
        visible_candidates = candidates
        st.caption("Admin view: all candidate profiles and enrolment evidence.")
    else:
        active_candidate_id = st.session_state.get("active_candidate_id") or st.session_state.get("authenticated_candidate_id")
        visible_candidates = [candidate for candidate in candidates if str(candidate["candidate_id"]) == str(active_candidate_id)]
        st.caption("Restricted view: Human Proctors and Reviewers see assigned or active-session candidate profiles only.")

    if not visible_candidates:
        st.warning("No assigned candidate profile is available for this role yet.")
        return

    st.write("Enrolled candidate list")
    list_rows = [
        {
            "Candidate": candidate.get("full_name"),
            "Identifier": candidate.get("candidate_id"),
            "Institution": candidate.get("institution"),
            "Profile": candidate.get("institution_type"),
            "Status": candidate.get("enrolment_status"),
            "Created": candidate.get("created_at"),
        }
        for candidate in visible_candidates
    ]
    st.dataframe(pd.DataFrame(list_rows), use_container_width=True, hide_index=True)

    search = st.text_input("Search candidate profiles", key=f"candidate_profiles_search_{role}", placeholder="Type name, Student ID, or Candidate ID")
    if not search.strip():
        st.info("Search by name, Student ID, Candidate ID, matric number, or registration number to display a profile.")
        return

    visible_candidates = _filter_candidates(visible_candidates, search)
    if not visible_candidates:
        st.warning("No candidate profile matches your search.")
        return

    labels = [f"{candidate['full_name']} ({candidate['candidate_id']})" for candidate in visible_candidates]
    selected = st.selectbox("Candidate", ["Select a candidate"] + labels, key=f"candidate_profiles_select_{role}")
    if selected == "Select a candidate":
        st.info("Select a candidate from the filtered result list to view details.")
        return
    candidate_id = selected.split("(")[-1].rstrip(")")
    render_candidate_profile(candidate_id, include_images=role == Role.ADMIN.value)
    return_to_top()


def _filter_candidates(candidates: list[dict[str, object]], search: str) -> list[dict[str, object]]:
    query = search.strip().lower()
    if not query:
        return candidates
    return [
        candidate
        for candidate in candidates
        if query in str(candidate.get("full_name", "")).lower()
        or query in str(candidate.get("candidate_id", "")).lower()
        or query in str(candidate.get("matric_number", "")).lower()
        or query in str(candidate.get("waec_registration_number", "")).lower()
    ]


def face_capture_eligible_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    eligible_statuses = {"registered_pending_face_capture", "face_enrolled", "authenticated"}
    return [candidate for candidate in candidates if candidate.get("enrolment_status") in eligible_statuses]


def render_enrolment_steps() -> None:
    col_dashboard, col_register, col_face, col_profile = st.columns(4)
    with col_dashboard:
        if st.button("Dashboard", type="primary" if st.session_state.enrolment_step == "dashboard" else "secondary"):
            st.session_state.enrolment_step = "dashboard"
            st.rerun()
    with col_register:
        if st.button("1. Registration + Consent", type="primary" if st.session_state.enrolment_step == "register" else "secondary"):
            st.session_state.enrolment_step = "register"
            st.rerun()
    with col_face:
        disabled = not st.session_state.get("enrolment_candidate_id")
        if st.button("2. Guided Face Capture", disabled=disabled, type="primary" if st.session_state.enrolment_step == "face" else "secondary"):
            st.session_state.enrolment_step = "face"
            st.rerun()
    with col_profile:
        profile_disabled = not _candidate_face_complete(st.session_state.get("enrolment_candidate_id"))
        if st.button(
            "3. View my Profile",
            disabled=profile_disabled,
            type="primary" if st.session_state.enrolment_step == "profile" else "secondary",
        ):
            st.session_state.enrolment_step = "profile"
            st.rerun()


def _candidate_face_complete(candidate_id: object | None) -> bool:
    return bool(candidate_id) and is_face_enrolment_complete(str(candidate_id))


def registration_wizard(role: str) -> None:
    st.markdown("#### Register candidate and capture consent")
    with st.expander("Admin field customization", expanded=False):
        st.caption("Prototype custom fields apply to this registration form submission.")
        field_count = st.number_input("Number of additional fields", min_value=0, max_value=8, value=len(st.session_state.custom_fields))
        current_fields = st.session_state.custom_fields[: int(field_count)]
        while len(current_fields) < int(field_count):
            current_fields.append({"label": f"Custom field {len(current_fields) + 1}", "type": "Text", "applies_to": "All", "value": ""})
        st.session_state.custom_fields = current_fields
        for index, field in enumerate(st.session_state.custom_fields):
            col_label, col_type, col_scope = st.columns([2, 1, 1])
            with col_label:
                field["label"] = st.text_input(f"Field {index + 1} label", field["label"], key=f"custom_label_{index}")
            with col_type:
                field["type"] = st.selectbox(
                    "Data type",
                    ["Text", "Number", "Date", "Email", "Boolean"],
                    index=["Text", "Number", "Date", "Email", "Boolean"].index(field.get("type", "Text")),
                    key=f"custom_type_{index}",
                )
            with col_scope:
                field["applies_to"] = st.selectbox(
                    "Applies to",
                    ["All", "Miva", "WAEC", "Generic"],
                    index=["All", "Miva", "WAEC", "Generic"].index(field.get("applies_to", "All")),
                    key=f"custom_scope_{index}",
                )

    institution_type = st.selectbox(
        "Institution profile",
        ["Miva", "WAEC", "Generic"],
        key="registration_institution_type",
    )
    st.caption("Changing this selection immediately filters the registration fields below.")
    suggested_candidate_id = generate_candidate_id(institution_type)
    suggested_email = default_email_for_institution(institution_type)

    country_index = COUNTRIES.index("Nigeria") if "Nigeria" in COUNTRIES else 0
    country = st.selectbox("Country", COUNTRIES, index=country_index, key="registration_country")
    if country == "Nigeria":
        state = st.selectbox("State / FCT", NIGERIA_STATES, key="registration_state")
        local_government_area = st.selectbox(
            "Local Government Area",
            NIGERIA_LGAS.get(state, []),
            key=f"registration_lga_{state}",
        )
    else:
        state = st.text_input("State / Province / Region", key="registration_foreign_state")
        local_government_area = st.text_input("City / Locality", key="registration_foreign_city")

    with st.form("candidate_form"):
        full_name = st.text_input("Full name", "Demo Candidate")
        if institution_type == "WAEC":
            institution = st.text_input("Institution", "WAEC")
            candidate_identifier = st.text_input("Candidate ID (10 digits)", suggested_candidate_id, key="waec_candidate_identifier")
            st.caption("WAEC Candidate ID = 7-digit centre number + 3-digit candidate number.")
            waec_registration_number = st.text_input("Candidate Registration Number", "WAEC/REG/2026-A1")
            matric_number = ""
            programme = ""
            department = ""
        elif institution_type == "Miva":
            institution = st.text_input("Institution", "Miva Open University")
            candidate_identifier = st.text_input("Student ID (digits only)", suggested_candidate_id, key="miva_candidate_identifier")
            matric_number = st.text_input("Matric Number", "MIVA/CSC/2026/001")
            programme = st.selectbox("Programme", ["Undergraduate", "Postgraduate"], key="miva_programme")
            department = st.text_input("Department", "Computer Science")
            waec_registration_number = ""
        else:
            institution = st.text_input("Institution", "Demo Institution")
            candidate_identifier = st.text_input("Candidate ID", suggested_candidate_id, key="generic_candidate_identifier")
            waec_registration_number = ""
            matric_number = ""
            programme = ""
            department = ""
        email = st.text_input("Email", suggested_email, key=f"registration_email_{institution_type}")
        gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"], key="registration_gender")
        date_of_birth = st.date_input("Date of birth", value=None)
        st.markdown("Address")
        st.info(f"Country: {country} | Region: {state} | Locality: {local_government_area}")
        postal_code = st.text_input("ZIP / Postal code", "")
        street_address = st.text_area("Street address", "")
        custom_values: dict[str, str] = {}
        built_in_extra_fields = {
            "Programme": programme,
            "Department": department,
        }
        custom_values.update({key: value for key, value in built_in_extra_fields.items() if value})
        for index, field in enumerate(st.session_state.custom_fields):
            label = field["label"].strip()
            applies_to = field.get("applies_to", "All")
            if label and applies_to in {"All", institution_type}:
                custom_values[label] = render_custom_field_input(label, field.get("type", "Text"), index)
        consent = st.checkbox(CONSENT_NOTICE)
        col_draft, col_submit = st.columns(2)
        with col_draft:
            draft_submitted = st.form_submit_button("Save biodata as draft")
        with col_submit:
            submitted = st.form_submit_button("Register candidate and continue")

    if draft_submitted or submitted:
        if not full_name.strip():
            st.error("Full name is required.")
            return
        if submitted and not consent:
            st.error("Consent is required before enrolment.")
            return
        try:
            candidate_id = register_candidate(
                full_name=full_name,
                candidate_id=candidate_identifier,
                institution=institution,
                email=email,
                institution_type=institution_type,
                waec_registration_number=waec_registration_number or None,
                matric_number=matric_number or None,
                gender=gender,
                date_of_birth=date_of_birth.isoformat() if date_of_birth else None,
                country=country,
                state=state,
                local_government_area=local_government_area,
                postal_code=postal_code,
                street_address=street_address,
                enrolment_status="registered_pending_face_capture" if submitted else "draft",
            )
        except CandidateDuplicateError as exc:
            st.warning(str(exc))
            existing_id = exc.existing_candidate_id
            col_existing, col_face, col_edit = st.columns(3)
            with col_existing:
                if st.button("View existing candidate", key=f"view_duplicate_{existing_id}"):
                    st.session_state.profile_candidate_id = existing_id
                    st.session_state.enrolment_candidate_id = existing_id
                    st.session_state.enrolment_step = "profile"
                    st.rerun()
            with col_face:
                existing = get_candidate(existing_id)
                can_continue = existing and existing.get("enrolment_status") in {"registered_pending_face_capture", "face_enrolled"}
                if st.button("Continue pending face capture", key=f"continue_duplicate_{existing_id}", disabled=not can_continue):
                    st.session_state.enrolment_candidate_id = existing_id
                    st.session_state.enrolment_step = "face"
                    st.rerun()
            with col_edit:
                st.caption("Draft editing is available from the candidate profile review panel.")
            return
        except ValueError as exc:
            st.error(str(exc))
            return
        save_candidate_custom_fields(candidate_id, custom_values)
        if submitted:
            capture_consent(candidate_id)
        clear_app_caches()
        st.session_state.enrolment_candidate_id = candidate_id
        if submitted:
            st.session_state.enrolment_step = "face"
            st.success(f"Candidate registered: {candidate_id}. Proceeding to guided face capture.")
            st.rerun()
        st.success(f"Draft biodata saved for {candidate_id}. Register the candidate when ready to start guided face capture.")


def render_custom_field_input(label: str, data_type: str, index: int) -> str:
    key = f"custom_value_{index}"
    if data_type == "Number":
        return str(st.number_input(label, key=key, step=1))
    if data_type == "Date":
        value = st.date_input(label, value=None, key=key)
        return value.isoformat() if value else ""
    if data_type == "Email":
        return st.text_input(label, key=key, placeholder="name@example.com")
    if data_type == "Boolean":
        return "Yes" if st.checkbox(label, key=key) else "No"
    return st.text_input(label, key=key)


def guided_face_enrolment() -> None:
    candidates = cached_candidates()
    st.markdown("#### Guided facial enrolment")
    st.caption("AI validation checks that a single face is visible before each sample is saved.")
    if not candidates:
        st.info("Please register or save candidate biodata before guided face capture.")
        if st.button("Back to registration"):
            st.session_state.enrolment_step = "register"
            st.rerun()
        return

    eligible_candidates = face_capture_eligible_candidates(candidates)
    if not eligible_candidates:
        st.warning("Please register or save candidate biodata before guided face capture.")
        st.caption("Draft-only and unsaved candidates cannot access facial enrolment because face samples must attach to an existing registered identity record.")
        if st.button("Back to registration"):
            st.session_state.enrolment_step = "register"
            st.rerun()
        return

    candidate_options = {f"{c['full_name']} ({c['candidate_id']})": c for c in eligible_candidates}
    default_candidate_id = st.session_state.get("enrolment_candidate_id")
    labels = list(candidate_options)
    default_index = 0
    if default_candidate_id:
        for index, label in enumerate(labels):
            if str(default_candidate_id) in label:
                default_index = index
                break
    selected = st.selectbox("Candidate for face capture", labels, index=default_index, key="face_capture_candidate_select")
    candidate = candidate_options[selected]
    candidate_id = str(candidate["candidate_id"])
    done = captured_directions(candidate_id)
    progress = len(done) / len(FACE_DIRECTIONS)
    st.progress(progress, text=f"{len(done)} of {len(FACE_DIRECTIONS)} directions captured")

    remaining = [direction for direction in FACE_DIRECTIONS if direction not in done]
    if not remaining:
        st.success("Guided facial enrolment is complete for this candidate.")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("View enrolled candidate"):
                st.session_state.profile_candidate_id = candidate_id
                st.session_state.enrolment_step = "profile"
                st.rerun()
        with col_b:
            if st.button("Register another candidate"):
                st.session_state.enrolment_step = "register"
                st.session_state.pop("enrolment_candidate_id", None)
                st.rerun()
        with col_c:
            st.caption("Next workflow: authenticate candidate and start session monitoring.")
        return

    direction = remaining[0]
    direction_label = direction.replace("_", " ").title()
    st.markdown(f"### Capture {len(done) + 1} of {len(FACE_DIRECTIONS)}: {direction_label}")
    st.markdown('<div class="capture-shell">', unsafe_allow_html=True)
    inject_capture_overlay(direction)
    st.markdown(
        '<div class="ai-status">AI guide: keep one face inside the circle, hold still, and improve lighting until the capture is accepted.</div>',
        unsafe_allow_html=True,
    )
    ai_col, fallback_col = st.columns([1, 1])
    with ai_col:
        if st.button("AI auto-capture valid frame"):
            with st.spinner("Watching webcam for a valid face frame..."):
                from src.enrolment.auto_capture import ai_auto_capture

                result = ai_auto_capture(direction=direction)
            if result["accepted"] and result["image_bytes"]:
                process_face_capture(candidate_id, direction, direction_label, bytes(result["image_bytes"]))
            else:
                st.warning(str(result["message"]))
    with fallback_col:
        st.caption("Fallback: use browser camera below if local webcam auto-capture is unavailable.")

    frame_shape = st.radio("Camera frame", ["Circular guide", "Original rectangle"], horizontal=True, index=0)
    fix_mirror = st.checkbox("Correct mirrored webcam image", value=True)
    if fix_mirror:
        st.markdown(
            """
            <style>
            div[data-testid="stCameraInput"] video,
            div[data-testid="stCameraInput"] img {
                transform: scaleX(-1) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    if frame_shape == "Original rectangle":
        st.markdown(
            """
            <style>
            div[data-testid="stCameraInput"] video,
            div[data-testid="stCameraInput"] img {
                max-width: 100% !important;
                width: 100% !important;
                height: auto !important;
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

    if image:
        image_bytes = image.getvalue()
        if fix_mirror:
            from src.vision.face_quality import mirror_image_bytes

            image_bytes = mirror_image_bytes(image_bytes)
        process_face_capture(candidate_id, direction, direction_label, image_bytes)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Back to registration"):
        st.session_state.enrolment_step = "register"
        st.rerun()


def process_face_capture(candidate_id: str, direction: str, direction_label: str, image_bytes: bytes) -> None:
    capture_hash = hashlib.sha256(image_bytes).hexdigest()
    state_key = f"processed_capture_{candidate_id}_{direction}"
    if st.session_state.get(state_key) == capture_hash:
        st.info("This capture has already been processed. Clear photo to retake or wait for the next direction.")
        return

    from src.vision.face_quality import assess_face_capture, extract_face_embedding

    assessment = assess_face_capture(image_bytes, direction)
    if not assessment["accepted"]:
        st.error(str(assessment["message"]))
        return

    embedding = extract_face_embedding(image_bytes, direction)
    duplicate_face = find_similar_face_candidate(candidate_id, embedding)
    if duplicate_face:
        st.error(
            f"Prototype duplicate-face check found a possible match with {duplicate_face['candidate_id']} "
            f"(similarity {duplicate_face['similarity']:.3f}). Review the existing profile before accepting this enrolment."
        )
        return
    file_path = candidate_enrolment_dir(candidate_id) / f"{direction}.jpg"
    embedding_path = candidate_enrolment_dir(candidate_id) / f"{direction}_embedding.npy"
    write_bytes(file_path, image_bytes)
    np.save(embedding_path, embedding)
    record_face_sample(
        candidate_id,
        direction,
        str(file_path),
        quality_score=float(assessment["quality_score"]),
        embedding_path=str(embedding_path),
    )
    st.session_state[state_key] = capture_hash
    if is_face_enrolment_complete(candidate_id):
        from src.storage.candidate_repository import update_enrolment_status

        update_enrolment_status(candidate_id, "face_enrolled")
        clear_app_caches()
        st.success("Accepted and saved. Guided facial enrolment is complete.")
    else:
        st.success(f"Accepted and saved {direction_label}. Loading the next capture...")
    st.rerun()


def find_similar_face_candidate(candidate_id: str, embedding: np.ndarray, threshold: float = 0.995) -> dict[str, object] | None:
    for candidate in cached_candidates():
        other_candidate_id = str(candidate["candidate_id"])
        if other_candidate_id == candidate_id:
            continue
        for sample in list_face_samples(other_candidate_id):
            embedding_path = sample.get("embedding_path")
            if not embedding_path or not Path(str(embedding_path)).exists():
                continue
            try:
                existing_embedding = np.load(str(embedding_path))
            except (OSError, ValueError):
                continue
            denom = float(np.linalg.norm(embedding) * np.linalg.norm(existing_embedding))
            if denom == 0:
                continue
            similarity = float(np.dot(embedding, existing_embedding) / denom)
            if similarity >= threshold:
                return {
                    "candidate_id": other_candidate_id,
                    "full_name": candidate.get("full_name"),
                    "similarity": similarity,
                }
    return None


def inject_capture_overlay(direction: str) -> None:
    arrows = {
        "front": "CENTER",
        "left": "←",
        "right": "→",
        "slight_up": "↑",
        "slight_down": "↓",
        "centre": "CENTER",
    }
    notes = {
        "front": "Look straight",
        "left": "Turn left",
        "right": "Turn right",
        "slight_up": "Tilt up",
        "slight_down": "Tilt down",
        "centre": "Centre face",
    }
    arrows.update({"left": "LEFT", "right": "RIGHT", "slight_up": "UP", "slight_down": "DOWN"})
    st.markdown(
        f"""
        <style>
        div[data-testid="stCameraInput"] {{
            --capture-guide-text: "{notes[direction]}";
            --capture-guide-arrow: "{arrows[direction]}";
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def session_control(role: str) -> str | None:
    candidates = cached_candidates()
    st.subheader("Session Control")
    st.caption("Staff RBAC controls Admin, Human Proctor, and Reviewer access. Candidates are not RBAC users; they authenticate separately through their enrolment profile.")
    if not candidates:
        st.warning("Register a candidate before starting a session.")
        return None

    if "session_wizard_step" not in st.session_state:
        st.session_state.session_wizard_step = 1
    step = int(st.session_state.session_wizard_step)

    candidate_options = {f"{c['full_name']} ({c['candidate_id']})": c for c in candidates}
    candidate_id = st.session_state.get("session_candidate_id")
    candidate = next((c for c in candidates if str(c["candidate_id"]) == str(candidate_id)), None)
    mode = st.session_state.get("session_monitoring_mode_value")
    if mode not in {"A", "B", "C"}:
        mode = None

    if step > 1 and candidate:
        render_wizard_summary("1. Candidate", f"{candidate['full_name']} ({candidate['candidate_id']})", 1)
    if step == 1:
        st.markdown("#### 1. Select Candidate")
        with st.container(border=True):
            labels = list(candidate_options)
            default_label = next((label for label in labels if candidate_id and str(candidate_id) in label), labels[0])
            selected = st.selectbox("Candidate", labels, index=labels.index(default_label), key="session_candidate_select")
            candidate = candidate_options[selected]
            candidate_id = str(candidate["candidate_id"])
            candidate_profile_summary(candidate_id)
            if st.button("Continue to monitoring mode", key="wizard_candidate_next"):
                st.session_state.session_candidate_id = candidate_id
                st.session_state.session_wizard_step = 2
                st.rerun()
        session_management_panel(role)
        render_audit_trail_panel()
        return_to_top()
        return st.session_state.get("active_session_id")

    if not candidate:
        st.session_state.session_wizard_step = 1
        st.rerun()

    mode_options = {
        "Mode B - dual-camera full mode": "B",
        "Mode A - single-camera CBT mode": "A",
        "Mode C - mirror-assisted low-resource mode": "C",
    }
    if step > 2 and mode:
        render_wizard_summary("2. Monitoring Mode", f"Mode {mode}", 2)
    if step == 2:
        st.markdown("#### 2. Select Monitoring Mode")
        with st.container(border=True):
            default_label = next((label for label, value in mode_options.items() if value == mode), "Mode B - dual-camera full mode")
            selected_mode_label = st.selectbox("Monitoring mode", list(mode_options), index=list(mode_options).index(default_label), key="session_monitoring_mode")
            mode = mode_options[selected_mode_label]
            plan = MonitoringModeController().configure(mode)
            render_monitoring_mode_card(plan)
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("Back to candidate", key="wizard_mode_back"):
                    st.session_state.session_wizard_step = 1
                    st.rerun()
            with col_next:
                if st.button("Continue to pre-exam checks", key="wizard_mode_next"):
                    st.session_state.session_monitoring_mode_value = mode
                    st.session_state.session_wizard_step = 3
                    st.rerun()
        session_management_panel(role)
        render_audit_trail_panel()
        return_to_top()
        return st.session_state.get("active_session_id")

    if not mode:
        st.session_state.session_wizard_step = 2
        st.rerun()

    latest_check = latest_device_check(str(candidate["candidate_id"]), mode)
    device_ready = device_check_allows_session_start(latest_check)
    if step > 3:
        status = "Passed" if device_ready else "Pending"
        render_wizard_summary("3. Pre-Exam Check", f"{status} for Mode {mode}", 3)
    if step == 3:
        st.markdown("#### 3. Run Pre-Exam Device and Environment Check")
        device_ready = pre_exam_device_check_panel(role, str(candidate["candidate_id"]), mode)
        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("Back to monitoring mode", key="wizard_checks_back"):
                st.session_state.session_wizard_step = 2
                st.rerun()
        with col_next:
            if st.button("Continue to authentication", key="wizard_checks_next", disabled=not device_ready):
                st.session_state.session_wizard_step = 4
                st.rerun()
        session_management_panel(role)
        render_audit_trail_panel()
        return_to_top()
        return st.session_state.get("active_session_id")

    authenticated = st.session_state.get("authenticated_candidate_id") == str(candidate["candidate_id"])
    if step > 4:
        render_wizard_summary("4. Authentication", "Passed" if authenticated else "Pending", 4)
    if step == 4:
        st.markdown("#### 4. Authenticate Candidate")
        authenticate_candidate_panel(role, candidate)
        authenticated = st.session_state.get("authenticated_candidate_id") == str(candidate["candidate_id"])
        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("Back to pre-exam checks", key="wizard_auth_back"):
                st.session_state.session_wizard_step = 3
                st.rerun()
        with col_next:
            if st.button("Continue to session start", key="wizard_auth_next", disabled=not authenticated):
                st.session_state.session_wizard_step = 5
                st.rerun()
        session_management_panel(role)
        render_audit_trail_panel()
        return_to_top()
        return st.session_state.get("active_session_id")

    st.markdown("#### 5. Start Prototype Session")
    with st.container(border=True):
        render_start_gate_status(authenticated, device_ready)
        if authenticated and device_ready and has_permission(role, "start_session"):
            if st.button("Start prototype session", key=f"start_session_{candidate['candidate_id']}_{mode}"):
                log_audit(role, "session_start_approved", str(candidate["candidate_id"]), f"monitoring_mode={mode}")
                session_id = start_session(str(candidate["candidate_id"]), str(candidate["candidate_id"]), mode)
                log_audit(role, "session_started", session_id, f"candidate_id={candidate['candidate_id']}; monitoring_mode={mode}")
                st.session_state.active_session_id = session_id
                st.session_state.active_candidate_id = str(candidate["candidate_id"])
                clear_app_caches()
                st.success(f"Started session {session_id}")
                st.rerun()
        else:
            st.info("Session start is locked until authentication and pre-exam checks are satisfied, or valid overrides are recorded.")
    col_back, col_reset = st.columns(2)
    with col_back:
        if st.button("Back to authentication", key="wizard_start_back"):
            st.session_state.session_wizard_step = 4
            st.rerun()
    with col_reset:
        if st.button("Start another session workflow", key="wizard_start_reset"):
            st.session_state.session_wizard_step = 1
            st.rerun()

    selected_session_id = session_management_panel(role)
    render_audit_trail_panel()
    return_to_top()
    return selected_session_id


def render_wizard_summary(title: str, value: str, step_number: int) -> None:
    with st.container(border=True):
        col_text, col_action = st.columns([3, 1])
        with col_text:
            st.markdown(f"**{title}**")
            st.caption(value)
        with col_action:
            if st.button("Edit", key=f"edit_session_step_{step_number}"):
                st.session_state.session_wizard_step = step_number
                st.rerun()


def render_monitoring_mode_card(plan) -> None:
    required = set(MODE_REQUIREMENTS[plan.mode])
    guidance = {
        "A": "CBT-centre limitation: Mode A accepts a single primary camera and relies more heavily on identity, audio, and behaviour checks because room visibility is limited.",
        "B": "Dual-camera full mode: Mode B is the recommended high-assurance configuration and requires both primary and secondary cameras.",
        "C": "Mirror-assisted limitation: Mode C supports low-resource setups by requiring a mirror in place of a secondary camera; reflected evidence is weighted conservatively.",
    }
    check_rows = "".join(
        f"<li><strong>{label}</strong>: {'Required' if name in required else 'Not required'}</li>"
        for name, label in CHECK_LABELS.items()
        if name in {"primary_camera", "secondary_camera", "microphone", "mirror"}
    )
    st.markdown(
        f"""
        <div class="status-card">
            <strong>Monitoring Mode {plan.mode}</strong><br>
            Enabled: {", ".join(plan.enabled_modules)}<br>
            Disabled: {", ".join(plan.disabled_modules) if plan.disabled_modules else "None"}
            <ul>{check_rows}</ul>
            <span>{guidance[plan.mode]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pre_exam_device_check_panel(role: str, candidate_id: str, mode: str) -> bool:
    latest_check = latest_device_check(candidate_id, mode)
    latest_candidate_check = latest_device_check(candidate_id)
    required = set(evaluate_device_checks(mode, {}).required_checks)
    prefix = f"device_{candidate_id}_{mode}"

    with st.container(border=True):
        st.caption("Checks are stored in SQLite and logged in the audit trail. Camera previews are inactive until explicitly started.")
        if latest_check:
            render_device_status_cards(latest_check)
            render_last_saved_check(latest_check)
        elif latest_candidate_check:
            st.warning("No saved device check for this candidate in the selected mode. Showing the candidate's most recent saved check below for reference only.")
            render_last_saved_check(latest_candidate_check)
        else:
            st.info("No saved device check for this candidate and monitoring mode yet.")

        can_manage_check = has_permission(role, "start_session")
        if not can_manage_check:
            st.warning("Only Admin or Human Proctor can record pre-exam checks or overrides.")
            return device_check_allows_session_start(latest_check)

        col_apply, col_note = st.columns([1, 2])
        with col_apply:
            if st.button("Apply required checks for selected mode", key=f"{prefix}_apply_required"):
                for check_name in CHECK_LABELS:
                    st.session_state[device_check_state_key(prefix, check_name)] = check_name in required
                st.rerun()
        with col_note:
            st.caption("This populates required items for the selected mode. Staff may still adjust the checklist for demonstration.")

        render_visible_device_tests(prefix, mode, required)

        with st.form(f"device_check_{candidate_id}_{mode}"):
            st.write("Record check results")
            col_a, col_b = st.columns(2)
            values: dict[str, bool] = {}
            for index, (check_name, label) in enumerate(CHECK_LABELS.items()):
                key = device_check_state_key(prefix, check_name)
                if key not in st.session_state:
                    st.session_state[key] = latest_check_allows(latest_check, check_name)
                target = col_a if index % 2 == 0 else col_b
                with target:
                    requirement = "Required" if check_name in required else "Not required"
                    values[check_name] = st.checkbox(
                        f"{label} ({requirement})",
                        key=key,
                        help="Mode requirement is enforced during evaluation.",
                    )
            submitted = st.form_submit_button("Save pre-exam check")

        if submitted:
            evaluation = evaluate_device_checks(mode, values)
            check_id = save_device_check(candidate_id, evaluation, role)
            log_audit(role, "device_check_saved", check_id, f"candidate_id={candidate_id}; mode={mode}; status={evaluation.overall_status}")
            clear_app_caches()
            st.success(f"Saved pre-exam check {check_id}: {evaluation.overall_status}.")
            st.rerun()

        with st.expander("Staff override for failed/missing checks", expanded=False):
            st.caption("Override is recorded for audit. It permits the prototype session to start without all checks passing.")
            override_reason = st.text_area("Override reason", key=f"device_override_reason_{candidate_id}_{mode}")
            if st.button("Record device-check override", key=f"device_override_{candidate_id}_{mode}"):
                evaluation = evaluate_device_checks(mode, {}, staff_override=True, override_reason=override_reason)
                if evaluation.overall_status != "override":
                    st.error("Enter a clear override reason before recording staff override.")
                else:
                    check_id = save_device_check(candidate_id, evaluation, role, staff_override=True, override_reason=override_reason)
                    log_audit(role, "device_check_override", check_id, f"candidate_id={candidate_id}; mode={mode}; reason={override_reason.strip()}")
                    clear_app_caches()
                    st.warning(f"Device-check override recorded: {check_id}.")
                    st.rerun()

    return device_check_allows_session_start(latest_device_check(candidate_id, mode))


def latest_check_allows(latest_check: dict[str, object] | None, check_name: str) -> bool:
    if not latest_check:
        return False
    return latest_check.get(f"{check_name}_status") == "passed"


def device_check_state_key(prefix: str, check_name: str) -> str:
    return f"{prefix}_{check_name}_check"


def render_visible_device_tests(prefix: str, mode: str, required: set[str]) -> None:
    with st.expander("Optional visible device checks", expanded=False):
        st.caption("Prototype checks are manual confirmations unless a user explicitly opens a camera preview. Browser microphone access is not used by Streamlit here.")
        col1, col2 = st.columns(2)
        with col1:
            render_camera_preview(prefix, "primary_camera", "Primary camera preview")
            if mode == "B":
                render_camera_preview(prefix, "secondary_camera", "Secondary camera preview")
            else:
                st.caption("Secondary camera preview is optional because this mode does not require it.")
            if st.button("Test microphone", key=f"{prefix}_mic_test"):
                st.session_state[device_check_state_key(prefix, "microphone")] = True
                st.success("Microphone check marked as passed for prototype demonstration.")
        with col2:
            if st.button("Check lighting", key=f"{prefix}_lighting_test"):
                st.session_state[device_check_state_key(prefix, "lighting")] = True
                st.success("Lighting check marked as passed.")
            if st.button("Confirm candidate presence", key=f"{prefix}_presence_test"):
                st.session_state[device_check_state_key(prefix, "candidate_presence")] = True
                st.success("Candidate presence confirmed.")
            if st.button("Confirm environment declaration", key=f"{prefix}_environment_test"):
                st.session_state[device_check_state_key(prefix, "environment_declaration")] = True
                st.success("Environment declaration confirmed.")
            if "mirror" in required and st.button("Confirm mirror placement", key=f"{prefix}_mirror_test"):
                st.session_state[device_check_state_key(prefix, "mirror")] = True
                st.success("Mirror placement confirmed for Mode C.")


def render_camera_preview(prefix: str, check_name: str, label: str) -> None:
    active_key = f"{prefix}_{check_name}_preview_active"
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button(label, key=f"{prefix}_{check_name}_preview_start"):
            st.session_state[active_key] = True
            st.rerun()
    with col_stop:
        if st.button("Stop preview", key=f"{prefix}_{check_name}_preview_stop", disabled=not st.session_state.get(active_key)):
            st.session_state[active_key] = False
            st.rerun()
    if st.session_state.get(active_key):
        image = st.camera_input(label, key=f"{prefix}_{check_name}_preview_input")
        if image:
            st.session_state[device_check_state_key(prefix, check_name)] = True
            st.session_state[active_key] = False
            st.success(f"{label} captured and marked as passed.")
            st.rerun()


def render_device_status_cards(check: dict[str, object]) -> None:
    statuses = {
        "Primary": check["primary_camera_status"],
        "Secondary": check["secondary_camera_status"],
        "Microphone": check["microphone_status"],
        "Lighting": check["lighting_status"],
        "Presence": check["candidate_presence_status"],
        "Environment": check["environment_declaration_status"],
        "Mirror": check["mirror_status"],
        "Overall": check["overall_status"],
    }
    cols = st.columns(4)
    for index, (label, status) in enumerate(statuses.items()):
        with cols[index % 4]:
            st.metric(label, str(status).replace("_", " ").title())


def render_last_saved_check(check: dict[str, object]) -> None:
    st.write("Last saved check")
    st.dataframe(
        pd.DataFrame(
            [
                {"field": "Check ID", "value": check["check_id"]},
                {"field": "Mode", "value": check["monitoring_mode"]},
                {"field": "Timestamp", "value": check["checked_at"]},
                {"field": "Checked by", "value": check["checked_by"]},
                {"field": "Overall status", "value": check["overall_status"]},
                {"field": "Override", "value": "Yes" if check.get("staff_override") else "No"},
                {"field": "Override reason", "value": check.get("override_reason") or ""},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_start_gate_status(authenticated: bool, device_ready: bool) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Authentication gate", "Passed" if authenticated else "Pending")
    with col2:
        st.metric("Pre-exam gate", "Passed" if device_ready else "Pending")


def session_management_panel(role: str) -> str | None:
    sessions = cached_sessions()
    with st.expander("Active/reporting sessions", expanded=bool(sessions)):
        if not sessions:
            st.info("No sessions have been started yet.")
            return None
        status_filter = st.selectbox("Session filter", ["active", "ended", "all"], key="session_status_filter")
        visible_sessions = [session for session in sessions if status_filter == "all" or session["session_status"] == status_filter]
        if not visible_sessions:
            st.info(f"No {status_filter} sessions found.")
            return None
        session_labels = [f"{s['session_id']} - {s['candidate_id']} - {s['session_status']}" for s in visible_sessions]
        chosen = st.selectbox("Active/reporting session", session_labels, key="active_reporting_session")
        session_id = chosen.split(" - ")[0]
        selected_session = next(s for s in visible_sessions if s["session_id"] == session_id)
        st.session_state.active_session_id = session_id
        st.session_state.active_candidate_id = selected_session["candidate_id"]
        if selected_session["session_status"] == "active" and has_permission(role, "start_session"):
            if st.button("End selected session", key=f"end_session_{session_id}"):
                end_session(session_id)
                log_audit(role, "session_ended", session_id, f"candidate_id={selected_session['candidate_id']}")
                clear_app_caches()
                st.success(f"Ended session {session_id}.")
                st.rerun()
        return session_id


def get_cached_session(session_id: str | None) -> dict[str, object] | None:
    if not session_id:
        return None
    return next((session for session in cached_sessions() if str(session["session_id"]) == str(session_id)), None)


def render_audit_trail_panel() -> None:
    with st.expander("Recent audit trail", expanded=False):
        logs = cached_audit_logs(30)
        if not logs:
            st.info("No audit records found.")
            return
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)


def candidate_profile_summary(candidate_id: str) -> None:
    with st.expander("View enrolled candidate profile", expanded=False):
        render_candidate_profile(candidate_id)


def render_candidate_profile(candidate_id: str, include_images: bool = False, allow_biodata_edit: bool = False) -> None:
    candidates = {str(candidate["candidate_id"]): candidate for candidate in cached_candidates()}
    candidate = candidates.get(candidate_id)
    if not candidate:
        st.info("Candidate profile not found.")
        return

    samples = list_face_samples(candidate_id)
    custom_fields = list_candidate_custom_fields(candidate_id)
    captured = captured_directions(candidate_id)
    consent_records = list_candidate_consent(candidate_id)
    latest_consent = consent_records[0] if consent_records else None
    id_label = "Student ID" if candidate.get("institution_type") == "Miva" else "Candidate ID"
    st.markdown(
        f"""
        <div class="profile-grid">
            <div class="profile-card"><span>{id_label}</span><strong>{candidate_id}</strong></div>
            <div class="profile-card"><span>Full name</span><strong>{candidate['full_name']}</strong></div>
            <div class="profile-card"><span>Institution</span><strong>{candidate['institution']}</strong></div>
            <div class="profile-card"><span>Enrolment status</span><strong>{candidate['enrolment_status']}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    identifier_rows = [
        {"field": "Institution profile", "value": candidate.get("institution_type")},
        {"field": "Email", "value": candidate.get("email")},
        {"field": "WAEC Registration Number", "value": candidate.get("waec_registration_number")},
        {"field": "WAEC Centre Number", "value": candidate.get("centre_number")},
        {"field": "WAEC Candidate Number", "value": candidate.get("candidate_number")},
        {"field": "Miva Matric Number", "value": candidate.get("matric_number")},
        {"field": "Gender", "value": candidate.get("gender")},
        {"field": "Date of Birth", "value": candidate.get("date_of_birth")},
        {"field": "Country", "value": candidate.get("country")},
        {"field": "State", "value": candidate.get("state")},
        {"field": "Local Government Area", "value": candidate.get("local_government_area")},
        {"field": "ZIP / Postal Code", "value": candidate.get("postal_code")},
        {"field": "Street Address", "value": candidate.get("street_address")},
        {"field": "Consent status", "value": latest_consent.get("consent_status") if latest_consent else "Not captured"},
        {"field": "Consent timestamp", "value": latest_consent.get("consent_timestamp") if latest_consent else ""},
    ]
    visible_identifier_rows = [row for row in identifier_rows if row["value"]]
    if visible_identifier_rows:
        st.write("Institutional and demographic details")
        st.dataframe(pd.DataFrame(visible_identifier_rows), use_container_width=True)
    if allow_biodata_edit:
        render_biodata_edit_form(candidate)
    st.progress(len(captured) / len(FACE_DIRECTIONS), text=f"{len(captured)} of {len(FACE_DIRECTIONS)} required face samples captured")
    if custom_fields:
        st.write("Custom fields")
        field_rows = pd.DataFrame(custom_fields)[["field_name", "field_value"]]
        st.dataframe(field_rows, use_container_width=True)
    if samples:
        st.write("Face enrolment records")
        visible_columns = ["capture_direction", "quality_score", "image_path", "embedding_path", "captured_at"]
        st.dataframe(pd.DataFrame(samples)[visible_columns], use_container_width=True)
        if include_images:
            st.write("Captured face samples")
            cols = st.columns(3)
            for index, sample in enumerate(samples):
                image_path = sample.get("image_path")
                if image_path:
                    with cols[index % 3]:
                        st.image(
                            str(image_path),
                            caption=f"{sample['capture_direction']} | quality {float(sample['quality_score']):.2f}",
                            use_container_width=True,
                        )


def list_candidate_consent(candidate_id: str) -> list[dict[str, object]]:
    rows = fetch_all(
        """
        SELECT * FROM consent
        WHERE candidate_id = ?
        ORDER BY consent_timestamp DESC
        """,
        (candidate_id,),
    )
    return [dict(row) for row in rows]


def render_biodata_edit_form(candidate: dict[str, object]) -> None:
    with st.expander("Review and edit biodata", expanded=False):
        st.caption("This updates biodata and institution metadata only. Face recapture remains a separate controlled action.")
        candidate_id = str(candidate["candidate_id"])
        institution_type = str(candidate.get("institution_type") or "Generic")
        with st.form(f"edit_biodata_{candidate_id}"):
            full_name = st.text_input("Full name", str(candidate.get("full_name") or ""))
            institution = st.text_input("Institution", str(candidate.get("institution") or ""))
            email = st.text_input("Email", str(candidate.get("email") or default_email_for_institution(institution_type)))
            if institution_type == "WAEC":
                waec_registration_number = st.text_input(
                    "WAEC Candidate Registration Number",
                    str(candidate.get("waec_registration_number") or ""),
                )
                matric_number = None
            elif institution_type == "Miva":
                matric_number = st.text_input("Miva Matric Number", str(candidate.get("matric_number") or ""))
                waec_registration_number = None
            else:
                matric_number = None
                waec_registration_number = None
            gender_options = ["Female", "Male", "Other", "Prefer not to say"]
            current_gender = str(candidate.get("gender") or "Prefer not to say")
            gender = st.selectbox(
                "Gender",
                gender_options,
                index=gender_options.index(current_gender) if current_gender in gender_options else 3,
                key=f"edit_gender_{candidate_id}",
            )
            date_of_birth = st.text_input("Date of birth", str(candidate.get("date_of_birth") or ""))
            country = st.text_input("Country", str(candidate.get("country") or ""))
            state = st.text_input("State / Region", str(candidate.get("state") or ""))
            local_government_area = st.text_input("Local Government Area / Locality", str(candidate.get("local_government_area") or ""))
            postal_code = st.text_input("ZIP / Postal code", str(candidate.get("postal_code") or ""))
            street_address = st.text_area("Street address", str(candidate.get("street_address") or ""))
            submitted = st.form_submit_button("Save biodata changes")
        if submitted:
            try:
                update_candidate_biodata(
                    candidate_id=candidate_id,
                    full_name=full_name,
                    institution=institution,
                    email=email,
                    waec_registration_number=waec_registration_number,
                    matric_number=matric_number,
                    gender=gender,
                    date_of_birth=date_of_birth or None,
                    country=country or None,
                    state=state or None,
                    local_government_area=local_government_area or None,
                    postal_code=postal_code or None,
                    street_address=street_address or None,
                )
            except ValueError as exc:
                st.error(str(exc))
                return
            clear_app_caches()
            st.success("Biodata updated. Face samples were not changed.")
            st.rerun()


def authenticate_candidate_panel(role: str, candidate: dict[str, object]) -> None:
    candidate_id = str(candidate["candidate_id"])
    with st.expander("Candidate authentication", expanded=True):
        if candidate.get("enrolment_status") not in {"face_enrolled", "authenticated"}:
            st.error("This candidate has not completed guided face enrolment.")
            return

        st.caption("Face authentication is inactive until started. This prevents the browser from opening the camera on page load.")
        auth_state_key = f"auth_camera_active_{candidate_id}"
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("Start face authentication", key=f"start_auth_{candidate_id}"):
                st.session_state[auth_state_key] = True
                st.rerun()
        with col_stop:
            if st.button("Stop authentication camera", key=f"stop_auth_{candidate_id}", disabled=not st.session_state.get(auth_state_key)):
                st.session_state[auth_state_key] = False
                st.rerun()

        if not st.session_state.get(auth_state_key):
            st.info("Camera is off. Start face authentication when the candidate is ready.")
            auth_image = None
        else:
            inject_auth_overlay()
            auth_image = st.camera_input("Authentication face capture", key=f"auth_{candidate_id}")
        if auth_image:
            try:
                from src.authentication.face_verifier import verify_face_against_enrolment
                from src.vision.face_quality import mirror_image_bytes

                result = verify_face_against_enrolment(candidate_id, mirror_image_bytes(auth_image.getvalue()))
            except ValueError as exc:
                st.error(str(exc))
                return
            if result["matched"]:
                from src.storage.candidate_repository import update_enrolment_status

                st.session_state.authenticated_candidate_id = candidate_id
                st.session_state[auth_state_key] = False
                update_enrolment_status(candidate_id, "authenticated")
                clear_app_caches()
                log_audit(role, "authentication_passed", candidate_id, f"confidence={result['confidence']}")
                st.success(f"Authenticated with confidence {result['confidence']}.")
            else:
                st.error(f"Authentication failed. Confidence {result['confidence']}: {result['message']}")

        if has_permission(role, "start_session"):
            with st.expander("Staff override"):
                st.caption("Prototype override for viva/demo only. It must not replace biometric authentication in production.")
                if st.button("Authorize session start by staff override"):
                    st.session_state.authenticated_candidate_id = candidate_id
                    st.session_state[auth_state_key] = False
                    log_audit(role, "authentication_override_recorded", candidate_id, "Staff authorized session start by override.")
                    st.warning("Staff override enabled for this candidate session.")


def inject_auth_overlay() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stCameraInput"] {
            --capture-guide-text: "Authentication";
            --capture-guide-arrow: "CENTER";
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    return_to_top()


def camera_stream_foundation_panel(role: str, session_id: str, candidate_id: str) -> None:
    session = get_cached_session(session_id)
    mode = str(session.get("monitoring_mode") if session else "B")
    required_roles = required_camera_roles(mode)
    devices = discover_camera_devices()
    primary_devices = [device for device in devices if device.role_hint == "primary"]
    secondary_devices = [device for device in devices if device.role_hint == "secondary"]

    with st.container(border=True):
        st.markdown("#### Dual-Camera Stream Foundation")
        st.caption(
            "Camera slots are browser-managed and no camera opens on page load. "
            "This panel records camera/system events through the common evidence-event schema."
        )
        col_primary, col_secondary, col_mode = st.columns(3)
        with col_primary:
            st.metric("Primary camera", "Required" if "primary" in required_roles else "Not Required")
        with col_secondary:
            st.metric("Secondary camera", "Required" if "secondary" in required_roles else "Not Required")
        with col_mode:
            st.metric("Monitoring mode", f"Mode {mode}")

        selected_primary = st.selectbox(
            "Primary camera slot",
            [device.label for device in primary_devices],
            key=f"camera_primary_slot_{session_id}",
        )
        secondary_labels = [device.label for device in secondary_devices]
        if "secondary" not in required_roles:
            secondary_labels = ["Not required for selected mode"] + secondary_labels
        selected_secondary = st.selectbox(
            "Secondary camera slot",
            secondary_labels,
            key=f"camera_secondary_slot_{session_id}",
        )

        primary_connected = st.checkbox(
            "Primary stream ready",
            value=True,
            key=f"camera_primary_ready_{session_id}",
        )
        secondary_connected = st.checkbox(
            "Secondary stream ready",
            value="secondary" in required_roles,
            disabled="secondary" not in required_roles,
            key=f"camera_secondary_ready_{session_id}",
        )

        statuses = evaluate_camera_streams(
            mode=mode,
            primary_connected=primary_connected,
            secondary_connected=secondary_connected,
            primary_label=selected_primary,
            secondary_label=selected_secondary,
        )
        status_cols = st.columns(2)
        for index, status in enumerate(statuses):
            with status_cols[index]:
                st.metric(status.label, status.display_state)
                st.caption(status.detail)

        if has_permission(role, "generate_demo_events"):
            col_record, col_note = st.columns([1, 2])
            with col_record:
                if st.button("Record camera readiness events", key=f"record_camera_readiness_{session_id}"):
                    for status in statuses:
                        event = camera_status_event(session_id, candidate_id, status)
                        save_event(event)
                        log_audit(role, "camera_status_event_recorded", event.event_id, f"{event.camera_id}:{event.event_type}")
                    clear_app_caches()
                    st.success("Camera readiness events saved to SQLite.")
                    st.rerun()
            with col_note:
                st.caption("Readiness events are persisted for event-stream continuity and later fusion/orchestration use.")

            with st.expander("Manual camera health event hooks", expanded=False):
                st.caption("These hooks simulate stream health events without object detection or malpractice decisions.")
                health_options = {
                    "Primary stream disconnected": (
                        "primary",
                        "camera_stream_disconnected",
                        "Primary camera stream disconnected during monitoring.",
                    ),
                    "Primary stream restored": (
                        "primary",
                        "camera_stream_restored",
                        "Primary camera stream was restored.",
                    ),
                    "Secondary stream disconnected": (
                        "secondary",
                        "camera_stream_disconnected",
                        "Secondary camera stream disconnected during monitoring.",
                    ),
                    "Secondary stream restored": (
                        "secondary",
                        "camera_stream_restored",
                        "Secondary camera stream was restored.",
                    ),
                }
                selected_health = st.selectbox("Camera health event", list(health_options), key=f"camera_health_select_{session_id}")
                if st.button("Generate camera health event", key=f"generate_camera_health_{session_id}"):
                    camera_id, event_type, description = health_options[selected_health]
                    event = manual_camera_health_event(session_id, candidate_id, camera_id, event_type, description)
                    save_event(event)
                    if event_type in {"camera_stream_disconnected", "camera_stream_missing"}:
                        alert = st.session_state.fusion_engine.ingest(event)
                        if alert:
                            save_alert(alert)
                    log_audit(role, "camera_health_event_generated", event.event_id, f"{event.camera_id}:{event.event_type}")
                    clear_app_caches()
                    st.success(f"Saved {event_type.replace('_', ' ')} event for {camera_id} camera.")
                    st.rerun()
        else:
            st.info("Your role can view camera stream status but cannot generate camera events.")

        camera_events = [
            event
            for event in cached_events(session_id)
            if str(event.get("source_module")) in {"primary_camera", "secondary_camera", "system_health"}
            and str(event.get("event_type", "")).startswith("camera_")
        ]
        st.write("Persisted camera/system events")
        if camera_events:
            st.dataframe(pd.DataFrame(camera_events), use_container_width=True, hide_index=True)
        else:
            st.info("No camera/system events have been recorded for this session yet.")


def monitoring_panel(role: str, session_id: str | None) -> None:
    st.subheader("Live Monitoring and Demo Events")
    if not session_id:
        st.info("Start or select a session to generate monitoring events.")
        return
    candidate_id = str(st.session_state.get("active_candidate_id"))
    camera_stream_foundation_panel(role, session_id, candidate_id)

    if has_permission(role, "generate_demo_events"):
        col1, col2 = st.columns(2)
        with col1:
            preset = st.selectbox("Visual/identity event", list(VISUAL_EVENT_PRESETS), key="monitoring_visual_event")
            if st.button("Generate selected event"):
                event = create_demo_visual_event(session_id, candidate_id, preset)
                save_event(event)
                alert = st.session_state.fusion_engine.ingest(event)
                if alert:
                    save_alert(alert)
                clear_app_caches()
                st.success("Structured event generated and fused.")
        with col2:
            if st.button("Generate background speech event"):
                event = create_background_speech_event(session_id, candidate_id)
                save_event(event)
                alert = st.session_state.fusion_engine.ingest(event)
                if alert:
                    save_alert(alert)
                clear_app_caches()
                st.success("Audio event generated and fused.")
    else:
        st.info("Your role cannot generate demo monitoring events.")

    events = cached_events(session_id)
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True)
    return_to_top()


def alert_review_panel(role: str, session_id: str | None) -> None:
    st.subheader("Fused Alerts and Human Review")
    if not session_id:
        st.info("Select a session to review alerts.")
        return

    alerts = cached_alerts(session_id)
    if not alerts:
        st.info("No fused alerts yet.")
        return

    st.dataframe(pd.DataFrame(alerts), use_container_width=True)
    if has_permission(role, "review_alerts"):
        alert_ids = [str(alert["alert_id"]) for alert in alerts]
        alert_id = st.selectbox("Alert to review", alert_ids, key="review_alert_select")
        decision = st.selectbox("Decision", ["accepted", "rejected", "escalated"], key="review_decision_select")
        comment = st.text_area("Reviewer comment")
        if st.button("Submit reviewer decision"):
            record_review(alert_id, role, decision, comment)
            clear_app_caches()
            st.success("Reviewer decision recorded.")
    else:
        st.info("Only Admin or Reviewer roles can submit final alert decisions.")
    return_to_top()


def reports_panel(role: str, session_id: str | None) -> None:
    st.markdown('<span id="top"></span>', unsafe_allow_html=True)
    st.subheader("Reports")
    sessions = cached_sessions()
    events = cached_events()
    alerts = cached_alerts()
    candidates = cached_candidates()

    with st.container(border=True):
        st.write("Smart filters")
        candidate_labels = ["All candidates"] + [f"{candidate['full_name']} ({candidate['candidate_id']})" for candidate in candidates]
        selected_candidate = st.selectbox("Candidate", candidate_labels, key="report_candidate_filter")
        session_labels = ["All sessions"] + [f"{session['session_id']} - {session['candidate_id']} - {session['session_status']}" for session in sessions]
        default_session_index = 0
        if session_id:
            for index, label in enumerate(session_labels):
                if str(session_id) in label:
                    default_session_index = index
                    break
        selected_session = st.selectbox("Session", session_labels, index=default_session_index, key="report_session_filter")
        col1, col2 = st.columns(2)
        with col1:
            risk_levels = ["All risk levels"] + sorted({str(alert["risk_level"]) for alert in alerts if alert.get("risk_level")})
            selected_risk = st.selectbox("Risk level", risk_levels, key="report_risk_filter")
            event_types = ["All event types"] + sorted({str(event["event_type"]) for event in events if event.get("event_type")})
            selected_event_type = st.selectbox("Event type", event_types, key="report_event_type_filter")
        with col2:
            review_statuses = ["All review statuses"] + sorted({str(alert["review_status"]) for alert in alerts if alert.get("review_status")})
            selected_review = st.selectbox("Review status", review_statuses, key="report_review_filter")
            date_range = st.date_input("Date range", value=(), key="report_date_filter")

    selected_candidate_id = None if selected_candidate == "All candidates" else selected_candidate.split("(")[-1].rstrip(")")
    selected_session_id = None if selected_session == "All sessions" else selected_session.split(" - ")[0]

    filtered_events = filter_report_rows(events, selected_candidate_id, selected_session_id, selected_event_type, None, date_range, "timestamp")
    filtered_alerts = filter_report_rows(alerts, selected_candidate_id, selected_session_id, None, selected_risk, date_range, "start_time")
    if selected_review != "All review statuses":
        filtered_alerts = [alert for alert in filtered_alerts if str(alert.get("review_status")) == selected_review]

    st.write("Table 1: Filtered Events")
    if filtered_events:
        st.dataframe(pd.DataFrame(filtered_events), use_container_width=True)
    else:
        st.info("No events match the selected filters.")

    st.write("Table 2: Filtered Fused Alerts")
    if filtered_alerts:
        st.dataframe(pd.DataFrame(filtered_alerts), use_container_width=True)
    else:
        st.info("No fused alerts match the selected filters.")

    export_session_id = selected_session_id or session_id
    if export_session_id and has_permission(role, "export_reports") and st.button("Export selected session JSON report"):
        path = export_session_report_json(export_session_id)
        st.success(f"Report exported to {path}")
    elif not export_session_id:
        st.caption("Select a specific session to export a JSON session report.")
    else:
        st.caption("Report export is available to Admin and Reviewer roles.")
    return_to_top()


def filter_report_rows(
    rows: list[dict[str, object]],
    candidate_id: str | None,
    session_id: str | None,
    event_type: str | None,
    risk_level: str | None,
    date_range: object,
    date_field: str,
) -> list[dict[str, object]]:
    filtered = rows
    if candidate_id:
        filtered = [row for row in filtered if str(row.get("candidate_id")) == candidate_id]
    if session_id:
        filtered = [row for row in filtered if str(row.get("session_id")) == session_id]
    if event_type and event_type != "All event types":
        filtered = [row for row in filtered if str(row.get("event_type")) == event_type]
    if risk_level and risk_level != "All risk levels":
        filtered = [row for row in filtered if str(row.get("risk_level")) == risk_level]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = [
            row
            for row in filtered
            if row.get(date_field)
            and start_date.isoformat() <= str(row.get(date_field))[:10] <= end_date.isoformat()
        ]
    return filtered


def main() -> None:
    apply_theme()
    st.markdown('<span id="top"></span>', unsafe_allow_html=True)
    role, page = selected_role_and_page()
    if page == "Home":
        home_page()
        render_footer()
        return

    render_hero()
    if page == "Enrolment":
        candidate_management(role)
    elif page == "Candidate Profiles":
        candidate_profiles_page(role)
    elif page == "Session":
        session_control(role)
    elif page == "Test Player":
        mock_test_player()
    session_id = st.session_state.get("active_session_id")
    if page == "Monitoring":
        monitoring_panel(role, session_id)
    elif page == "Review":
        alert_review_panel(role, session_id)
    elif page == "Reports":
        reports_panel(role, session_id)
    render_footer()


if __name__ == "__main__":
    main()
