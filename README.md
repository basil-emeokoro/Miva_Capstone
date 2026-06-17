# Explainable Multi-Modal Proctoring Prototype

Local-first capstone prototype for secure remote-proctored assessments in Nigeria.

Platform identity: SERPS - Secure Explainable Remote Proctoring System.

The system demonstrates candidate enrolment, consent capture, monitoring-mode selection, mock assessment delivery, structured event generation, explainable event fusion, role-aware human review, and report export.

## Core Principle

AI modules do not punish candidates. Detection modules generate evidence events, the Event Fusion Engine assigns explainable risk, and a human reviewer makes the final decision.

## Prototype Features

- Candidate registration and consent capture
- Prototype guided face enrolment metadata
- Admin, Human Proctor, and Reviewer RBAC
- Mode A, B, and C monitoring configuration
- Lightweight mock assessment/test player
- Demo visual, identity, and audio event generation
- Rule-based Event Fusion Engine
- Explainable fused alerts
- Reviewer accept/reject/escalate workflow
- JSON session report export
- SQLite local storage

## Run Locally

```powershell
pip install -r requirements.txt
python main.py
python -m streamlit run app.py --server.port 8502
```

## Known Limitations

- This is not a production-grade proctoring platform.
- Camera previews are user-triggered only. This preserves browser privacy and prevents camera activation on page load.
- Pre-exam device checks are prototype confirmations. Primary/secondary camera checks can use explicit Streamlit camera previews; microphone, lighting, candidate presence, environment declaration, and mirror placement are manual staff confirmations.
- Streamlit does not provide a built-in local microphone test equivalent to `st.camera_input`, so microphone readiness is represented as a manual prototype check.
- Streamlit tabs eagerly default to the first tab and do not provide full routed-page behaviour, so this prototype uses sidebar-controlled page navigation and session-state wizard steps for cleaner flow control.
- Face recognition is implemented for enrolment/authentication, while advanced voice verification and object detection remain represented through prototype event flows.
- The mock assessment is not a full exam engine.
- RBAC is local prototype authorization only.
- SQLite is used for local demonstration.

## Monitoring Modes and Pre-Exam Checks

- Mode A - single-camera CBT mode: requires primary camera, microphone, lighting, candidate presence, and environment declaration. Secondary camera and mirror are not required.
- Mode B - dual-camera full mode: requires primary camera, secondary camera, microphone, lighting, candidate presence, and environment declaration. Mirror is not required.
- Mode C - mirror-assisted low-resource mode: requires primary camera, microphone, lighting, candidate presence, environment declaration, and mirror placement. Secondary camera is not required.

## Public Documentation

- `docs/development_log.md` records implementation progress and limitations.
- `docs/system_architecture.md` summarizes the prototype architecture.
