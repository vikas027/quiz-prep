import yaml
from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


def test_list_empty(tmp_db):
    from src import db

    db.init_db()
    result = runner.invoke(app, ["questions", "list"])
    assert result.exit_code == 0
    assert "No quizzes" in result.output


def test_load_creates_set(tmp_db, tmp_path):
    yaml_file = tmp_path / "myquiz.yaml"
    yaml_file.write_text("""
- question: "What is 2+2?"
  choices: ["A. 3", "B. 4", "C. 5", "D. 6"]
  answer: "B. 4"
  category: "Math"
""")
    result = runner.invoke(app, ["questions", "load", str(yaml_file)])
    assert result.exit_code == 0
    assert "Imported 1" in result.output

    result2 = runner.invoke(app, ["questions", "list", "myquiz"])
    assert result2.exit_code == 0
    assert "What is 2+2?" in result2.output


def test_load_replace(tmp_db, tmp_path):
    yaml_file = tmp_path / "q.yaml"
    yaml_file.write_text("""
- question: "Old Q?"
  choices: ["A. a", "B. b"]
  answer: "A. a"
""")
    runner.invoke(app, ["questions", "load", str(yaml_file)])
    yaml_file.write_text("""
- question: "New Q?"
  choices: ["A. x", "B. y"]
  answer: "B. y"
""")
    result = runner.invoke(app, ["questions", "load", str(yaml_file), "--replace"])
    assert result.exit_code == 0
    assert "Cleared 1" in result.output
    assert "Imported 1" in result.output


def test_delete_question(tmp_db, tmp_path):
    from src import db

    db.init_db()
    s = db.create_set("test", "Test")
    q = db.add_question(s["id"], "Q?", ["A. a", "B. b"], "A. a")
    result = runner.invoke(app, ["questions", "delete", "test", str(q["id"])])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_export(tmp_db, tmp_path):
    from src import db

    db.init_db()
    s = db.create_set("export-test", "Export Test")
    db.add_question(s["id"], "Q?", ["A. a", "B. b"], "A. a")
    out = tmp_path / "out.yaml"
    result = runner.invoke(app, ["questions", "export", "export-test", "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    data = yaml.safe_load(out.read_text())
    assert len(data) == 1
