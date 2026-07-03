"""Text chunking service for document processing."""

import re


class TextSplitterService:
    """Split text into semantic chunks for embedding."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize text splitter.

        Args:
            chunk_size: Target size of each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks (in characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def split_text(self, text: str) -> list[str]:
        """
        Split text into semantic chunks.

        Uses paragraph boundaries when possible, falls back to sentence boundaries,
        and finally character-based splitting if needed.
        """
        text = text.strip()
        if not text:
            return []

        # Try to split by paragraphs first (double newlines)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if len(paragraphs) <= 1:
            # Fall back to single newlines
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        if len(paragraphs) <= 1:
            # Final fallback: return the whole text as one chunk
            return [text] if len(text) > 0 else []

        chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            # If a single paragraph is larger than chunk_size, split it further.
            if para_len > self.chunk_size * 1.5:
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                for sentence in sentences:
                    if len(sentence) > self.chunk_size:
                        # Split very long sentences into smaller pieces
                        for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                            chunk = sentence[i : i + self.chunk_size]
                            if current_length + len(chunk) > self.chunk_size and current_chunk:
                                chunks.append(" ".join(current_chunk))
                                current_chunk = [chunk]
                                current_length = len(chunk)
                            else:
                                current_chunk.append(chunk)
                                current_length += len(chunk)
                    else:
                        if current_length + len(sentence) > self.chunk_size and current_chunk:
                            chunks.append(" ".join(current_chunk))
                            current_chunk = [sentence]
                            current_length = len(sentence)
                        else:
                            current_chunk.append(sentence)
                            current_length += len(sentence)
            else:
                # Normal-sized paragraph
                if current_length + para_len > self.chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [paragraph]
                    current_length = para_len
                else:
                    current_chunk.append(paragraph)
                    current_length += para_len

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Apply overlap by prepending part of the previous chunk
        if self.chunk_overlap > 0 and len(chunks) > 1:
            result = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap :] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                result.append(overlap_text + chunks[i])
            return result

        return chunks
