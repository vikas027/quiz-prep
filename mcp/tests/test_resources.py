import asyncio
import json
from unittest.mock import MagicMock, patch

import httpx


def _mock_resp(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    resp.raise_for_status.return_value = None if status < 400 else None
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
    return resp


def test_catalog_resource_returns_json():
    from resources import get_catalog

    data = [{"name": "cka", "label": "CKA"}]
    with patch("httpx.request", return_value=_mock_resp(data)):
        result = get_catalog()
    parsed = json.loads(result)
    assert parsed[0]["name"] == "cka"


def test_catalog_resource_empty_not_error():
    from resources import get_catalog

    with patch("httpx.request", return_value=_mock_resp([])):
        result = get_catalog()
    assert json.loads(result) == []


def test_questions_resource():
    from resources import get_quiz_questions

    data = [{"id": 1, "question": "Q?", "answer": "A. yes"}]
    with patch("httpx.request", return_value=_mock_resp(data)):
        result = get_quiz_questions("cka")
    parsed = json.loads(result)
    assert parsed[0]["id"] == 1


def test_scores_resource():
    from resources import get_quiz_scores

    data = [{"score": 8, "total": 10, "pct": 80}]
    with patch("httpx.request", return_value=_mock_resp(data)):
        result = get_quiz_scores("cka")
    parsed = json.loads(result)
    assert parsed[0]["pct"] == 80


def test_questions_resource_sends_limit_param():
    from resources import get_quiz_questions

    with patch("httpx.request", return_value=_mock_resp([])) as mock:
        get_quiz_questions("cka")
    params = mock.call_args.kwargs.get("params", {})
    assert params.get("limit") == 50


def test_scores_resource_empty_not_error():
    from resources import get_quiz_scores

    with patch("httpx.request", return_value=_mock_resp([])):
        result = get_quiz_scores("cka")
    assert json.loads(result) == []


# --- MCP registry tests ---


def test_exactly_5_tools_registered():
    import resources as _resources  # noqa: F401 — registers resources
    import tools as _tools  # noqa: F401 — registers tools
    from app import mcp

    tool_list = asyncio.run(mcp.list_tools())
    assert len(tool_list) == 5, f"Expected 5 tools, got {len(tool_list)}: {[t.name for t in tool_list]}"


def test_exactly_3_resources_registered():
    import resources as _resources  # noqa: F401
    import tools as _tools  # noqa: F401
    from app import mcp

    resource_list = asyncio.run(mcp.list_resources())
    templates = asyncio.run(mcp.list_resource_templates())
    total = len(resource_list) + len(templates)
    assert total == 3, f"Expected 3 resources/templates, got {total}"


def test_all_tool_parameters_have_descriptions():
    import resources as _resources  # noqa: F401
    import tools as _tools  # noqa: F401
    from app import mcp

    tool_list = asyncio.run(mcp.list_tools())
    for tool in tool_list:
        for param_name, param_info in tool.parameters.get("properties", {}).items():
            assert "description" in param_info, f"Tool '{tool.name}' param '{param_name}' missing description"


def test_read_only_tools_have_annotation():
    import resources as _resources  # noqa: F401
    import tools as _tools  # noqa: F401
    from app import mcp

    read_only = {"list_quizzes", "get_questions"}
    tool_list = asyncio.run(mcp.list_tools())
    for tool in tool_list:
        if tool.name in read_only:
            assert tool.annotations.readOnlyHint is True, f"Tool '{tool.name}' should have readOnlyHint=True"


def test_destructive_tools_have_annotation():
    import resources as _resources  # noqa: F401
    import tools as _tools  # noqa: F401
    from app import mcp

    destructive = {"manage_quiz", "manage_question"}
    tool_list = asyncio.run(mcp.list_tools())
    for tool in tool_list:
        if tool.name in destructive:
            assert tool.annotations.destructiveHint is True, f"Tool '{tool.name}' should have destructiveHint=True"
