# quiz-prep

> Self-hosted certification exam practice. Upload your own question banks, drill by category, track your progress, and let Claude manage it all through MCP.

[![release](https://img.shields.io/github/v/release/vikas027/quiz-prep?logo=github&label=release)](https://github.com/vikas027/quiz-prep/releases)
[![docker](https://img.shields.io/docker/v/vikas027/quiz-prep?sort=semver&logo=docker&label=docker)](https://hub.docker.com/r/vikas027/quiz-prep)
[![docker pulls](https://img.shields.io/docker/pulls/vikas027/quiz-prep?logo=docker&label=pulls)](https://hub.docker.com/r/vikas027/quiz-prep)
[![ci](https://img.shields.io/github/actions/workflow/status/vikas027/quiz-prep/ci.yml?logo=github&label=ci)](https://github.com/vikas027/quiz-prep/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-mkdocs-blue?logo=materialformkdocs)](https://vikas027.github.io/quiz-prep/)
[![python](https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![license](https://img.shields.io/github/license/vikas027/quiz-prep)](LICENSE)

---

## What is this?

quiz-prep is a self-hosted platform for practising certification exams. You own your question banks — import them as YAML, tag questions by topic, disable ones you already know, and review per-choice explanations when you get something wrong.

It ships as a single container with a dark-mode web UI, a REST API with Swagger, an interactive CLI, and a standalone **MCP server** so Claude, Cursor, or Codex can browse, import, and manage your question banks directly.

---

## Features

- **Web UI** — dark/light glassmorphism design; quiz picker, category filter, question count, timer; live feedback with per-choice explanations or score-at-end mode; keyboard navigation throughout
- **Disable questions** — mark questions you know cold so they are skipped by default; re-enable individually or all at once; filter by enabled / disabled / all when starting a quiz
- **Star questions** — mark questions as important to revisit; filter by important only when starting a quiz; unstar all at once from the settings screen
- **Import / export** — upload YAML from the browser; export any quiz back to YAML; duplicate detection keeps your banks clean
- **Score history** — tracks last N results per quiz; retake failed questions only
- **REST API** — full CRUD at `/api/v1/`; Swagger UI at `/swagger`; Hurl integration tests
- **CLI** — `quiz run`, `quiz questions`, `quiz scores` — all the same data, no server required
- **MCP server** — 5 tools + 3 resources over SSE; connect Claude, Cursor, or Codex to list quizzes, browse questions, import banks, and record scores
- **Docker / Kubernetes** — single image, SQLite on a named volume; k8s manifests included

---

## Quickstart

### Docker (recommended)

```bash
git clone https://github.com/vikas027/quiz-prep.git
cd quiz-prep
mise run up          # build + start → http://localhost:8080
mise run seed-all    # load sample question banks
```

Then open [http://localhost:8080](http://localhost:8080). To tear down:

```bash
mise run clean       # stop container + remove volume
```

### Local (no Docker)

```bash
mise run install     # install Python deps
mise run dev         # uvicorn with auto-reload → http://localhost:8080
mise run seed-all    # load sample question banks
mise run quiz        # run interactive CLI quiz
```

### CLI only

```bash
mise run install
mise run seed-all
quiz run cka               # run the CKA question bank
quiz run --limit 10        # 10 random questions
quiz run --mistakes        # drill your previous wrong answers
```

> **Prerequisites:** [mise](https://mise.jdx.dev) (`brew install mise`), Docker + Docker Compose (for `mise run up`), [Hurl](https://hurl.dev) (`brew install hurl`) for API tests.

---

## Question format

Question banks are plain YAML files. The minimal structure:

```yaml
---
quiz_name: "CKA"
questions:
  - question: A Pod is stuck in Pending. kubectl describe shows 'Insufficient cpu'. What is the cause?
    choices:
      - A. The container image cannot be pulled
      - B. No node has enough CPU to satisfy the Pod's resource requests
      - C. The liveness probe is failing
      - D. The namespace has no NetworkPolicy
    answer: B. No node has enough CPU to satisfy the Pod's resource requests
    category: Workloads
    explanation: >-
      'Insufficient cpu' means the scheduler cannot find a node with enough
      unallocated CPU. Solutions include adding nodes, reducing CPU requests,
      or freeing capacity.
    disabled: true          # skip this question by default (you know it cold)
    important: true         # star this question to revisit it
    choice_explanations:    # per-choice explanations shown in live feedback
      A: Image pull failures show as ImagePullBackOff, not Insufficient cpu.
      B: Correct — this is a scheduling failure, not a runtime failure.
      C: Liveness probes run after the container starts; they cause CrashLoopBackOff.
      D: NetworkPolicy controls traffic, not scheduling.
```

Upload from the web UI, CLI, or API. See [Question Format docs](https://vikas027.github.io/quiz-prep/question-format/) for the full reference.

---

## MCP server

quiz-prep ships a standalone MCP server (`vikas027/quiz-prep-mcp`) that exposes 5 tools and 3 resources over SSE. Once connected, you can ask Claude to manage your question banks without leaving your editor.

### Connect

```bash
# Set your deployment URL (once)
# In mise.toml [env] or .mise.local.toml:
QUIZ_MCP_URL = "https://your-domain.example.com"

# Register with Claude Code (user scope, all projects)
mise run mcp-claude-add

# Or manually:
claude mcp add --scope user --transport sse quiz-prep https://your-domain.example.com/mcp/sse
```

For Cursor, add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "quiz-prep": {
      "url": "https://your-domain.example.com/mcp/sse",
      "transport": "sse"
    }
  }
}
```

### What Claude can do

```
"List all available quizzes"
"How many questions are in the cka quiz?"
"List questions in the cka quiz filtered to the Networking category"
"Import questions from /path/to/myquiz.yaml into the cka quiz"
"Export all questions from the gitops quiz as YAML"
"Disable question 42 in the cka quiz"
"Show my score history for the aws-sa quiz"
```

The MCP server is a separate Docker image (`vikas027/quiz-prep-mcp`) with its own release lifecycle and semantic version.

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `QUIZ_DB` | `./data/quiz.db` | Path to the SQLite database |
| `PORT` | `8080` | Server listen port |
| `QUIZ_SCORE_MAX` | `10` | Max score history entries per quiz |
| `MCP_PORT` | `8000` | MCP server listen port |
| `QUIZ_APP_URL` | `http://localhost:8080` | Quiz API base URL (MCP server uses this to reach the app) |
| `MCP_AUTH_TOKEN` | — | Optional static bearer token for the MCP server |

---

## Development

```bash
mise run lint        # ruff check + format
mise run test        # pytest unit tests
mise run hurl        # Hurl API integration tests (server must be running)
mise run mcp-test    # MCP unit tests
mise run docs-serve  # MkDocs preview → http://127.0.0.1:8000
```

All `mise run` tasks are defined in [`mise.toml`](mise.toml). Full docs at [vikas027.github.io/quiz-prep](https://vikas027.github.io/quiz-prep/).

---

## Project structure

```
src/
  db.py          SQLite data layer — all SQL lives here
  api/           FastAPI app (routes, schemas, main)
  cli/           Typer CLI (quiz run, questions, scores)
  web/           Single-page app (index.html)
mcp/             Standalone MCP server (FastMCP SSE)
tests/
  cli/           pytest unit tests
  api/           Hurl integration tests
  fixtures/      Sample YAML question banks
docs/            MkDocs source
```

---

## Contributing

1. Fork the repo and create a branch
2. Make your changes with tests
3. Run `mise run lint && mise run test && mise run hurl` (server running)
4. Open a PR against `main`

Please follow [Conventional Commits](https://www.conventionalcommits.org/) — the release pipeline depends on it.

See [CONTRIBUTING.md](docs/contributing.md) for the full guide.

---

## License

MIT — see [LICENSE](LICENSE).
