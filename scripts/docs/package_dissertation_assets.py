from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "docs" / "dissertation"
SERPS_VERSION = "1.0"


@dataclass(frozen=True)
class DiagramDefinition:
    figure: str
    slug: str
    title: str
    chapter: str
    mermaid: str
    caption: str
    source: str


def build_dissertation_assets(
    *,
    project_root: Path = PROJECT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    mode: str = "dissertation",
) -> dict[str, Any]:
    """Generate reproducible dissertation artefacts from implementation sources."""
    output_root = Path(output_root)
    paths = _ensure_directories(output_root)
    artefacts: list[dict[str, Any]] = []
    limitations: list[str] = []

    diagrams = _diagram_definitions(project_root)
    captions = []
    for diagram in diagrams:
        source_path = paths["uml"] / f"{_figure_token(diagram.figure)}_{diagram.slug}.mmd"
        _write_text(source_path, diagram.mermaid)
        artefacts.append(_manifest_entry(source_path, "mermaid", diagram.source, "generated"))
        captions.append(
            {
                "figure": diagram.figure,
                "title": diagram.title,
                "chapter": diagram.chapter,
                "caption": diagram.caption,
                "source": "Author's implementation-derived architecture, SERPS v1.0.",
                "editable_source": _relative(source_path, project_root),
            }
        )

    render_note = _render_mermaid_if_available(paths["uml"], paths["figures"], project_root)
    if render_note:
        limitations.append(render_note)
        limitation_path = paths["figures"] / "DIAGRAM_EXPORT_LIMITATIONS.md"
        _write_text(limitation_path, f"# Diagram Export Limitation\n\n{render_note}\n")
        artefacts.append(_manifest_entry(limitation_path, "limitation", "Mermaid renderer availability", "documented"))
    else:
        for rendered in sorted(paths["figures"].glob("*.*")):
            if rendered.suffix.lower() in {".svg", ".png"}:
                artefacts.append(_manifest_entry(rendered, rendered.suffix.lower().lstrip("."), "Mermaid CLI render", "generated"))

    openapi_result = _export_openapi(paths["api"], project_root)
    artefacts.extend(openapi_result["artefacts"])
    limitations.extend(openapi_result["limitations"])

    scenario_result = _export_viva_scenarios(paths["chapter5_eval"], project_root)
    artefacts.extend(scenario_result["artefacts"])
    limitations.extend(scenario_result["limitations"])

    architecture_path = paths["chapter3_arch"] / "serps_frozen_architecture_summary.json"
    _write_json(architecture_path, _architecture_summary())
    artefacts.append(_manifest_entry(architecture_path, "json", "Frozen SERPS architecture", "generated"))

    screenshot_note = paths["screenshots"] / "SCREENSHOT_CAPTURE_LIMITATIONS.md"
    _write_text(
        screenshot_note,
        "# Screenshot Capture Limitation\n\n"
        "Automated screenshot capture is scaffolded for Dissertation Mode but is not executed by this foundation build. "
        "Future builds should drive the Streamlit UI through Playwright or an equivalent browser runner after the app "
        "is started in a controlled demonstration mode. No screenshots are fabricated by this pipeline.\n",
    )
    artefacts.append(_manifest_entry(screenshot_note, "limitation", "Screenshot automation scaffold", "documented"))

    captions_path = paths["captions"] / "captions.json"
    _write_json(captions_path, {"captions": captions})
    artefacts.append(_manifest_entry(captions_path, "json", "Caption generator", "generated"))

    captions_md_path = paths["captions"] / "captions.md"
    _write_text(captions_md_path, _captions_markdown(captions))
    artefacts.append(_manifest_entry(captions_md_path, "markdown", "Caption generator", "generated"))

    manifest = {
        "serps_version": SERPS_VERSION,
        "mode": mode,
        "git_commit_hash": _git_commit(project_root),
        "working_tree_dirty": _working_tree_dirty(project_root),
        "generation_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generating_script": _relative(Path(__file__).resolve(), project_root),
        "private_sources_excluded": [
            "Dissertation-Requirements.docx",
            "Dissertation-Requirements.pdf",
            "System Specification.pdf",
            "private dissertation drafts and writing guidance",
        ],
        "limitations": limitations,
        "artefacts": artefacts,
    }
    manifest_path = output_root / "manifest.json"
    _write_json(manifest_path, manifest)
    _write_json(paths["manifests"] / "manifest.json", manifest)
    manifest["manifest_path"] = _relative(manifest_path, project_root)
    return manifest


