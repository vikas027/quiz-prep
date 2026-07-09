import random
from typing import Annotated

import typer
from rich.console import Console

from src import db

console = Console()
MISTAKES_KEY = "__mistakes__"


def run(
    quiz_name: Annotated[str | None, typer.Argument(help="Quiz name (omit for interactive picker)")] = None,
    mistakes: Annotated[bool, typer.Option("--mistakes", "-m", help="Drill previous mistakes")] = False,
    limit: Annotated[int | None, typer.Option("--limit", "-n", help="Number of questions")] = None,
    no_shuffle: Annotated[bool, typer.Option("--no-shuffle", help="Keep original question order")] = False,
) -> None:
    import questionary

    db.init_db()

    if mistakes:
        s = db.get_set(MISTAKES_KEY)
        if not s:
            console.print("[yellow]No mistakes recorded yet. Take a full quiz first.[/yellow]")
            raise typer.Exit(1)
        questions = db.list_questions(s["id"])
        console.print(f"[bold]Drilling {len(questions)} mistake(s)[/bold]\n")
    else:
        if quiz_name:
            s = db.get_set(quiz_name)
            if not s:
                console.print(f"[red]Quiz '{quiz_name}' not found.[/red]")
                raise typer.Exit(1)
        else:
            sets = db.list_sets()
            if not sets:
                console.print("[red]No quizzes found. Use 'quiz questions load FILE' first.[/red]")
                raise typer.Exit(1)
            if len(sets) == 1:
                s = sets[0]
            else:
                label = questionary.select(
                    "Select a quiz:", choices=[f"{s['label']} ({s['name']})" for s in sets]
                ).ask()
                if label is None:
                    raise typer.Exit(0)
                s = next(x for x in sets if f"{x['label']} ({x['name']})" == label)
        questions = db.list_questions(s["id"])
        console.print(f"[bold]{s['label']}[/bold] — {len(questions)} questions\n")

    if not questions:
        console.print("[yellow]No questions in this quiz.[/yellow]")
        raise typer.Exit(1)

    if not no_shuffle:
        random.shuffle(questions)
    if limit:
        questions = questions[:limit]

    score = 0
    wrong: list[dict] = []

    for i, q in enumerate(questions, start=1):
        category = f" [dim]({q['category']})[/dim]" if q.get("category") else ""
        console.print(f"\n[bold]Question {i}/{len(questions)}[/bold]{category}")
        answer = questionary.select(q["question"], choices=q["choices"]).ask()
        if answer is None:
            console.print("\n[yellow]Quiz cancelled.[/yellow]")
            return
        if answer == q["answer"]:
            console.print("✓ Correct!", style="bold green")
            score += 1
        else:
            console.print(f"✗ Wrong. Correct: [green]{q['answer']}[/green]", style="red")
            wrong.append(q)
        if q.get("explanation"):
            console.print(f"[dim]{q['explanation'].strip()}[/dim]")

    pct = round(score / len(questions) * 100)
    color = "green" if pct >= 80 else "yellow" if pct >= 60 else "red"
    console.print(f"\n[bold {color}]Score: {score}/{len(questions)} ({pct}%)[/bold {color}]")

    if not mistakes:
        db.add_score(s["id"], score, len(questions))

    mistakes_set = db.get_set(MISTAKES_KEY) or db.create_set(MISTAKES_KEY, "Mistakes")
    db.delete_all_questions(mistakes_set["id"])
    if wrong:
        db.import_questions(mistakes_set["id"], wrong)
        console.print(f"[dim]→ {len(wrong)} mistake(s) saved — run with --mistakes to drill[/dim]")
    else:
        console.print("[dim]→ No mistakes — cleared previous mistakes[/dim]")
