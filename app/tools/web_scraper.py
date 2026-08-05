from typing import Any, Dict, Optional, List
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.web_scraper")


class WebScraperInput(ToolInputSchema):
    url: str
    extract_type: str = "text"
    max_pages: int = 1
    wait_time: float = 2.0


class WebScraperTool(BaseTool):
    name = "web_scraper"
    description = "Scrape web pages and extract content"
    input_schema = WebScraperInput
    required_permissions = ["web:scrape"]

    def run(
        self,
        url: str,
        extract_type: str = "text",
        max_pages: int = 1,
        wait_time: float = 2.0,
    ) -> ToolResult:
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            if extract_type == "text":
                for script in soup.find_all("script"):
                    script.decompose()
                for style in soup.find_all("style"):
                    style.decompose()
                text = soup.get_text(separator="\n", strip=True)
            elif extract_type == "markdown":
                text = self._html_to_markdown(soup)
            elif extract_type == "links":
                links = [a.get("href", "") for a in soup.find_all("a", href=True)]
                text = "\n".join(links)
            elif extract_type == "structured":
                text = self._extract_structured(soup)
            else:
                text = soup.get_text(separator="\n", strip=True)

            result = {
                "url": url,
                "extract_type": extract_type,
                "content": text[:10000],
                "title": soup.title.string if soup.title else "",
                "status_code": response.status_code,
            }
            logger.info(f"Web scraping completed: {url}")
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return ToolResult(success=False, error=str(e))

    def _html_to_markdown(self, soup: Any) -> str:
        lines = []
        for element in soup.find_all(["h1", "h2", "h3", "p", "ul", "ol", "li", "a", "blockquote"]):
            if element.name.startswith("h"):
                level = int(element.name[1])
                lines.append(f"{'#' * level} {element.get_text(strip=True)}")
            elif element.name == "p":
                lines.append(element.get_text(strip=True))
            elif element.name in ["ul", "ol"]:
                for li in element.find_all("li"):
                    lines.append(f"- {li.get_text(strip=True)}")
            elif element.name == "a":
                href = element.get("href", "")
                text = element.get_text(strip=True)
                lines.append(f"[{text}]({href})")
            elif element.name == "blockquote":
                lines.append(f"> {element.get_text(strip=True)}")
        return "\n\n".join(lines)

    def _extract_structured(self, soup: Any) -> str:
        structured = {
            "title": soup.title.string if soup.title else "",
            "headings": [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])],
            "paragraphs": [p.get_text(strip=True) for p in soup.find_all("p")],
            "links": [{"text": a.get_text(strip=True), "href": a.get("href", "")} for a in soup.find_all("a", href=True)],
            "images": [{"alt": img.get("alt", ""), "src": img.get("src", "")} for img in soup.find_all("img")],
        }
        import json
        return json.dumps(structured, indent=2, ensure_ascii=False)