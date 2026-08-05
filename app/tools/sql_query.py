from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.sql_query")


class SQLQueryInput(ToolInputSchema):
    query: str
    table: Optional[str] = None
    limit: int = 100


class SQLQueryTool(BaseTool):
    name = "sql_query"
    description = "Execute a read-only SQL query against the database"
    input_schema = SQLQueryInput
    required_permissions = ["db:read"]

    def __init__(self, db_session: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.db_session = db_session

    def run(self, query: str, table: Optional[str] = None, limit: int = 100) -> ToolResult:
        if self.db_session is None:
            return ToolResult(success=False, error="Database session not configured")
        try:
            from sqlalchemy import text
            stmt = text(query)
            result = self.db_session.execute(stmt)
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []
            data = [dict(zip(columns, row)) for row in rows[:limit]]
            return ToolResult(success=True, data={"columns": columns, "rows": data, "count": len(data)})
        except Exception as e:
            logger.error(f"SQL query failed: {e}")
            return ToolResult(success=False, error=str(e))
