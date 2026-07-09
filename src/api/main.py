from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src import db
from src.api.routes import questions, quizzes, scores


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    db.init_db()
    yield


app = FastAPI(
    title="Quiz API",
    description="Certification exam practice — API-first quiz platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url="/redoc",
)

app.include_router(quizzes.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")

_site = Path(__file__).parent.parent.parent / "site"
if _site.exists():

    @app.get("/docs", include_in_schema=False)
    def _docs_redirect() -> RedirectResponse:
        return RedirectResponse(url="/docs/")

    app.mount("/docs", StaticFiles(directory=_site, html=True), name="docs-site")

_web = Path(__file__).parent.parent / "web"
app.mount("/", StaticFiles(directory=_web, html=True), name="web")
