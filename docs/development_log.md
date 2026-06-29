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

## Dual-Camera Management and Event Stream Foundation

- Added a camera discovery abstraction that exposes safe browser-managed primary and secondary camera slots without opening camera hardware.
- Added monitoring-mode-aware camera requirements: Mode A and Mode C require primary camera only, while Mode B requires primary and secondary cameras.
- Added a camera stream status model with `ready`, `missing`, `disconnected`, and `not_required` states.
- Added camera readiness status cards and manual stream-health event hooks on the Monitoring page.
- Exposed the camera foundation directly in Monitoring through an active/reporting session selector, monitoring-mode display, primary/secondary selectors, requirement indicators, status cards, readiness events, missing-camera events, disconnected-camera events, and a recent camera/system events table.
- Persisted camera/system events through the common SQLite `events` table using the shared evidence-event schema.
- Prepared missing/disconnected camera events for Contextual Intelligence Engine ingestion while keeping camera modules advisory only.
- Preserved the privacy rule that no camera opens on page load.
- Documented that Streamlit is only the dashboard/control surface. Continuous dual-camera monitoring should move to service boundaries such as `streamlit-webrtc`, FastAPI/OpenCV, background workers, WebRTC/browser streams, or secure exam-player event ingestion.

## Computer Vision Intelligence Foundation

- Added modular vision files for face presence analysis, prototype head-pose signalling, object-detection hooks, and visual evidence-event creation.
- Added required visual event types: `face_present`, `face_absent`, `face_obstructed`, `camera_obstructed`, `multiple_persons_detected`, `looking_away`, `head_movement_anomaly`, `mobile_phone_detected`, and `unauthorised_object_detected`.
- Exposed a Visual Intelligence Foundation panel in Monitoring with selected session context, primary/secondary camera context, manual visual event hooks, optional still-image face analysis, and recent visual events.
- Persisted visual events through the common SQLite `events` table using the shared `EvidenceEvent` schema so Reports and the Contextual Intelligence Engine can consume them.
- Preserved the rule that no camera opens on page load; real continuous visual analysis remains a future service-layer integration.
- Kept visual intelligence advisory only. Human review remains responsible for final decisions.

## Multi-Modal Event Fusion Engine Foundation

- Extended the fusion engine into a Streamlit-independent intelligence layer that can correlate persisted SQLite evidence events across configurable time windows.
- Added modular prototype rules for primary-camera avoidance, possible third-party assistance, unauthorised presence, reduced monitoring confidence, and high-risk behavioural patterns.
- Added duplicate suppression by event signature, weighted confidence aggregation, current risk score, rolling risk score, risk trend, risk-level classification, contributing modules, and reasoning trace.
- Migrated the `fused_alerts` table with confidence, current/rolling score, risk trend, contributing modules, and reasoning trace fields while keeping raw evidence events immutable.
- Exposed risk score, trend, explanation preview, recent fused alerts, and a user-triggered stored-event fusion action in Monitoring.
- Updated Reports to show raw events, fused alerts, fusion timeline, risk trend, and contributing-module summaries.
- Updated Review so human reviewers inspect explainable fused alerts and supporting raw events rather than isolated event rows only.
- Preserved the rule that fusion does not make final misconduct decisions; it prepares explainable risk assessments for human review and later orchestration.

## Contextual Intelligence Engine Refinement

- Adopted the Contextual Intelligence Engine (CIE) as the primary SERPS reasoning layer following Addenda 3 and 4.
- Preserved the existing Event Fusion Engine work as the CIE Event Fusion Module instead of deleting or duplicating useful logic.
- Added CIE submodules for Event Fusion, Temporal Behaviour Memory, Risk Scoring, Contextual Reasoning, and Explainability Interface.
- Added temporal behaviour memory summaries so CIE can distinguish isolated events from persistent behavioural patterns.
- Added contextual risk adjustment hooks that consider event frequency, module diversity, persistent behaviour, and a future reviewer-feedback placeholder.
- Updated Monitoring wording to show CIE status while keeping the Event Fusion Module visible as a subcomponent.
- Updated Review and Reports wording to use CIE-generated contextual/fused alerts, risk timeline, and temporal behaviour summaries.
- Updated architecture documentation to show the revised pipeline: Sensors, Detection Modules, Structured Event Generation, CIE, Agentic Decision Support, Human Reviewer, Final Decision.

