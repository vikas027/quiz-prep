#!/usr/bin/env python3
"""Seed all quiz question banks.

When the server is running (local or Docker), seeds via HTTP API so it
reaches the correct data store (Docker volume or local DB).
Falls back to the CLI when no server is running.
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
FIXTURES = [
    ROOT / "tests/fixtures/claude.yaml",
    ROOT / "tests/fixtures/aws-sa.yaml",
    ROOT / "tests/fixtures/cka.yaml",
    ROOT / "tests/fixtures/gitops.yaml",
]
BASE = "http://localhost:8080"


def slugify(label: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", label.lower())).strip("-")


def seed_via_api() -> None:
    import httpx

    with httpx.Client(base_url=BASE, timeout=30) as client:
        for path in FIXTURES:
            data = yaml.safe_load(path.read_text())
            label = data.get("quiz_name", path.stem)
            slug = slugify(label)

            client.post("/api/v1/quizzes", json={"name": slug, "label": label})
            client.delete(f"/api/v1/quizzes/{slug}/questions")

            with path.open("rb") as f:
                resp = client.post(
                    f"/api/v1/quizzes/{slug}/import",
                    files={"file": (path.name, f, "text/yaml")},
                )
            resp.raise_for_status()
            r = resp.json()
            msg = f"✓ Imported {r['imported']} questions into {slug}"
            if r.get("skipped"):
                msg += f" ({r['skipped']} duplicate(s) skipped)"
            print(msg)


def seed_via_cli() -> None:
    for path in FIXTURES:
        result = subprocess.run(
            ["quiz", "questions", "load", str(path), "--replace"],
            cwd=ROOT,
        )
        if result.returncode != 0:
            sys.exit(result.returncode)


def server_running() -> bool:
    try:
        import httpx

        httpx.get(f"{BASE}/api/v1/quizzes", timeout=3)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    if server_running():
        print(f"Server detected at {BASE} — seeding via API")
        seed_via_api()
    else:
        print("No server running — seeding via CLI into local DB")
        seed_via_cli()
