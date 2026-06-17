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

## Prototype Limitations

- Face recognition, voice verification, camera feeds, and YOLO detection are represented by prototype/demo event flows at this stage.
- Streamlit supports browser camera capture through `st.camera_input`, but the app keeps camera activation user-triggered for privacy. Streamlit does not provide an equivalent built-in microphone probe, so microphone readiness is recorded as a manual prototype confirmation.
- Streamlit has limited native page-routing and wizard primitives. The prototype uses sidebar navigation, session state, and collapsed summary panels to approximate routed pages and wizard progression.
- The test player is intentionally lightweight and is not a production examination engine.
- RBAC is local prototype authorization, not enterprise identity management.
