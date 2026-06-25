# SERPS Technical Readiness Report

Date: 2026-06-25  
Baseline implementation commit verified before this report: `0d284a1 ai: integrate live perception modules with contextual intelligence engine`

## Verification Snapshot

- `python -m py_compile app.py`: passed.
- `python -m pytest -q`: passed, `53 passed` after IPIME foundation tests were added.
- Streamlit startup smoke test: HTTP `200` on local probe.
- Startup warnings/tracebacks: no deprecated `use_container_width` warning observed; no Windows `WinError 10054` traceback observed in captured startup log.
- Camera on page load: no camera activation path is invoked at startup. Camera/image analysis remains user-triggered.

## Subsystem Readiness

| # | Subsystem | Current status | What works now | Limited or simulated | Evidence | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Enrolment and consent | Implemented | Candidate biodata, institution-aware fields, consent capture, draft/registered statuses, and biodata-before-face-capture gate are in place. | Prototype role simulator is not enterprise login. | `app.py`, `src/storage/candidate_repository.py`, `tests/test_candidate_repository.py` | Keep stable; add final validation polish only if viva testing exposes form issues. |
| 2 | Guided facial enrolment | Partially Implemented | Multi-direction capture workflow, saved face samples, quality records, and profile evidence display exist. | Continuous AI-guided pose auto-capture is limited by Streamlit camera input; current flow remains user-triggered. | `src/enrolment/face_enrolment.py`, `src/vision/face_quality.py`, `tests/test_face_enrolment.py` | Move continuous capture to WebRTC/FastAPI/OpenCV service after viva-critical modules. |
| 3 | Duplicate enrolment prevention | Partially Implemented | Duplicate Student/Candidate ID, email, matric/registration constraints are handled cleanly; prototype face duplicate support is documented. | Full production-grade biometric duplicate search remains limited. | `src/storage/candidate_repository.py`, `tests/test_candidate_repository.py` | Strengthen face-similarity duplicate scan when identity sprint resumes. |
| 4 | Candidate profiles | Implemented | Searchable candidate list, profile display, biodata, institution details, face records, and role-aware visibility are available. | Candidate self-service is represented inside one local prototype dashboard. | `app.py`, `src/storage/candidate_repository.py` | Keep stable; add pagination only if data volume grows. |
| 5 | Authentication | Partially Implemented | Candidate authentication gate, face verification against enrolment templates, staff override, and audit logging exist. | Authentication is still local prototype face verification, not enterprise biometric/liveness infrastructure. | `app.py`, `src/authentication/face_verifier.py`, `tests/test_face_verifier.py` | Strengthen continuous identity assurance and liveness checks. |
| 6 | Pre-exam device/environment checks | Implemented | Mode-aware checks, SQLite persistence, last-saved check display, override, audit trail, and session gating are implemented. | Device checks are partly manual confirmations; microphone probing is simulated. | `app.py`, `src/environment/device_checker.py`, `tests/test_environment_checker.py` | Keep stable; later replace manual confirmations with backend probes. |
| 7 | Monitoring Mode Controller | Implemented | Modes A, B, and C drive camera/check requirements and dashboard guidance. | Mode behaviour is prototype policy logic, not institutional policy integration. | `src/monitoring/mode_controller.py`, `tests/test_monitoring_mode_controller.py` | Keep stable as the governing mode contract for AI services. |
| 8 | Dual-camera management | Partially Implemented | Primary/secondary camera slots, mode-aware requirement cards, readiness events, health events, and persistence are visible in Monitoring. | Browser camera discovery/continuous dual streams are not live yet; no automatic camera activation. | `src/camera/camera_stream.py`, `app.py`, `tests/test_camera_stream.py` | Next camera sprint should connect OpenCV/WebRTC stream adapters. |
| 9 | Visual intelligence | Partially Implemented | OpenCV still-frame face/camera obstruction analysis, face presence/absence events, multiple persons where detectable, and coarse head-position signals exist. | Real continuous gaze/pose tracking is not yet live; MediaPipe landmarks are future integration. | `src/vision/face_detector.py`, `src/vision/head_pose_estimator.py`, `src/vision/visual_event_detector.py`, `tests/test_visual_event_detector.py` | Integrate MediaPipe face landmarks or OpenCV stream worker. |
| 10 | Object detection / YOLO adapter | Partially Implemented | Optional lazy YOLO adapter maps mobile phone, laptop/tablet, book/document, headphones/earpiece, and handheld-object evidence. | YOLO package/model may be absent; no continuous object stream yet. | `src/vision/object_detector.py`, `src/vision/visual_event_detector.py` | Add installation profile and service-worker endpoint for real frame streams. |
| 11 | Audio intelligence | Partially Implemented | Structured audio events and feature-window analysis support voice activity, background speech, prolonged speech, abnormal silence, noise, and suspicious patterns. | No live microphone capture; features are supplied manually or via future service. | `src/audio/audio_event_detector.py`, `tests/test_audio_event_detector.py` | Add WebRTC VAD/Silero adapter behind FastAPI. |
| 12 | Identity assurance | Partially Implemented | Periodic identity evidence events support verified, low confidence, mismatch, unknown face, and substitution signals. | Continuous identity tracking and liveness remain future work. | `src/authentication/identity_event_detector.py`, `tests/test_identity_event_detector.py` | Connect face verifier output to periodic monitoring service. |
| 13 | Behavioural analytics | Prototype/Simulation | CIE scenario controls and event hooks can simulate repeated looking away, face absence, and suspicious patterns. | No dedicated behavioural model or keystroke/mouse analytics yet. | `app.py`, `tests/test_contextual_intelligence_engine.py` | Implement lightweight behavioural event producer after live visual/audio inputs mature. |
| 14 | Structured event generation | Implemented | Common immutable `EvidenceEvent` schema is used by camera, visual, audio, identity, and API ingestion. | Event taxonomy will grow as detectors mature. | `src/fusion/event_schema.py`, `src/storage/event_repository.py`, multiple tests | Keep schema stable; add versioning if external clients expand. |
| 15 | FastAPI service boundary | Partially Implemented | Structured event API plus `/vision/analyse-frame`, `/audio/analyse-features`, and `/identity/analyse-confidence` endpoints exist. | FastAPI is not launched automatically with Streamlit and is not yet a long-running AI worker. | `src/services/event_api.py`, `tests/test_event_api.py` | Add service runner/docs and connect external detector workers. |
| 16 | Contextual Intelligence Engine | Implemented | CIE wraps fusion, temporal memory, risk scoring, contextual reasoning, and explainability; Monitoring shows viva-ready CIE console. | Rule-based prototype; ML/probabilistic fusion remains future work. | `src/contextual_intelligence/*`, `app.py`, `tests/test_contextual_intelligence_engine.py` | Keep frozen; tune rules only with test scenarios and reviewer feedback. |
| 17 | Temporal Behaviour Memory | Implemented | Repeated patterns and temporal-window sensitivity are tested and visible through CIE scenarios. | Memory is windowed/rule-based, not long-term behavioural modelling. | `src/contextual_intelligence/temporal_behaviour_memory.py`, tests | Add session-level summaries for final reports. |
| 18 | Risk Scoring Engine | Implemented | Current/rolling score, risk level, trend, duplicate suppression, and confidence aggregation are in place. | Thresholds are prototype-configured; not institution-calibrated. | `src/contextual_intelligence/risk_scoring_engine.py`, `src/fusion/fusion_engine.py`, tests | Preserve; calibrate thresholds during final demo scenario testing. |
| 19 | Explainability Interface | Implemented | Alerts include explanations, reasoning trace, contributing events/modules, confidence, and human-review boundary. | Explanations are rule-based, not SHAP/LIME. | `src/contextual_intelligence/explainability_interface.py`, `app.py`, tests | Keep; improve wording for final technical report. |
| 20 | Agentic Decision Support | Prototype/Simulation | Orchestration foundation recommends workflow actions and is documented in the CIE pipeline. | Full task routing/escalation automation is not yet implemented as a rich module. | `src/orchestration/agentic_orchestrator.py`, docs | Continue feeding agent output into IPIME policy workflows. |
| 21 | Human review workflow | Partially Implemented | Review page exposes CIE-generated alerts, explanation, supporting events, decision status, and reviewer actions. | Workflow is local prototype; no multi-reviewer queue or secure login. | `app.py`, `src/storage/event_repository.py` | Improve reviewer queue and decision audit after agent sprint. |
| 22 | Reports/export | Partially Implemented | Reports show filters, raw events, contextual alerts, risk timeline, temporal summary, and JSON export. | Formal PDF/Word technical reports and richer charts remain future work. | `app.py`, docs | Add final viva export template and incident summary. |
| 23 | Privacy/security/audit | Partially Implemented | Consent, camera privacy rule, audit trail, immutable raw events, local-first SQLite, and role simulator warnings are implemented. | No production authentication, encryption-at-rest, RBAC provider, or retention automation. | `app.py`, `src/storage/*`, `README.md` | Document clearly in Chapter 4/5; add minimal retention/privacy notes to final report. |
| 24 | Streamlit dashboard | Implemented | Home, navigation, SERPS branding, staged enrolment/session flows, Monitoring CIE console, Review, Reports, and footer are operational. | Streamlit is not suitable as the real monitoring engine for continuous camera/audio streams. | `app.py`, README, smoke test | Keep as operations dashboard; move inference into services. |
| 25 | Viva/demo readiness | Partially Implemented | End-to-end demo flow exists: enrol, authenticate, check devices, start session, generate/live-analyse events, CIE reasoning, review, report. | Live continuous AI is still partial; manual fallback remains necessary for reliability. | `README.md`, `docs/development_log.md`, tests | Run scripted demo rehearsals and seed clean data before viva. |

