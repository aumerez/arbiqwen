"""PDF document processor using pypdf."""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _load_pdf_reader():
    """Import PdfReader (pypdf preferred, fall back to PyPDF2)."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore
    return PdfReader


def _parse_pdf_date(raw: str | None) -> datetime | None:
    """PDF dates are typically 'D:YYYYMMDDHHmmSS' (with optional TZ suffix)."""
    if not raw:
        return None
    s = raw.strip()
    if s.startswith("D:"):
        s = s[2:]
    # Try successively shorter prefixes to match whatever precision is present.
    for length, fmt in ((14, "%Y%m%d%H%M%S"), (12, "%Y%m%d%H%M"), (10, "%Y%m%d%H"), (8, "%Y%m%d")):
        if len(s) >= length:
            try:
                return datetime.strptime(s[:length], fmt)
            except ValueError:
                continue
    return None


class PDFProcessor:
    """Extract text and metadata from PDF files."""

    async def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        PdfReader = _load_pdf_reader()

        def _extract():
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)

        return await asyncio.to_thread(_extract)

    async def extract_metadata(self, file_path: str) -> dict:
        """Best-effort metadata extraction — returns {} on any failure."""
        PdfReader = _load_pdf_reader()

        def _get_field(info, attr: str, dict_key: str):
            """Read a field from a pypdf DocumentInformation (attr or dict-like)."""
            val = getattr(info, attr, None)
            if val is None and hasattr(info, "get"):
                val = info.get(dict_key)
            if val is None:
                return None
            val = str(val).strip()
            return val or None

        def _extract():
            try:
                reader = PdfReader(file_path)
                info = getattr(reader, "metadata", None)
                if info is None:
                    return {}

                author = _get_field(info, "author", "/Author")
                title = _get_field(info, "title", "/Title")

                # creation_date may already be a datetime in newer pypdf
                raw_date = getattr(info, "creation_date", None)
                if raw_date is None and hasattr(info, "get"):
                    raw_date = info.get("/CreationDate")

                if isinstance(raw_date, datetime):
                    authored_at: datetime | None = raw_date
                elif isinstance(raw_date, str):
                    authored_at = _parse_pdf_date(raw_date)
                else:
                    authored_at = None

                return {"author": author, "doc_title": title, "authored_at": authored_at}
            except Exception as e:
                logger.debug("PDF metadata extraction failed for %s: %s", file_path, e)
                return {}

        return await asyncio.to_thread(_extract)