def _ensure_directories(output_root: Path) -> dict[str, Path]:
    paths = {
        "root": output_root,
        "chapter3": output_root / "chapter3",
        "figures": output_root / "chapter3" / "figures",
        "uml": output_root / "chapter3" / "uml",
        "chapter3_arch": output_root / "chapter3" / "architecture",
        "flowcharts": output_root / "chapter3" / "flowcharts",
        "api": output_root / "chapter3" / "api",
        "chapter4": output_root / "chapter4",
        "screenshots": output_root / "chapter4" / "screenshots",
        "testing": output_root / "chapter4" / "testing",
        "interfaces": output_root / "chapter4" / "interfaces",
        "outputs": output_root / "chapter4" / "outputs",
        "logs": output_root / "chapter4" / "logs",
        "chapter5": output_root / "chapter5",
        "chapter5_eval": output_root / "chapter5" / "evaluation",
        "metrics": output_root / "chapter5" / "metrics",
        "charts": output_root / "chapter5" / "charts",
        "reports": output_root / "chapter5" / "reports",
        "manifests": output_root / "manifests",
        "captions": output_root / "captions",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    for empty_key in ("flowcharts", "testing", "interfaces", "outputs", "logs", "metrics", "charts", "reports"):
        keep = paths[empty_key] / ".gitkeep"
        keep.touch(exist_ok=True)
    return paths


def _diagram_definitions(project_root: Path) -> list[DiagramDefinition]:
    return [
        DiagramDefinition(
            "Figure 3.1",
            "high_level_architecture",
            "High-Level Architecture of SERPS",
            "Chapter 3",
            """flowchart LR
    Candidate["Candidate / Exam Environment"] --> Sensors["Sensor Layer"]
    Sensors --> Detection["Detection Modules"]
    Detection --> Events["Structured Evidence Events"]
    Events --> CIE["Contextual Intelligence Engine"]
    CIE --> Agent["Agentic Decision Support"]
    Agent --> IPIME["Institutional Policy & Incident Management Engine"]
    IPIME --> Reviewer["Human Reviewer"]
    Reviewer --> Decision["Final Decision"]
    CIE --> SQLite["SQLite Evidence Store"]
    SQLite --> Dashboard["Streamlit Dashboard"]
    API["FastAPI Structured Event API"] --> Events
""",
            "High-level architecture of SERPS showing the frozen governance pipeline from sensors through human review.",
            "Frozen architecture definition and implemented modules.",
        ),
        DiagramDefinition(
            "Figure 3.2",
            "layered_architecture",
            "Detailed Layered Architecture",
            "Chapter 3",
            """flowchart TB
    subgraph UI["Presentation Layer"]
        Streamlit["Streamlit Dashboard"]
        TestPlayer["Prototype Test Player"]
    end
    subgraph API["Service Boundary"]
        FastAPI["FastAPI Structured Event API"]
    end
    subgraph Detection["Detection Layer"]
        Camera["Camera Stream Foundation"]
        Vision["Visual Intelligence"]
        Audio["Audio Intelligence"]
        Identity["Identity Assurance"]
        Behaviour["Behavioural Analytics"]
    end
    subgraph Reasoning["Contextual Intelligence Engine"]
        Fusion["Event Fusion Module"]
        Memory["Temporal Behaviour Memory"]
        Scoring["Risk Scoring Engine"]
        Context["Contextual Reasoning Module"]
        Explain["Explainability Interface"]
    end
    subgraph Governance["Governance Layer"]
        Agent["Agentic Decision Support"]
        Policy["IPIME Policy-as-Code"]
        Review["Human Review Workflow"]
    end
    subgraph Storage["Persistence Layer"]
        DB["SQLite"]
        Audit["Audit Trail"]
        Evidence["Evidence Packages"]
    end
    UI --> API
    API --> Detection
    Detection --> Reasoning
    Reasoning --> Governance
    Governance --> Storage
    Detection --> Storage
    UI --> Storage
""",
            "Detailed layered architecture of SERPS, separating user interface, service boundary, detection, CIE reasoning, governance, and persistence.",
            "Implemented package layout under src/ and app.py.",
        ),
        DiagramDefinition(
            "Figure 3.3",
            "system_workflow",
            "System Workflow",
            "Chapter 3",
            """flowchart TD
    Start([Start]) --> Enrol["Register candidate and consent"]
    Enrol --> Face["Guided facial enrolment"]
    Face --> PreExam["Pre-exam device and environment checks"]
    PreExam --> Auth["Candidate authentication"]
    Auth --> Session["Start monitored session"]
    Session --> Evidence["Generate structured evidence"]
    Evidence --> CIE["CIE contextual reasoning"]
    CIE --> Agent["Agent recommends action"]
    Agent --> Policy["IPIME evaluates institutional policy"]
    Policy --> Ack{"Candidate acknowledgement required?"}
    Ack -- Yes --> CandidateAck["Candidate explains and acknowledges incident"]
    Ack -- No --> Review["Human reviewer reviews evidence"]
    CandidateAck --> Review
    Review --> Outcome["Final authorised outcome"]
    Outcome --> Report["Audit and reports"]
    Report --> End([End])
""",
            "End-to-end workflow of candidate enrolment, session gating, evidence generation, contextual reasoning, policy response, human review, and reporting.",
            "Implemented UI workflow and viva scenario validation pipeline.",
        ),
        DiagramDefinition(
            "Figure 3.4",
            "use_case_diagram",
            "Use Case Diagram",
            "Chapter 3",
            """flowchart LR
    Candidate((Candidate))
    Reviewer((Reviewer / Proctor))
    Admin((Administrator))
    SysAdmin((System Administrator))
    Enrol["Register and Consent"]
    Capture["Complete Face Capture"]
    Authenticate["Authenticate for Exam"]
    TakeExam["Take Prototype Assessment"]
    Monitor["Monitor Session"]
    Review["Review Contextual Alerts"]
    Policy["Manage Institutional Policies"]
    Reports["Generate Reports"]
    API["Maintain API / Services"]
    Candidate --> Enrol
    Candidate --> Capture
    Candidate --> Authenticate
    Candidate --> TakeExam
    Reviewer --> Monitor
    Reviewer --> Review
    Reviewer --> Reports
    Admin --> Enrol
    Admin --> Policy
    Admin --> Reports
    SysAdmin --> API
    SysAdmin --> Policy
""",
            "Use case view of SERPS actors and major capabilities supported by the prototype.",
            "Implemented navigation modules and role simulator.",
        ),
        DiagramDefinition(
            "Figure 3.5",
            "activity_diagram",
            "Activity Diagram",
            "Chapter 3",
            """flowchart TD
    A([Candidate arrives]) --> B["Verify candidate profile"]
    B --> C{"Biodata and consent saved?"}
    C -- No --> D["Complete registration"]
    C -- Yes --> E["Run pre-exam checks"]
    D --> E
    E --> F{"Checks pass or staff override?"}
    F -- No --> E
    F -- Yes --> G["Authenticate candidate"]
    G --> H{"Authentication pass or override?"}
    H -- No --> G
    H -- Yes --> I["Start session"]
    I --> J["Detection modules emit EvidenceEvent rows"]
    J --> K["CIE evaluates temporal context"]
    K --> L["Agent recommends action"]
    L --> M["IPIME applies institution policy"]
    M --> N{"Incident acknowledgement required?"}
    N -- Yes --> O["Candidate acknowledgement workflow"]
    N -- No --> P["Reviewer queue"]
    O --> P
    P --> Q["Reviewer records action and rationale"]
    Q --> R([Final outcome recorded])
""",
            "Activity diagram covering the complete examination governance lifecycle implemented in SERPS.",
            "Session, CIE, IPIME, and review modules.",
        ),
        DiagramDefinition(
            "Figure 3.6",
            "sequence_diagram",
            "Sequence Diagram",
            "Chapter 3",
            """sequenceDiagram
    participant Candidate
    participant UI as SERPS UI
    participant API as FastAPI Backend
    participant CIE as Contextual Intelligence Engine
    participant Agent as Agentic Decision Support
    participant IPIME
    participant DB as SQLite
    participant Reviewer
    Candidate->>UI: Complete enrolment and authentication
    UI->>DB: Store candidate, consent, checks, session
    API->>DB: Persist structured EvidenceEvent
    API->>CIE: Submit evidence for contextual reasoning
    CIE->>DB: Store contextual/fused alert
    CIE->>Agent: Provide risk and explanation
    Agent->>IPIME: Send recommended intervention
    IPIME->>DB: Store policy decision
    IPIME-->>UI: Candidate acknowledgement workflow if required
    Candidate->>UI: Submit explanation and acknowledgement
    UI->>DB: Store acknowledgement
    Reviewer->>UI: Review alert, evidence, policy decision
    UI->>DB: Store reviewer decision and audit trail
""",
            "Sequence of interactions between the candidate, SERPS UI, FastAPI backend, CIE, agentic decision support, IPIME, database, and reviewer.",
            "FastAPI service, Streamlit UI, CIE, policy, and storage modules.",
        ),
        DiagramDefinition(
            "Figure 3.7",
            "entity_relationship_diagram",
            "Entity Relationship Diagram",
            "Chapter 3",
            _database_er_mermaid(project_root),
            "Entity relationship diagram generated from the implemented SQLite schema.",
            "src/storage/database.py SCHEMA constant.",
        ),
        DiagramDefinition(
            "Figure 3.8",
            "system_flowchart",
            "System Flowchart",
            "Chapter 3",
            """flowchart TD
    Input[/Sensor and user inputs/] --> Detect[Detection modules]
    Detect --> Structured[Create immutable EvidenceEvent]
    Structured --> Store[(SQLite events)]
    Store --> Window[Select temporal window]
    Window --> Fusion[Event Fusion Module]
    Fusion --> Memory[Temporal Behaviour Memory]
    Memory --> Score[Risk Scoring Engine]
    Score --> Explain[Explainability Interface]
    Explain --> Agent[Agentic Decision Support]
    Agent --> Policy[IPIME policy workflow]
    Policy --> Human[Human reviewer]
    Human --> Final[/Final decision and report/]
""",
            "System flowchart of the SERPS evidence processing and governance pathway.",
            "Frozen processing pipeline and implemented modules.",
        ),
        DiagramDefinition(
            "Figure 3.9",
            "api_interaction_model",
            "API Interaction Model",
            "Chapter 3",
            """flowchart LR
    External["External detector / secure exam player"] --> EventsAPI["POST /events"]
    External --> VisionAPI["POST /vision/analyse-frame"]
    External --> AudioAPI["POST /audio/analyse-features"]
    External --> IdentityAPI["POST /identity/analyse-confidence"]
    EventsAPI --> Store["SQLite EvidenceEvent"]
    VisionAPI --> Store
    AudioAPI --> Store
    IdentityAPI --> Store
    Store --> CIE["Contextual Intelligence Engine"]
    CIE --> Alerts["Contextual alerts"]
    Alerts --> Dashboard["Streamlit dashboard"]
    Alerts --> Review["Human review"]
""",
            "API interaction model derived from the implemented FastAPI structured-event service boundary.",
            "src/services/event_api.py FastAPI endpoints.",
        ),
    ]


def _database_er_mermaid(project_root: Path) -> str:
    source = (project_root / "src" / "storage" / "database.py").read_text(encoding="utf-8")
    schema_match = re.search(r'SCHEMA\s*=\s*"""(?P<schema>.*?)"""', source, flags=re.DOTALL)
    schema = schema_match.group("schema") if schema_match else source
    tables = re.findall(r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\);", schema, flags=re.DOTALL | re.IGNORECASE)
    lines = ["erDiagram"]
    relationships: list[str] = []
    for table, body in tables:
        lines.append(f"    {table} {{")
        for raw_column in body.splitlines():
            column = raw_column.strip().rstrip(",")
            if not column or column.upper().startswith("FOREIGN KEY"):
                continue
            parts = column.split()
            if len(parts) < 2:
                continue
            name, dtype = parts[0], parts[1]
            marker = " PK" if "PRIMARY KEY" in column.upper() else ""
            lines.append(f"        {dtype} {name}{marker}")
        lines.append("    }")
        for column, ref_table, _ref_column in re.findall(r"FOREIGN KEY\((\w+)\)\s+REFERENCES\s+(\w+)\((\w+)\)", body, flags=re.IGNORECASE):
            relationships.append(f"    {ref_table} ||--o{{ {table} : {column}")
    lines.extend(sorted(set(relationships)))
    return "\n".join(lines) + "\n"


def _render_mermaid_if_available(source_dir: Path, output_dir: Path, project_root: Path) -> str | None:
    renderer = shutil.which("mmdc")
    if not renderer:
        return (
            "Mermaid CLI (mmdc) is not installed in this environment, so the foundation build generated editable .mmd "
            "sources only. Install Mermaid CLI to export SVG/PNG without changing the source diagrams."
        )
    for source in sorted(source_dir.glob("*.mmd")):
        for suffix in (".svg", ".png"):
            output = output_dir / f"{source.stem}{suffix}"
            subprocess.run([renderer, "-i", str(source), "-o", str(output)], cwd=project_root, check=True)
    return None


def _export_openapi(api_dir: Path, project_root: Path) -> dict[str, Any]:
    try:
        sys.path.insert(0, str(project_root))
        from src.services.event_api import create_app

        app = create_app()
        openapi = app.openapi()
        path = api_dir / "openapi.json"
        _write_json(path, openapi)
        return {"artefacts": [_manifest_entry(path, "json", "FastAPI OpenAPI schema", "generated")], "limitations": []}
    except Exception as exc:  # pragma: no cover - defensive documentation path
        path = api_dir / "OPENAPI_EXPORT_LIMITATIONS.md"
        message = f"OpenAPI export could not be completed in this environment: {exc}"
        _write_text(path, f"# OpenAPI Export Limitation\n\n{message}\n")
        return {"artefacts": [_manifest_entry(path, "limitation", "FastAPI OpenAPI schema", "documented")], "limitations": [message]}
    finally:
        try:
            sys.path.remove(str(project_root))
        except ValueError:
            pass


def _export_viva_scenarios(output_dir: Path, project_root: Path) -> dict[str, Any]:
    try:
        sys.path.insert(0, str(project_root))
        from src.evaluation.viva_scenarios import list_viva_scenarios

        scenarios = []
        for scenario in list_viva_scenarios():
            scenarios.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "expected_risk_level": scenario.expected_risk_level,
                    "expected_policy_response": scenario.expected_policy_response,
                    "reviewer_action": scenario.reviewer_action,
                    "final_outcome_status": scenario.final_outcome_status,
                    "policy_profile": scenario.policy_profile,
                    "event_count": sum(event.count for event in scenario.events),
                    "event_types": [event.event_type for event in scenario.events],
                    "notes": scenario.notes,
                }
            )
        path = output_dir / "viva_scenario_catalog.json"
        _write_json(path, {"scenarios": scenarios})
        return {"artefacts": [_manifest_entry(path, "json", "Implemented viva scenario catalog", "generated")], "limitations": []}
    except Exception as exc:  # pragma: no cover - defensive documentation path
        path = output_dir / "VIVA_SCENARIO_EXPORT_LIMITATIONS.md"
        message = f"Viva scenario export could not be completed in this environment: {exc}"
        _write_text(path, f"# Viva Scenario Export Limitation\n\n{message}\n")
        return {"artefacts": [_manifest_entry(path, "limitation", "Implemented viva scenario catalog", "documented")], "limitations": [message]}
    finally:
        try:
            sys.path.remove(str(project_root))
        except ValueError:
            pass


