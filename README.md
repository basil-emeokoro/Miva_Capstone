# Explainable Multi-Modal Proctoring Prototype

Local-first capstone prototype for secure remote-proctored assessments in Nigeria.

Platform identity: SERPS — Secure Explainable Remote Proctoring System.

The system demonstrates candidate enrolment, consent capture, monitoring-mode selection, mock assessment delivery, structured event generation, explainable event fusion, role-aware human review, and report export.

## Core Principle

AI modules do not punish candidates. Detection modules generate evidence events, the Event Fusion Engine assigns explainable risk, and a human reviewer makes the final decision.

## Prototype Features

- Candidate registration and consent capture
- Prototype guided face enrolment metadata
- Admin, Human Proctor, and Reviewer RBAC
- Mode A, B, and C monitoring configuration
- Lightweight mock assessment/test player
- Demo visual, identity, and audio event generation
- Rule-based Event Fusion Engine
- Explainable fused alerts
- Reviewer accept/reject/escalate workflow
- JSON session report export
- SQLite local storage

## Run Locally

```powershell
pip install -r requirements.txt
python main.py
python -m streamlit run app.py --server.port 8502
```

## Known Limitations

- This is not a production-grade proctoring platform.
- Camera, face recognition, voice verification, and object detection are currently represented through prototype event flows.
- The mock assessment is not a full exam engine.
- RBAC is local prototype authorization only.
- SQLite is used for local demonstration.

## Public Documentation

- `docs/development_log.md` records implementation progress and limitations.
- `docs/system_architecture.md` summarizes the prototype architecture.
