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
-> Human Reviewer
-> Final Decision / Reports / Audit Trail
```

The Contextual Intelligence Engine is the central reasoning layer. The Event Fusion Module is now a CIE subcomponent rather than the top-level intelligence layer. Detection modules generate evidence only. The reviewer remains responsible for final decisions.

## Local Prototype Stack

- Python
- Streamlit dashboard
- FastAPI structured-event service boundary
- SQLite database
- OpenCV still-frame visual analysis
- Optional MediaPipe/YOLO-ready detector adapters
- Modular audio event definitions for future VAD/STT detectors
- Contextual intelligence with event fusion, temporal behaviour memory, risk scoring, contextual reasoning, and explainability
- JSON report export
- Pytest tests

## Frozen Architecture Boundary

Detection modules are perception modules only. They generate immutable structured `EvidenceEvent` records for the Contextual Intelligence Engine. They must not calculate final misconduct decisions or bypass CIE risk reasoning.

Streamlit is the dashboard/control surface. Continuous AI inference should run through service boundaries such as FastAPI, OpenCV workers, WebRTC/browser streams, or a secure exam-player integration. The first live-integration milestone introduces this boundary through `src/services/event_api.py`.

## AI Capability Integration Boundary

The first AI capability sprint strengthens the perception layer without changing the reference architecture.

- Visual analysis can process an explicitly supplied frame through OpenCV face/camera checks, coarse head-pose signalling, and optional YOLO object mapping.
- Object detection is adapter-based so newer YOLO models can replace the current optional local model with minimal code changes.
- Audio analysis accepts detector feature windows from future Whisper, WebRTC VAD, Silero VAD, or equivalent workers.
- Identity assurance converts periodic face-verification confidence into evidence events for CIE ingestion.
- FastAPI exposes structured endpoints for frame, audio-feature, identity-confidence, and generic event ingestion.
- Streamlit exposes Live AI controls for user-triggered frame/feature analysis and preserves Demonstration/Simulation controls for viva reliability.

## Monitoring Modes

- Mode A: single-camera CBT centre mode.
- Mode B: dual-camera recommended full mode.
- Mode C: single-camera plus mirror low-resource mode.
