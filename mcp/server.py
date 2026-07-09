import logging

import resources  # noqa: F401 — side-effect: registers resources
import tools  # noqa: F401 — side-effect: registers tools
from app import mcp
from client import MCP_PORT
from starlette.requests import Request
from starlette.responses import PlainTextResponse


class _NoHealthFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "GET /health" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(_NoHealthFilter())


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=MCP_PORT)
