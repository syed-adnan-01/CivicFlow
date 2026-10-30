"""
Text chunking engine for RAG source documents.
Splits text along paragraph and section boundaries with controlled overlap (400-800 tokens).
Preserves structural headings, page numbers, and full citation metadata on every chunk.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class GeneratedChunk:
    chunk_id: str
    chunk_index: int
    chunk_text: str
    page_number: Optional[int]
    section_heading: Optional[str]
    content_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Chunks document text into citeable, context-preserving segments.
    """

    # Rough approximation: 1 token ~ 4 characters.
    # 400–800 tokens -> ~1600–3200 characters.
    # 80 tokens overlap -> ~320 characters.
    DEFAULT_MIN_CHARS = 800
    DEFAULT_MAX_CHARS = 2400
    DEFAULT_OVERLAP_CHARS = 300

    def __init__(
        self,
        min_chars: int = DEFAULT_MIN_CHARS,
        max_chars: int = DEFAULT_MAX_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    ) -> None:
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_document(
        self,
        document_id: UUID,
        text: str,
        page_title: str,
        source_url: str,
        authority: str,
        service_scope: str,
        verification_status: str,
        retrieved_at: str,
        last_checked_at: Optional[str] = None,
        effective_date: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List[GeneratedChunk]:
        """
        Splits text into chunks and attaches required Section 7.7 ChromaDB metadata.
        """
        if not text or not text.strip():
            return []

        # Detect paragraph and heading boundaries
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        raw_chunks: List[Tuple[str, Optional[str]]] = []
        current_paragraphs: List[str] = []
        current_heading: Optional[str] = None
        current_len = 0

        heading_pattern = re.compile(r"^(?:#{1,4}\s+|[0-9]+\.\s+|[A-Z\s]{4,}:)")

        for para in paragraphs:
            is_heading = bool(heading_pattern.match(para) and len(para) < 120)
            if is_heading:
                current_heading = para.lstrip("#").strip()

            para_len = len(para)
            should_split_heading = is_heading and current_len >= self.min_chars
            should_split_size = (current_len + para_len > self.max_chars and current_len >= self.min_chars)

            if (should_split_heading or should_split_size) and current_paragraphs:
                chunk_body = "\n\n".join(current_paragraphs)
                raw_chunks.append((chunk_body, current_heading))

                # Handle overlap: retain last paragraph if it fits within overlap window and is not a heading
                overlap_text = current_paragraphs[-1] if current_paragraphs else ""
                if len(overlap_text) <= self.overlap_chars and not heading_pattern.match(overlap_text):
                    current_paragraphs = [overlap_text, para]
                    current_len = len(overlap_text) + para_len
                else:
                    current_paragraphs = [para]
                    current_len = para_len
            else:
                current_paragraphs.append(para)
                current_len += para_len

        if current_paragraphs:
            chunk_body = "\n\n".join(current_paragraphs)
            raw_chunks.append((chunk_body, current_heading))

        # Build structured GeneratedChunk objects
        generated: List[GeneratedChunk] = []
        for idx, (body, heading) in enumerate(raw_chunks):
            chunk_id = f"{document_id}_chunk_{idx}"
            chunk_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

            # Metadata required by QueueLess 2.3 Section 7.7
            metadata: Dict[str, Any] = {
                "knowledge_document_id": str(document_id),
                "chunk_id": chunk_id,
                "chunk_index": idx,
                "page_title": page_title,
                "canonical_url": source_url,
                "authority": authority,
                "service_scope": service_scope,
                "verification_status": verification_status,
                "active": verification_status == "VERIFIED",
                "retrieved_at": retrieved_at,
                "last_checked_at": last_checked_at or "",
                "effective_date": effective_date or "",
                "content_hash": chunk_hash,
                "page_number": page_number if page_number is not None else -1,
                "section_heading": heading or "",
            }

            generated.append(
                GeneratedChunk(
                    chunk_id=chunk_id,
                    chunk_index=idx,
                    chunk_text=body,
                    page_number=page_number,
                    section_heading=heading,
                    content_hash=chunk_hash,
                    metadata=metadata,
                )
            )

        return generated

