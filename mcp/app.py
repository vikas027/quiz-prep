import os

from fastmcp import FastMCP

_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN")

if _AUTH_TOKEN:
    from fastmcp.server.auth import StaticTokenVerifier

    mcp = FastMCP(
        "quiz-prep",
        auth=StaticTokenVerifier(
            tokens={
                _AUTH_TOKEN: {"sub": "quiz-mcp-client", "client_id": "quiz-mcp"},
            }
        ),
    )
else:
    import warnings

    warnings.warn("MCP_AUTH_TOKEN is not set — server is unauthenticated", stacklevel=1)
    mcp = FastMCP("quiz-prep")
