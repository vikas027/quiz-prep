import json
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

_DB_PATH_DEFAULT = "./data/quiz.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS question_sets (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    label      TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS questions (
    id                  INTEGER PRIMARY KEY,
    set_id              INTEGER NOT NULL REFERENCES question_sets(id) ON DELETE CASCADE,
    question            TEXT    NOT NULL,
    choices             TEXT    NOT NULL,
    answer              TEXT    NOT NULL,
    category            TEXT,
    explanation         TEXT,
    choice_explanations TEXT,
    disabled            INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_questions_set_question
    ON questions(set_id, question);
CREATE TABLE IF NOT EXISTS score_runs (
    id       INTEGER PRIMARY KEY,
    set_id   INTEGER NOT NULL REFERENCES question_sets(id) ON DELETE CASCADE,
    score    INTEGER NOT NULL,
    total    INTEGER NOT NULL,
    taken_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def _db_path() -> Path:
    return Path(os.environ.get("QUIZ_DB", _DB_PATH_DEFAULT))


def _score_max() -> int:
    return int(os.environ.get("QUIZ_SCORE_MAX", "10"))


@contextmanager
def _conn() -> Generator[sqlite3.Connection]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(SCHEMA)
        try:
            conn.execute("ALTER TABLE questions ADD COLUMN choice_explanations TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE questions ADD COLUMN disabled INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass


def list_sets() -> list[dict]:
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT qs.id, qs.name, qs.label, qs.created_at, COUNT(q.id) AS question_count"
                " FROM question_sets qs LEFT JOIN questions q ON q.set_id = qs.id"
                " GROUP BY qs.id ORDER BY qs.label"
            )
        ]


def get_set(name: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM question_sets WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None


def create_set(name: str, label: str) -> dict:
    with _conn() as conn:
        conn.execute("INSERT INTO question_sets (name, label) VALUES (?, ?)", (name, label))
        row = conn.execute(
            "SELECT qs.id, qs.name, qs.label, qs.created_at, COUNT(q.id) AS question_count"
            " FROM question_sets qs LEFT JOIN questions q ON q.set_id = qs.id WHERE qs.name = ?",
            (name,),
        ).fetchone()
        return dict(row)


def delete_set(name: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM question_sets WHERE name = ?", (name,))
        return cur.rowcount > 0


def _deserialise(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["choices"] = json.loads(d["choices"])
    if d.get("choice_explanations"):
        d["choice_explanations"] = json.loads(d["choice_explanations"])
    return d


def list_questions(
    set_id: int,
    category: str | None = None,
    limit: int | None = None,
    show: str = "enabled",
) -> list[dict]:
    sql = "SELECT * FROM questions WHERE set_id = ?"
    params: list[object] = [set_id]
    if category:
        sql += " AND category = ?"
        params.append(category)
    if show == "enabled":
        sql += " AND disabled = 0"
    elif show == "disabled":
        sql += " AND disabled = 1"
    sql += " ORDER BY id"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    with _conn() as conn:
        return [_deserialise(r) for r in conn.execute(sql, params).fetchall()]


def add_question(
    set_id: int,
    question: str,
    choices: list[str],
    answer: str,
    category: str | None = None,
    explanation: str | None = None,
    choice_explanations: dict | None = None,
    disabled: bool = False,
) -> dict | None:
    """Returns None if an identical question already exists in the set."""
    with _conn() as conn:
        cols = "set_id, question, choices, answer, category, explanation, choice_explanations, disabled"
        cur = conn.execute(
            f"INSERT OR IGNORE INTO questions ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                set_id,
                question,
                json.dumps(choices),
                answer,
                category,
                explanation,
                json.dumps(choice_explanations) if choice_explanations else None,
                int(disabled),
            ),
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _deserialise(row)


def update_question(question_id: int, **kwargs: object) -> dict | None:
    if not kwargs:
        with _conn() as conn:
            row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
            return _deserialise(row) if row else None
    if "choices" in kwargs:
        kwargs["choices"] = json.dumps(kwargs["choices"])
    if "choice_explanations" in kwargs and kwargs["choice_explanations"] is not None:
        kwargs["choice_explanations"] = json.dumps(kwargs["choice_explanations"])
    setters = ", ".join(f"{k} = ?" for k in kwargs)
    with _conn() as conn:
        conn.execute(
            f"UPDATE questions SET {setters} WHERE id = ?",
            (*kwargs.values(), question_id),
        )
        row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
        return _deserialise(row) if row else None


def delete_question(question_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        return cur.rowcount > 0


def enable_all_questions(set_id: int) -> int:
    with _conn() as conn:
        cur = conn.execute("UPDATE questions SET disabled = 0 WHERE set_id = ? AND disabled = 1", (set_id,))
        return cur.rowcount


def delete_all_questions(set_id: int) -> int:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM questions WHERE set_id = ?", (set_id,))
        return cur.rowcount


def import_questions(set_id: int, questions: list[dict]) -> tuple[int, int]:
    """Returns (imported, skipped) where skipped are exact duplicates."""
    imported = 0
    with _conn() as conn:
        for q in questions:
            ce = q.get("choice_explanations")
            cols = "set_id, question, choices, answer, category, explanation, choice_explanations, disabled"
            cur = conn.execute(
                f"INSERT OR IGNORE INTO questions ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    set_id,
                    q["question"],
                    json.dumps(q["choices"]),
                    q["answer"],
                    q.get("category"),
                    q.get("explanation"),
                    json.dumps(ce) if ce else None,
                    int(bool(q.get("disabled", False))),
                ),
            )
            imported += cur.rowcount
    return imported, len(questions) - imported


def list_scores(set_id: int, limit: int | None = None) -> list[dict]:
    cap = limit if limit is not None else _score_max()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM score_runs WHERE set_id = ? ORDER BY taken_at DESC, id DESC LIMIT ?",
            (set_id, cap),
        ).fetchall()
        return [{**dict(r), "pct": round(r["score"] / r["total"] * 100) if r["total"] else 0} for r in rows]


def add_score(set_id: int, score: int, total: int) -> dict:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO score_runs (set_id, score, total) VALUES (?, ?, ?)",
            (set_id, score, total),
        )
        conn.execute(
            "DELETE FROM score_runs WHERE set_id = ? AND id NOT IN ("
            "  SELECT id FROM score_runs WHERE set_id = ? ORDER BY taken_at DESC, id DESC LIMIT ?"
            ")",
            (set_id, set_id, _score_max()),
        )
        row = conn.execute("SELECT * FROM score_runs WHERE id = ?", (cur.lastrowid,)).fetchone()
        d = dict(row)
        d["pct"] = round(d["score"] / d["total"] * 100) if d["total"] else 0
        return d
