"""End-to-end over the real stdio transport: the server runs as a
subprocess and the client speaks newline-delimited JSON-RPC to it."""

import sys

from mcpserver.client import MCPClient


def test_full_session_over_subprocess():
    client = MCPClient([sys.executable, "-m", "mcpserver"])
    try:
        info = client.initialize()
        assert info["serverInfo"]["name"] == "mcp-from-scratch-demo"

        tools = client.request("tools/list")["result"]["tools"]
        assert {t["name"] for t in tools} == {"calculator", "now"}

        result = client.call_tool("calculator", {"expression": "7*8"})
        assert result["content"][0]["text"] == "7*8 = 56"

        result = client.call_tool("now", {})
        assert result["content"][0]["text"].endswith("Z")

        bad = client.call_tool("calculator", {"expression": "1/0"})
        assert bad["isError"] is True
    finally:
        client.close()
