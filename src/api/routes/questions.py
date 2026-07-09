from fastapi import APIRouter, HTTPException, status

from src import db
from src.api.schemas import (
    BulkDeleteResult,
    BulkEnableResult,
    DeleteResult,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
)

router = APIRouter(prefix="/quizzes/{name}/questions", tags=["questions"])


def _get_set_or_404(name: str) -> dict:
    s = db.get_set(name)
    if not s:
        raise HTTPException(status_code=404, detail=f"Quiz '{name}' not found")
    return s


@router.get("", response_model=list[QuestionOut])
def list_questions(
    name: str,
    category: str | None = None,
    limit: int | None = None,
    show: str = "enabled",
) -> list[dict]:
    if show not in ("enabled", "disabled", "all"):
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="show must be 'enabled', 'disabled', or 'all'")
    s = _get_set_or_404(name)
    return db.list_questions(s["id"], category=category, limit=limit, show=show)


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def add_question(name: str, body: QuestionCreate) -> dict:
    s = _get_set_or_404(name)
    result = db.add_question(
        s["id"],
        body.question,
        body.choices,
        body.answer,
        body.category,
        body.explanation,
        body.choice_explanations,
        body.disabled,
    )
    if result is None:
        raise HTTPException(status_code=409, detail="An identical question already exists in this quiz")
    return result


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(name: str, question_id: int, body: QuestionUpdate) -> dict:
    _get_set_or_404(name)
    updated = db.update_question(question_id, **body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return updated


@router.delete("/{question_id}", response_model=DeleteResult)
def delete_question(name: str, question_id: int) -> dict:
    _get_set_or_404(name)
    if not db.delete_question(question_id):
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return {"deleted": str(question_id)}


@router.post("/enable-all-disabled", response_model=BulkEnableResult, status_code=status.HTTP_200_OK)
def enable_all_disabled(name: str) -> dict:
    s = _get_set_or_404(name)
    count = db.enable_all_questions(s["id"])
    return {"enabled_count": count}


@router.delete("", response_model=BulkDeleteResult)
def delete_all_questions(name: str) -> dict:
    s = _get_set_or_404(name)
    count = db.delete_all_questions(s["id"])
    return {"deleted_count": count}
