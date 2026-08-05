from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.exceptions import ToolExecutionError
from app.core.logging import get_logger

logger = get_logger("tools.calculator")


class CalculatorInput(ToolInputSchema):
    expression: str


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a mathematical expression safely"
    input_schema = CalculatorInput
    required_permissions = []

    def run(self, expression: str) -> ToolResult:
        try:
            import ast
            import operator
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
            }
            allowed_names = {}

            def _validate(node):
                if isinstance(node, ast.Expression):
                    _validate(node.body)
                elif isinstance(node, ast.BinOp):
                    if type(node.op) not in allowed_operators:
                        raise ToolExecutionError(self.name, f"Operator {type(node.op).__name__} not allowed")
                    _validate(node.left)
                    _validate(node.right)
                elif isinstance(node, ast.UnaryOp):
                    if type(node.op) not in allowed_operators:
                        raise ToolExecutionError(self.name, f"Unary operator {type(node.op).__name__} not allowed")
                    _validate(node.operand)
                elif isinstance(node, ast.Call):
                    raise ToolExecutionError(self.name, "Function calls are not allowed")
                elif isinstance(node, ast.Name):
                    if node.id not in allowed_names:
                        raise ToolExecutionError(self.name, f"Name '{node.id}' is not allowed")
                elif isinstance(node, ast.Constant):
                    if not isinstance(node.value, (int, float)):
                        raise ToolExecutionError(self.name, "Only numeric constants are allowed")
                else:
                    raise ToolExecutionError(self.name, f"Expression contains disallowed element: {type(node).__name__}")

            node = ast.parse(expression, mode="eval")
            _validate(node)
            result = eval(compile(node, "<string>", "eval"), {"__builtins__": {}}, allowed_names)
            return ToolResult(success=True, data={"expression": expression, "result": result})
        except Exception as e:
            logger.error(f"Calculator failed: {e}")
            return ToolResult(success=False, error=str(e))
