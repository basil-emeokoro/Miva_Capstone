from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.utils.config_loader import ROOT_DIR


def load_sample_questions(path: str | Path | None = None) -> list[dict[str, Any]]:
    question_path = Path(path) if path else ROOT_DIR / "data" / "sample" / "questions.json"
    with question_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def grade_answers(answers: dict[str, str], questions: list[dict[str, Any]] | None = None) -> dict[str, object]:
    question_list = questions or load_sample_questions()
    correct = 0
    for question in question_list:
        if answers.get(question["question_id"]) == question["answer"]:
            correct += 1
    total = len(question_list)
    return {
        "correct": correct,
        "total": total,
        "percentage": round((correct / total) * 100, 2) if total else 0.0,
    }
