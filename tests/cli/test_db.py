from src import db


def test_init_creates_tables(tmp_db):
    db.init_db()
    import sqlite3

    conn = sqlite3.connect(tmp_db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"question_sets", "questions", "score_runs"} <= tables


def test_create_and_list_set(tmp_db):
    db.init_db()
    created = db.create_set("cka", "CKA Exam")
    assert created["name"] == "cka"
    assert created["label"] == "CKA Exam"
    sets = db.list_sets()
    assert len(sets) == 1
    assert sets[0]["name"] == "cka"


def test_get_set_not_found(tmp_db):
    db.init_db()
    assert db.get_set("missing") is None


def test_delete_set(tmp_db):
    db.init_db()
    db.create_set("cka", "CKA Exam")
    assert db.delete_set("cka") is True
    assert db.list_sets() == []


def test_add_and_list_questions(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    q = db.add_question(
        set_id=s["id"],
        question="What is a Pod?",
        choices=["A. A node", "B. A container group", "C. A service", "D. A volume"],
        answer="B. A container group",
        category="Workloads",
    )
    assert q["question"] == "What is a Pod?"
    assert isinstance(q["choices"], list)
    questions = db.list_questions(s["id"])
    assert len(questions) == 1


def test_list_questions_filter_category(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    db.add_question(s["id"], "Q1", ["A. a", "B. b"], "A. a", category="Net")
    db.add_question(s["id"], "Q2", ["A. a", "B. b"], "A. a", category="Storage")
    assert len(db.list_questions(s["id"], category="Net")) == 1


def test_delete_question(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    q = db.add_question(s["id"], "Q?", ["A. a", "B. b"], "A. a")
    assert db.delete_question(q["id"]) is True
    assert db.list_questions(s["id"]) == []


def test_delete_all_questions(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    db.add_question(s["id"], "Q1", ["A. a", "B. b"], "A. a")
    db.add_question(s["id"], "Q2", ["A. a", "B. b"], "A. a")
    count = db.delete_all_questions(s["id"])
    assert count == 2
    assert db.list_questions(s["id"]) == []


def test_import_questions(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    imported, skipped = db.import_questions(
        s["id"],
        [
            {"question": "Q?", "choices": ["A. a", "B. b"], "answer": "A. a", "category": "Net"},
            {"question": "Q2?", "choices": ["A. x", "B. y"], "answer": "B. y"},
        ],
    )
    assert imported == 2
    assert skipped == 0


def test_import_deduplicates(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    questions = [{"question": "Q?", "choices": ["A. a", "B. b"], "answer": "A. a"}]
    imported1, skipped1 = db.import_questions(s["id"], questions)
    assert imported1 == 1 and skipped1 == 0
    imported2, skipped2 = db.import_questions(s["id"], questions)
    assert imported2 == 0 and skipped2 == 1
    assert len(db.list_questions(s["id"])) == 1


def test_add_and_list_scores(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    db.add_score(s["id"], 8, 10)
    db.add_score(s["id"], 9, 10)
    scores = db.list_scores(s["id"])
    assert scores[0]["score"] == 9  # newest first
    assert scores[0]["pct"] == 90


def test_score_history_capped(tmp_db, monkeypatch):
    monkeypatch.setenv("QUIZ_SCORE_MAX", "3")
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    for i in range(5):
        db.add_score(s["id"], i, 10)
    assert len(db.list_scores(s["id"])) == 3


def test_delete_set_cascades(tmp_db):
    db.init_db()
    s = db.create_set("cka", "CKA Exam")
    db.add_question(s["id"], "Q?", ["A. a", "B. b"], "A. a")
    db.add_score(s["id"], 5, 10)
    db.delete_set("cka")
    assert db.list_questions(s["id"]) == []
    assert db.list_scores(s["id"]) == []
