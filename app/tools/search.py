from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.search")


class SearchInput(ToolInputSchema):
    query: str
    max_results: int = 5


class SearchTool(BaseTool):
    name = "search"
    description = "Perform a web search"
    input_schema = SearchInput
    required_permissions = ["web:search"]

    def run(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            import requests
            search_url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": 1}
            response = requests.get(search_url, params=params, timeout=10)
            data = response.json()
            results = []
            for item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(item, dict) and "Text" in item:
                    results.append({"title": item.get("Text", ""), "url": item.get("FirstURL", "")})
            return ToolResult(success=True, data={"query": query, "results": results})
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(success=False, error=str(e))
