from __future__ import annotations

import hashlib
import pandas as pd
import streamlit as st
import numpy as np

from src.audio.audio_event_detector import create_background_speech_event
from src.enrolment.auto_capture import ai_auto_capture
from src.enrolment.consent_manager import CONSENT_NOTICE, capture_consent
from src.enrolment.face_enrolment import (
    FACE_DIRECTIONS,
    captured_directions,
    is_face_enrolment_complete,
    list_face_samples,
    record_face_sample,
)
from src.authentication.face_verifier import verify_face_against_enrolment
from src.fusion.fusion_engine import FusionEngine
from src.reporting.session_report import export_session_report_json
from src.review import record_review
from src.security.access_control import Role, has_permission
from src.security.audit_logger import log_audit
from src.session.environment_checker import CHECK_LABELS, device_check_allows_session_start, evaluate_device_checks
from src.session.exam_controller import grade_answers, load_sample_questions
from src.session.monitoring_mode_controller import MonitoringModeController
from src.session.session_manager import list_sessions, start_session
from src.storage.candidate_repository import (
    list_candidate_custom_fields,
    list_candidates,
    register_candidate,
    save_candidate_custom_fields,
)
from src.storage.database import initialize_database
from src.storage.device_check_repository import latest_device_check, save_device_check
from src.storage.event_repository import list_alerts, list_events, save_alert, save_event
from src.utils.file_utils import candidate_enrolment_dir, write_bytes
from src.utils.geodata import COUNTRIES, NIGERIA_LGAS, NIGERIA_STATES
from src.vision.face_quality import assess_face_capture, extract_face_embedding, mirror_image_bytes
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
        st.session_state.custom_fields = [{"label": "Custom Reference", "type": "Text", "applies_to": "Generic", "value": ""}]
    active_enrolment_candidate = st.session_state.get("enrolment_candidate_id")
    if st.session_state.enrolment_step == "profile" and not _candidate_face_complete(active_enrolment_candidate):
        st.session_state.enrolment_step = "register"

    render_enrolment_steps()
    if st.session_state.enrolment_step == "register":
        registration_wizard(role)
    elif st.session_state.enrolment_step == "face":
        guided_face_enrolment()
    else:
        profile_candidate_id = st.session_state.get("profile_candidate_id") or st.session_state.get("enrolment_candidate_id")
        candidate_profile_browser(str(profile_candidate_id) if profile_candidate_id else None)


def candidate_profile_browser(default_candidate_id: str | None = None) -> None:
    candidates = list_candidates()
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
    render_candidate_profile(candidate_id)


def candidate_profiles_page(role: str) -> None:
    st.subheader("Candidate Profiles")
    candidates = list_candidates()
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

    search = st.text_input("Search candidate profiles", key=f"candidate_profiles_search_{role}", placeholder="Type name, Student ID, or Candidate ID")
    visible_candidates = _filter_candidates(visible_candidates, search)
    if not visible_candidates:
        st.warning("No candidate profile matches your search.")
        return

    labels = [f"{candidate['full_name']} ({candidate['candidate_id']})" for candidate in visible_candidates]
    selected = st.selectbox("Candidate", labels, key=f"candidate_profiles_select_{role}")
    candidate_id = selected.split("(")[-1].rstrip(")")
    render_candidate_profile(candidate_id, include_images=role == Role.ADMIN.value)


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


