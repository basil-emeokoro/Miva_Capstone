# System Architecture Summary

The prototype follows the locked architecture from the specification:

```text
Sensors / Demo Inputs
-> Detection Modules
-> Structured Evidence Events
-> Event Fusion Engine
-> Explainability Layer
-> Agentic AI Orchestrator
-> Dashboard / Human Reviewer
-> Reports and Audit Trail
```

The Event Fusion Engine is central. Detection modules generate evidence only. The reviewer remains responsible for final decisions.

## Local Prototype Stack

- Python
- Streamlit dashboard
- SQLite database
- Rule-based event fusion and explainability
- JSON report export
- Pytest tests

## Monitoring Modes

- Mode A: single-camera CBT centre mode.
- Mode B: dual-camera recommended full mode.
- Mode C: single-camera plus mirror low-resource mode.