## CIE Monitoring Console and Scenario Validation

- Refined the Monitoring page so the CIE section presents a viva-ready reasoning flow: evidence, contextual reasoning, risk score, explanation, and reviewer recommendation.
- Added top-level CIE cards for current session, current risk, risk trend, confidence, and reviewer recommendation.
- Added a live evidence timeline, contextual correlation chips, reviewer-friendly explanation panel, and recommendation panel while keeping raw events and contextual/fused alert tables as expandable technical details.
- Added CIE Demo/Test Scenarios A-J for camera events, visual events, audio events, multimodal fusion, false-positive suppression, explanation completeness, temporal memory, duplicate suppression, report reconciliation, and review-boundary validation.
- Added temporal window sensitivity support for 30-second, 2-minute, and 5-minute windows.
- Expanded unit tests for isolated-event suppression, repeated-event escalation, multimodal escalation, duplicate suppression, temporal-window sensitivity, explanation completeness, reviewer recommendation, and raw-event immutability.

## Live AI Detection Integration Foundation

- Began replacing manual-only visual/audio event generation with service-ready detector modules that still emit only structured `EvidenceEvent` records.
- Extended OpenCV face analysis so decoded frames can be analysed without opening camera hardware and can provide face box/frame metadata for prototype head-pose signalling.
- Added a visual frame-analysis pipeline that can emit face presence/absence/obstruction, camera obstruction, head-pose/gaze-position, and optional object-detection events from a single uploaded frame.
- Added a lazy optional YOLO adapter for mobile-phone and unauthorised-object evidence. The adapter does not load on page startup and returns a clean unavailable diagnostic when the local YOLO stack/model is absent.
- Added modular audio event definitions for background speech, prolonged speech, abnormal silence, environmental noise, and suspicious audio patterns, keeping Whisper/WebRTC VAD/Silero VAD replaceable behind the same event contract.
- Added a FastAPI structured-event API boundary so future OpenCV, MediaPipe, YOLO, audio, WebRTC, or exam-player services can submit events without coupling inference to Streamlit.
- Updated Monitoring so uploaded still images can run through the visual analysis pipeline and audio events can be selected from the modular audio event set.
- Preserved the camera privacy rule: no camera opens on page load, and Streamlit remains the operations dashboard rather than the inference engine.

## CIE Monitoring UI Refinement

- Replaced the CIE Live Event Stream HTML renderer with native Streamlit containers, columns, metrics, captions, and dividers so raw HTML source is never displayed to the panel.
- Updated CIE display metrics so older contextual alerts without stored confidence/current-score values derive coherent confidence and risk display values from contributing raw evidence.
- Made reviewer recommendation labels dynamic from risk level: Low = Observe, Medium = Warn, High = Escalate, Critical = Immediate Human Review.
- Reworked contextual correlation into grouped evidence sections for camera health, visual intelligence, audio intelligence, object detection, identity, and system evidence while preserving technical tables in expanders.

## Windows Runtime Compatibility

- Investigated repeated `ConnectionResetError: [WinError 10054]` tracebacks during local Streamlit execution on Windows/Python 3.13.
- Confirmed the dashboard does not import or start the FastAPI structured-event service during Streamlit startup; the `Uvicorn server started` message comes from the Streamlit runtime.
- Added a Windows-only asyncio compatibility guard that suppresses only the benign `_ProactorBasePipeTransport._call_connection_lost` `WinError 10054` disconnect traceback. Other connection errors continue to propagate normally.
- Documented the issue as a harmless browser/client disconnect or shutdown warning when it occurs during Streamlit/Uvicorn transport cleanup.

## AI Capability Integration Sprint 1

