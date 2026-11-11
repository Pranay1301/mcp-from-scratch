"""Tools exposed by the demo server."""

from __future__ import annotations

import ast
import operator
import time

from .server import Tool

_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 100 or abs(left) > 1e6):
            raise ValueError("power exceeds demo limit")
        value = _BINOPS[type(node.op)](left, right)
        if isinstance(value, complex) or abs(value) > 1e100:
            raise ValueError("result exceeds demo limit")
        return value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand)
    raise ValueError("only + - * / ** % on numbers")


calculator = Tool(
    name="calculator",
    description="Evaluate an arithmetic expression like 2+3*4.",
    input_schema={
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
    fn=lambda args: f"{args['expression']} = {_eval(ast.parse(str(args['expression']), mode='eval'))}",
)

now = Tool(
    name="now",
    description="Current UTC time, ISO 8601.",
    input_schema={"type": "object", "properties": {}},
    fn=lambda args: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
)
