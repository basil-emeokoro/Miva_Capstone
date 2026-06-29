# SERPS Viva Demonstration and Production Frontend Plan

## SERPS Capstone Positioning

SERPS is a capstone prototype with documentation automation and reproducible dissertation artefacts.

It should be presented as the Miva Open University MIT capstone implementation of a secure, explainable, AI-assisted remote proctoring governance prototype. The system demonstrates how multimodal evidence can be generated, structured, reasoned over, explained, routed through institutional policy, and reviewed by authorised human exam officials.

SERPS should not be described as being converted into a general research platform. The current focus remains the capstone implementation, viva demonstration, dissertation evidence generation, and reproducible technical artefacts.

## Viva Opening Statement

Good day. My dissertation is titled **Secure Explainable Remote Proctoring System for AI-Assisted Examination Integrity Monitoring**. The implemented prototype is SERPS, the Secure Explainable Remote Proctoring System.

The motivation for this work is the growth of remote and computer-based assessments, where institutions need credible ways to support examination integrity without relying on opaque AI decisions or intrusive one-dimensional monitoring. Existing proctoring tools often focus on isolated camera or audio signals, but examination incidents usually require context: what happened, when it happened, how often it happened, which modality observed it, and whether the evidence is strong enough for human review.

The research problem addressed by SERPS is how to design a privacy-aware, explainable, multimodal proctoring prototype that can convert monitoring signals into structured evidence, reason over them contextually, and support institutional review without making automatic misconduct decisions.

The main architectural contribution is the Contextual Intelligence Engine, supported by temporal behavioural memory, explainability, Agentic Decision Support, and the Institutional Policy & Incident Management Engine. Together, these components demonstrate a governance pipeline rather than a raw video cheating classifier.

In the demonstration, I will first show the dashboard and role simulator, then demonstrate enrolment and session preparation where relevant. I will then run selected viva scenarios to show how evidence events flow through the CIE, how risk and explanations are generated, how IPIME applies institutional procedure, how candidate acknowledgement works where required, and how the final decision remains with the human reviewer.

## Architecture Defence

SERPS follows the frozen Version 1.0 decision pipeline:

Sensor Layer

↓

Detection Modules

↓

Structured Evidence Events

↓

Contextual Intelligence Engine (CIE)

↓

Agentic Decision Support

↓

Institutional Policy & Incident Management Engine (IPIME)

↓

Candidate Acknowledgement, where policy requires

↓

Human Reviewer

↓

Final Institutional Decision

The Sensor Layer captures potential inputs such as camera, audio, identity, device, and session signals. Detection modules interpret those inputs only as observable evidence. They do not decide whether misconduct occurred.

Structured Evidence Events create a consistent evidence format across modalities. This prevents camera, audio, identity, and system-health modules from becoming isolated systems. Every event can be persisted, audited, correlated, explained, and reported.

The CIE is the only reasoning layer. No detection module bypasses it because isolated perception signals are insufficient for institutional action. For example, a single looking-away event should not be treated the same as repeated gaze deviation combined with background speech and mobile phone detection. The CIE evaluates temporal proximity, frequency, confidence, source module, risk weight, and behavioural persistence.

Agentic Decision Support receives CIE output and recommends operational action, such as observe, warn, escalate, or request review. It does not determine guilt.

IPIME translates CIE and Agent outputs into institution-specific process. This is necessary because WAEC, universities, and other institutions may use different procedural responses for similar risk levels. IPIME determines workflow, not disciplinary outcome.

Candidate acknowledgement is included where institutional policy requires due process. The candidate is informed that a potential examination integrity concern was detected and is asked to provide an explanation. The wording deliberately avoids accusing the candidate of malpractice.

Human review remains final because SERPS is designed as human-centred decision support. Automatic misconduct decisions are avoided to preserve due process, reduce false-positive harm, support explainability, and align the system with institutional governance.

## Primary Remote Viva Demonstration Plan

The recommended viva demonstration approach is to run SERPS locally and share the screen with the panel.

This is the primary approach because it gives the demonstrator full control over local SQLite data, browser permissions, camera behaviour, scenario execution, and fallback simulation controls. It also avoids cloud-hosting limitations during a time-sensitive defence.

Recommended flow:

1. Start SERPS locally with `python -m streamlit run app.py`.
2. Share the local browser window with the panel.
3. Use the sidebar Prototype Role Simulator to move between Admin, Reviewer/Proctor, and Candidate/Test Player perspectives.
4. Start from the Home page to explain the SERPS modules.
5. Demonstrate candidate enrolment, consent, profile, session preparation, and monitoring mode selection if time allows.
6. Open Monitoring and use **Viva Split-Screen Demonstration Mode** to show the candidate-facing exam interface beside the reviewer/proctor intelligence console.
7. If two physical cameras are connected, run the live dual-camera validation after explicitly selecting the devices and starting validation.
8. Show that sampled live frames can produce structured camera/visual evidence for the CIE where feasible.
9. Run selected viva scenarios as controlled evaluation evidence or as fallback where live hardware is unavailable.
10. Show the full governance pipeline:

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
- Viva split-screen demonstration mode with separated candidate-facing and reviewer/proctor-facing views.
- Candidate enrolment, consent, profile management, and guided facial enrolment workflow.
- Authentication and pre-exam device/environment gating.
- Monitoring Mode Controller for Mode A, Mode B, and Mode C.
- Controlled physical dual-camera discovery, primary/secondary selection, labelled preview sampling, FPS/resolution/status display, and stream-health evidence generation.
- Explicit sampled-frame handoff from live camera validation into visual detector modules where feasible.
- Candidate-facing primary-camera phone evidence, distinct from room-facing secondary-camera object evidence.
- IPIME-configurable temporary screen shield for candidate-facing phone or possible screen-capture risk, using due-process wording and preserving human review.
- Structured evidence event generation and SQLite persistence.
- Computer vision, audio, identity, camera/system event foundations.
- Contextual Intelligence Engine with temporal memory, risk scoring, contextual reasoning, and explainability.
- Agentic Decision Support recommendations.
- IPIME policy response and candidate acknowledgement workflow.
- Human review workflow, reports, audit trail, and viva scenario validation.
- Documentation automation for implementation-derived dissertation artefacts.

Prototype or simulated in the current capstone:

- Some monitoring evidence is generated through controlled demo hooks or scenario runners.
- Continuous real-time browser video/audio processing is not fully production-grade in Streamlit; current live camera validation is explicit sampled validation rather than always-on streaming.
- Object detection and identity assurance are modular foundations rather than full enterprise deployments. Candidate-facing phone detection is a structured evidence signal and should not be presented as an automatic malpractice finding.
- Cloud deployment is optional and secondary, not the primary examination environment.

Future enhancement:

- Production WebRTC camera/audio streaming.
- Dedicated live dual-camera service for continuous monitoring beyond the controlled validation panel.
- React/Next.js candidate and proctor frontends.
- FastAPI-hosted inference workers.
- PostgreSQL or managed database persistence.
- Scalable multi-user candidate/proctor separation.
- Stronger live AI models for gaze, head pose, object detection, voice activity, and continuous identity assurance.
- Institutional integrations and secure exam-browser integration.

## Research Contributions

SERPS makes the following capstone-level implementation contributions:

- **Explainable multimodal remote proctoring architecture:** SERPS integrates camera, audio, identity, device, behavioural, and session evidence into a coherent governance workflow.
- **Contextual Intelligence Engine:** The CIE centralises reasoning so detection modules remain perception-only and do not make misconduct decisions.
- **Temporal behavioural memory:** SERPS distinguishes isolated events from persistent patterns by considering frequency and temporal windows.
- **Contextual risk reasoning:** Risk is derived from confidence, modality, event frequency, temporal proximity, and correlated evidence rather than from a single raw detector output.
- **Institutional Policy & Incident Management Engine:** IPIME translates contextual risk into configurable institutional procedure without determining guilt.
- **Human-centred governance workflow:** Candidate acknowledgement, reviewer rationale, audit trail, and final human decision are built into the process.
- **Documentation automation for reproducible dissertation artefacts:** SERPS generates implementation-derived diagrams, manifests, captions, OpenAPI evidence, scenario summaries, and packaged dissertation assets.

## Limitations and Future Work

Current prototype limitations:

- Streamlit is effective for viva dashboard demonstration but is not a full production real-time proctoring frontend.
- Some evidence events remain controlled simulations or user-triggered validations rather than continuous autonomous detection.
- Live dual-camera validation is a controlled capability test with sampled-frame detector handoff. Continuous dual-camera proctoring should be moved to a service/WebRTC architecture in production.
- SQLite is appropriate for local capstone demonstration but not for scalable multi-user deployment.
- Camera and audio access depend on local device permissions and operating-system behaviour.
- YOLO/object detection, continuous identity assurance, and audio intelligence are modular foundations that require further production hardening.

Future production enhancements:

- React/Next.js frontend for separate candidate, proctor, reviewer, and administrator experiences.
- FastAPI background inference services for camera, audio, identity, and event ingestion.
- WebRTC-based browser streaming for continuous low-latency monitoring.
- PostgreSQL or another managed database for durable concurrent access.
- Stronger AI models for gaze, head pose, object detection, face verification, speech detection, and environmental analysis.
- Institutional integrations with CBT platforms, secure exam browsers, and official case-management systems.
- Deployment hardening, authentication, encryption, audit retention, and NDPA-aligned privacy controls.

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
4. Show Viva Split-Screen Demonstration Mode and explain that candidates do not see reviewer intelligence in production.
5. Run one low-risk or normal scenario and show raw evidence events.
6. Run one high-risk or critical scenario and show CIE risk, explanation, Agentic recommendation, and IPIME response.
7. Open Review and record a human reviewer action.
8. Open Reports and show the validation/report trace.

### 15-Minute Demo Path

1. Open Home and explain the full SERPS pipeline.
2. Show Enrolment dashboard, consent capture, candidate profile, and facial enrolment evidence.
3. Show Session Control with monitoring mode, pre-exam checks, authentication gate, and session start gating.
4. Open Monitoring and show Viva Split-Screen Demonstration Mode.
5. If two physical cameras are connected, run live dual-camera validation to show Primary/Secondary labels, FPS/resolution/status, and live frame-to-evidence handoff.
6. Explain dual-camera foundation, visual intelligence, audio hooks, and CIE console.
7. Run selected viva scenarios:
   - normal candidate behaviour;
   - brief looking away;
   - repeated gaze deviation;
   - mobile phone detected;
   - critical combined scenario.
8. For a scenario requiring policy intervention, show IPIME response and Candidate Incident Acknowledgement.
9. Open Review and demonstrate that the reviewer, not the AI, records the final decision.
10. Open Reports and show raw events, contextual alerts, viva scenario validation summary, and evidence trace.
11. Briefly show documentation automation outputs under `docs/dissertation/` if asked about dissertation artefact reproducibility.

### Fallback Plan

If live hardware, camera access, browser permissions, or network conditions fail:

1. Keep SERPS running locally and avoid activating camera-dependent workflows.
2. Use the viva scenario validation runner to generate structured evidence events.
3. Demonstrate the CIE, Agentic Decision Support, IPIME, acknowledgement, review, and reports using controlled scenarios.
4. Explain that the fallback mode is intentional: SERPS supports both Live AI Mode and clearly labelled Demonstration/Simulation Mode so viva evidence can be reproduced even when live hardware is unavailable.
5. Emphasise that no camera opens on page load and that camera access is user-triggered for privacy-by-design reasons.

## Live Dual-Camera Validation

The Monitoring page includes a controlled live dual-camera capability test. This is a technical validation of the dual-camera architecture, not a new architectural feature.

The validation supports:

- explicit OpenCV camera discovery;
- primary and secondary physical camera selection;
- side-by-side labelled previews after user activation;
- FPS, resolution, and connection status display;
- structured camera readiness or disconnection events;
- sampled-frame handoff into OpenCV visual analysis where feasible;
- optional secondary object-detection adapter execution where locally available;
- persistence through the common EvidenceEvent schema;
- CIE ingestion of live camera health and detector-derived visual evidence.

The privacy rule remains unchanged: physical cameras are never opened on page load. Discovery and validation require explicit user action, and selected devices are released after the validation sample is captured.

The current live path is not automatic surveillance. It is an explicit validation run that samples selected devices, releases them, and labels generated events as live evidence. Simulation controls remain available separately for viva stability.

If simultaneous continuous streaming becomes necessary beyond the controlled capstone validation, the recommended production path is a FastAPI/OpenCV/WebRTC service where Streamlit remains the operations dashboard and the backend service manages real-time streams.