def render_enrolment_steps() -> None:
    col_register, col_face, col_profile = st.columns(3)
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
            candidate_identifier = st.text_input("Candidate ID (10 digits)", "1234567001")
            st.caption("WAEC Candidate ID = 7-digit centre number + 3-digit candidate number.")
            waec_registration_number = st.text_input("Candidate Registration Number", "WAEC/REG/2026-A1")
            matric_number = ""
            programme = ""
            department = ""
        elif institution_type == "Miva":
            institution = st.text_input("Institution", "Miva Open University")
            candidate_identifier = st.text_input("Student ID (digits only)", "10000001")
            matric_number = st.text_input("Matric Number", "MIVA/CSC/2026/001")
            programme = st.selectbox("Programme", ["Undergraduate", "Postgraduate"], key="miva_programme")
            department = st.text_input("Department", "Computer Science")
            waec_registration_number = ""
        else:
            institution = st.text_input("Institution", "Demo Institution")
            candidate_identifier = st.text_input("Candidate ID", "CAND-DEMO-001")
            waec_registration_number = ""
            matric_number = ""
            programme = ""
            department = ""
        email = st.text_input("Email", "candidate@example.com")
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
        submitted = st.form_submit_button("Register candidate and continue")

    if submitted:
        if not consent:
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
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        save_candidate_custom_fields(candidate_id, custom_values)
        capture_consent(candidate_id)
        st.session_state.enrolment_candidate_id = candidate_id
        st.session_state.enrolment_step = "face"
        st.success(f"Candidate registered: {candidate_id}. Proceeding to guided face capture.")
        st.rerun()


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

    assessment = assess_face_capture(image_bytes, direction)
    if not assessment["accepted"]:
        st.error(str(assessment["message"]))
        return

    file_path = candidate_enrolment_dir(candidate_id) / f"{direction}.jpg"
    embedding_path = candidate_enrolment_dir(candidate_id) / f"{direction}_embedding.npy"
    write_bytes(file_path, image_bytes)
    embedding = extract_face_embedding(image_bytes, direction)
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
        st.success("Accepted and saved. Guided facial enrolment is complete.")
    else:
        st.success(f"Accepted and saved {direction_label}. Loading the next capture...")
    st.rerun()


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
    candidates = list_candidates()
    st.subheader("Session Control")
    st.caption("Staff RBAC controls Admin, Human Proctor, and Reviewer access. Candidates are not RBAC users; they authenticate separately through their enrolment profile.")
    if not candidates:
        st.warning("Register a candidate before starting a session.")
        return None

    candidate_options = {f"{c['full_name']} ({c['candidate_id']})": c for c in candidates}
    selected = st.selectbox("Candidate", list(candidate_options), key="session_candidate_select")
    candidate = candidate_options[selected]
    candidate_id = str(candidate["candidate_id"])
    candidate_profile_summary(candidate_id)

    mode_options = {
        "Mode B - dual-camera full mode": "B",
        "Mode A - single-camera CBT mode": "A",
        "Mode C - mirror-assisted low-resource mode": "C",
    }
    selected_mode_label = st.selectbox("Monitoring mode", list(mode_options), key="session_monitoring_mode")
    mode = mode_options[selected_mode_label]
    plan = MonitoringModeController().configure(mode)
    render_monitoring_mode_card(plan)
    st.caption(plan.confidence_note)
    device_ready = pre_exam_device_check_panel(role, candidate_id, mode)

    authenticate_candidate_panel(role, candidate)

    authenticated = st.session_state.get("authenticated_candidate_id") == candidate_id
    if not authenticated:
        st.warning("Authenticate this enrolled candidate before starting a session.")
    if not device_ready:
        st.warning("Pre-exam device and environment checks must pass, or a staff override must be recorded, before session start.")

    can_start = authenticated and device_ready
    if has_permission(role, "start_session") and st.button("Start prototype session", disabled=not can_start):
        session_id = start_session(candidate_id, candidate_id, mode)
        log_audit(role, "session_started", session_id, f"candidate_id={candidate_id}; monitoring_mode={mode}")
        st.session_state.active_session_id = session_id
        st.session_state.active_candidate_id = candidate_id
        st.success(f"Started session {session_id}")

    sessions = list_sessions()
    if sessions:
        session_labels = [f"{s['session_id']} - {s['candidate_id']} - {s['session_status']}" for s in sessions]
        chosen = st.selectbox("Active/reporting session", session_labels, key="active_reporting_session")
        session_id = chosen.split(" - ")[0]
        st.session_state.active_session_id = session_id
        st.session_state.active_candidate_id = next(s["candidate_id"] for s in sessions if s["session_id"] == session_id)
        return session_id
    return None


def render_monitoring_mode_card(plan) -> None:
    st.markdown(
        f"""
        <div class="status-card">
            <strong>Monitoring Mode {plan.mode}</strong><br>
            Enabled: {", ".join(plan.enabled_modules)}<br>
            Disabled: {", ".join(plan.disabled_modules) if plan.disabled_modules else "None"}
        </div>
        """,
        unsafe_allow_html=True,
    )