def _architecture_summary() -> dict[str, Any]:
    return {
        "serps_version": SERPS_VERSION,
        "architecture_status": "Version 1.0 frozen",
        "pipeline": [
            "Sensor Layer",
            "Detection Modules",
            "Structured Evidence Generation",
            "Contextual Intelligence Engine",
            "Agentic Decision Support",
            "Institutional Policy & Incident Management Engine",
            "Human Reviewer",
            "Final Decision",
        ],
        "contextual_intelligence_engine": [
            "Event Fusion Module",
            "Temporal Behaviour Memory",
            "Risk Scoring Engine",
            "Contextual Reasoning Module",
            "Explainability Interface",
        ],
        "governance_rules": [
            "Detection modules emit structured evidence only.",
            "CIE is the sole reasoning engine.",
            "Agentic Decision Support recommends actions only.",
            "IPIME determines institution-specific workflow only.",
            "Human reviewers make final decisions.",
        ],
    }


def _captions_markdown(captions: list[dict[str, str]]) -> str:
    lines = ["# SERPS Figure Captions", ""]
    for item in captions:
        lines.extend(
            [
                f"## {item['figure']}: {item['title']}",
                "",
                item["caption"],
                "",
                f"Source: {item['source']}",
                "",
            ]
        )
    return "\n".join(lines)


