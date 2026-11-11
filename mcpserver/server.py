"""A minimal MCP server over stdio (newline-delimited JSON-RPC 2.0).

Implements the 2025-03-26 lifecycle:
  - "initialize"            -> server info + capabilities
  - "notifications/initialized" (no reply)
  - "ping"                  -> {}
  - "tools/list"            -> tool descriptors with JSON Schema inputs
  - "tools/call"            -> content blocks or a JSON-RPC error

One JSON object per line, both directions (the original stdio transport).
Unknown methods get -32601; a tool raising becomes an isError content
block, which is what the spec asks for - tool failures are data, not
protocol errors.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

PROTOCOL_VERSION = "2025-03-26"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: object  # callable(dict) -> str

    def descriptor(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class MCPServer:
    def __init__(self, name: str, version: str, tools: list[Tool]):
        self.name = name
        self.version = version
        self.tools = {t.name: t for t in tools}
        self.initialized = False

    # -- protocol handlers -------------------------------------------------

    def handle(self, msg: dict) -> dict | None:
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
            return self._error(None, -32600, "invalid request")
        if "params" in msg and not isinstance(msg["params"], dict):
            return self._error(msg.get("id"), -32602, "params must be an object")
        method = msg.get("method", "")
        msg_id = msg.get("id")

        if "id" not in msg:
            return None
        if method == "initialize":
            self.initialized = True
            return self._result(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "notifications/initialized":
            return None  # notifications never get a reply
        if method == "ping":
            return self._result(msg_id, {})
        if method == "tools/list":
            return self._result(msg_id, {"tools": [t.descriptor() for t in self.tools.values()]})
        if method == "tools/call":
            return self._call_tool(msg_id, msg.get("params") or {})
        if msg_id is None:
            return None  # unknown notification: ignore
        return self._error(msg_id, -32601, f"method not found: {method}")

    def _call_tool(self, msg_id, params: dict) -> dict:
        name = params.get("name", "")
        tool = self.tools.get(name)
        if tool is None:
            return self._error(msg_id, -32602, f"unknown tool: {name}")
        try:
            text = str(tool.fn(params.get("arguments") or {}))
            content = [{"type": "text", "text": text}]
            return self._result(msg_id, {"content": content, "isError": False})
        except Exception as e:
            content = [{"type": "text", "text": f"{type(e).__name__}: {e}"}]
            return self._result(msg_id, {"content": content, "isError": True})

    @staticmethod
    def _result(msg_id, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    # -- stdio transport ---------------------------------------------------

    def serve(self, stdin=None, stdout=None) -> None:
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                stdout.write(json.dumps(self._error(None, -32700, "parse error")) + "\n")
                stdout.flush()
                continue
            reply = self.handle(msg)
            if reply is not None:
                stdout.write(json.dumps(reply) + "\n")
                stdout.flush()
