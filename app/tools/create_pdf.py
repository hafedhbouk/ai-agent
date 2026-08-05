from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.create_pdf")


class CreatePDFInput(ToolInputSchema):
    title: str
    content: str
    filename: Optional[str] = None


class CreatePDFTool(BaseTool):
    name = "create_pdf"
    description = "Generate a PDF document from text content"
    input_schema = CreatePDFInput
    required_permissions = ["pdf:create"]

    def run(self, title: str, content: str, filename: Optional[str] = None) -> ToolResult:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            import io
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = [Paragraph(title, styles["Heading1"]), Spacer(1, 12)]
            for line in content.split("\n"):
                story.append(Paragraph(line, styles["BodyText"]))
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            logger.info(f"PDF created: {filename or 'document.pdf'}")
            return ToolResult(success=True, data={"filename": filename or "document.pdf", "size": len(pdf_bytes), "content_type": "application/pdf"})
        except ImportError:
            return ToolResult(success=False, error="reportlab is not installed. Install it to use PDF generation.")
        except Exception as e:
            logger.error(f"PDF creation failed: {e}")
            return ToolResult(success=False, error=str(e))