- Preserved the frozen SERPS architecture and kept the CIE unchanged as the contextual reasoning layer.
- Strengthened the perception layer so visual, object, audio, and identity components emit only structured `EvidenceEvent` records.
- Extended coarse head-pose signalling with direction metadata derived from detected face position. This remains a lightweight signal until MediaPipe/WebRTC landmark tracking is introduced.
- Expanded the optional YOLO adapter to map mobile phones, laptops/tablets, books/documents, headphones/earpieces, and suspicious handheld objects into visual evidence events. YOLO remains lazy-loaded and optional.
- Added feature-window audio analysis for future Whisper, WebRTC VAD, Silero VAD, or equivalent services. It can emit voice activity, background speech, prolonged speech, abnormal silence, environmental noise, and suspicious audio pattern evidence.
- Added identity assurance evidence generation for periodic verification, low identity confidence, face mismatch, unknown face, and candidate substitution signals.
- Extended the FastAPI structured-event boundary with `/vision/analyse-frame`, `/audio/analyse-features`, and `/identity/analyse-confidence` endpoints.
- Updated Monitoring with explicit Live AI and Demonstration/Simulation modes for visual and audio evidence. Live AI remains user-triggered and does not open cameras or microphones automatically.
- Detection modules still do not compute misconduct decisions or bypass CIE; reviewers remain the final decision-makers.

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
6. Contextual Intelligence Engine generates explainable contextual/fused alerts.
7. Agentic AI orchestration foundation prioritises and routes alert actions.
8. Human reviewer accepts, rejects, or escalates.
9. Report is generated for the session.

## Institutional Policy and Incident Management Foundation

- Added the Institutional Policy & Incident Management Engine as a governance layer after Agentic Decision Support and before Human Review, preserving the frozen SERPS architecture.
- Added policy-as-code configuration in `config/institutional_policies.json` for WAEC, University/Miva, and Generic incident workflows.
- Added SQLite persistence for policy decisions, candidate incident acknowledgements, and reviewer incident actions.
- Added a candidate Incident Acknowledgement Form in the mock Test Player for policies that require assessment pause and candidate explanation.
- Added Review-page IPIME controls showing agent priority, selected institutional workflow, acknowledgement requirement, notification target, and preserved evidence status.
- Added reviewer incident actions: Observe, Continue Monitoring, Issue Warning, Escalate, Refer to Senior Reviewer, and Close Incident.
- Added incident evidence-package JSON export in Reports with candidate/session metadata, contextual risk, contributing events, candidate acknowledgement, reviewer action, and audit reference note.
- Candidate-facing wording avoids misconduct conclusions and preserves due process: the system reports a potential examination integrity concern for authorised human review.

## End-to-End Viva Scenario Validation

- Added a controlled viva scenario validation harness that exercises the frozen governance pipeline end to end without introducing a new reasoning layer.
- Added 10 evaluation scenarios covering normal candidate behaviour, brief gaze deviation, repeated gaze deviation, mobile-phone evidence, background speech, multiple persons, repeated face absence, identity mismatch, suspicious camera disconnection, and a critical combined multimodal incident.
- Each scenario persists raw evidence events, invokes the existing Contextual Intelligence Engine, invokes Agentic Decision Support, evaluates IPIME policy-as-code, and stores expected-vs-actual validation output.
- Monitoring now exposes scenario selection, scenario execution, generated evidence, CIE risk/explanation, Agentic priority, IPIME response, candidate acknowledgement capture where required, reviewer action, and scenario evidence-package export.
- Reports now include a Viva Scenario Validation Summary table for Chapter 5 evaluation and viva demonstration records.
- Added pytest coverage for low-risk behaviour, isolated-event suppression, repeated-event escalation, multimodal escalation, critical acknowledgement workflow, IPIME human-review boundary, acknowledgement persistence, reviewer decision persistence, and summary traceability.
- Scenario wording and records remain validation traces only; they must not be presented as production cheating labels or final misconduct determinations.

## Final Polish Sprint

