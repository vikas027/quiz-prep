#!/usr/bin/env python3
"""Import a single YAML question bank via the MCP server (bypasses OAuth2).

Usage:
    python3 scripts/seed_mcp.py <file.yaml> [mcp_sse_url]

Defaults mcp_sse_url to $QUIZ_MCP_URL env var, or http://localhost:8000/sse.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

import yaml


def slugify(label: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", label.lower())).strip("-") or "quiz"


async def seed(path: Path, mcp_url: str) -> None:
    from fastmcp import Client
    from fastmcp.client.transports import SSETransport

    raw = path.read_text()
    data = yaml.safe_load(raw)
    label = data.get("quiz_name", path.stem) if isinstance(data, dict) else path.stem
    slug = slugify(label)

    transport = SSETransport(url=mcp_url, sse_read_timeout=120)
    print(f"→ Connecting to {mcp_url} ...")
    async with Client(transport) as client:
        print(f"→ Creating quiz '{slug}' ...")
        try:
            await client.call_tool("manage_quiz", {"action": "create", "quiz_name": slug, "label": label})
        except Exception:
            pass
        print(f"→ Importing {path.name} ...")
        result = await client.call_tool("manage_quiz", {"action": "import", "quiz_name": slug, "yaml_content": raw})

    data = result.data if result else {}
    if isinstance(data, dict):
        msg = f"✓ Imported {data.get('imported', '?')} question(s) into '{slug}'"
        if data.get("skipped"):
            msg += f" ({data['skipped']} duplicate(s) skipped)"
    else:
        msg = f"✓ Done: {data}"
    print(msg)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/seed_mcp.py <file.yaml> [mcp_sse_url]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    base = os.environ.get("QUIZ_MCP_URL", "http://localhost:8000")
    mcp_url = sys.argv[2] if len(sys.argv) > 2 else f"{base}/mcp/sse"

    try:
        asyncio.run(asyncio.wait_for(seed(path, mcp_url), timeout=120))
    except TimeoutError:
        print("✗ Timed out after 120s — is the MCP server reachable?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
