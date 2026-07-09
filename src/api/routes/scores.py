from fastapi import APIRouter, HTTPException, status

from src import db
from src.api.schemas import ScoreCreate, ScoreOut

router = APIRouter(prefix="/quizzes/{name}/scores", tags=["scores"])


def _get_set_or_404(name: str) -> dict:
    s = db.get_set(name)
    if not s:
        raise HTTPException(status_code=404, detail=f"Quiz '{name}' not found")
    return s


@router.get("", response_model=list[ScoreOut])
def list_scores(name: str, limit: int | None = None) -> list[dict]:
    s = _get_set_or_404(name)
    return db.list_scores(s["id"], limit=limit)


@router.post("", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def add_score(name: str, body: ScoreCreate) -> dict:
    s = _get_set_or_404(name)
    return db.add_score(s["id"], body.score, body.total)
