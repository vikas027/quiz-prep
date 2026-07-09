# MCP Server

The quiz-prep MCP server exposes 5 tools and 3 resources over SSE transport at `/mcp/sse`.
It lets any MCP-compatible client list quizzes, browse questions, import question banks, and record scores.

---

## Connecting

Two scenarios depending on how the MCP server is deployed:

**Scenario A — MCP is publicly reachable** (e.g. `https://your-domain.example.com/mcp/sse` is exposed without auth): register directly with the public URL.

**Scenario B — MCP is inside a Kubernetes cluster** (behind a VPN, auth proxy, or not exposed externally): open a port-forward first, then register with the local address.

### Scenario A — Public URL

#### Claude Code

```bash
mise run mcp-claude-add
# equivalent:
claude mcp add --scope user --transport sse quiz-prep https://your-domain.example.com/mcp/sse
```

Or add to `.mcp.json` in the project root (shared, gitignored):

```json
{
  "mcpServers": {
    "quiz-prep": {
      "type": "sse",
      "url": "https://your-domain.example.com/mcp/sse"
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json` or via **Cursor Settings → MCP**:

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

#### Codex

Add to `~/.codex/config.yaml`:

```yaml
mcp_servers:
  - name: quiz-prep
    url: https://your-domain.example.com/mcp/sse
    transport: sse
```

### Scenario B — Kubernetes port-forward

Use this when the MCP server is not publicly exposed or is behind an auth proxy.

```bash
# Open a port-forward to the MCP service
kubectl port-forward -n quiz svc/quiz-mcp 8000:8000

# Register with the local address (in a separate terminal)
claude mcp add --scope user --transport sse quiz-prep http://localhost:8000/sse
```

For Cursor or Codex, use `http://localhost:8000/sse` as the URL while the port-forward is running.

---

## Best Practices Followed

Documents how the quiz-prep MCP server implements established best practices for tool design, error handling, and server configuration.

### Tool descriptions

Effective tool descriptions use 40–50 words covering five elements: purpose, input format, output format, use cases, and boundary conditions. Short descriptions produce poor routing accuracy and wrong argument values.

Every quiz-prep tool description includes all five elements. Example:

> `manage_quiz` — "Creates, deletes, imports, or exports a quiz set. action: 'create' (requires
> label string), 'delete' (requires confirm_delete=true — irreversible), 'import' (requires
> yaml_content string — appends new questions, skips exact text duplicates, returns imported and
> skipped counts), 'export' (returns YAML string of all questions). NOT for individual question
> edits — use manage_question." (48 words)

- Purpose: ✅ "Creates, deletes, imports, or exports a quiz set"
- Input format: ✅ each action's requirements listed (label, confirm_delete, yaml_content)
- Output format: ✅ import → imported/skipped counts; export → YAML string
- Use cases: ✅ each action scoped to one lifecycle operation
- Boundary: ✅ "NOT for individual question edits — use manage_question"

**File:** `mcp/tools.py`

---

### Tool registration fields

All three required fields are present on every tool: `name` (snake_case, specific), `description` (primary routing signal, 40–50 words), and `input_schema` (field-level descriptions with examples). Missing field descriptions cause wrong argument values at call time.

- `name`: all tools use specific snake_case names (`list_quizzes`, `manage_question`, not `tool_1`)
- `description`: 40–50 words per tool
- `input_schema`: all parameters use `Annotated[T, Field(description="...")]` with explicit descriptions and examples, e.g.:
  - `action: Annotated[str, Field(description="Must be one of: 'create', 'delete', 'import', 'export'")]`
  - `quiz_name: Annotated[str, Field(description="Quiz set slug, e.g. 'cka', 'aws-sa'")]`

**File:** `mcp/tools.py`

---

### No keyword routing rules

Keyword routing rules in system prompts ("when user mentions import, use manage_quiz") override description-based selection and degrade routing accuracy. They accumulate into conflicts over time.

No keyword routing rules exist in any system prompt, tool description, or client config. Tool routing relies entirely on the model's semantic understanding of tool descriptions.

**File:** `mcp/tools.py`

---

### Structured error responses

Generic error messages yield very low agent recovery. Structured errors with `errorCategory`, `isRetryable`, `customerMessage`, and `suggestedAction` enable agents to respond correctly — retrying transient failures, correcting validation input, and escalating permission issues immediately.

All errors raise `ToolError` with a compact JSON payload:
`{"errorCategory": "...", "isRetryable": bool, "attempted": "METHOD /path", "customerMessage": "...", "suggestedAction": "..."}`

| Status | errorCategory | isRetryable |
|---|---|---|
| 400, 422 | validation | true |
| 401, 403 | permission | false |
| 404, 409 | business | false |
| 429 | rate_limit | true |
| network, 5xx | transient | true |

Internal hostnames and infrastructure details are never exposed in error messages.

**File:** `mcp/client.py`

---

### Distinct errors per failure type

Returning identical error messages for all failure types causes agents to retry permission errors that can never succeed, and to give up on transient errors that would succeed on retry. Each HTTP status returns a distinct `errorCategory` and unique `customerMessage`.

**File:** `mcp/client.py`

---

### Distinguishing access failures from empty results

Access failures (timeout, connection refused) and valid empty results (200 OK, no rows) look identical to callers but must be handled differently.

- Returns `[]` (or `{}`) as-is when the API responds 200 with empty body — not an error
- Raises `ToolError` when a query fails to execute (network error, HTTP 5xx)
- Transient error messages include the attempted path: "temporarily unavailable (GET /quizzes/cka)"

**File:** `mcp/client.py`

---

### Retry strategy

Transient errors are retried locally before propagating. Propagated errors include failure type, `isRetryable`, attempted path, and suggested action.

- Retries `httpx.RequestError` (network/transient) once with 1 s sleep
- HTTP 429 retries once, respecting `Retry-After` header (bounded to 5 s)
- All other HTTP 4xx errors propagate immediately

**File:** `mcp/client.py`

---

### Model-driven tool selection

Four `tool_choice` modes exist: `auto` (model decides freely), `any` (must call a tool), `tool` (forces a specific tool), `none` (text-only). For general-purpose assistants, `auto` is correct.

`auto` is never overridden in client config or server configuration. The server does not impose `tool_choice` — that decision belongs to the client.

**File:** `mcp/app.py`

---

## Additional practices

### Tool count

11 quiz-prep API endpoints are grouped into 5 semantic tools: `list_quizzes`, `get_questions`, `manage_quiz`, `manage_question`, `manage_scores`. Fewer, broader tools improve routing accuracy over many narrow ones.

### Read-only and destructive annotations

`list_quizzes` and `get_questions` use `annotations={"readOnlyHint": True}`.
`manage_quiz` and `manage_question` use `annotations={"destructiveHint": True}`.

**File:** `mcp/tools.py`

### Resources vs Tools

3 Resources expose browseable data without inflating the tool count:

- `quiz://catalog` — list all quiz sets
- `quiz://{name}/questions` — up to 50 questions for a quiz set
- `quiz://{name}/scores` — score history for a quiz set

**File:** `mcp/resources.py`

### Secrets and scope

Server URL is provided via environment variable — never hardcoded in client config. Auth uses `StaticTokenVerifier` when `MCP_AUTH_TOKEN` env var is set.

**File:** `mcp/app.py`

### Independent lifecycle

Separate Docker image (`vikas027/quiz-prep-mcp`), separate release-please component, and separate CI workflow. MCP tags (`mcp-v0.1.0`) are independent from app tags (`v1.0.0`).
