# SERPS Technical Readiness Report

Date: 2026-06-26  
Baseline implementation commit verified before this report: `7351d34 evaluation: add end-to-end viva scenario validation`

## Verification Snapshot

- `python -m py_compile app.py`: passed.
- `python -m pytest -q`: passed, `64 passed` after documentation automation coverage was added.
- Streamlit startup smoke test: HTTP `200` on local probe.
- Startup warnings/tracebacks: no deprecated `use_container_width` warning observed; no Windows `WinError 10054` traceback observed in captured startup log.
- Camera on page load: no camera activation path is invoked at startup. Camera/image analysis remains user-triggered.
- Release candidate hardening update: Monitoring now includes a viva split-screen demonstration mode and the live dual-camera validator can pass explicitly sampled physical camera frames into detector modules to produce structured `EvidenceEvent` records for CIE ingestion.

## Feature Complete Readiness Audit

This audit determines whether SERPS is ready to enter final polish and dissertation artefact automation. It does not introduce new features; it classifies the current implementation against the frozen Version 1.0 architecture.

| # | Area | Readiness classification | Audit finding | Recommended action |
| --- | --- | --- | --- | --- |
| 1 | Enrolment and consent | Ready for viva | Institution-aware biodata, consent capture, draft/registered states, duplicate validation, and biodata-before-face-capture gating are implemented. | Freeze behaviour; polish labels only if final rehearsal exposes wording issues. |
| 2 | Facial enrolment | Needs minor polish | Guided multi-direction capture, stored samples, quality records, and profile display work. Continuous AI-guided auto-capture remains limited by Streamlit camera input. | Keep browser fallback for viva; document WebRTC/FastAPI path for production-grade capture. |
| 3 | Authentication | Needs minor polish | Session start is gated by candidate authentication or explicit staff override. Face verification is functional as a local prototype. | Strengthen liveness and periodic re-authentication after final polish. |
| 4 | Device/environment checks | Ready for viva | Mode-aware checks, SQLite persistence, override, audit, and session gate integration are implemented. | Keep stable; use clean demo records for final viva. |
| 5 | Monitoring Mode Controller | Ready for viva | Modes A, B, and C correctly affect device requirements, camera requirements, and monitoring guidance. | Freeze as the policy contract for monitoring and session checks. |
| 6 | Dual-camera foundation | Ready for viva | Primary/secondary camera selectors, requirement cards, readiness controls, health events, controlled OpenCV physical camera validation, labelled frame previews, persistence, and Reports visibility are implemented without page-load camera activation. Explicitly sampled live frames can now feed detector modules. | Keep manual/prototype hooks available until continuous stream workers are introduced. |
| 7 | Visual intelligence | Needs minor polish | Structured visual events, still-frame analysis, OpenCV fallback, optional object hooks, Monitoring controls, and live sampled-frame detector handoff exist. | Improve continuous MediaPipe/YOLO service integration later; do not change architecture. |
| 8 | Audio intelligence | Needs minor polish | Audio feature analysis and structured audio events exist for background speech, prolonged speech, silence, noise, and suspicious patterns. | Add microphone/VAD integration later through service boundary. |
| 9 | Identity assurance | Needs minor polish | Identity events and authentication confidence signals feed the evidence pipeline. | Add periodic identity worker and stronger substitution checks later. |
| 10 | Structured evidence events | Ready for viva | Camera, visual, audio, identity, scenario, and system events use the common immutable evidence-event schema. | Keep schema stable; add taxonomy entries only when detectors mature. |
| 11 | CIE | Ready for viva | Contextual Intelligence Engine performs fusion, temporal memory, risk scoring, reasoning, explanations, and reviewer recommendations. | Tune wording and thresholds only through controlled scenario tests. |
| 12 | Agentic Decision Support | Ready for viva | Agentic recommendations are generated from contextual risk and passed into the governance workflow. | Keep recommendations advisory; avoid autonomous final decisions. |
| 13 | IPIME | Ready for viva | Configurable institution policy workflow translates CIE/agent output into procedural responses without deciding guilt. | Keep policy-as-code model; add institution templates only if required for viva examples. |
| 14 | Candidate Incident Acknowledgement | Ready for viva | Candidate incident acknowledgement, neutral due-process wording, explanation capture, timestamps, and incident package linkage are implemented. | Rehearse one high/critical scenario to confirm panel-facing clarity. |
| 15 | Human Review | Needs minor polish | Review page supports CIE alerts, evidence, explanations, reviewer actions, rationale, and final outcome trace. | Polish queue labels and reviewer action wording before viva. |
| 16 | Reports/export | Needs minor polish | Reports show raw events, contextual alerts, risk timeline, scenario validation, and exportable evidence traces. | Improve final evidence-pack/report presentation during polish. |
| 17 | Viva scenario validation | Ready for viva | Ten controlled end-to-end scenarios validate raw evidence, CIE reasoning, agent recommendation, IPIME response, acknowledgement, review, and traceability. | Use these scenarios as Chapter 5 evaluation evidence. |
| 18 | FastAPI service boundary | Needs minor polish | Structured event ingestion and AI analysis endpoints exist; Streamlit remains the dashboard. | Document service startup and keep AI inference outside Streamlit where practical. |
| 19 | Privacy/security/audit | Needs minor polish | Consent, camera privacy, immutable evidence, audit trail, role-simulator warning, and local-first persistence are implemented. | Clearly document prototype limits: no enterprise SSO, hardened RBAC, encryption-at-rest, or retention automation. |
| 20 | Dashboard usability | Ready for viva | Home, navigation, staged workflows, CIE console, Monitoring, Review, Reports, footer, and split-screen candidate/reviewer viva demonstration are functional and viva-readable. | Use the split-screen mode for panel explanation and keep demo data curated. |
| 21 | Test coverage | Ready for viva | Unit/integration tests cover candidate integrity, camera events, visual/audio/identity events, CIE, IPIME, and viva scenarios. | Maintain tests; add only regression tests for final polish fixes. |
| 22 | Runtime stability | Ready for viva | Compile/tests pass in the current baseline; deprecated Streamlit width warnings and Windows disconnect noise were addressed. | Continue final smoke tests on the viva machine. |
| 23 | Remaining prototype limitations | Future enhancement | Continuous production-grade AI streaming, enterprise authentication, hardened storage, and scalable multi-session operations are beyond the current prototype scope. | Describe honestly in Chapter 4/5 and position as deployment work. |