def pre_exam_device_check_panel(role: str, candidate_id: str, mode: str) -> bool:
    st.subheader("Pre-Exam Device and Environment Check")
    st.caption("Checks are stored in SQLite, shown here as dashboard status cards, and logged in the audit trail. This panel does not open the camera automatically.")

    latest_check = latest_device_check(candidate_id, mode)
    if latest_check:
        render_device_status_cards(latest_check)
    else:
        st.info("No saved device check for this candidate and monitoring mode yet.")

    can_manage_check = has_permission(role, "start_session")
    if not can_manage_check:
        st.warning("Only Admin or Human Proctor can record pre-exam checks or overrides.")
        return device_check_allows_session_start(latest_check)

    with st.form(f"device_check_{candidate_id}_{mode}"):
        required = set(evaluate_device_checks(mode, {}).required_checks)
        st.write("Record check results")
        col_a, col_b = st.columns(2)
        values: dict[str, bool] = {}
        for index, (check_name, label) in enumerate(CHECK_LABELS.items()):
            target = col_a if index % 2 == 0 else col_b
            with target:
                help_text = "Required for selected monitoring mode." if check_name in required else "Optional for selected monitoring mode."
                values[check_name] = st.checkbox(
                    label,
                    value=latest_check_allows(latest_check, check_name),
                    disabled=check_name not in required,
                    help=help_text,
                    key=f"{candidate_id}_{mode}_{check_name}_check",
                )
        submitted = st.form_submit_button("Save pre-exam check")

    if submitted:
        evaluation = evaluate_device_checks(mode, values)
        check_id = save_device_check(candidate_id, evaluation, role)
        log_audit(role, "device_check_saved", check_id, f"candidate_id={candidate_id}; mode={mode}; status={evaluation.overall_status}")
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
                st.warning(f"Device-check override recorded: {check_id}.")
                st.rerun()

    return device_check_allows_session_start(latest_device_check(candidate_id, mode))


def latest_check_allows(latest_check: dict[str, object] | None, check_name: str) -> bool:
    if not latest_check:
        return False
    return latest_check.get(f"{check_name}_status") == "passed"


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
    st.caption(f"Latest check: {check['check_id']} | Mode {check['monitoring_mode']} | Checked by {check['checked_by']} at {check['checked_at']}")


def candidate_profile_summary(candidate_id: str) -> None:
    with st.expander("View enrolled candidate profile", expanded=False):
        render_candidate_profile(candidate_id)


def render_candidate_profile(candidate_id: str, include_images: bool = False) -> None:
    candidates = {str(candidate["candidate_id"]): candidate for candidate in list_candidates()}
    candidate = candidates.get(candidate_id)
    if not candidate:
        st.info("Candidate profile not found.")
        return

    samples = list_face_samples(candidate_id)
    custom_fields = list_candidate_custom_fields(candidate_id)
    captured = captured_directions(candidate_id)
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
    ]
    visible_identifier_rows = [row for row in identifier_rows if row["value"]]
    if visible_identifier_rows:
        st.write("Institutional and demographic details")
        st.dataframe(pd.DataFrame(visible_identifier_rows), use_container_width=True)
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
                        st.image(str(image_path), caption=str(sample["capture_direction"]), use_container_width=True)


def authenticate_candidate_panel(role: str, candidate: dict[str, object]) -> None:
    candidate_id = str(candidate["candidate_id"])
    with st.expander("Candidate authentication", expanded=True):
        if candidate.get("enrolment_status") != "face_enrolled":
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
                result = verify_face_against_enrolment(candidate_id, mirror_image_bytes(auth_image.getvalue()))
            except ValueError as exc:
                st.error(str(exc))
                return
            if result["matched"]:
                st.session_state.authenticated_candidate_id = candidate_id
                st.session_state[auth_state_key] = False
                st.success(f"Authenticated with confidence {result['confidence']}.")
            else:
                st.error(f"Authentication failed. Confidence {result['confidence']}: {result['message']}")

        if has_permission(role, "start_session"):
            with st.expander("Staff override"):
                st.caption("Prototype override for viva/demo only. It must not replace biometric authentication in production.")
                if st.button("Authorize session start by staff override"):
                    st.session_state.authenticated_candidate_id = candidate_id
                    st.session_state[auth_state_key] = False
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


def monitoring_panel(role: str, session_id: str | None) -> None:
    st.subheader("Live Monitoring and Demo Events")
    if not session_id:
        st.info("Start or select a session to generate monitoring events.")
        return
    candidate_id = str(st.session_state.get("active_candidate_id"))

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
        alert_id = st.selectbox("Alert to review", alert_ids, key="review_alert_select")
        decision = st.selectbox("Decision", ["accepted", "rejected", "escalated"], key="review_decision_select")
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

    tabs = st.tabs(["Enrolment", "Candidate Profiles", "Session", "Test Player", "Monitoring", "Review", "Reports"])
    with tabs[0]:
        candidate_management(role)
    with tabs[1]:
        candidate_profiles_page(role)
    with tabs[2]:
        session_id = session_control(role)
    with tabs[3]:
        mock_test_player()
    session_id = st.session_state.get("active_session_id")
    with tabs[4]:
        monitoring_panel(role, session_id)
    with tabs[5]:
        alert_review_panel(role, session_id)
    with tabs[6]:
        reports_panel(role, session_id)


if __name__ == "__main__":
    main()