## Remaining Critical Gaps Before Viva

1. Continuous camera/audio monitoring is not yet live; current live AI is user-triggered through uploaded frames and feature windows.
2. MediaPipe landmark-based gaze/head-pose tracking is not yet integrated.
3. YOLO depends on optional local package/model availability and is not yet exercised through continuous frames.
4. Audio has no real microphone/VAD stream yet.
5. Identity assurance has event producers, but not a periodic background verification loop.
6. Agentic Decision Support is still a foundation, not a rich proctor workflow coordinator.
7. Reports are useful for prototype validation but not yet polished as final viva/incident report documents.

## Recommended Next Implementation Sprint

Recommended next sprint: **Live Visual Stream Adapter + MediaPipe Landmark Foundation**.

Post-report governance update: IPIME foundation has been added after this readiness baseline. It introduces configurable institutional policy workflows, candidate acknowledgement, reviewer incident actions, and structured evidence-package export without changing the frozen CIE reasoning layer.

Scope:

- Add a backend-safe frame processing adapter that can accept frames without Streamlit owning the camera loop.
- Integrate MediaPipe face landmarks where available for gaze/head-pose signals.
- Keep OpenCV fallback for environments where MediaPipe is unavailable.
- Emit only `EvidenceEvent` records for face present/absent, looking away, head movement anomaly, face obstruction, and camera obstruction.
- Preserve manual demo controls as fallback.

