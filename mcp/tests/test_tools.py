from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastmcp.exceptions import ToolError


def _mock_resp(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


# --- list_quizzes ---


def test_list_quizzes_returns_all():
    from tools import list_quizzes

    data = [{"id": 1, "name": "cka", "label": "CKA"}]
    with patch("httpx.request", return_value=_mock_resp(data)):
        result = list_quizzes()
    assert result == data


def test_list_quizzes_empty_is_not_error():
    from tools import list_quizzes

    with patch("httpx.request", return_value=_mock_resp([])):
        result = list_quizzes()
    assert result == []


# --- get_questions ---


def test_get_questions_no_filter():
    from tools import get_questions

    data = [{"id": 1, "question": "What is a Pod?", "answer": "A. container group"}]
    with patch("httpx.request", return_value=_mock_resp(data)) as mock:
        result = get_questions("cka")
    assert result == data
    call_kwargs = mock.call_args
    assert call_kwargs.kwargs.get("params") == {"limit": 50, "show": "enabled"}


def test_get_questions_with_category_and_limit():
    from tools import get_questions

    with patch("httpx.request", return_value=_mock_resp([])) as mock:
        get_questions("cka", category="Networking", limit=5)
    params = mock.call_args.kwargs["params"]
    assert params["category"] == "Networking"
    assert params["limit"] == 5


# --- manage_quiz ---


def test_manage_quiz_create():
    from tools import manage_quiz

    data = {"id": 1, "name": "new-quiz", "label": "New Quiz"}
    with patch("httpx.request", return_value=_mock_resp(data, 201)) as mock:
        result = manage_quiz("create", "new-quiz", label="New Quiz")
    assert result["name"] == "new-quiz"
    assert mock.call_args.kwargs["json"] == {"name": "new-quiz", "label": "New Quiz"}


def test_manage_quiz_create_requires_label():
    from tools import manage_quiz

    with pytest.raises(ToolError, match="label"):
        manage_quiz("create", "new-quiz")


def test_manage_quiz_delete_fails_without_confirmation():
    from tools import manage_quiz

    with pytest.raises(ToolError, match="confirm_delete"):
        manage_quiz("delete", "cka")


def test_manage_quiz_delete_succeeds_with_confirmation():
    from tools import manage_quiz

    with patch("httpx.request", return_value=_mock_resp({"deleted": "cka"})) as mock:
        manage_quiz("delete", "cka", confirm_delete=True)
    assert mock.call_args.args[0] == "DELETE"
    assert "/quizzes/cka" in mock.call_args.args[1]


def test_manage_quiz_import_requires_yaml():
    from tools import manage_quiz

    with pytest.raises(ToolError, match="yaml_content"):
        manage_quiz("import", "cka")


def test_manage_quiz_unknown_action():
    from tools import manage_quiz

    with pytest.raises(ToolError, match="Unknown action"):
        manage_quiz("fly", "cka")


# --- manage_question ---


def test_manage_question_add_success():
    from tools import manage_question

    data = {"id": 42, "question": "Q?", "answer": "A. yes"}
    with patch("httpx.request", return_value=_mock_resp(data, 201)):
        result = manage_question(
            "add",
            "cka",
            question="Q?",
            choices=["A. yes", "B. no"],
            answer="A. yes",
        )
    assert result["id"] == 42


def test_manage_question_add_requires_fields():
    from tools import manage_question

    with pytest.raises(ToolError, match="question, choices, and answer"):
        manage_question("add", "cka", question="Q?")


def test_manage_question_update_requires_id():
    from tools import manage_question

    with pytest.raises(ToolError, match="question_id"):
        manage_question("update", "cka", question="New text")


def test_manage_question_update_requires_at_least_one_field():
    from tools import manage_question

    with pytest.raises(ToolError, match="at least one field"):
        manage_question("update", "cka", question_id=42)


def test_manage_question_update_answer_alone_rejected():
    from tools import manage_question

    with pytest.raises(ToolError, match="Updating 'answer' alone is not allowed"):
        manage_question("update", "cka", question_id=42, answer="B. new answer")


def test_manage_question_add_answer_must_be_in_choices():
    from tools import manage_question

    with pytest.raises(ToolError, match="exactly match one of the choices"):
        manage_question(
            "add",
            "cka",
            question="Q?",
            choices=["A. yes", "B. no"],
            answer="C. maybe",
        )


def test_manage_scores_record_score_cannot_exceed_total():
    from tools import manage_scores

    with pytest.raises(ToolError, match="cannot exceed total"):
        manage_scores("record", "cka", score=11, total=10)


def test_manage_question_delete_requires_id():
    from tools import manage_question

    with pytest.raises(ToolError, match="question_id"):
        manage_question("delete", "cka")


def test_manage_question_delete_fails_without_confirmation():
    from tools import manage_question

    with pytest.raises(ToolError, match="confirm_delete"):
        manage_question("delete", "cka", question_id=42)


def test_manage_question_delete_succeeds_with_confirmation():
    from tools import manage_question

    with patch("httpx.request", return_value=_mock_resp({"deleted": "42"})) as mock:
        manage_question("delete", "cka", question_id=42, confirm_delete=True)
    assert "DELETE" in str(mock.call_args.args[0])
    assert "/questions/42" in mock.call_args.args[1]


# --- manage_scores ---


def test_manage_scores_get():
    from tools import manage_scores

    data = [{"id": 1, "score": 8, "total": 10, "pct": 80}]
    with patch("httpx.request", return_value=_mock_resp(data)):
        result = manage_scores("get", "cka")
    assert result[0]["pct"] == 80


def test_manage_scores_record():
    from tools import manage_scores

    data = {"id": 5, "score": 9, "total": 10, "pct": 90}
    with patch("httpx.request", return_value=_mock_resp(data, 201)) as mock:
        result = manage_scores("record", "cka", score=9, total=10)
    assert result["pct"] == 90
    assert mock.call_args.kwargs["json"] == {"score": 9, "total": 10}


def test_manage_scores_record_requires_score_and_total():
    from tools import manage_scores

    with pytest.raises(ToolError, match="score and total"):
        manage_scores("record", "cka", score=9)


def test_manage_scores_unknown_action():
    from tools import manage_scores

    with pytest.raises(ToolError, match="Unknown action"):
        manage_scores("summarise", "cka")
