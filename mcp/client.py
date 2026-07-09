import json as _json
import logging
import os
import time

import httpx
from fastmcp.exceptions import ToolError

QUIZ_APP_URL = os.environ.get("QUIZ_APP_URL", "http://localhost:8080")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

_log = logging.getLogger(__name__)


def _tool_error(
    *,
    category: str,
    retryable: bool,
    method: str,
    path: str,
    customer_message: str,
    suggested_action: str,
) -> ToolError:
    payload = {
        "errorCategory": category,
        "isRetryable": retryable,
        "attempted": f"{method} {path}",
        "customerMessage": customer_message,
        "suggestedAction": suggested_action,
    }
    return ToolError(_json.dumps(payload, separators=(",", ":")))


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{QUIZ_APP_URL}/api/v1{path}"
    for attempt in range(2):
        try:
            resp = httpx.request(method, url, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            try:
                detail = e.response.json().get("detail", "")
            except Exception:
                detail = e.response.text[:200]
            if status == 400:
                raise _tool_error(
                    category="validation",
                    retryable=True,
                    method=method,
                    path=path,
                    customer_message=f"Invalid input: {detail}",
                    suggested_action="Correct the input and retry.",
                )
            if status in (401, 403):
                raise _tool_error(
                    category="permission",
                    retryable=False,
                    method=method,
                    path=path,
                    customer_message="Authorization error — access denied.",
                    suggested_action="Do not retry.",
                )
            if status == 404:
                raise _tool_error(
                    category="business",
                    retryable=False,
                    method=method,
                    path=path,
                    customer_message=f"Resource not found: {path}",
                    suggested_action="Check the quiz name and try again.",
                )
            if status == 409:
                raise _tool_error(
                    category="business",
                    retryable=False,
                    method=method,
                    path=path,
                    customer_message=f"Resource already exists: {path}",
                    suggested_action="Use a different name or delete the existing one.",
                )
            if status == 422:
                raise _tool_error(
                    category="validation",
                    retryable=True,
                    method=method,
                    path=path,
                    customer_message=f"Validation error: {detail}",
                    suggested_action="Correct the input and retry.",
                )
            if status == 429:
                if attempt == 0:
                    retry_after = e.response.headers.get("Retry-After")
                    delay = min(float(retry_after or 1), 5)
                    time.sleep(delay)
                    continue
                raise _tool_error(
                    category="rate_limit",
                    retryable=True,
                    method=method,
                    path=path,
                    customer_message="Quiz service rate limit reached.",
                    suggested_action="Retry shortly.",
                )
            raise _tool_error(
                category="transient",
                retryable=True,
                method=method,
                path=path,
                customer_message=f"Quiz service error {status}.",
                suggested_action="Retry shortly.",
            )
        except httpx.RequestError as exc:
            _log.error(
                "Quiz backend unreachable (%s %s%s): %s — check QUIZ_APP_URL=%s",
                method,
                QUIZ_APP_URL,
                path,
                type(exc).__name__,
                QUIZ_APP_URL,
            )
            if attempt == 0:
                time.sleep(1)
                continue
            raise _tool_error(
                category="transient",
                retryable=True,
                method=method,
                path=path,
                customer_message=f"Quiz backend unreachable ({QUIZ_APP_URL}). Check that the service is running.",
                suggested_action="Verify QUIZ_APP_URL and retry.",
            )


def _api_call_json(method: str, path: str, **kwargs) -> dict | list:
    return _request(method, path, **kwargs).json()


def _api_call_text(method: str, path: str, **kwargs) -> str:
    return _request(method, path, **kwargs).text


def _api_call(method: str, path: str, **kwargs) -> dict | list:
    return _api_call_json(method, path, **kwargs)