def _manifest_entry(path: Path, artefact_type: str, source: str, status: str) -> dict[str, str]:
    return {
        "path": _relative(path, PROJECT_ROOT),
        "artefact_type": artefact_type,
        "source": source,
        "status": status,
        "checksum_sha256": _sha256(path),
    }


def _figure_token(figure: str) -> str:
    normalised = figure.lower().replace("figure", "fig")
    return re.sub(r"[^a-z0-9]+", "_", normalised).strip("_")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, content: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_commit(project_root: Path) -> str:
    return _run_git(project_root, ["rev-parse", "--short", "HEAD"]) or "unknown"


def _working_tree_dirty(project_root: Path) -> bool:
    return bool(_run_git(project_root, ["status", "--short"]))


def _run_git(project_root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=project_root, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SERPS dissertation artefacts from implementation sources.")
    parser.add_argument("--mode", default="dissertation", choices=["dissertation"], help="Documentation build mode.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Output root for generated documentation artefacts.")
    args = parser.parse_args()

    manifest = build_dissertation_assets(output_root=Path(args.output_root), mode=args.mode)
    print(f"Generated {len(manifest['artefacts'])} documentation artefact(s).")
    print(f"Manifest: {manifest['manifest_path']}")
    if manifest["limitations"]:
        print("Limitations:")
        for limitation in manifest["limitations"]:
            print(f"- {limitation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
