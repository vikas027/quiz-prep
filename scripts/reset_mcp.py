#!/usr/bin/env python3
"""Delete a quiz and all its questions via the MCP server (bypasses OAuth2).

Usage:
    python3 scripts/reset_mcp.py <quiz_name> [mcp_sse_url]

Defaults mcp_sse_url to $QUIZ_MCP_URL env var, or http://localhost:8000/sse.
"""

import asyncio
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import SSETransport


async def reset(quiz: str, mcp_url: str) -> None:
    transport = SSETransport(url=mcp_url, sse_read_timeout=120)
    print(f"→ Connecting to {mcp_url} ...")
    async with Client(transport) as client:
        print(f"→ Deleting quiz '{quiz}' ...")
        await client.call_tool("manage_quiz", {"action": "delete", "quiz_name": quiz, "confirm_delete": True})
    print(f"✓ Deleted quiz '{quiz}' and all its questions")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/reset_mcp.py <quiz_name> [mcp_sse_url]", file=sys.stderr)
        sys.exit(1)

    quiz = sys.argv[1]
    base = os.environ.get("QUIZ_MCP_URL", "http://localhost:8000")
    mcp_url = sys.argv[2] if len(sys.argv) > 2 else f"{base}/mcp/sse"

    try:
        asyncio.run(asyncio.wait_for(reset(quiz, mcp_url), timeout=120))
    except TimeoutError:
        print("✗ Timed out after 120s — is the MCP server reachable?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
