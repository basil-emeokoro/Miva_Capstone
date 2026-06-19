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
- SQLite database
- Contextual intelligence with event fusion, temporal behaviour memory, risk scoring, contextual reasoning, and explainability
- JSON report export
- Pytest tests

## Monitoring Modes

- Mode A: single-camera CBT centre mode.
- Mode B: dual-camera recommended full mode.
- Mode C: single-camera plus mirror low-resource mode.
