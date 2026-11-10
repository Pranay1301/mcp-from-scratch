"""Run the demo server: python3 -m mcpserver"""

from .server import MCPServer
from .tools import calculator, now

if __name__ == "__main__":
    MCPServer("mcp-from-scratch-demo", "0.1.0", [calculator, now]).serve()
