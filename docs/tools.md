# Tools

## Frontend
| Tool | Version | Purpose |
|------|---------|---------|
| Tailwind CSS | v4.3 (CDN) | Utility-first CSS framework |
| Vanilla JavaScript | ES2024 | SPA interactivity, keyboard nav |

## Backend
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14.6 | Runtime |
| FastAPI | 0.139.0 | API framework with auto Swagger |
| Pydantic | v2 | Request/response validation |
| SQLite | stdlib | Database (via raw sqlite3) |
| Gunicorn + UvicornWorker | latest | Production WSGI/ASGI server |
| Typer | latest | CLI framework |
| Rich | latest | Terminal output styling |
| questionary | 2.1.0 | Interactive CLI prompts |

## Testing
| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 8.x | Unit tests for CLI and DB layer |
| Hurl | 8.0.1 | HTTP API integration tests |

## Infrastructure
| Tool | Version | Purpose |
|------|---------|---------|
| Docker | — | Container runtime |
| docker compose | v2 | Local multi-container orchestration |
| Kubernetes | — | Production deployment |
| mise | latest | Task runner (replaces Make) |

## CI/CD
| Tool | Version | Purpose |
|------|---------|---------|
| GitHub Actions | — | CI/CD pipeline |
| release-please | v5.0.0 | Semver releases from conventional commits |
| Renovate | latest | Automated dependency updates |
| Dependabot | — | GitHub-native dependency alerts |
| cosign | v4.1.2 | Keyless container image signing |
| Trivy | v0.36.0 | Container vulnerability scanning |

## Code Quality
| Tool | Version | Purpose |
|------|---------|---------|
| ruff | 0.15.20 | Linter + formatter (replaces flake8/black/isort) |
| mypy | 1.10.0 | Static type checker |
| pre-commit | 3.7.0 | Git hook runner |
| actionlint | v1.7.12 | GitHub Actions workflow linter |
| hadolint | v2.14.0 | Dockerfile linter |
| yamllint | v1.38.0 | YAML style checker |

## Docs
| Tool | Version | Purpose |
|------|---------|---------|
| MkDocs | latest | Static site generator |
| MkDocs Material | latest | Theme |