### Top 10 Remaining Issues

1. Continuous camera and audio streams are not yet production-live; manual/demo controls remain necessary.
2. MediaPipe landmark-driven gaze/head-pose detection needs stronger live integration.
3. YOLO object detection depends on optional local model/package availability.
4. Live microphone/VAD capture is not yet connected to the dashboard flow.
5. Continuous identity assurance is not yet running as a background verification loop.
6. Evidence-pack and report exports need final presentation polish.
7. Reviewer workflow is local-prototype level, not multi-user enterprise workflow.
8. FastAPI boundaries exist, but AI services are not yet deployed as independent long-running workers.
9. Demo SQLite data can accumulate old sessions, events, and scenario records unless curated before viva.
10. Private dissertation/report files must remain untracked and outside the public implementation repository.

### Top 5 Viva Risks

1. Live hardware variability: browser permissions, lighting, or camera availability may affect live AI demonstrations.
2. AI detector variability: optional YOLO/MediaPipe/audio dependencies may not behave consistently on every machine.
3. Data clutter: repeated testing can leave old sessions and alerts that make the demo harder to explain.
4. Governance misunderstanding: panel members may misread SERPS as an automatic malpractice decision system unless the human-review boundary is emphasised.
5. Streamlit constraints: reruns and browser-camera limits can make continuous monitoring appear less live than the architecture supports.

### Recommended Final Polish Sprint

The next sprint should be a final polish sprint, not a new architecture sprint:

