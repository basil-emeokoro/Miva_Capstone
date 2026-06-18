# Explainable Multi-Modal Proctoring Prototype

Local-first capstone prototype for secure remote-proctored assessments in Nigeria.

Platform identity: SERPS - Secure Explainable Remote Proctoring System.

The system demonstrates candidate enrolment, consent capture, monitoring-mode selection, mock assessment delivery, structured event generation, explainable event fusion, role-aware human review, and report export.

## Core Principle

AI modules do not punish candidates. Detection modules generate evidence events, the Event Fusion Engine assigns explainable risk, and a human reviewer makes the final decision.

## Prototype Features

- Candidate registration and consent capture
- Prototype guided face enrolment metadata
- Draft registration and duplicate-enrolment validation
- Admin, Human Proctor, and Reviewer RBAC
- Mode A, B, and C monitoring configuration
- Dual-camera stream status foundation using common event schema
- Lightweight mock assessment/test player
- Demo visual, identity, and audio event generation
- Rule-based Event Fusion Engine
- Explainable fused alerts
- Reviewer accept/reject/escalate workflow
- JSON session report export
- SQLite local storage

## Prototype Access Model

The sidebar role selector is a Prototype Role Simulator for viva demonstration only. In production, officials, admins, proctors, and reviewers would access SERPS after secure staff login and role assignment. Candidates would not access the SERPS dashboard; they would use only enrolment/capture and exam authentication workflows, normally through a secure exam browser or test-player integration.

For local demonstration, the same machine may simulate both dashboard staff actions and candidate-facing behaviour.

## Viva Demonstration Flow

1. Panel/member acts as Admin or Proctor in the SERPS dashboard.
2. Candidate biodata is saved, consent is captured, and the face enrolment workflow is completed.
3. Candidate authenticates before session start.
4. Candidate starts the mock assessment.
5. Monitoring modules generate normal and suspicious demo events.
6. The Event Fusion Engine produces explainable fused alerts.
7. The Agentic AI orchestration foundation prioritises and routes the alerts.
8. Human reviewer accepts, rejects, or escalates the alert.
9. A session report is generated.

## Run Locally

```powershell
pip install -r requirements.txt
python main.py
python -m streamlit run app.py --server.port 8502
```

## Known Limitations

- This is not a production-grade proctoring platform.
- The app now lazy-loads heavier face-processing modules behind user-triggered camera actions and caches short-lived read-only lists for candidates, sessions, events, alerts, audit records, and the logo. Streamlit still reruns scripts after widget interaction, so large local databases may require pagination in a production build.
- Camera previews are user-triggered only. This preserves browser privacy and prevents camera activation on page load.
- Dual-camera management currently records browser-managed camera slots and stream-health events. It does not open or continuously stream cameras on page load.
- Pre-exam device checks are prototype confirmations. Primary/secondary camera checks can use explicit Streamlit camera previews; microphone, lighting, candidate presence, environment declaration, and mirror placement are manual staff confirmations.
- Streamlit does not provide a built-in local microphone test equivalent to `st.camera_input`, so microphone readiness is represented as a manual prototype check.
- Streamlit tabs eagerly default to the first tab and do not provide full routed-page behaviour, so this prototype uses sidebar-controlled page navigation and session-state wizard steps for cleaner flow control.
- Streamlit `st.camera_input` is not ideal for continuous AI-guided face movement detection and automatic pose capture. Production-grade capture should use `streamlit-webrtc`, a FastAPI/WebSocket + OpenCV video stream, or a dedicated React/WebRTC frontend so face landmarks can be inspected continuously and valid left/right/up/down/centre poses can be auto-captured.
- Face recognition is implemented for enrolment/authentication, while advanced voice verification and object detection remain represented through prototype event flows.
- Prototype duplicate-face detection compares new face embeddings against saved enrolment templates, but it is not a production biometric de-duplication service.
- The mock assessment is not a full exam engine.
- RBAC is local prototype authorization only.
- SQLite is used for local demonstration.

## Enrolment Integrity

- Miva uses Student ID as the primary institution identifier.
- WAEC uses Candidate ID as the primary institution identifier.
- Email, matric number, WAEC registration number, and candidate/student identifiers are checked before insert to prevent duplicate enrolment.
- SQLite integrity errors are caught and returned as user-facing validation messages rather than raw tracebacks.
- Candidate status may be `draft`, `registered_pending_face_capture`, `face_enrolled`, or `authenticated`.

## Monitoring Modes and Pre-Exam Checks

- Mode A - single-camera CBT mode: requires primary camera, microphone, lighting, candidate presence, and environment declaration. Secondary camera and mirror are not required.
- Mode B - dual-camera full mode: requires primary camera, secondary camera, microphone, lighting, candidate presence, and environment declaration. Mirror is not required.
- Mode C - mirror-assisted low-resource mode: requires primary camera, microphone, lighting, candidate presence, environment declaration, and mirror placement. Secondary camera is not required.

## Dual-Camera Event Foundation

- The Monitoring page exposes primary and secondary camera slots without activating camera hardware.
- Monitoring includes an active/reporting session selector, monitoring-mode display, primary/secondary selectors, requirement cards, readiness status cards, and manual readiness/missing/disconnected event hooks.
- Camera readiness and health events are persisted through the same SQLite `events` table used by visual, audio, identity, and behavioural events.
- Camera events use the common evidence-event schema and are ready for Event Fusion Engine ingestion.
- Streamlit remains the UI/control shell for dashboards, manual prototype hooks, review, and report preview. It is not the real monitoring engine.
- Continuous monitoring should be driven later by service boundaries such as FastAPI endpoints, OpenCV/background workers, `streamlit-webrtc`, WebRTC/browser streams, or an external secure exam-player integration.

## Monitoring Roadmap

The Monitoring module is still a controlled prototype. Future implementation should support single-candidate view, grouped candidate/session view, multi-session analytics, visual dashboards, flagged-candidate classification, event distribution, risk-level summaries, reviewer/proctor queues, and Agentic AI prioritisation of infringements.

## Public Documentation

- `docs/development_log.md` records implementation progress and limitations.
- `docs/system_architecture.md` summarizes the prototype architecture.
