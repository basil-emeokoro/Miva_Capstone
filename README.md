# Explainable Multi-Modal Proctoring Prototype

Local-first capstone prototype for secure remote-proctored assessments in Nigeria.

Platform identity: SERPS - Secure Explainable Remote Proctoring System.

The system demonstrates candidate enrolment, consent capture, monitoring-mode selection, mock assessment delivery, structured event generation, contextual intelligence, role-aware human review, and report export.

## Core Principle

AI modules do not punish candidates. Detection modules generate evidence events, the Contextual Intelligence Engine assigns explainable risk through event fusion, temporal memory, contextual reasoning, and risk scoring. A human reviewer makes the final decision.

## Prototype Features

- Candidate registration and consent capture
- Prototype guided face enrolment metadata
- Draft registration and duplicate-enrolment validation
- Admin, Human Proctor, and Reviewer RBAC
- Mode A, B, and C monitoring configuration
- Dual-camera stream status foundation using common event schema
- Visual intelligence event foundation for face, camera, gaze/head-pose, person-count, and object-related evidence events
- Live-detection integration foundation with OpenCV frame analysis, optional MediaPipe/YOLO-ready adapters, modular audio event definitions, and a FastAPI structured-event boundary
- Lightweight mock assessment/test player
- Demo visual, identity, and audio event generation
- Contextual Intelligence Engine with Event Fusion Module, Temporal Behaviour Memory, Risk Scoring Engine, Contextual Reasoning Module, and Explainability Interface
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
6. The Contextual Intelligence Engine produces explainable contextual/fused alerts.
7. The Agentic AI orchestration foundation prioritises and routes the alerts.
8. Human reviewer accepts, rejects, or escalates the alert.
9. A session report is generated.

## Run Locally

```powershell
pip install -r requirements.txt
python main.py
python -m streamlit run app.py --server.port 8502
```

Optional detector adapters can be installed separately when the local Python environment supports them:

```powershell
pip install ultralytics mediapipe
```

## Known Limitations

- This is not a production-grade proctoring platform.
- The app now lazy-loads heavier face-processing modules behind user-triggered camera actions and caches short-lived read-only lists for candidates, sessions, events, alerts, audit records, and the logo. Streamlit still reruns scripts after widget interaction, so large local databases may require pagination in a production build.
- Camera previews are user-triggered only. This preserves browser privacy and prevents camera activation on page load.
- Dual-camera management currently records browser-managed camera slots and stream-health events. It does not open or continuously stream cameras on page load.
- Pre-exam device checks are prototype confirmations. Primary/secondary camera checks can use explicit Streamlit camera previews; microphone, lighting, candidate presence, environment declaration, and mirror placement are manual staff confirmations.
- Streamlit does not provide a built-in local microphone test equivalent to `st.camera_input`, so microphone readiness is represented as a manual prototype check.
- Streamlit tabs eagerly default to the first tab and do not provide full routed-page behaviour, so this prototype uses sidebar-controlled page navigation and session-state wizard steps for cleaner flow control.
- On Windows/Python 3.13, Streamlit's Uvicorn runtime may emit a benign `WinError 10054` asyncio disconnect traceback when a browser/client pipe closes. SERPS installs a narrow Windows-only guard for that specific shutdown noise; FastAPI services are not started inside the Streamlit dashboard.
- Streamlit `st.camera_input` is not ideal for continuous AI-guided face movement detection and automatic pose capture. Production-grade capture should use `streamlit-webrtc`, a FastAPI/WebSocket + OpenCV video stream, or a dedicated React/WebRTC frontend so face landmarks can be inspected continuously and valid left/right/up/down/centre poses can be auto-captured.
- Face recognition is implemented for enrolment/authentication, while advanced voice verification and object detection remain represented through prototype event flows.
- OpenCV still-frame analysis is active for user-uploaded evidence. MediaPipe and YOLO are optional local adapters at this milestone; if unavailable, SERPS continues to use structured prototype hooks rather than failing at startup.
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
- Camera events use the common evidence-event schema and are ready for Contextual Intelligence Engine ingestion.
- Streamlit remains the UI/control shell for dashboards, manual prototype hooks, review, and report preview. It is not the real monitoring engine.
- Continuous monitoring should be driven later by service boundaries such as FastAPI endpoints, OpenCV/background workers, `streamlit-webrtc`, WebRTC/browser streams, or an external secure exam-player integration.

