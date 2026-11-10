"""mcp-from-scratch - a minimal Model Context Protocol server, stdlib only.

JSON-RPC 2.0 over stdio: initialize handshake, tools/list, tools/call.
No SDK - the protocol is small enough to implement directly, which is the
point of the project.
"""

from .server import MCPServer, Tool

__all__ = ["MCPServer", "Tool"]
