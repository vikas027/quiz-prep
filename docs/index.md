# quiz-prep

Self-hosted certification exam practice. Upload YAML question banks, run quizzes in the browser or terminal.

## Features

- **Web UI** — dark/light mode, quiz picker, category filter, timer, score history
- **REST API** — full CRUD + Swagger at `/swagger`, MkDocs at `/docs`
- **CLI** — interactive quiz, question management, score history
- **Docker + Kubernetes** — persistent SQLite on a named volume

---

## Prerequisites

Install these tools before running any `mise run` command:

| Tool | Install | Purpose |
|------|---------|---------|
| [mise](https://mise.jdx.dev) | `brew install mise` | Task runner (replaces make/npm scripts) |
| [Docker](https://docs.docker.com/get-docker/) | Docker Desktop or `brew install docker` | Container builds and `mise run up` |
| [Docker Compose](https://docs.docker.com/compose/) | Bundled with Docker Desktop | Multi-container stack |
| [Hurl](https://hurl.dev) | `brew install hurl` | API integration tests (`mise run hurl`) |
| Python 3.14+ | `mise install` (auto via `.python-version`) | Runtime + CLI |

`mise install` auto-provisions the correct Python version via `.python-version`. All other Python deps are installed by `mise run install`.

---

## Quickstart (Docker)

The fastest way to run, test, and tear down the full stack.

### 1. Start the server

```bash
mise run up
```

Builds the Docker image, starts the container, and serves the app at **[http://localhost:8080](http://localhost:8080)**.
Automatically runs `install`, `docs-build`, and `lint` before starting.

To tail logs in a separate terminal:

```bash
mise run logs
```

### 2. Load sample data

```bash
mise run seed-all
```

Imports the bundled sample question banks via the HTTP API (works with Docker volumes). Open **[http://localhost:8080](http://localhost:8080)** — all quizzes now appear in the picker.

### 3. Run API tests

```bash
mise run hurl
```

Runs all Hurl test suites against the live server. Tests are self-contained (they create and clean up their own data). No seed data required.

Expected output:

```
Succeeded files: X (100.0%)
Failed files:    0 (0.0%)
```

### 4. Clean up

**Stop only (keep data):**

```bash
mise run down
```

Stops the container. The `quiz_data` volume is preserved — data survives a restart.

**Stop and wipe data:**

```bash
mise run clean
```

Stops the container **and removes the `quiz_data` volume**. Run `mise run seed-all` again after the next `mise run up`.

---

## Quickstart (CLI)

No Docker needed. Uses the local SQLite file at `data/quiz.db`.

!!! info "CLI vs web server"
    CLI commands (`quiz run`, `quiz questions`, etc.) read and write the SQLite database **directly** — they do not go through the HTTP server. Stopping `mise run dev` or `mise run up` does not affect CLI functionality. Both the web server and the CLI share the same `data/quiz.db` file.

### 1. Install dependencies

```bash
mise run install
```

### 2. Load sample data

```bash
mise run seed-all
```

Seeds all 4 question banks. Detects whether the local dev server is running — uses the HTTP API if it is, otherwise writes directly to the local DB via CLI.

### 3. Run the quiz interactively

```bash
mise run quiz
```

Shows an interactive picker with all seeded quizzes. Navigate with `↑↓`, select with `Enter`.

Or target a specific quiz:

```bash
quiz run cka               # run CKA quiz
quiz run --limit 5         # only 5 questions
quiz run --mistakes        # drill your previous wrong answers
```

### 4. Manage questions via CLI

```bash
quiz questions list                    # list all quiz banks
quiz questions list cka                # list questions in CKA
quiz questions add cka                 # interactive prompt to add a question
quiz questions delete cka 42           # delete question by ID
quiz questions load myquiz.yaml        # import a YAML file
quiz questions export cka              # dump CKA back to YAML (stdout)
quiz questions export cka --out backup.yaml
```

### 5. Run unit tests

```bash
mise run test
```

Runs the pytest suite for the data layer and CLI commands.

Expected output:

```
All tests passed.
```

### 6. Clean up

```bash
mise run reset-db
```

Deletes `data/quiz.db`. No volume or container to worry about.

---

## Local development (no Docker)

!!! warning "Ensure Docker is not already running on :8080"
    Run `mise run clean` or `mise run down` before starting local dev.
    Both Docker and uvicorn cannot share port 8080.

### 1. Start the server

```bash
mise run dev
```

Starts uvicorn with auto-reload at **http://localhost:8080**.

### 2. Run API tests

```bash
mise run hurl
```

Runs all Hurl test suites against the live server. Tests are self-contained.

### 3. Load sample data

```bash
mise run seed-all
```

Detects the running server and seeds all 4 question banks via the HTTP API into the local `data/quiz.db`.

### 4. Run the quiz

```bash
mise run quiz
```

Opens an interactive quiz picker in the terminal. Navigate with `↑↓`, select with `Enter`.

Or target a specific quiz:

```bash
quiz run cka               # run CKA quiz
quiz run --limit 5         # only 5 questions
quiz run --mistakes        # drill your previous wrong answers
```

### 5. Clean up

```bash
mise run clean
```

Stops uvicorn and removes all local data.

---

## MCP server

quiz-prep exposes an MCP server at `/mcp/sse` (SSE transport). Claude can list quizzes, browse questions, manage question banks, and record scores through it.

!!! note "Set your MCP URL"
    Update `QUIZ_MCP_URL` in `mise.toml` with either your deployed URL or a `kubectl port-forward` address before running any `mcp-*` tasks:

    ```toml
    QUIZ_MCP_URL = "https://your-domain.example.com"   # deployed instance
    # or
    QUIZ_MCP_URL = "http://localhost:8000"              # kubectl port-forward
    ```

### When the MCP is publicly reachable

Use this when the `/mcp` route is exposed without auth:

```bash
mise run mcp-claude-add
# equivalent:
claude mcp add --scope user --transport sse quiz-prep https://your-domain.example.com/mcp/sse
```

### When the MCP is inside a Kubernetes cluster

Use this when the server is behind a VPN, auth proxy, or not publicly exposed. Open a port-forward first, then register with the local address:

```bash
kubectl port-forward -n quiz svc/quiz-mcp 8000:8000
claude mcp add --scope user --transport sse quiz-prep http://localhost:8000/sse
```

### Run a quiz (browser)

Open **[https://your-domain.example.com](https://your-domain.example.com)**, pick a quiz, set the number of questions and timer, then click **Start Quiz →**.

### Manage question banks via mise

The `mcp-remote-*` tasks call the MCP server directly — no OAuth2 required:

```bash
# Import a single YAML file (creates quiz if it doesn't exist, skips duplicates)
FILE=tests/fixtures/cka.yaml mise run mcp-remote-seed-file

# Import all YAML files in a folder
FOLDER=tests/fixtures mise run mcp-remote-seed-folder

# Delete a quiz and all its questions
QUIZ=cka mise run mcp-remote-reset-quiz

# Check MCP server health
mise run mcp-remote-health
```

### Manage question banks via Claude

Once MCP is connected (`mise run mcp-claude-add`), ask Claude directly:

```
# List all quizzes (includes question count per quiz)
"List all available quizzes"

# Browse questions — always filter by category to avoid dumping all tokens
"List questions in the cka quiz filtered to the Networking category"
"How many questions are in the cka quiz?"

# Import questions from a file path
"Import questions from /path/to/myquiz.yaml into the cka quiz"

# Export questions (MCP returns YAML directly — no curl needed)
"Export all questions from the gitops quiz as YAML"

# Disable / re-enable a question
"Disable question 42 in the cka quiz"
"Show me all disabled questions in the cka quiz"
"Re-enable question 42 in the cka quiz"

# Delete a quiz
"Delete the cka quiz — I confirm the deletion"

# Score history
"Show my score history for the aws-sa quiz"
```

For the full list of MCP-related `mise` tasks (local dev, lint, build, Docker), see [`mise.toml`](https://github.com/vikas027/quiz-prep/blob/main/mise.toml).

---

## Kubernetes

```bash
# Replace OWNER in k8s.yaml with your GitHub username first
mise run k8s-apply         # apply all manifests
mise run k8s-status        # check pod/PVC status
mise run k8s-logs          # tail pod logs
mise run seed-k8s          # copy all fixture YAMLs into the running pod
```

---

## Docs

```bash
mise run docs-serve        # preview at http://127.0.0.1:8000
mise run docs-build        # build static site (strict mode)
```
