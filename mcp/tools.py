from typing import Annotated, Literal

from app import mcp
from client import _api_call, _api_call_text
from fastmcp.exceptions import ToolError
from pydantic import Field


@mcp.tool(
    description=(
        "Lists all quiz sets with name, label, ID, and question_count. No input required. "
        "Returns an array of quiz metadata. Use to discover available quizzes before querying questions or scores. "
        "Returns empty list when no quizzes exist — that is not an error. "
        "NOT for getting questions — use get_questions for that."
    ),
    annotations={"readOnlyHint": True},
)
def list_quizzes() -> list[dict]:
    return _api_call("GET", "/quizzes")


@mcp.tool(
    description=(
        "Returns questions from a specific quiz set. "
        "Filter by category string or cap count with limit integer. "
        "show controls which questions are returned: 'enabled' (default, excludes disabled), "
        "'disabled' (only disabled), 'all' (everything). "
        "Each item has question text, choices list, answer string, disabled flag, optional category, and explanation. "
        "Returns empty list when no questions match — not an error. "
        "NOT for creating or deleting questions — use manage_question."
    ),
    annotations={"readOnlyHint": True},
)
def get_questions(
    quiz_name: Annotated[
        str,
        Field(description="Quiz set slug, e.g. 'cka', 'aws-sa', 'gitops'", pattern=r"^[a-z0-9_-]+$"),
    ],
    category: Annotated[
        str | None,
        Field(description="Filter to one topic category, e.g. 'Networking'. Omit for all categories."),
    ] = None,
    limit: Annotated[
        int,
        Field(description="Maximum number of questions to return. Defaults to 50. Maximum 200.", ge=1, le=200),
    ] = 50,
    show: Annotated[
        Literal["enabled", "disabled", "all"],
        Field(description="'enabled' (default) skips disabled; 'disabled' returns only disabled; 'all' returns both."),
    ] = "enabled",
) -> list[dict]:
    params: dict = {"limit": limit, "show": show}
    if category:
        params["category"] = category
    return _api_call("GET", f"/quizzes/{quiz_name}/questions", params=params)


@mcp.tool(
    description=(
        "Creates, deletes, imports, or exports a quiz set. "
        "action: 'create' (requires label string), 'delete' (requires confirm_delete=true — irreversible), "
        "'import' (requires yaml_content string — appends new questions, skips exact text duplicates, "
        "returns imported and skipped counts), 'export' (returns YAML string of all questions). "
        "NOT for individual question edits — use manage_question."
    ),
    annotations={"destructiveHint": True},
)
def manage_quiz(
    action: Annotated[
        Literal["create", "delete", "import", "export"],
        Field(description="Operation to perform: 'create', 'delete', 'import', or 'export'"),
    ],
    quiz_name: Annotated[
        str,
        Field(description="Quiz set slug matching ^[a-z0-9_-]+$, e.g. 'cka', 'aws-sa'", pattern=r"^[a-z0-9_-]+$"),
    ],
    label: Annotated[
        str | None,
        Field(description="Human-readable display name for 'create' action, e.g. 'CKA Exam'"),
    ] = None,
    yaml_content: Annotated[
        str | None,
        Field(
            description=(
                "YAML string for 'import': a list of questions OR dict with 'questions' key. "
                "Appends; skips exact duplicates."
            )
        ),
    ] = None,
    confirm_delete: Annotated[
        bool,
        Field(description="Must be true to execute 'delete'. Prevents accidental deletion."),
    ] = False,
) -> dict | str:
    if action == "create":
        if not label:
            raise ToolError("'create' action requires a label parameter")
        return _api_call("POST", "/quizzes", json={"name": quiz_name, "label": label})
    if action == "delete":
        if not confirm_delete:
            raise ToolError(
                f"Destructive action denied: set confirm_delete=true to delete quiz '{quiz_name}' and all its data."
            )
        return _api_call("DELETE", f"/quizzes/{quiz_name}")
    if action == "import":
        if not yaml_content:
            raise ToolError("'import' action requires yaml_content parameter")
        files = {"file": ("questions.yaml", yaml_content.encode(), "text/yaml")}
        return _api_call("POST", f"/quizzes/{quiz_name}/import", files=files)
    if action == "export":
        return _api_call_text("GET", f"/quizzes/{quiz_name}/export")
    raise ToolError(f"Unknown action '{action}'. Must be: create, delete, import, export")


