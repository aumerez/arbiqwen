"""Plain text processor."""

import asyncio


class TXTProcessor:
    """Extract text from plain text files."""

    async def extract_text(self, file_path: str) -> str:
        """Read text from a .txt file."""

        def _read():
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def extract_metadata(self, file_path: str) -> dict:
        """Plain text has no embedded metadata."""
        return {}