- Preserved the frozen SERPS architecture and avoided new architecture or scope expansion.
- Improved the Monitoring viva scenario panel with a visible governance pipeline trace covering structured evidence, CIE, Agentic Decision Support, IPIME, candidate acknowledgement, human review, and report/audit trace.
- Strengthened reviewer workflow wording so reviewer decisions are framed as human procedural outcomes, require rationale, and do not imply automatic misconduct findings.
- Clarified candidate acknowledgement as a due-process response to a potential examination integrity concern rather than an admission or system verdict.
- Expanded session JSON reports with policy decisions, viva scenario validation records, evidence-package manifest entries, due-process notes, and human-review boundary language.
- Added focused pytest coverage for governance-aware session report contents.
- Confirmed camera inputs remain behind explicit capture, preview, or authentication controls; no camera opens on Home/page load.

## Prototype Limitations

- Face recognition, voice verification, camera feeds, and YOLO detection are represented by prototype/demo event flows at this stage.
- Streamlit supports browser camera capture through `st.camera_input`, but the app keeps camera activation user-triggered for privacy. Streamlit does not provide an equivalent built-in microphone probe, so microphone readiness is recorded as a manual prototype confirmation.
- Streamlit's browser camera input is not designed for continuous AI-guided pose tracking and automatic capture. The future path is `streamlit-webrtc`, FastAPI/WebSocket + OpenCV backend streaming, or a dedicated React/WebRTC frontend for continuous landmark inspection, left/right/up/down/centre pose validation, auto-capture, and automatic progression to the next direction.
- Streamlit has limited native page-routing and wizard primitives. The prototype uses sidebar navigation, session state, and collapsed summary panels to approximate routed pages and wizard progression.
- The test player is intentionally lightweight and is not a production examination engine.
- RBAC is local prototype authorization, not enterprise identity management.
- Monitoring remains a prototype module. Future work should add single-candidate view, grouped candidate/session view, multiple session analytics, visual dashboards, flagged candidate classification, event distribution, risk summary, reviewer/proctor queue, and Agentic AI prioritisation of infringements.

## Repository Discipline

- The repository should contain SERPS implementation code, software architecture documentation, tests, runtime configuration, README content, and development documentation only.
- Private thesis/report drafting guidance should remain outside the tracked implementation repository unless explicitly approved for publication.
- Private dissertation-writing guidance, chapter revision notes, and report-preparation drafts are ignored to prevent accidental commits.

## Documentation Automation Framework Sprint 1

- Added a documentation automation foundation that supports SERPS as a capstone prototype with reproducible dissertation artefacts, without changing the frozen architecture.
- Added `scripts/docs/package_dissertation_assets.py` as the single command for rebuilding implementation-derived dissertation artefacts.
- Created `docs/dissertation/` with Chapter Three, Chapter Four, Chapter Five, captions, and manifest output areas.
- Generated editable Mermaid sources for high-level architecture, layered architecture, system workflow, use case, activity, sequence, ERD, system flowchart, and API interaction model.
- Generated the ERD from the implemented SQLite schema in `src/storage/database.py`.
- Exported FastAPI OpenAPI JSON from `src/services/event_api.py`.
- Exported the viva scenario catalog from `src/evaluation/viva_scenarios.py`.
- Added caption JSON/Markdown outputs and a manifest containing SERPS version, Git commit, generation timestamp, generating script, checksums, and documented limitations.
- Mermaid SVG/PNG rendering is optional and depends on local Mermaid CLI availability. When `mmdc` is absent, the pipeline records the limitation and preserves editable sources rather than fabricating figures.
- Private `Dissertation-Requirements.docx` and `Dissertation-Requirements.pdf` remain ignored and untracked.

## Milestone Tagging

- Introduced annotated Git milestone tags for traceable dissertation and viva baselines.
- `v1.0.0-feature-complete` marks the feature-complete SERPS implementation before documentation automation.
- `v1.1.0-documentation-framework` marks the Documentation Automation Framework foundation commit.
- Milestone tags are used to identify reproducible implementation states for dissertation figures, Chapter 4/5 evidence, viva rehearsals, and future release packaging.

