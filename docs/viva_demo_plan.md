# SERPS Viva Demonstration and Production Frontend Plan

## SERPS Capstone Positioning

SERPS is a capstone prototype with documentation automation and reproducible dissertation artefacts.

It should be presented as the Miva Open University MIT capstone implementation of a secure, explainable, AI-assisted remote proctoring governance prototype. The system demonstrates how multimodal evidence can be generated, structured, reasoned over, explained, routed through institutional policy, and reviewed by authorised human exam officials.

SERPS should not be described as being converted into a general research platform. The current focus remains the capstone implementation, viva demonstration, dissertation evidence generation, and reproducible technical artefacts.

## Primary Remote Viva Demonstration Plan

The recommended viva demonstration approach is to run SERPS locally and share the screen with the panel.

This is the primary approach because it gives the demonstrator full control over local SQLite data, browser permissions, camera behaviour, scenario execution, and fallback simulation controls. It also avoids cloud-hosting limitations during a time-sensitive defence.

Recommended flow:

1. Start SERPS locally with `python -m streamlit run app.py`.
2. Share the local browser window with the panel.
3. Use the sidebar Prototype Role Simulator to move between Admin, Reviewer/Proctor, and Candidate/Test Player perspectives.
4. Start from the Home page to explain the SERPS modules.
5. Demonstrate candidate enrolment, consent, profile, session preparation, and monitoring mode selection if time allows.
6. Open Monitoring and run selected viva scenarios.
7. Show the full governance pipeline:

Detection -> Evidence Events -> CIE -> Agentic Recommendation -> IPIME -> Candidate Acknowledgement -> Human Review -> Report.

The panel should see that SERPS does not label a candidate as guilty. It detects risk indicators, explains contextual reasoning, applies configurable institutional workflow, and leaves final decisions to authorised reviewers.

## Optional Cloud Deployment Note

Cloud deployment through Render, Streamlit Cloud, or a similar service may be useful only as a secondary showcase.

It should not be treated as the primary viva environment because:

- Browser camera access depends on the remote client's browser permissions and HTTPS/device support.
- Local SQLite persistence may not be reliable on free or ephemeral cloud hosting.
- Render free-tier storage and process limitations can interrupt long demonstrations.
- Multi-user real-time candidate/proctor separation is limited in the current Streamlit prototype.
- Continuous video/audio monitoring is better supported by a future production stack with WebRTC and background workers.

If a cloud deployment is shown, it should be described as a convenience preview of the dashboard, not the authoritative viva setup. The reliable demonstration path remains local execution plus screen sharing.

## Viva-Facing Explanation of Current SERPS

SERPS is a Secure Explainable Remote Proctoring System prototype for AI-assisted examination monitoring and governance.

The problem it addresses is that remote examinations can generate many isolated signals, such as camera disconnection, face absence, background speech, looking away, mobile phone detection, or identity mismatch. A basic system may either ignore these signals or overreact to them. SERPS instead converts signals into structured evidence, reasons contextually, explains risk, applies institutional workflow, and supports human review.

The Contextual Intelligence Engine is central because it is the only reasoning layer. Detection modules produce evidence events only. The CIE correlates evidence across time, modules, confidence values, and behavioural patterns. This prevents isolated events from being treated the same as persistent or multimodal risk patterns.

The Institutional Policy & Incident Management Engine is included because institutions respond differently to exam integrity concerns. For example, one institution may warn and continue, while another may require a candidate acknowledgement workflow. IPIME translates CIE and Agent outputs into configured institutional process without making a disciplinary decision.

Human review remains final because SERPS is designed around human-in-the-loop governance. AI-generated alerts are decision-support artefacts. Authorised reviewers evaluate evidence, explanations, candidate responses, and institutional policy before recording any final outcome.

Implemented live in the current capstone prototype:

- Streamlit dashboard and navigation.
- Candidate enrolment, consent, profile management, and guided facial enrolment workflow.
- Authentication and pre-exam device/environment gating.
- Monitoring Mode Controller for Mode A, Mode B, and Mode C.
- Structured evidence event generation and SQLite persistence.
- Computer vision, audio, identity, camera/system event foundations.
- Contextual Intelligence Engine with temporal memory, risk scoring, contextual reasoning, and explainability.
- Agentic Decision Support recommendations.
- IPIME policy response and candidate acknowledgement workflow.
- Human review workflow, reports, audit trail, and viva scenario validation.
- Documentation automation for implementation-derived dissertation artefacts.

Prototype or simulated in the current capstone:

- Some monitoring evidence is generated through controlled demo hooks or scenario runners.
- Continuous real-time browser video/audio processing is not fully production-grade in Streamlit.
- Object detection and identity assurance are modular foundations rather than full enterprise deployments.
- Cloud deployment is optional and secondary, not the primary examination environment.

Future enhancement:

- Production WebRTC camera/audio streaming.
- React/Next.js candidate and proctor frontends.
- FastAPI-hosted inference workers.
- PostgreSQL or managed database persistence.
- Scalable multi-user candidate/proctor separation.
- Stronger live AI models for gaze, head pose, object detection, voice activity, and continuous identity assurance.
- Institutional integrations and secure exam-browser integration.

## React / Production Frontend Note

React or Next.js is not part of the current capstone implementation.

Streamlit remains appropriate for the capstone dashboard and viva prototype because it allows rapid demonstration of enrolment, monitoring, CIE reasoning, policy response, review, reporting, and documentation automation in one local environment.

FastAPI provides the service/API boundary and is the correct direction for backend integration. It supports future structured evidence ingestion, AI service integration, and external exam-player communication without replacing the current Streamlit dashboard.

A future production version would likely use:

- React or Next.js for candidate, proctor, reviewer, and admin frontends.
- FastAPI for backend services and structured evidence APIs.
- PostgreSQL for durable multi-user persistence.
- WebRTC for browser camera/audio streaming.
- Background workers for continuous AI inference and event processing.

React should not be implemented now. It should be treated as a post-dissertation production upgrade.

## Recommended Demo Script

### 5-Minute Demo Path

1. Open Home and introduce SERPS as a capstone prototype with documentation automation and reproducible dissertation artefacts.
2. Show the Prototype Role Simulator and explain that it simulates Admin, Proctor/Reviewer, and Candidate/Test Player views on one local machine for viva purposes.
3. Open Monitoring and select an active session.
4. Run one low-risk or normal scenario and show raw evidence events.
5. Run one high-risk or critical scenario and show CIE risk, explanation, Agentic recommendation, and IPIME response.
6. Open Review and record a human reviewer action.
7. Open Reports and show the validation/report trace.

### 15-Minute Demo Path

1. Open Home and explain the full SERPS pipeline.
2. Show Enrolment dashboard, consent capture, candidate profile, and facial enrolment evidence.
3. Show Session Control with monitoring mode, pre-exam checks, authentication gate, and session start gating.
4. Open Monitoring and explain dual-camera foundation, visual intelligence, audio hooks, and CIE console.
5. Run selected viva scenarios:
   - normal candidate behaviour;
   - brief looking away;
   - repeated gaze deviation;
   - mobile phone detected;
   - critical combined scenario.
6. For a scenario requiring policy intervention, show IPIME response and Candidate Incident Acknowledgement.
7. Open Review and demonstrate that the reviewer, not the AI, records the final decision.
8. Open Reports and show raw events, contextual alerts, viva scenario validation summary, and evidence trace.
9. Briefly show documentation automation outputs under `docs/dissertation/` if asked about dissertation artefact reproducibility.

### Fallback Plan

If live hardware, camera access, browser permissions, or network conditions fail:

1. Keep SERPS running locally and avoid activating camera-dependent workflows.
2. Use the viva scenario validation runner to generate structured evidence events.
3. Demonstrate the CIE, Agentic Decision Support, IPIME, acknowledgement, review, and reports using controlled scenarios.
4. Explain that the fallback mode is intentional: SERPS supports both Live AI Mode and Demonstration/Simulation Mode so viva evidence can be reproduced even when live hardware is unavailable.
5. Emphasise that no camera opens on page load and that camera access is user-triggered for privacy-by-design reasons.

