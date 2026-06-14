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

## Prototype Limitations

- Face recognition, voice verification, camera feeds, and YOLO detection are represented by prototype/demo event flows at this stage.
- The test player is intentionally lightweight and is not a production examination engine.
- RBAC is local prototype authorization, not enterprise identity management.
