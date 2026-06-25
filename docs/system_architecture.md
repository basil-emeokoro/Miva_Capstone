# System Architecture Summary

The prototype follows the locked architecture from the specification:

```text
Sensors / Demo Inputs
-> Detection Modules
-> Structured Evidence Events
-> Contextual Intelligence Engine
   -> Event Fusion Module
   -> Temporal Behaviour Memory
   -> Risk Scoring Engine
   -> Contextual Reasoning Module
   -> Explainability Interface
-> Agentic Decision Support
-> Institutional Policy & Incident Management Engine
-> Human Reviewer
-> Final Decision / Reports / Audit Trail
```

The Contextual Intelligence Engine is the central reasoning layer. The Event Fusion Module is now a CIE subcomponent rather than the top-level intelligence layer. Detection modules generate evidence only. Agentic Decision Support recommends operational action. The Institutional Policy & Incident Management Engine translates contextual risk and agent recommendations into institution-specific procedure. The reviewer remains responsible for final decisions.

## Local Prototype Stack

- Python
- Streamlit dashboard
- FastAPI structured-event service boundary
- SQLite database
- OpenCV still-frame visual analysis
- Optional MediaPipe/YOLO-ready detector adapters
- Modular audio event definitions for future VAD/STT detectors
- Contextual intelligence with event fusion, temporal behaviour memory, risk scoring, contextual reasoning, and explainability
- Institutional policy-as-code for incident workflow selection
- JSON report export
- Pytest tests

## Frozen Architecture Boundary

Detection modules are perception modules only. They generate immutable structured `EvidenceEvent` records for the Contextual Intelligence Engine. They must not calculate final misconduct decisions or bypass CIE risk reasoning.

The Institutional Policy & Incident Management Engine does not decide guilt. It evaluates CIE alert output and Agentic Decision Support recommendations against configurable institutional rules, then records procedural workflow decisions such as warning, acknowledgement, escalation, evidence preservation, and reviewer notification.

Streamlit is the dashboard/control surface. Continuous AI inference should run through service boundaries such as FastAPI, OpenCV workers, WebRTC/browser streams, or a secure exam-player integration. The first live-integration milestone introduces this boundary through `src/services/event_api.py`.

## AI Capability Integration Boundary

The first AI capability sprint strengthens the perception layer without changing the reference architecture.

- Visual analysis can process an explicitly supplied frame through OpenCV face/camera checks, coarse head-pose signalling, and optional YOLO object mapping.
- Object detection is adapter-based so newer YOLO models can replace the current optional local model with minimal code changes.
- Audio analysis accepts detector feature windows from future Whisper, WebRTC VAD, Silero VAD, or equivalent workers.
- Identity assurance converts periodic face-verification confidence into evidence events for CIE ingestion.
- FastAPI exposes structured endpoints for frame, audio-feature, identity-confidence, and generic event ingestion.
- Streamlit exposes Live AI controls for user-triggered frame/feature analysis and preserves Demonstration/Simulation controls for viva reliability.

## Institutional Policy and Incident Management

`src/policy/policy_engine.py` loads configurable rules from `config/institutional_policies.json`. Current prototype policies cover WAEC, University/Miva, and Generic workflows.

- WAEC high-risk alerts require a candidate incident acknowledgement workflow and reviewer notification.
- University/Miva medium-risk alerts warn/continue assessment while preserving evidence for review.
- Generic critical-risk alerts recommend suspension workflow, senior reviewer notification, and evidence preservation.

Candidate incident acknowledgement is exposed through the mock Test Player when a policy requires acknowledgement. The wording avoids misconduct conclusions and states that authorised examination officials review the evidence before any determination. Reviewer incident actions are recorded separately from CIE alert records.

## Monitoring Modes

- Mode A: single-camera CBT centre mode.
- Mode B: dual-camera recommended full mode.
- Mode C: single-camera plus mirror low-resource mode.
