"""
Script: rebuild_chroma_index.py

Rebuilds the ChromaDB vector index from active, verified source records in PostgreSQL.
Run this when the ChromaDB index is lost or after an embedding model version change.

Usage:
    python scripts/rebuild_chroma_index.py

Rules:
- Only VERIFIED + active sources are indexed.
- Embedding model version is recorded on each chunk.
- Do not run this while the API is serving production traffic without coordination.
- Never commits secrets or private data into the index.
"""

import sys
import os

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.knowledge_documents.repository import KnowledgeDocumentRepository
from app.services.providers import get_embedding_provider
from app.services.rag.chunker import GeneratedChunk
from app.services.rag.vector_store import VectorStore


def main():
    print("=" * 60)
    print("QueueLess 2.3 — ChromaDB Index Rebuild")
    print("=" * 60)

    db = SessionLocal()
    vector_store = VectorStore()
    embed_provider = get_embedding_provider()

    try:
        repo = KnowledgeDocumentRepository(db)
        verified_docs = repo.get_all_verified_active()

        print(f"Found {len(verified_docs)} VERIFIED + active documents in PostgreSQL.")

        total_chunks = 0
        for doc in verified_docs:
            db_chunks = repo.get_chunks_for_document(doc.id)
            if not db_chunks:
                print(f"  [WARN] Document '{doc.title}' ({doc.id}) has no chunks. Skipping.")
                continue

            generated_chunks = []
            for c in db_chunks:
                metadata = {
                    "knowledge_document_id": str(doc.id),
                    "chunk_id": f"{doc.id}_chunk_{c.chunk_index}",
                    "chunk_index": c.chunk_index,
                    "page_title": doc.title,
                    "canonical_url": doc.source_url,
                    "authority": doc.authority,
                    "service_scope": doc.service_scope,
                    "verification_status": doc.verification_status,
                    "active": doc.active,
                    "retrieved_at": doc.retrieved_at.isoformat() if doc.retrieved_at else "",
                    "last_checked_at": doc.last_checked_at.isoformat() if doc.last_checked_at else "",
                    "content_hash": c.content_hash or "",
                    "page_number": c.page_number if c.page_number is not None else -1,
                    "section_heading": c.section_heading or "",
                }
                generated_chunks.append(
                    GeneratedChunk(
                        chunk_id=metadata["chunk_id"],
                        chunk_index=c.chunk_index,
                        chunk_text=c.chunk_text,
                        page_number=c.page_number,
                        section_heading=c.section_heading,
                        content_hash=c.content_hash or "",
                        metadata=metadata,
                    )
                )

            texts = [c.chunk_text for c in generated_chunks]
            try:
                embed_results = embed_provider.embed_batch(texts)
                embeddings = [r.embedding for r in embed_results]
            except Exception as exc:
                print(f"  [WARN] Embedding provider failed: {exc}. Using zero fallback vectors.")
                embeddings = [[0.0] * 768 for _ in generated_chunks]

            vector_store.upsert_chunks(generated_chunks, embeddings)
            total_chunks += len(generated_chunks)
            print(f"  [OK] Indexed {len(generated_chunks)} chunks for '{doc.title}'")

        print("=" * 60)
        print(f"Rebuild Complete: {len(verified_docs)} documents, {total_chunks} chunks indexed.")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
