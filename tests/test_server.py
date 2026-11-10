import io
import json

from mcpserver.server import MCPServer
from mcpserver.tools import calculator, now


def _server():
    return MCPServer("test-server", "0.0.1", [calculator, now])


def test_initialize_handshake():
    reply = _server().handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    result = reply["result"]
    assert result["protocolVersion"] == "2025-03-26"
    assert result["serverInfo"]["name"] == "test-server"
    assert "tools" in result["capabilities"]


def test_notification_gets_no_reply():
    assert _server().handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_tools_list_descriptors():
    reply = _server().handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = {t["name"]: t for t in reply["result"]["tools"]}
    assert set(tools) == {"calculator", "now"}
    assert tools["calculator"]["inputSchema"]["required"] == ["expression"]


def test_tools_call_calculator():
    reply = _server().handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "calculator", "arguments": {"expression": "6*7"}},
    })
    result = reply["result"]
    assert result["isError"] is False
    assert result["content"][0] == {"type": "text", "text": "6*7 = 42"}


def test_tools_call_unknown_tool_is_protocol_error():
    reply = _server().handle({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "nope", "arguments": {}},
    })
    assert reply["error"]["code"] == -32602


def test_tool_exception_is_error_content_not_protocol_error():
    reply = _server().handle({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "calculator", "arguments": {"expression": "1/0"}},
    })
    assert "result" in reply
    assert reply["result"]["isError"] is True
    assert "ZeroDivisionError" in reply["result"]["content"][0]["text"]


def test_unknown_method():
    reply = _server().handle({"jsonrpc": "2.0", "id": 6, "method": "resources/list"})
    assert reply["error"]["code"] == -32601


def test_serve_over_pipes():
    stdin = io.StringIO(
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"calculator","arguments":{"expression":"2+2"}}}\n'
        "not json\n"
    )
    stdout = io.StringIO()
    _server().serve(stdin=stdin, stdout=stdout)
    lines = [json.loads(l) for l in stdout.getvalue().splitlines()]
    assert lines[0]["result"]["serverInfo"]["name"] == "test-server"
    assert lines[1]["result"]["content"][0]["text"] == "2+2 = 4"
    assert lines[2]["error"]["code"] == -32700  # parse error
