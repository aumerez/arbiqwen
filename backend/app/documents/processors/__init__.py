# Document processors (PDF, DOCX, PPTX, XLSX, CSV, TXT)
from typing import Protocol


class DocumentProcessor(Protocol):
    """Protocol for document text extraction."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from a document file."""
        ...
