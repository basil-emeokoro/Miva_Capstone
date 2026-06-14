from src.session.exam_controller import grade_answers


def test_grade_answers_scores_demo_submission() -> None:
    questions = [
        {"question_id": "Q1", "answer": "A"},
        {"question_id": "Q2", "answer": "B"},
    ]
    result = grade_answers({"Q1": "A", "Q2": "C"}, questions)
    assert result["correct"] == 1
    assert result["total"] == 2
    assert result["percentage"] == 50.0
