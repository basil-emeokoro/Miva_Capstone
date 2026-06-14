from __future__ import annotations

from pathlib import Path

from src.utils.config_loader import load_config, resolve_project_path


def candidate_enrolment_dir(candidate_id: str) -> Path:
    config = load_config()
    path = resolve_project_path(config["storage"]["enrolment_dir"]) / candidate_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_bytes(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path