This is the highest-impact next step because visual perception is the most visible viva proof that SERPS is moving from simulation toward live AI evidence generation.

## Streamlit Limitation Risks

- Streamlit reruns the script after widget interaction, which is not ideal for continuous monitoring loops.
- `st.camera_input` is user-triggered and not designed for continuous AI-guided pose tracking.
- Streamlit has no built-in microphone stream suitable for real VAD.
- Multi-session live monitoring can become slow if large tables/images render on every rerun.

Workaround:

- Keep Streamlit as dashboard/control surface.
- Use FastAPI, OpenCV workers, WebRTC/browser clients, or `streamlit-webrtc` for continuous stream capture and event generation.
- Render only summaries by default; keep large tables in expanders.

## Where FastAPI Is Already Useful

- `src/services/event_api.py` provides a clean service boundary for external detectors.
- Generic `/events` accepts already-structured evidence.
- `/vision/analyse-frame` can analyse a supplied image frame and persist visual evidence.
- `/audio/analyse-features` converts VAD/STT-style features into evidence.
- `/identity/analyse-confidence` converts periodic identity confidence into evidence.
- These endpoints keep future AI workers independent of Streamlit and preserve the CIE contract.

## Where Real AI Detection Still Needs Strengthening

- MediaPipe or equivalent landmarks for real gaze/head-pose.
- Continuous OpenCV/WebRTC camera worker.
- YOLO model installation/profile and object-detection test images.
- VAD/microphone adapter for background speech, silence, and prolonged speech.
- Periodic identity verification loop using enrolled templates.
- Behavioural analytics beyond repeated-event simulation.

## Prototype Limitations for Chapter 4/5

- SERPS is a local-first research prototype, not a production proctoring service.
- Streamlit is used for dashboard and demonstration, not as a production monitoring engine.
- Camera and audio live detection are partially implemented and service-ready, but not yet continuous in the browser.
- YOLO, MediaPipe, Whisper/Silero/WebRTC VAD are optional or future-strengthened integrations depending on local environment.
- The system generates observable risk indicators and explainable recommendations; it does not decide misconduct.
- Prototype RBAC is a role simulator, not enterprise authentication.
- SQLite is acceptable for prototype evidence persistence but should be replaced with hardened storage for deployment.
- Human reviewer decision remains final.
