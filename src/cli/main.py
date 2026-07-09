import typer

from src.cli.commands import questions_cmd, quiz_cmd, scores_cmd

app = typer.Typer(name="quiz", help="Quiz — certification exam practice CLI")
app.add_typer(questions_cmd.app, name="questions")
app.add_typer(scores_cmd.app, name="scores")
app.command("run")(quiz_cmd.run)

if __name__ == "__main__":
    app()
