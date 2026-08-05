from typing import Any, Dict, Optional, List
from pathlib import Path
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.ocr")


class OCRInput(ToolInputSchema):
    file_path: str
    output_format: str = "text"
    language: str = "eng"


class OCRTool(BaseTool):
    name = "ocr"
    description = "Extract text from images and PDFs using OCR"
    input_schema = OCRInput
    required_permissions = ["document:read"]

    def __init__(self, ocr_engine: str = "tesseract", **kwargs):
        super().__init__(**kwargs)
        self.ocr_engine = ocr_engine

    def run(self, file_path: str, output_format: str = "text", language: str = "eng") -> ToolResult:
        try:
            from pathlib import Path
            path = Path(file_path)
            if not path.exists():
                return ToolResult(success=False, error=f"File not found: {file_path}")

            ext = path.suffix.lower()
            if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}:
                text = self._ocr_image(path, language)
            elif ext == ".pdf":
                text = self._ocr_pdf(path, language)
            else:
                return ToolResult(success=False, error=f"Unsupported file type for OCR: {ext}")

            result = {"text": text, "format": output_format, "language": language, "file": file_path}
            logger.info(f"OCR completed for {file_path}: {len(text)} chars extracted")
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            return ToolResult(success=False, error=str(e))

    def _ocr_image(self, path: Path, language: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(str(path))
            return pytesseract.image_to_string(img, lang=language)
        except ImportError:
            return self._fallback_ocr_image(path)

    def _ocr_pdf(self, path: Path, language: str) -> str:
        try:
            import pytesseract
            from pdf2image import convert_from_path
            images = convert_from_path(str(path))
            texts = []
            for img in images:
                text = pytesseract.image_to_string(img, lang=language)
                texts.append(text)
            return "\n\n".join(texts)
        except ImportError:
            return self._fallback_ocr_pdf(path)

    def _fallback_ocr_image(self, path: Path) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["tesseract", str(path), "stdout", "-l", "eng"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.stdout
        except Exception:
            return f"[OCR fallback] Could not extract text from {path.name}"

    def _fallback_ocr_pdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            texts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
            return "\n\n".join(texts) if texts else f"[OCR fallback] No text extracted from {path.name}"
        except Exception:
            return f"[OCR fallback] Could not extract text from {path.name}"