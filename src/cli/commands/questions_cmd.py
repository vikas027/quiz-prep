from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from src import db

app = typer.Typer(help="Manage question banks")
console = Console()


def _require_set(name: str) -> dict:
    s = db.get_set(name)
    if not s:
        console.print(f"[red]Quiz '{name}' not found. Use 'quiz questions list' to see available quizzes.[/red]")
        raise typer.Exit(1)
    return s


@app.command("list")
def list_questions(
    name: Annotated[str | None, typer.Argument(help="Quiz name (omit to list all sets)")] = None,
) -> None:
    db.init_db()
    if name is None:
        sets = db.list_sets()
        if not sets:
            console.print("[dim]No quizzes yet. Use 'quiz questions load FILE' to import one.[/dim]")
            return
        t = Table("Name", "Label", "ID")
        for s in sets:
            t.add_row(s["name"], s["label"], str(s["id"]))
        console.print(t)
    else:
        s = _require_set(name)
        questions = db.list_questions(s["id"])
        if not questions:
            console.print(f"[dim]No questions in '{name}'.[/dim]")
            return
        t = Table("ID", "Category", "Question")
        for q in questions:
            t.add_row(str(q["id"]), q.get("category") or "—", q["question"][:80])
        console.print(t)


@app.command("load")
def load_questions(
    file: Annotated[Path, typer.Argument(help="YAML file to import")],
    quiz_name: Annotated[str | None, typer.Option("--name", "-n", help="Set name (default: file stem)")] = None,
    label: Annotated[str | None, typer.Option("--label", "-l", help="Set label")] = None,
    replace: Annotated[bool, typer.Option("--replace", help="Delete existing questions first")] = False,
) -> None:
    db.init_db()
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)
    with open(file) as f:
        docs = list(yaml.safe_load_all(f))
    questions: list[dict] = []
    yaml_name: str | None = None
    yaml_label: str | None = None
    for doc in docs:
        if isinstance(doc, list):
            questions.extend(doc)
        elif isinstance(doc, dict) and "questions" in doc:
            yaml_label = str(doc["quiz_name"]) if "quiz_name" in doc else None
            yaml_name = yaml_label.lower().replace(" ", "-") if yaml_label else None
            qs = doc["questions"]
            if isinstance(qs, list):
                questions.extend(qs)

    name = quiz_name or yaml_name or file.stem.lower().replace(" ", "-")
    lbl = label or yaml_label or file.stem.replace("-", " ").replace("_", " ").title()

    s = db.get_set(name) or db.create_set(name, lbl)

    if replace:
        deleted = db.delete_all_questions(s["id"])
        console.print(f"[dim]Cleared {deleted} existing questions.[/dim]")

    imported, skipped = db.import_questions(s["id"], questions)
    msg = f"[green]✓[/green] Imported [bold]{imported}[/bold] questions into [bold]{name}[/bold]"
    if skipped:
        msg += f" [dim]({skipped} duplicate{'s' if skipped > 1 else ''} skipped)[/dim]"
    console.print(msg)


@app.command("add")
def add_question(
    name: Annotated[str, typer.Argument(help="Quiz name")],
) -> None:
    import questionary

    db.init_db()
    s = _require_set(name)

    question = questionary.text("Question text:").ask()
    if not question:
        raise typer.Exit(0)

    choices_raw = questionary.text("Choices (comma-separated, prefix A./B./C./D.):").ask()
    choices = [c.strip() for c in (choices_raw or "").split(",") if c.strip()]
    if len(choices) < 2:
        console.print("[red]Need at least 2 choices.[/red]")
        raise typer.Exit(1)

    answer = questionary.select("Correct answer:", choices=choices).ask()
    category = questionary.text("Category (optional):").ask() or None
    explanation = questionary.text("Explanation (optional):").ask() or None

    q = db.add_question(s["id"], question, choices, answer, category, explanation)
    console.print(f"[green]✓[/green] Added question [bold]{q['id']}[/bold]")


@app.command("delete")
def delete_question(
    name: Annotated[str, typer.Argument(help="Quiz name")],
    question_id: Annotated[int, typer.Argument(help="Question ID")],
) -> None:
    db.init_db()
    _require_set(name)
    if db.delete_question(question_id):
        console.print(f"[green]✓[/green] Deleted question {question_id}")
    else:
        console.print(f"[red]Question {question_id} not found.[/red]")
        raise typer.Exit(1)


@app.command("export")
def export_questions(
    name: Annotated[str, typer.Argument(help="Quiz name")],
    output: Annotated[Path | None, typer.Option("--out", "-o", help="Output file (default: stdout)")] = None,
) -> None:
    db.init_db()
    s = _require_set(name)
    questions = db.list_questions(s["id"])
    for q in questions:
        q.pop("id", None)
        q.pop("set_id", None)
        q.pop("created_at", None)
    content = yaml.dump(questions, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if output:
        output.write_text(content)
        console.print(f"[green]✓[/green] Exported {len(questions)} questions to {output}")
    else:
        console.print(content)