- Curate or reset demo data so viva scenarios start from a clean state.
- Polish Monitoring, Review, Reports, and incident acknowledgement wording for non-developer panel members.
- Improve evidence-pack/report display and export naming.
- Confirm all scenario groups demonstrate low, medium, high, and critical pathways.
- Add only regression tests for defects found during rehearsal.
- Run full browser smoke testing on the intended demonstration machine.
- Reconfirm no private dissertation artefacts are tracked.

### Dissertation Automation Readiness

Dissertation artefact automation can begin after the final polish sprint. The implementation is now feature-complete enough to support Chapter 4/5 evidence generation because the complete governance pipeline is present, scenario validation is implemented, and Reports expose traceable raw events, contextual alerts, policy responses, acknowledgements, and reviewer outcomes.

Automation should consume implementation evidence and controlled scenario outputs. It should not introduce new architecture or commit private dissertation drafts into the software repository.

### Final Polish Sprint Resolution

The final polish sprint reduced viva risk without changing the frozen architecture:

- Viva scenario validation now presents a clearer SERPS governance pipeline trace from structured evidence through CIE, Agentic Decision Support, IPIME, candidate acknowledgement, human review, and report/audit trace.
- Reviewer workflow wording now frames decisions as authorised human review outcomes, requires reviewer rationale, and avoids any automatic misconduct conclusion.
- Candidate incident acknowledgement wording was reinforced as a due-process step for a potential integrity concern, not a finding of guilt.
- Session JSON reports now include policy decisions, viva scenario validation runs, evidence-pack manifests, due-process notes, and human-review boundary language.
- Report/evidence package downloads are labelled more clearly for viva demonstration and incident traceability.
- Test coverage was expanded to verify that session reports include governance and due-process sections.

Remaining items are future enhancements rather than blockers for viva:

- Continuous browser camera/audio monitoring should move to WebRTC/FastAPI/OpenCV workers.
- MediaPipe, YOLO, VAD, and continuous identity assurance should be strengthened after the viva-ready prototype is frozen.
- Enterprise authentication, hardened RBAC, encryption-at-rest, retention automation, and multi-reviewer production workflow remain deployment concerns.
- PDF-quality formal evidence packs can be added after the JSON evidence trail is accepted.

### Private / Untracked File Discipline

The following must remain untracked/private unless explicitly approved:

- `System Specification.pdf`
- `Dissertation-Requirements.docx`
- `Dissertation-Requirements.pdf`
- `docs/chapter3_revision_guidance.md`
- `.private/`
- dissertation drafts, supervisor notes, thesis writing guidance, private addenda, and report-planning materials

The repository should contain only SERPS source code, tests, runtime configuration, software architecture documentation, implementation documentation, README/release material, and approved development logs.

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
| 8 | Dual-camera management | Partially Implemented | Primary/secondary camera slots, mode-aware requirement cards, readiness events, health events, controlled OpenCV physical camera validation, sampled frame previews, detector handoff, and persistence are visible in Monitoring. | Continuous dual-stream proctoring is not always-on yet; current validation samples selected devices after explicit user action and releases them. | `src/camera/camera_stream.py`, `src/camera/live_camera_validator.py`, `app.py`, tests | Continuous production monitoring should use OpenCV/WebRTC/FastAPI stream adapters. |
| 9 | Visual intelligence | Partially Implemented | OpenCV still-frame face/camera obstruction analysis, face presence/absence events, multiple persons where detectable, coarse head-position signals, and live sampled-frame analysis exist. | Real continuous gaze/pose tracking is not yet live; MediaPipe landmarks are future integration. | `src/vision/face_detector.py`, `src/vision/head_pose_estimator.py`, `src/vision/visual_event_detector.py`, `tests/test_visual_event_detector.py` | Integrate MediaPipe face landmarks or OpenCV stream worker. |
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
| 25 | Viva/demo readiness | Partially Implemented | End-to-end demo flow exists: enrol, authenticate, check devices, start session, show split-screen candidate/reviewer view, generate/live-analyse events, CIE reasoning, review, report. | Live continuous AI is still partial; manual fallback remains necessary for reliability. | `README.md`, `docs/development_log.md`, tests | Run scripted demo rehearsals and seed clean data before viva. |

