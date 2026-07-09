from typing import Annotated

import yaml
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

from src import db
from src.api.schemas import DeleteResult, ImportResult, QuizSetCreate, QuizSetOut

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def _get_set_or_404(name: str) -> dict:
    s = db.get_set(name)
    if not s:
        raise HTTPException(status_code=404, detail=f"Quiz '{name}' not found")
    return s


@router.get("", response_model=list[QuizSetOut])
def list_quizzes() -> list[dict]:
    return db.list_sets()


@router.post("", response_model=QuizSetOut, status_code=status.HTTP_201_CREATED)
def create_quiz(body: QuizSetCreate) -> dict:
    if db.get_set(body.name):
        raise HTTPException(status_code=409, detail=f"Quiz '{body.name}' already exists")
    return db.create_set(body.name, body.label)


@router.delete("/{name}", response_model=DeleteResult)
def delete_quiz(name: str) -> dict:
    if not db.delete_set(name):
        raise HTTPException(status_code=404, detail=f"Quiz '{name}' not found")
    return {"deleted": name}


@router.post("/{name}/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def import_yaml(name: str, file: Annotated[UploadFile, File()]) -> dict:
    s = _get_set_or_404(name)
    raw = await file.read()
    try:
        data = yaml.safe_load(raw)
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict) and isinstance(data.get("questions"), list):
            questions = data["questions"]
        else:
            raise ValueError("YAML must be a list of questions or a dict with a 'questions' key")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {exc}") from exc
    required = {"question", "choices", "answer"}
    for i, item in enumerate(questions):
        if not isinstance(item, dict) or not required.issubset(item):
            missing = required - set(item) if isinstance(item, dict) else required
            raise HTTPException(status_code=400, detail=f"Item {i} missing required fields: {missing}")
    imported, skipped = db.import_questions(s["id"], questions)
    return {"name": name, "imported": imported, "skipped": skipped}


@router.get("/{name}/export")
def export_yaml(name: str) -> Response:
    s = _get_set_or_404(name)
    questions = db.list_questions(s["id"], show="all")
    for q in questions:
        q.pop("id", None)
        q.pop("set_id", None)
        q.pop("created_at", None)
        if not q.get("disabled"):
            q.pop("disabled", None)
    content = yaml.dump(questions, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return Response(content=content, media_type="text/yaml")
