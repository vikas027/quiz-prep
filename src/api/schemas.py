from pydantic import BaseModel, Field, field_validator, model_validator


class QuizSetCreate(BaseModel):
    name: str = Field(min_length=1, pattern=r"^[a-z0-9_-]+$")
    label: str = Field(min_length=1)


class QuizSetOut(BaseModel):
    id: int
    name: str
    label: str
    question_count: int
    created_at: str


class QuestionCreate(BaseModel):
    question: str
    choices: list[str]
    answer: str
    category: str | None = None
    explanation: str | None = None
    choice_explanations: dict[str, str] | None = None
    disabled: bool = False

    @field_validator("answer")
    @classmethod
    def answer_in_choices(cls, v: str, info) -> str:  # type: ignore[override]
        choices = info.data.get("choices", [])
        if choices and v not in choices:
            raise ValueError(f"answer must be one of: {choices}")
        return v


class QuestionUpdate(BaseModel):
    question: str | None = None
    choices: list[str] | None = None
    answer: str | None = None
    category: str | None = None
    explanation: str | None = None
    choice_explanations: dict[str, str] | None = None
    disabled: bool | None = None


class QuestionOut(BaseModel):
    id: int
    set_id: int
    question: str
    choices: list[str]
    answer: str
    category: str | None
    explanation: str | None
    choice_explanations: dict[str, str] | None
    disabled: bool
    created_at: str


class ScoreCreate(BaseModel):
    score: int = Field(ge=0)
    total: int = Field(gt=0)

    @model_validator(mode="after")
    def score_le_total(self) -> ScoreCreate:
        if self.score > self.total:
            raise ValueError(f"score ({self.score}) cannot exceed total ({self.total})")
        return self


class ScoreOut(BaseModel):
    id: int
    set_id: int
    score: int
    total: int
    pct: int
    taken_at: str


class ImportResult(BaseModel):
    name: str
    imported: int
    skipped: int


class DeleteResult(BaseModel):
    deleted: str


class BulkDeleteResult(BaseModel):
    deleted_count: int


class BulkEnableResult(BaseModel):
    enabled_count: int