@mcp.tool(
    description=(
        "Adds, updates, or deletes one question in a quiz set. "
        "Returns saved question dict for add/update, deletion confirmation for delete. "
        "'add' needs question, choices list, answer matching a choice; "
        "'update' needs question_id and fields to change; "
        "'delete' needs question_id and confirm_delete=true. "
        "NOT for bulk import — use manage_quiz."
    ),
    annotations={"destructiveHint": True},
)
def manage_question(
    action: Annotated[
        Literal["add", "update", "delete"],
        Field(description="Operation to perform: 'add', 'update', or 'delete'"),
    ],
    quiz_name: Annotated[
        str,
        Field(description="Quiz set slug, e.g. 'cka'", pattern=r"^[a-z0-9_-]+$"),
    ],
    question_id: Annotated[
        int | None,
        Field(description="Question ID integer, required for 'update' and 'delete' actions", ge=1),
    ] = None,
    question: Annotated[
        str | None,
        Field(description="Full question text string, required for 'add'"),
    ] = None,
    choices: Annotated[
        list[str] | None,
        Field(description="List of choice strings prefixed A./B./C./D., e.g. ['A. yes', 'B. no'], required for 'add'"),
    ] = None,
    answer: Annotated[
        str | None,
        Field(description="Answer string that must exactly match one of the choices, required for 'add'"),
    ] = None,
    category: Annotated[
        str | None,
        Field(description="Topic category string, e.g. 'Networking'. Optional."),
    ] = None,
    explanation: Annotated[
        str | None,
        Field(description="Explanation text shown after answering. Optional."),
    ] = None,
    disabled: Annotated[
        bool | None,
        Field(description="true = exclude from default quiz runs (still stored); false = re-enable. Optional."),
    ] = None,
    confirm_delete: Annotated[
        bool,
        Field(description="Must be true to execute 'delete'. Prevents accidental deletion."),
    ] = False,
) -> dict:
    if action == "add":
        if not all([question, choices, answer]):
            raise ToolError("'add' action requires question, choices, and answer")
        if answer not in choices:
            raise ToolError(f"answer must exactly match one of the choices; got '{answer}'")
        body: dict = {"question": question, "choices": choices, "answer": answer}
        if category:
            body["category"] = category
        if explanation:
            body["explanation"] = explanation
        if disabled is not None:
            body["disabled"] = disabled
        return _api_call("POST", f"/quizzes/{quiz_name}/questions", json=body)
    if action == "update":
        if question_id is None:
            raise ToolError("'update' action requires question_id")
        body = {}
        for key, val in [
            ("question", question),
            ("choices", choices),
            ("answer", answer),
            ("category", category),
            ("explanation", explanation),
        ]:
            if val is not None:
                body[key] = val
        if disabled is not None:
            body["disabled"] = disabled
        if not body:
            raise ToolError("'update' action requires at least one field to change")
        if "answer" in body and "choices" not in body:
            raise ToolError(
                "Updating 'answer' alone is not allowed: the API schema (QuestionUpdate) does not "
                "re-validate answer against existing choices. Provide 'choices' together with 'answer' "
                "so the MCP can verify consistency before writing."
            )
        if "answer" in body and "choices" in body and body["answer"] not in body["choices"]:
            raise ToolError("answer must exactly match one of the updated choices")
        return _api_call("PUT", f"/quizzes/{quiz_name}/questions/{question_id}", json=body)
    if action == "delete":
        if question_id is None:
            raise ToolError("'delete' action requires question_id")
        if not confirm_delete:
            raise ToolError(f"Destructive action denied: set confirm_delete=true to delete question {question_id}.")
        return _api_call("DELETE", f"/quizzes/{quiz_name}/questions/{question_id}")
    raise ToolError(f"Unknown action '{action}'. Must be: add, update, delete")


@mcp.tool(
    description=(
        "Records a completed quiz score or retrieves score history for a quiz set. "
        "action: 'get' (returns history newest-first, optional limit integer), "
        "'record' (requires score integer and total integer, score must not exceed total, "
        "returns entry with pct field). "
        "NOT for quiz questions — use get_questions for that."
    ),
)
def manage_scores(
    action: Annotated[
        Literal["get", "record"],
        Field(description="Operation to perform: 'get' (retrieve history) or 'record' (save a new score)"),
    ],
    quiz_name: Annotated[
        str,
        Field(description="Quiz set slug, e.g. 'cka'", pattern=r"^[a-z0-9_-]+$"),
    ],
    score: Annotated[
        int | None,
        Field(description="Number of correct answers, required for 'record' action", ge=0),
    ] = None,
    total: Annotated[
        int | None,
        Field(description="Total number of questions attempted, required for 'record' action", gt=0),
    ] = None,
    limit: Annotated[
        int | None,
        Field(description="Maximum history entries to return for 'get' action. Default is 10.", ge=1),
    ] = None,
) -> dict | list:
    if action == "get":
        params: dict = {}
        if limit:
            params["limit"] = limit
        return _api_call("GET", f"/quizzes/{quiz_name}/scores", params=params)
    if action == "record":
        if score is None or total is None:
            raise ToolError("'record' action requires score and total integers")
        if score > total:
            raise ToolError(f"score ({score}) cannot exceed total ({total})")
        return _api_call("POST", f"/quizzes/{quiz_name}/scores", json={"score": score, "total": total})
    raise ToolError(f"Unknown action '{action}'. Must be: get, record")