## Documentation Automation Framework Sprint 1 Extension

- Extended the dissertation asset pipeline without changing SERPS architecture or adding new runtime features.
- Added OpenAPI endpoint summary generation alongside the full OpenAPI JSON export.
- Added Chapter Four screenshot and test-evidence planning outputs so the framework knows what to capture without fabricating screenshots or logs.
- Added Chapter Five evaluation artefacts derived from the implemented viva scenario catalog: scenario summary JSON, risk-distribution CSV, policy-response CSV, and risk-distribution SVG.
- Added a grouped asset index and richer manifest metadata including chapter, figure, description, environment, and package metadata.
- Added `docs/dissertation/dissertation_assets.zip` packaging for generated dissertation artefacts.
- Expanded pytest coverage to verify the package, asset index, OpenAPI summary, screenshot plan, scenario summary, chart output, and manifest package checksum.

## Viva Demonstration and Live Dual-Camera Validation

- Added `docs/viva_demo_plan.md` with remote viva demonstration guidance, opening statement, architecture defence, research contributions, limitation boundaries, fallback plan, and production frontend roadmap.
- Added `docs/viva_question_bank.md` with grouped viva questions and concise model answers across motivation, literature, methodology, architecture, CIE, explainability, Agentic AI, IPIME, identity, vision, audio, Streamlit, FastAPI, privacy, limitations, and future work.
- Added a controlled OpenCV live dual-camera validation module in `src/camera/live_camera_validator.py`.
- Monitoring now includes an explicit live dual-camera capability test: physical camera discovery, primary/secondary selection, side-by-side labelled frame previews, FPS/resolution/status display, and structured camera events that feed the existing CIE.
- The privacy rule remains intact: physical cameras are not opened on page load; discovery and validation require explicit user action and release selected devices after sampling.
- Added pytest coverage using fake camera captures so live camera validation logic remains testable without hardware in CI.

## Release Candidate Live Proctoring Demonstration Hardening

- Added a viva split-screen demonstration mode in Monitoring to show a candidate-facing exam view beside a reviewer/proctor intelligence view.
- Candidate view shows identity, mock exam context, timer, authentication/monitoring status, and due-process incident acknowledgement when IPIME requires it. It does not expose CIE internals, risk scores, policy rules, or reviewer decisions.
- Reviewer/proctor view shows the governance pipeline, CIE risk/confidence/recommendation, primary/secondary camera evidence status, recent event timeline, explainability, IPIME response, and reviewer action capture.
- Extended live dual-camera validation so explicitly sampled physical camera frames can be encoded and passed into visual detector modules.
- Live sampled frames can now generate stream-health evidence and detector-derived visual evidence before ingestion by the Contextual Intelligence Engine.
- Optional secondary object detection remains guarded behind an explicit control and continues gracefully if the local YOLO adapter/model is unavailable.
- Manual demonstration/simulation controls remain available and labelled as fallback controls for viva reliability.
- The architecture remains unchanged: hardware and detectors produce structured evidence only; CIE reasons over evidence; Agentic Decision Support recommends; IPIME applies procedure; human reviewers decide.

## Candidate-Facing Phone Policy Response

- Added candidate-facing primary-camera phone evidence types: `candidate_facing_phone_detected`, `phone_towards_screen_detected`, `possible_screen_capture_attempt`, and `repeated_phone_visibility`.
- Primary-camera YOLO phone detections are mapped to candidate-facing phone evidence, while secondary-camera detections remain room-facing `mobile_phone_detected` evidence.
- Extended institutional policy-as-code with configurable candidate-facing phone actions, including temporary screen shield, acknowledgement, warning, escalation, and review routing depending on institution and event type.
- Added a prototype screen shield to the candidate Test Player and viva split-screen candidate view. The shield protects exam content only when IPIME policy actions require it and uses due-process wording.
- The pipeline remains unchanged: detector evidence -> CIE -> Agentic Decision Support -> IPIME -> optional screen shield/acknowledgement -> Human Reviewer -> Report.
