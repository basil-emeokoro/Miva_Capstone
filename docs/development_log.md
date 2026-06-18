# Development Log

## Phase 1-4 Foundation

- Initialized local Git repository.
- Added prototype RBAC, test player, and sample demo questions.
- Added local-first configuration in `config.yaml`.
- Added SQLite schema for candidates, consent, enrolment, sessions, events, fused alerts, reviewer decisions, and audit logs.
- Added prototype RBAC for Admin, Human Proctor, and Reviewer roles.
- Added monitoring mode controller for Mode A, Mode B, and Mode C.
- Added structured event and fused alert schemas.
- Added rule-based risk scoring, explanation generation, and Agentic AI orchestration foundation.
- Added lightweight mock test player with sample questions.
- Added Streamlit dashboard shell.

## Pre-Exam Device and Environment Check Refinement

- Refined Session Control into a staged workflow: candidate selection, monitoring mode, pre-exam checks, authentication, and session start.
- Added Mode A, Mode B, and Mode C guidance with mode-specific required checks.
- Added one-click required-check selection for the selected monitoring mode.
- Added optional visible prototype checks. Camera previews are only opened after an explicit user action; microphone, lighting, candidate presence, environment declaration, and mirror placement are manual prototype confirmations.
- Added latest saved device-check visibility from SQLite, including check ID, mode, timestamp, staff user, overall status, and override status.
- Added recent audit-trail visibility for authentication, overrides, device checks, session approval, session start, and session end events.
- Added active/ended/all session filtering and an end-session action to reduce repeated-testing clutter.

## Navigation and UX Refinement

- Replaced eager top-tab navigation with sidebar-controlled page navigation so the app opens to a Home landing page by default.
- Added a Home page with SERPS identity, module summary cards, academic prototype warning, and human-in-the-loop reminder.
- Refined Enrolment so candidate registration fields remain hidden until "Register New Candidate" is selected.
- Refined Candidate Profiles so profile details render only after search and explicit selection.
- Converted Session Control into a session-state wizard where only the active step is expanded and completed steps collapse into summaries.
- Added report filters for candidate, session, risk level, review status, date range, and event type, plus a Return to Top link.
- Added a subtle SERPS footer across application pages.
- Expanded the prototype test player to 15 questions covering remote proctoring, event fusion, explainable AI, identity assurance, privacy-aware monitoring, and human review.

## Enrolment Integrity and Access-Model Refinement

- Added repository-level validation for candidate/student identifiers, email address format, Miva matric number, and WAEC registration number before SQLite insertion.
- Added clean duplicate-handling paths so existing candidates can be viewed or pending face capture can be continued instead of exposing raw SQLite tracebacks.
- Added draft biodata support with status progression: `draft`, `registered_pending_face_capture`, `face_enrolled`, and `authenticated`.
- Kept guided face capture locked until a persisted candidate record exists and registration/consent has moved past draft state.
- Added profile review details for biodata, institution-specific identifiers, address, consent status, face-capture direction labels, quality scores, and image previews.
- Added a controlled biodata edit panel that updates demographic and institution metadata without touching enrolled face samples.
- Added a prototype duplicate-face guard by comparing new capture embeddings against existing saved enrolment templates. This is suitable for demonstration only, not a production biometric identity service.
- Relabelled the sidebar role control as a Prototype Role Simulator and documented that production staff roles would come from secure login while candidates would not use the SERPS dashboard.
- Made the footer clearer and centred while preserving the academic prototype tone.

## Load-Time Optimisation Notes

- The app now caches short-lived read-only data for candidates, sessions, events, alerts, audit records, and the SERPS logo.
- Heavier face-processing imports are lazy-loaded behind camera/authentication/capture actions instead of being imported during page load.
- Large tables are not rendered on the Home page, and Candidate Profiles show the list first while full profile evidence waits for explicit selection.
- Streamlit still reruns the script after widget interaction; a production implementation should add server-side pagination and dedicated API endpoints as records grow.

## Viva Demonstration Flow

1. Panel/member acts as Admin or Human Proctor in the SERPS dashboard.
2. Candidate profile is enrolled with biodata, consent, and face samples.
3. Candidate authenticates before session start.
4. Candidate starts the mock assessment.
5. Monitoring module generates normal and suspicious visual/audio/identity events.
6. Event Fusion Engine generates explainable fused alerts.
7. Agentic AI orchestration foundation prioritises and routes alert actions.
8. Human reviewer accepts, rejects, or escalates.
9. Report is generated for the session.

## Prototype Limitations

- Face recognition, voice verification, camera feeds, and YOLO detection are represented by prototype/demo event flows at this stage.
- Streamlit supports browser camera capture through `st.camera_input`, but the app keeps camera activation user-triggered for privacy. Streamlit does not provide an equivalent built-in microphone probe, so microphone readiness is recorded as a manual prototype confirmation.
- Streamlit's browser camera input is not designed for continuous AI-guided pose tracking and automatic capture. The future path is `streamlit-webrtc`, FastAPI/WebSocket + OpenCV backend streaming, or a dedicated React/WebRTC frontend for continuous landmark inspection, left/right/up/down/centre pose validation, auto-capture, and automatic progression to the next direction.
- Streamlit has limited native page-routing and wizard primitives. The prototype uses sidebar navigation, session state, and collapsed summary panels to approximate routed pages and wizard progression.
- The test player is intentionally lightweight and is not a production examination engine.
- RBAC is local prototype authorization, not enterprise identity management.
- Monitoring remains a prototype module. Future work should add single-candidate view, grouped candidate/session view, multiple session analytics, visual dashboards, flagged candidate classification, event distribution, risk summary, reviewer/proctor queue, and Agentic AI prioritisation of infringements.
