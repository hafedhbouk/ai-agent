from pathlib import Path
from typing import Optional, List
from app.rag.schemas import DocumentMetadata
from app.core.logging import get_logger
from app.core.exceptions import AgentPlatformException

logger = get_logger("rag.ingestor")


class DocumentIngestionError(AgentPlatformException):
    def __init__(self, filename: str, message: str):
        super().__init__(f"Failed to ingest document '{filename}': {message}", "DOCUMENT_INGESTION_ERROR")


class DocumentIngestor:
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}

    def __init__(self, upload_dir: str = "./data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise DocumentIngestionError(file_path.name, "File does not exist")
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DocumentIngestionError(
                file_path.name,
                f"Unsupported file type: {file_path.suffix}. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}",
            )

    async def ingest_file(self, file_path: Path, collection_name: str) -> DocumentMetadata:
        self.validate_file(file_path)
        try:
            content = await self._extract_text(file_path)
            metadata = DocumentMetadata(
                source=str(file_path),
                content=content,
                filename=file_path.name,
                mime_type=self._get_mime_type(file_path),
                metadata={"collection_name": collection_name, "file_path": str(file_path)},
            )
            logger.info(f"Ingested file: {file_path.name} ({len(content)} chars)")
            return metadata
        except Exception as e:
            logger.error(f"Failed to ingest file {file_path.name}: {e}")
            raise DocumentIngestionError(file_path.name, str(e))

    async def _extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return await self._extract_pdf(file_path)
        elif suffix == ".docx":
            return await self._extract_docx(file_path)
        elif suffix in {".txt", ".md", ".markdown"}:
            return await self._extract_text_file(file_path)
        else:
            raise DocumentIngestionError(file_path.name, f"Unsupported format: {suffix}")

    async def _extract_pdf(self, file_path: Path) -> str:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        texts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
        return "\n\n".join(texts)

    async def _extract_docx(self, file_path: Path) -> str:
        import docx2txt
        text = docx2txt.process(str(file_path))
        return text

    async def _extract_text_file(self, file_path: Path) -> str:
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise DocumentIngestionError(file_path.name, "Could not decode file with any supported encoding")

    def _get_mime_type(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        mime_types = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".txt": "text/plain", ".md": "text/markdown", ".markdown": "text/markdown"}
        return mime_types.get(suffix, "application/octet-stream")
