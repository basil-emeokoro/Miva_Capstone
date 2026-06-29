# SERPS Viva Question Bank

This question bank supports viva preparation for SERPS, a capstone prototype with documentation automation and reproducible dissertation artefacts. Answers are concise model responses and should be adapted naturally during the defence.

## Problem Motivation

1. **What problem does SERPS address?**  
SERPS addresses the challenge of supporting examination integrity in remote or computer-based assessments without relying on opaque or automatic misconduct decisions.

2. **Why is remote proctoring a relevant problem?**  
Remote and hybrid assessments are expanding, but institutions need credible identity assurance, monitoring, evidence handling, and review workflows.

3. **What is wrong with simple camera-only proctoring?**  
Camera-only monitoring can miss context, overreact to isolated behaviour, and fail to combine audio, identity, device, and behavioural evidence.

4. **Why is explainability important in proctoring?**  
Examination integrity decisions affect students significantly, so evidence and reasoning must be understandable to reviewers and defensible to institutions.

5. **Why should AI not make final misconduct decisions?**  
AI can produce false positives and lacks institutional authority. SERPS supports human reviewers; it does not replace due process.

## Literature and Research Gap

6. **What gap does SERPS respond to in existing systems?**  
It responds to the lack of explainable, multimodal, context-aware, human-centred proctoring workflows that combine evidence and institutional policy.

7. **How does SERPS differ from a raw cheating detector?**  
SERPS detects observable risk indicators, structures them as evidence, reasons contextually, and supports review rather than classifying candidates as cheaters.

8. **Why is multimodal evidence useful?**  
Multiple evidence sources can strengthen or weaken interpretation. For example, background speech plus repeated looking away is more meaningful than either signal alone.

9. **Why is institutional policy relevant to the literature gap?**  
Different institutions respond differently to incidents. SERPS models policy workflow separately from AI reasoning.

10. **What makes SERPS suitable as a capstone contribution?**  
It implements a coherent prototype that links AI perception, contextual reasoning, policy workflow, review, reporting, and reproducible documentation artefacts.

## Methodology

11. **What methodology was used?**  
The project follows design science and prototype-driven implementation: identify the problem, design the artefact, implement, evaluate using scenarios, and document limitations.

12. **Why use controlled viva scenarios?**  
They provide repeatable evaluation cases for low, medium, high, and critical risk patterns without depending on unpredictable live hardware.

13. **How is the system evaluated?**  
Through module tests, end-to-end scenario validation, manual browser checks, evidence persistence, CIE outputs, IPIME responses, review trace, and reports.

14. **Why include both live and simulation modes?**  
Live mode demonstrates practical AI capability, while simulation mode ensures reproducibility during viva when hardware or permissions fail.

15. **How do you avoid fabricating evaluation evidence?**  
Generated dissertation artefacts are derived from implementation code, schema, scenario definitions, OpenAPI exports, and recorded outputs.

## System Architecture

16. **What is the frozen SERPS pipeline?**  
Sensor Layer -> Detection Modules -> Structured Evidence Events -> CIE -> Agentic Decision Support -> IPIME -> Candidate Acknowledgement where required -> Human Reviewer -> Final Institutional Decision.

17. **Why is the architecture layered?**  
Layering prevents perception, reasoning, policy, and final decision-making from being mixed together.

18. **Why do detection modules not bypass the CIE?**  
Because isolated signals need contextual interpretation before any recommendation or institutional workflow is triggered.

19. **What is the role of Structured Evidence Events?**  
They provide a common schema for all monitoring evidence, making events persistent, auditable, explainable, and suitable for CIE correlation.

20. **Why is SQLite used?**  
SQLite is appropriate for local capstone demonstration and reproducibility. Production would use PostgreSQL or another managed database.

## Contextual Intelligence Engine

21. **What is the CIE?**  
The Contextual Intelligence Engine is the central SERPS reasoning layer that correlates evidence, applies temporal memory, scores risk, and generates explanations.

22. **Why is CIE central to the contribution?**  
It moves SERPS beyond isolated alerts into contextual, explainable, multimodal reasoning.

23. **What is temporal behavioural memory?**  
It tracks event frequency and persistence within time windows so repeated behaviours are treated differently from isolated events.

24. **How does the CIE calculate risk?**  
It considers risk weight, confidence, event frequency, temporal proximity, contributing modules, and contextual patterns.

25. **What does CIE output?**  
It outputs contextual alerts with risk score, risk level, confidence, explanation, reasoning trace, and reviewer recommendation context.

## Explainability

