"""Document processor registry to select the right processor for a mimetype."""

from app.documents.models import DocumentIndexMode

from .csv import CSVProcessor
from .docx import DOCXProcessor
from .pdf import PDFProcessor
from .pptx import PPTXProcessor
from .txt import TXTProcessor
from .xlsx import XLSXProcessor

# Maps MIME type → (processor class, extension, friendly label)
_SUPPORTED_TYPES: dict[str, tuple[type, str, str]] = {
    "application/pdf": (PDFProcessor, ".pdf", "PDF"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (DOCXProcessor, ".docx", "Word"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (PPTXProcessor, ".pptx", "PowerPoint"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (XLSXProcessor, ".xlsx", "Excel"),
    "text/csv": (CSVProcessor, ".csv", "CSV"),
    "text/plain": (TXTProcessor, ".txt", "Text"),
    "text/markdown": (TXTProcessor, ".md", "Markdown"),
}

# The single mimetype → handling-mode decision, made once at ingest time and
# then persisted on documents.index_mode. Tabular files (xlsx/csv) get a
# discovery stub; everything else is full RAG.
_TABULAR_MIMETYPES: frozenset[str] = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "text/csv",
    }
)


def index_mode_for_mimetype(mimetype: str) -> DocumentIndexMode:
    """Decide the ingestion handling mode for a freshly-uploaded document.

    Tabular → `stub`; everything else supported → `full`. (`none` is reserved
    for external/integration-backed datasets set on their own ingestion path.)
    """
    if mimetype in _TABULAR_MIMETYPES:
        return DocumentIndexMode.stub
    return DocumentIndexMode.full


class DocumentProcessorRegistry:
    """Registry for document processors by mimetype."""

    def __init__(self):
        self._processors = _SUPPORTED_TYPES

    def get_processor(self, mimetype: str):
        """Get the processor instance for a given mimetype."""
        entry = self._processors.get(mimetype)
        if entry is None:
            raise ValueError(f"Unsupported mimetype: {mimetype}")
        processor_class = entry[0]
        return processor_class()

    def register(self, mimetype: str, processor_class: type, extension: str = "", label: str = ""):
        """Register a custom processor for a mimetype."""
        self._processors[mimetype] = (processor_class, extension, label)

    @staticmethod
    def get_supported_types() -> list[dict[str, str]]:
        """Return the list of supported MIME types with metadata."""
        return [
            {"mimetype": mime, "extension": ext, "label": label} for mime, (_, ext, label) in _SUPPORTED_TYPES.items()
        ]

    @staticmethod
    def get_allowed_mimetypes() -> list[str]:
        """Return the list of allowed MIME type strings (for upload validation)."""
        return list(_SUPPORTED_TYPES.keys())

    @staticmethod
    def resolve_mimetype(filename: str | None, content_type: str | None) -> str | None:
        """Resolve a trusted mimetype for an upload.

        OS / browser multipart APIs send inconsistent content_type values for
        the same file (e.g. .md as "", "text/plain", or "text/markdown"; .docx
        sometimes as "application/octet-stream"). The user-chosen extension is
        more reliable, so resolve by extension first and fall back to the
        content_type allowlist only when the extension is unknown. Returns None
        if neither resolves — the caller should reject the upload.
        """
        if filename and "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()
            for mime, (_, registered_ext, _) in _SUPPORTED_TYPES.items():
                if ext == registered_ext:
                    return mime
        if content_type and content_type in _SUPPORTED_TYPES:
            return content_type
        return None