## End-to-End Viva Scenario Validation Addendum

SERPS now includes a controlled evaluation harness for Chapter 5 and viva demonstration. The harness exercises the frozen governance pipeline without adding a new reasoning layer:

```text
Structured Evidence Events
-> Contextual Intelligence Engine
-> Agentic Decision Support
-> Institutional Policy & Incident Management Engine
-> Candidate Acknowledgement where required
-> Human Reviewer
-> Final Outcome / Report Trace
```

The Monitoring page exposes 10 realistic validation scenarios, including normal behaviour, isolated looking away, repeated gaze deviation, mobile-phone evidence, background speech, multiple persons, repeated face absence, identity mismatch, suspicious camera disconnection, and a critical combined multimodal case. Each scenario records expected risk, actual risk, expected policy response, actual policy response, acknowledgement state, reviewer-decision state, pass/needs-review status, and final outcome status in SQLite. Reports include a Viva Scenario Validation Summary table for evaluation evidence.

These scenarios are controlled validation cases only. They are not production cheating labels and do not make final examination decisions.

## Documentation Automation Framework Addendum

SERPS now includes a Documentation Automation Framework foundation. It supports a single rebuild command:

```powershell
python scripts/docs/package_dissertation_assets.py
```

Current generated artefacts include editable Mermaid diagrams for Chapter Three architecture figures, a SQLite-derived ERD, FastAPI OpenAPI JSON and endpoint summary, Chapter Four screenshot/test-evidence plans, a Chapter Five viva scenario catalog, evaluation summaries, CSV metric outputs, a risk-distribution SVG chart, separate captions, an asset index, a packaged `dissertation_assets.zip`, and a manifest with checksums, version metadata, environment metadata, and package metadata.

Status: **Partially Implemented**. The framework is ready for controlled dissertation artefact generation and packaging, but live screenshot capture, automated test-report execution, rendered architecture SVG/PNG export, and richer evaluation charts still need strengthening. Mermaid rendering depends on local Mermaid CLI (`mmdc`); the current environment records this limitation and preserves editable sources.

Recommended next documentation action: add automated screenshot capture through a controlled browser runner and add evaluation chart generation from stored viva scenario outputs.

## Viva Demonstration and Live Camera Validation Addendum

SERPS now includes viva-facing demonstration documentation:

- `docs/viva_demo_plan.md` describes the local screen-share demonstration, opening statement, architecture defence, 5-minute and 15-minute demo paths, fallback plan, cloud deployment limitations, and React/Next.js production frontend boundary.
- `docs/viva_question_bank.md` contains grouped viva questions and concise model answers.

Monitoring also includes a controlled live dual-camera capability test. It uses OpenCV to discover physical camera indices only after explicit user action, allows Primary/Secondary selection, captures side-by-side validation frames, displays FPS/resolution/connection status, records structured camera events, and feeds those events into the existing CIE. The feature validates the dual-camera design while preserving the privacy rule that cameras never activate on page load.

Status: **Implemented for controlled validation**. Continuous dual-camera streaming remains a future production enhancement best handled by WebRTC/OpenCV/FastAPI services with Streamlit retained as the operations dashboard.

## Milestone Version Tags

SERPS now uses annotated Git milestone tags as reproducible research checkpoints:

| Tag | Commit | Meaning |
| --- | --- | --- |
| `v1.0.0-feature-complete` | `6991d9b` | Feature-complete SERPS Version 1.0 baseline before documentation automation. |
| `v1.1.0-documentation-framework` | `b50e41a` | Documentation Automation Framework foundation and generated artefact baseline. |

These tags make it possible to regenerate dissertation artefacts from known implementation states and to demonstrate exactly which version was used during viva preparation.

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