26. **What is explained to the reviewer?**  
The reviewer sees contributing events, modules, confidence, risk score, temporal context, and why risk increased or remained low.

27. **How does explainability reduce harm?**  
It prevents opaque accusations by showing evidence and reasoning that a human can accept, reject, or investigate further.

28. **Does explanation mean the AI is always correct?**  
No. Explanation supports review; it does not guarantee correctness or replace human judgement.

## Agentic AI

29. **What does Agentic Decision Support do?**  
It recommends operational responses such as observe, warn, escalate, or request review based on CIE output.

30. **Can the Agent terminate an exam?**  
No. It may recommend action, but final decisions remain with authorised humans and institutional policy.

31. **Why include Agentic AI at all?**  
It demonstrates how contextual AI output can be coordinated into practical reviewer-facing recommendations without bypassing governance.

## IPIME

32. **What is IPIME?**  
The Institutional Policy & Incident Management Engine converts contextual risk and Agent recommendations into configurable institutional procedures.

33. **Why is IPIME separate from the CIE?**  
CIE reasons about evidence; IPIME applies institutional workflow. Keeping them separate prevents risk scoring from becoming disciplinary decision-making.

34. **What is policy-as-code in SERPS?**  
It means institutional procedures are configurable instead of hardcoded, supporting WAEC, university, and generic workflows.

35. **Why include candidate acknowledgement?**  
It supports due process by allowing the candidate to provide an explanation when policy requires an incident response.

## Identity Assurance

36. **What identity assurance is implemented?**  
The prototype supports enrolment, facial capture records, authentication gating, identity-confidence events, and identity mismatch scenario validation.

37. **What remains future work in identity assurance?**  
Continuous face verification, robust unknown-person detection, and production-grade substitution detection require stronger live AI services.

38. **How is duplicate enrolment handled?**  
The system validates unique student/candidate IDs, email, institution-specific identifiers, and includes prototype face duplicate checks with documented limitations.

## Computer Vision

39. **What visual intelligence is implemented?**  
SERPS supports face presence/absence, camera obstruction, multiple-person, looking-away, and object-event foundations with structured evidence output.

40. **Does visual intelligence decide cheating?**  
No. It emits evidence events only. CIE and human review handle contextual interpretation.

41. **What does live dual-camera validation prove?**  
It proves that two physical cameras can be discovered, selected, sampled, displayed, and converted into structured camera events without auto-activating on page load.

42. **Does live camera validation feed the AI evidence pipeline?**  
Yes. Explicitly sampled live frames can be encoded, passed into the visual detector layer, converted into structured EvidenceEvents, and ingested by the CIE.

43. **Why include Viva Split-Screen Demonstration Mode?**  
It helps the panel see the separation between candidate-facing exam experience and reviewer/proctor intelligence, while making clear that production candidates would not see the reviewer dashboard.

## Audio Intelligence

44. **What audio intelligence is currently supported?**  
The prototype includes structured audio event generation for background speech, prolonged speech, silence, environmental noise, and suspicious audio patterns.

45. **Is continuous audio analysis production-grade?**  
No. The modular design allows future Whisper, Silero VAD, or WebRTC VAD integration.

## Streamlit and FastAPI

46. **Why use Streamlit?**  
Streamlit is suitable for a capstone dashboard, rapid viva demonstration, controlled workflows, and local reproducibility.

47. **What is Streamlit not suitable for?**  
It is not ideal for production-grade multi-user real-time WebRTC monitoring or long-running continuous AI inference.

48. **Why include FastAPI?**  
FastAPI provides an API/service boundary for structured event ingestion and future AI service integration.

49. **Why not build React now?**  
React/Next.js is a future production frontend direction. It is outside the current capstone scope.

## Privacy and NDPA

50. **How does SERPS support privacy by design?**  
Cameras do not activate on page load, evidence is structured and auditable, candidate-facing messages avoid accusation, and human review remains final.

51. **How does SERPS relate to NDPA concerns?**  
It demonstrates data minimisation, consent capture, auditability, explainability, and controlled evidence handling, although full legal compliance would require institutional deployment review.

## Limitations and Future Work

52. **What are the main prototype limitations?**  
Continuous live monitoring is not fully production-grade, SQLite is local, some AI modules are simulation or user-triggered, and cloud deployment is secondary.

53. **What would you improve after submission?**  
I would implement React/Next.js frontends, FastAPI inference workers, PostgreSQL persistence, WebRTC streaming, stronger AI models, and institutional integrations.

54. **What is the most important future research direction?**  
Strengthening live AI perception while preserving the governance pipeline: detection modules produce evidence, CIE reasons, IPIME applies process, and humans decide.
