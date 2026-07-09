# CLI Reference

The CLI is installed as the `quiz` command. Run `mise run install` to set up the environment.

```bash
quiz --help
```

---

## quiz run

Run an interactive quiz session.

```bash
quiz run [QUIZ_NAME] [OPTIONS]
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `QUIZ_NAME` | Quiz name to run (omit for interactive picker) |

**Options**

| Option | Description |
|--------|-------------|
| `--mistakes`, `-m` | Drill questions you got wrong last time |
| `--limit N`, `-n N` | Limit to N questions |
| `--no-shuffle` | Keep original question order |

**Examples**

```bash
quiz run                  # pick from available quizzes
quiz run aws-saa          # run specific quiz
quiz run --mistakes       # drill previous mistakes
quiz run aws-saa -n 20   # run 20 random questions
```

---

## quiz questions

Manage question banks.

### quiz questions list

```bash
quiz questions list [QUIZ_NAME]
```

Without `QUIZ_NAME` — lists all available quiz sets.
With `QUIZ_NAME` — lists questions in that set (truncated at 80 chars).

### quiz questions load

```bash
quiz questions load FILE [OPTIONS]
```

Import questions from a YAML file into the database.

**Arguments**

| Argument | Description |
|----------|-------------|
| `FILE` | Path to YAML file |

**Options**

| Option | Description |
|--------|-------------|
| `--name NAME`, `-n NAME` | Set name (default: file stem) |
| `--label LABEL`, `-l LABEL` | Display label |
| `--replace` | Delete existing questions before importing |

**Examples**

```bash
quiz questions load tests/fixtures/sample.yaml
quiz questions load exam.yaml --name my-exam --label "My Exam"
quiz questions load exam.yaml --replace
```

### quiz questions add

```bash
quiz questions add QUIZ_NAME
```

Interactively add a single question to an existing quiz.

### quiz questions delete

```bash
quiz questions delete QUIZ_NAME QUESTION_ID
```

Delete a question by its numeric ID.

### quiz questions export

```bash
quiz questions export QUIZ_NAME [--out FILE]
```

Export all questions for a quiz as YAML. Prints to stdout by default.

**Options**

| Option | Description |
|--------|-------------|
| `--out FILE`, `-o FILE` | Write to file instead of stdout |

---

## quiz scores

View score history.

### quiz scores list

```bash
quiz scores list QUIZ_NAME [--limit N]
```

Show recent quiz runs for a quiz, sorted newest first.

**Options**

| Option | Description |
|--------|-------------|
| `--limit N`, `-n N` | Number of runs to show (default: 10) |

**Example output**

```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━┓
┃ Date                ┃ Score ┃ Total ┃ %    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━┩
│ 2024-01-01 12:00:00 │ 38    │ 42    │ 90%  │
└─────────────────────┴───────┴───────┴──────┘
```
