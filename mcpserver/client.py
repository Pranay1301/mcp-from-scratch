"""A minimal MCP stdio client: spawn the server, handshake, call tools.

    python3 -m mcpserver.client

This is how the tests exercise the real transport - the server runs as a
subprocess and speaks newline-delimited JSON-RPC over its pipes.
"""

from __future__ import annotations

import json
import subprocess
import sys


class MCPClient:
    def __init__(self, argv: list[str]):
        self.proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )
        self._next_id = 0

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}})
        reply = json.loads(self.proc.stdout.readline())
        assert reply["id"] == self._next_id, "out-of-order reply"
        return reply

    def notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def _send(self, msg: dict) -> None:
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def initialize(self) -> dict:
        reply = self.request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "mcp-from-scratch-client", "version": "0.1"},
        })
        self.notify("notifications/initialized")
        return reply["result"]

    def call_tool(self, name: str, arguments: dict) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments})["result"]

    def close(self) -> None:
        self.proc.stdin.close()
        self.proc.wait(timeout=5)


def main() -> int:
    client = MCPClient([sys.executable, "-m", "mcpserver"])
    print("initialize:", json.dumps(client.initialize()))
    tools = client.request("tools/list")["result"]["tools"]
    print("tools/list:", [t["name"] for t in tools])
    print("tools/call calculator:", client.call_tool("calculator", {"expression": "6*7"}))
    print("tools/call now:", client.call_tool("now", {}))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
