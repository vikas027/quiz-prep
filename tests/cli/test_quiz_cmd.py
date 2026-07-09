from typer.testing import CliRunner

from src import db
from src.cli.main import app

runner = CliRunner()


def test_run_no_quizzes(tmp_db):
    db.init_db()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1
    assert "No quizzes found" in result.output


def test_run_missing_quiz(tmp_db):
    db.init_db()
    result = runner.invoke(app, ["run", "ghost"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_run_no_mistakes_yet(tmp_db):
    db.init_db()
    result = runner.invoke(app, ["run", "--mistakes"])
    assert result.exit_code == 1
    assert "No mistakes" in result.output