## Visual Intelligence Foundation

- The Monitoring page exposes visual intelligence controls for face presence, face absence, face obstruction, camera obstruction, multiple persons, looking away, head movement anomaly, mobile phone, and unauthorised object events.
- Manual/prototype hooks generate structured visual events using the common `EvidenceEvent` schema and persist them in SQLite.
- Optional still-image upload analysis performs local OpenCV face/camera obstruction checks without opening the browser camera.
- Uploaded frames now pass through a service-style visual analysis pipeline that can emit face status, head-pose/gaze-position signals, and optional YOLO object evidence when the local YOLO stack is available.
- The vision module generates evidence only. It does not classify malpractice or make final decisions.
- Continuous visual monitoring remains a service-layer responsibility for later OpenCV, FastAPI, background worker, `streamlit-webrtc`, WebRTC, or secure exam-player integration.

## Live AI Detection Integration Foundation

- Visual detectors remain perception-only and emit `EvidenceEvent` objects for CIE ingestion.
- OpenCV provides the current local face/camera obstruction analysis.
- MediaPipe and YOLO are treated as optional live-AI adapters. They are not loaded on page startup and must be invoked behind user-triggered controls or service workers.
- Audio intelligence now defines structured events for background speech, prolonged speech, abnormal silence, environmental noise, and suspicious audio patterns. Whisper, WebRTC VAD, Silero VAD, or equivalent detectors can be substituted later without changing the CIE contract.
- `src/services/event_api.py` introduces a FastAPI structured-event API boundary so future camera/audio workers, secure exam players, or edge services can submit events without coupling inference to Streamlit.
- Streamlit remains an operations dashboard and demo control surface. It is not the monitoring engine.

## Contextual Intelligence Engine

Addenda 3 and 4 elevate the previous Event Fusion Engine into a broader Contextual Intelligence Engine (CIE). This is a controlled refinement, not an architectural redesign. The Event Fusion Module remains visible as a CIE subcomponent.

- The CIE reads immutable raw `EvidenceEvent` records from SQLite and correlates them within configurable windows such as 5, 10, or 30 seconds.
- The Event Fusion Module provides prototype rules for primary-camera avoidance, possible third-party assistance, unauthorised presence, reduced monitoring confidence, and high-risk behavioural patterns.
- Temporal Behaviour Memory distinguishes isolated events from persistent patterns across recent monitoring windows.
- The Risk Scoring Engine computes continuous confidence-based current and rolling risk scores.
- Contextual/fused alerts store contributing events, contributing modules, current risk score, rolling risk score, risk trend, confidence, explanation, recommended reviewer action, and reasoning trace.
- Raw evidence events are not overwritten. Fused alerts are separate review objects for human-supervised decision-making.
- The Monitoring page exposes CIE status, current/rolling risk, trend, contributing modules, explanation preview, and recent contextual/fused alerts.
- The Monitoring page now presents a viva-ready CIE console showing evidence flow, live event timeline, contextual correlation, explainability, and reviewer recommendation before technical audit tables.
- A CIE Demo/Test Scenarios panel supports Groups A-J for camera, visual, audio, multimodal fusion, false-positive suppression, explanation, temporal memory, duplicate suppression, report reconciliation, and review-boundary validation.
- Temporal window sensitivity can be demonstrated using 30-second, 2-minute, and 5-minute windows.
- Reports expose raw events, contextual/fused alerts, risk timeline, temporal behaviour summary, and contributing-module summaries.
- The Review page presents CIE-generated alerts as explainable cases with supporting raw events before reviewer accept/reject/escalate decisions.
- The CIE is independent of Streamlit and can be called from future FastAPI services, background workers, a secure exam player, or unit tests.
- SERPS detects observable risk indicators. It must not be presented as a raw-video cheating classifier or an automatic misconduct decision system.

## Monitoring Roadmap

The Monitoring module is still a controlled prototype. Future implementation should support single-candidate view, grouped candidate/session view, multi-session analytics, visual dashboards, flagged-candidate classification, event distribution, risk-level summaries, reviewer/proctor queues, and Agentic AI prioritisation of infringements.

## Public Documentation

- `docs/development_log.md` records implementation progress and limitations.
- `docs/system_architecture.md` summarizes the prototype architecture.
