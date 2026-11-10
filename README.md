# mcp-from-scratch — a Model Context Protocol server with no SDK

A working MCP server implemented directly from the protocol: JSON-RPC 2.0
over stdio (newline-delimited), the `initialize` handshake, `tools/list`,
`tools/call`, pings, notifications, and spec-shaped errors. Standard
library only — the protocol is small enough to read end to end, and this
repo proves it.

## What it implements

- **Lifecycle**: `initialize` returns `protocolVersion` (2025-03-26),
  capabilities, and server info; `notifications/initialized` gets no
  reply, as the spec requires.
- **Tools**: `tools/list` returns descriptors with JSON Schema inputs;
  `tools/call` returns content blocks. The demo server exposes a safe
  arithmetic calculator (AST-parsed, no `eval`) and a UTC clock.
- **Errors, the spec's way**: unknown method → `-32601`, unknown tool →
  `-32602`, malformed JSON on the wire → `-32700`, and a tool that throws
  becomes an `isError: true` content block — tool failures are data for
  the model to reason about, not protocol errors.
- **A real client** (`mcpserver/client.py`): spawns the server as a
  subprocess and speaks the protocol over its pipes — the same transport
  Claude Desktop and other hosts use.

## Run it

```bash
python3 -m mcpserver.client     # spawn server, handshake, list + call tools
python3 -m mcpserver            # run the server bare on stdio
python3 -m pytest tests/ -q     # 9 tests
```

Executed client output:

```
initialize: {"protocolVersion": "2025-03-26", ... "serverInfo": {"name": "mcp-from-scratch-demo", "version": "0.1.0"}}
tools/list: ['calculator', 'now']
tools/call calculator: {'content': [{'type': 'text', 'text': '6*7 = 42'}], 'isError': False}
tools/call now: {'content': [{'type': 'text', 'text': '2026-11-10T19:02:46Z'}], 'isError': False}
```

## Measured results

Executed on this machine, 2026-11-11, Python 3.10:

- **9/9 tests pass**, including an end-to-end test that runs the server as
  a real subprocess and drives the full session (handshake → list → calls
  → error cases) over actual pipes.

## Honest limits

- Tools only: no `resources/*` or `prompts/*` methods yet (unknown
  methods correctly return `-32601` — tested).
- stdio transport only; no HTTP/SSE transport.
- No schema validation of tool arguments beyond what each tool enforces;
  a production server would validate against `inputSchema` before calling.
- Protocol version is pinned to 2025-03-26; version negotiation with a
  host proposing something newer is not implemented.

## Layout

```
mcpserver/   server (protocol + transport), client, tools, __main__
tests/       9 tests, including the subprocess end-to-end session
```
