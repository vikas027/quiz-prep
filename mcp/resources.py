import json as _json

from app import mcp
from client import _api_call
from fastmcp.exceptions import ResourceError, ToolError


@mcp.resource("quiz://catalog")
def get_catalog() -> str:
    """All quiz sets available in the database. Browse to discover quiz names."""
    try:
        return _json.dumps(_api_call("GET", "/quizzes"), indent=2)
    except ToolError as e:
        raise ResourceError(str(e))


@mcp.resource("quiz://{name}/questions")
def get_quiz_questions(name: str) -> str:
    """Up to 50 questions in the specified quiz set. Use get_questions tool for paged reads."""
    try:
        return _json.dumps(_api_call("GET", f"/quizzes/{name}/questions", params={"limit": 50}), indent=2)
    except ToolError as e:
        raise ResourceError(str(e))


@mcp.resource("quiz://{name}/scores")
def get_quiz_scores(name: str) -> str:
    """Score history for the specified quiz set, newest first."""
    try:
        return _json.dumps(_api_call("GET", f"/quizzes/{name}/scores"), indent=2)
    except ToolError as e:
        raise ResourceError(str(e))
