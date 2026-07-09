from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from src import db

app = typer.Typer(help="View score history")
console = Console()


@app.command("list")
def list_scores(
    name: Annotated[str, typer.Argument(help="Quiz name")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Number of runs to show")] = 10,
) -> None:
    db.init_db()
    s = db.get_set(name)
    if not s:
        console.print(f"[red]Quiz '{name}' not found.[/red]")
        raise typer.Exit(1)
    scores = db.list_scores(s["id"], limit=limit)
    if not scores:
        console.print(f"[dim]No score history for '{name}' yet.[/dim]")
        return
    t = Table("Date", "Score", "Total", "%")
    for sc in scores:
        pct = sc["pct"]
        color = "green" if pct >= 80 else "yellow" if pct >= 60 else "red"
        t.add_row(sc["taken_at"][:19], str(sc["score"]), str(sc["total"]), f"[{color}]{pct}%[/{color}]")
    console.print(t)
