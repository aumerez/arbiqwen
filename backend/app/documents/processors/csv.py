"""CSV document processor.

CSV is tabular, so it is ingested in `stub` mode — a discovery summary (column
headers + row count) is indexed for retrieval rather than embedding every row.
`extract_text` exists for the generic processor contract / fallback.
"""

import asyncio
import csv as _csv
import logging

logger = logging.getLogger(__name__)

# Cap rows scanned for the stub so a huge CSV doesn't stall ingestion.
_STUB_SCAN_ROWS = 5000


class CSVProcessor:
    """Extract a discovery stub (and, as a fallback, text) from a CSV file."""

    async def extract_text(self, file_path: str) -> str:
        """Best-effort full text (tab-joined rows). Tabular files normally use
        `extract_stub` instead; this is the generic-contract fallback."""

        def _extract() -> str:
            parts: list[str] = []
            with open(file_path, encoding="utf-8", errors="replace", newline="") as f:
                for row in _csv.reader(f):
                    line = "\t".join(row)
                    if line.strip():
                        parts.append(line)
            return "\n".join(parts)

        return await asyncio.to_thread(_extract)

    async def extract_stub(self, file_path: str) -> dict:
        """Discovery stub: column headers + approximate row count."""

        def _extract() -> dict:
            try:
                with open(file_path, encoding="utf-8", errors="replace", newline="") as f:
                    reader = _csv.reader(f)
                    headers = next(reader, [])
                    headers = [h.strip() for h in headers if h.strip()]
                    row_count = 0
                    for row_count, _ in enumerate(reader, start=1):
                        if row_count >= _STUB_SCAN_ROWS:
                            break
                    return {
                        "sheets": [{"name": "csv", "columns": headers, "row_count": row_count}],
                        "summary": f"CSV with {len(headers)} column(s): {', '.join(headers)}. ~{row_count} data row(s).",
                    }
            except Exception as e:  # noqa: BLE001 — stub extraction is best-effort
                logger.debug("CSV stub extraction failed for %s: %s", file_path, e)
                return {"sheets": [], "summary": "CSV file (summary unavailable)"}

        return await asyncio.to_thread(_extract)

    async def extract_metadata(self, file_path: str) -> dict:
        """CSV carries no document properties."""
        return {}
