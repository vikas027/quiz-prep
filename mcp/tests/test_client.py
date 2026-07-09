import json as _j
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


def _parse_error(exc: ToolError) -> dict:
    return _j.loads(str(exc))


def test_api_call_success():
    from client import _api_call

    with patch("httpx.request", return_value=_mock_resp({"ok": True})):
        result = _api_call("GET", "/quizzes")
    assert result == {"ok": True}


def test_api_call_404_raises_structured_error():
    from client import _api_call

    with patch("httpx.request", return_value=_mock_resp({}, 404)):
        with pytest.raises(ToolError) as exc_info:
            _api_call("GET", "/quizzes/ghost")
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "business"
    assert err["isRetryable"] is False
    assert "/quizzes/ghost" in err["attempted"]
    assert "customerMessage" in err
    assert "suggestedAction" in err


def test_api_call_409_raises_structured_error():
    from client import _api_call

    with patch("httpx.request", return_value=_mock_resp({}, 409)):
        with pytest.raises(ToolError) as exc_info:
            _api_call("POST", "/quizzes")
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "business"
    assert err["isRetryable"] is False


def test_api_call_422_raises_structured_error():
    from client import _api_call

    resp = _mock_resp({"detail": "answer not in choices"}, 422)
    with patch("httpx.request", return_value=resp):
        with pytest.raises(ToolError) as exc_info:
            _api_call("POST", "/quizzes/cka/questions")
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "validation"
    assert err["isRetryable"] is True
    assert "answer not in choices" in err["customerMessage"]


def test_api_call_401_raises_permission_error():
    from client import _api_call

    with patch("httpx.request", return_value=_mock_resp({}, 401)):
        with pytest.raises(ToolError) as exc_info:
            _api_call("GET", "/quizzes")
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "permission"
    assert err["isRetryable"] is False


def test_api_call_retries_once_on_network_error():
    from client import _api_call

    call_count = 0

    def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("timeout")
        return _mock_resp({"ok": True})

    with patch("httpx.request", side_effect=fake_request):
        with patch("client.time.sleep"):
            result = _api_call("GET", "/quizzes")
    assert call_count == 2
    assert result == {"ok": True}


def test_api_call_raises_after_two_network_errors():
    from client import _api_call

    with patch("httpx.request", side_effect=httpx.ConnectError("timeout")):
        with patch("client.time.sleep"):
            with pytest.raises(ToolError) as exc_info:
                _api_call("GET", "/quizzes")
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "transient"
    assert err["isRetryable"] is True


def test_api_call_transient_error_includes_path():
    from client import _api_call

    with patch("httpx.request", side_effect=httpx.ConnectError("timeout")):
        with patch("client.time.sleep"):
            with pytest.raises(ToolError) as exc_info:
                _api_call("GET", "/quizzes/cka")
    err = _parse_error(exc_info.value)
    assert "/quizzes/cka" in err["attempted"]


def test_api_call_404_does_not_retry():
    from client import _api_call

    call_count = 0

    def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _mock_resp({}, 404)

    with patch("httpx.request", side_effect=fake_request):
        with pytest.raises(ToolError) as exc_info:
            _api_call("GET", "/quizzes/ghost")
    assert call_count == 1
    err = _parse_error(exc_info.value)
    assert err["isRetryable"] is False


def test_api_call_429_retries_once_then_raises():
    from client import _api_call

    call_count = 0

    def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        resp = _mock_resp({}, 429)
        resp.headers = {"Retry-After": "1"}
        return resp

    with patch("httpx.request", side_effect=fake_request):
        with patch("client.time.sleep"):
            with pytest.raises(ToolError) as exc_info:
                _api_call("GET", "/quizzes")
    assert call_count == 2
    err = _parse_error(exc_info.value)
    assert err["errorCategory"] == "rate_limit"
    assert err["isRetryable"] is True


def test_api_call_429_retry_then_success():
    from client import _api_call

    call_count = 0

    def fake_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            resp = _mock_resp({}, 429)
            resp.headers = {}
            return resp
        return _mock_resp([{"name": "cka"}])

    with patch("httpx.request", side_effect=fake_request):
        with patch("client.time.sleep"):
            result = _api_call("GET", "/quizzes")
    assert call_count == 2
    assert result[0]["name"] == "cka"


def test_api_call_empty_list_is_not_error():
    from client import _api_call

    with patch("httpx.request", return_value=_mock_resp([])):
        result = _api_call("GET", "/quizzes")
    assert result == []


def test_api_call_different_errors_get_different_categories():
    from client import _api_call

    def get_error(status):
        with patch("httpx.request", return_value=_mock_resp({"detail": "x"}, status)):
            with pytest.raises(ToolError) as exc_info:
                _api_call("POST", "/quizzes")
        return _parse_error(exc_info.value)

    assert get_error(404)["errorCategory"] == "business"
    assert get_error(409)["errorCategory"] == "business"
    assert get_error(422)["errorCategory"] == "validation"
    assert get_error(401)["errorCategory"] == "permission"

    messages = [get_error(s)["customerMessage"] for s in (404, 409, 422, 401)]
    assert len(set(messages)) == len(messages)
