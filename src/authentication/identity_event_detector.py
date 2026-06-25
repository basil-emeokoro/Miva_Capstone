from __future__ import annotations

from dataclasses import dataclass

from src.fusion.event_schema import EvidenceEvent


@dataclass(frozen=True)
class IdentityEventDefinition:
    label: str
    event_type: str
    risk_weight: float
    confidence: float
    description: str


@dataclass(frozen=True)
class IdentityAnalysisResult:
    event_type: str
    confidence: float
    description: str
    detector_name: str = "identity_assurance_pipeline"


IDENTITY_EVENT_DEFINITIONS: dict[str, IdentityEventDefinition] = {
    "identity_verified": IdentityEventDefinition(
        "Identity verified",
        "identity_verified",
        0.02,
        0.9,
        "Candidate identity confidence is within the expected range.",
    ),
    "identity_confidence_low": IdentityEventDefinition(
        "Identity confidence low",
        "identity_confidence_low",
        0.5,
        0.72,
        "Candidate identity confidence is below the expected verification range.",
    ),
    "face_mismatch_detected": IdentityEventDefinition(
        "Face mismatch detected",
        "face_mismatch_detected",
        0.78,
        0.82,
        "Current face sample does not match the enrolled candidate template.",
    ),
    "candidate_substitution_suspected": IdentityEventDefinition(
        "Candidate substitution suspected",
        "candidate_substitution_suspected",
        0.86,
        0.84,
        "Identity evidence suggests possible candidate substitution.",
    ),
    "unknown_face_detected": IdentityEventDefinition(
        "Unknown face detected",
        "unknown_face_detected",
        0.74,
        0.8,
        "An unknown face was detected during identity assurance.",
    ),
}


def create_identity_event(
    session_id: str,
    candidate_id: str,
    event_type: str,
    confidence: float | None = None,
    description: str | None = None,
    evidence_path: str | None = None,
) -> EvidenceEvent:
    try:
        definition = IDENTITY_EVENT_DEFINITIONS[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported identity event type: {event_type}") from exc
    return EvidenceEvent(
        session_id=session_id,
        candidate_id=candidate_id,
        source_module="identity",
        event_type=definition.event_type,
        risk_weight=definition.risk_weight,
        confidence=confidence if confidence is not None else definition.confidence,
        camera_id="primary",
        evidence_path=evidence_path,
        description=description or definition.description,
    )


def create_identity_event_from_analysis(
    session_id: str,
    candidate_id: str,
    result: IdentityAnalysisResult,
    evidence_path: str | None = None,
) -> EvidenceEvent:
    return create_identity_event(
        session_id=session_id,
        candidate_id=candidate_id,
        event_type=result.event_type,
        confidence=result.confidence,
        description=f"{result.detector_name}: {result.description}",
        evidence_path=evidence_path,
    )


def analyse_identity_confidence(
    confidence: float,
    threshold: float = 0.65,
    substitution_threshold: float = 0.35,
    unknown_face: bool = False,
    detector_name: str = "periodic_face_verifier",
) -> IdentityAnalysisResult:
    """Translate identity verification output into an evidence signal only."""
    score = max(0.0, min(float(confidence), 1.0))
    if unknown_face:
        return IdentityAnalysisResult(
            "unknown_face_detected",
            max(0.7, 1.0 - score),
            f"Unknown face observed while candidate confidence was {score:.2f}.",
            detector_name,
        )
    if score >= threshold:
        return IdentityAnalysisResult(
            "identity_verified",
            score,
            f"Periodic identity confidence {score:.2f} met the threshold {threshold:.2f}.",
            detector_name,
        )
    if score <= substitution_threshold:
        return IdentityAnalysisResult(
            "candidate_substitution_suspected",
            max(0.75, 1.0 - score),
            f"Identity confidence {score:.2f} is below substitution threshold {substitution_threshold:.2f}.",
            detector_name,
        )
    return IdentityAnalysisResult(
        "face_mismatch_detected" if score < threshold * 0.85 else "identity_confidence_low",
        max(0.68, 1.0 - score),
        f"Identity confidence {score:.2f} is below threshold {threshold:.2f}.",
        detector_name,
    )
