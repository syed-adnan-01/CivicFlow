"""
Demo Seeding Script: seed_demo_corpus.py
Seeds clean, verified official knowledge sources into PostgreSQL and indexes them into ChromaDB.
Enforces QueueLess 2.3 Section 7.2, 7.3 & Phase 6 (Day 19).
"""

from datetime import datetime, timezone
import json
import os
import sys
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.providers import get_embedding_provider
from app.services.rag.chunker import GeneratedChunk
from app.services.rag.vector_store import VectorStore


def seed_demo_sources():
    print("=" * 60)
    print("QueueLess 2.3 — Seeding Official Demo Knowledge Corpus")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)

    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "fixtures",
        "verified_sources",
        "demo_official_sources.json",
    )

    if not os.path.exists(fixture_path):
        print(f"Error: Fixture file not found at {fixture_path}")
        return

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    vector_store = VectorStore()
    embedding_provider = get_embedding_provider()

    try:
        sources = data.get("sources", [])
        total_indexed = 0
        now = datetime.now(timezone.utc)

        for s in sources:
            doc_id = UUID(s["id"])
            existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

            if existing:
                doc = existing
                doc.title = s["title"]
                doc.authority = s["authority"]
                doc.source_url = s["source_url"]
                doc.service_scope = s["service_scope"]
                doc.verification_status = s["verification_status"]
                doc.active = s["active"]
                doc.review_notes = s.get("review_notes", "")
                doc.last_checked_at = now
            else:
                doc = KnowledgeDocument(
                    id=doc_id,
                    title=s["title"],
                    authority=s["authority"],
                    source_url=s["source_url"],
                    service_scope=s["service_scope"],
                    verification_status=s["verification_status"],
                    active=s["active"],
                    review_notes=s.get("review_notes", ""),
                    retrieved_at=now,
                    last_checked_at=now,
                    version=1,
                )
                db.add(doc)

            db.commit()

            # Clean previous chunks
            db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_document_id == doc_id).delete()
            db.commit()

            chunks_data = s.get("chunks", [])
            chunks_to_index = []

            for c in chunks_data:
                chunk_idx = c["chunk_index"]
                chunk_id = f"{doc_id}_chunk_{chunk_idx}"
                chunk_text = c["chunk_text"]

                chunk_obj = KnowledgeChunk(
                    knowledge_document_id=doc_id,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text,
                    page_number=c.get("page_number", 1),
                    section_heading=c.get("section_heading", ""),
                    embedding_model="models/text-embedding-004",
                    active=doc.active,
                )
                db.add(chunk_obj)

                if doc.active and doc.verification_status == "VERIFIED":
                    metadata = {
                        "knowledge_document_id": str(doc_id),
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_idx,
                        "page_title": doc.title,
                        "canonical_url": doc.source_url,
                        "authority": doc.authority,
                        "service_scope": doc.service_scope,
                        "verification_status": doc.verification_status,
                        "active": True,
                        "retrieved_at": "2026-10-30T00:00:00Z",
                        "last_checked_at": "2026-10-30T00:00:00Z",
                        "page_number": c.get("page_number", 1),
                        "section_heading": c.get("section_heading", ""),
                    }
                    chunks_to_index.append(
                        GeneratedChunk(
                            chunk_id=chunk_id,
                            chunk_index=chunk_idx,
                            chunk_text=chunk_text,
                            page_number=c.get("page_number", 1),
                            section_heading=c.get("section_heading", ""),
                            content_hash="sha256_demo",
                            metadata=metadata,
                        )
                    )

            db.commit()

            # Embed and upsert into ChromaDB only for VERIFIED + active sources
            if chunks_to_index:
                embeddings = []
                for chk in chunks_to_index:
                    try:
                        emb = embedding_provider.embed(chk.chunk_text)
                        embeddings.append(emb.embedding)
                    except Exception as exc:
                        print(f"Warning: Remote embedding failed ({exc}); using fallback vector.")
                        embeddings.append([0.1] * 768)

                vector_store.upsert_chunks(chunks_to_index, embeddings)
                total_indexed += len(chunks_to_index)
                print(f"[VERIFIED & INDEXED] {doc.title} -> {len(chunks_to_index)} chunks in ChromaDB")
            else:
                print(f"[EXCLUDED FROM RETRIEVAL] {doc.title} (Status: {doc.verification_status}, Active: {doc.active})")

        print("=" * 60)
        print(f"Seeding Complete! Total active verified chunks indexed in ChromaDB: {total_indexed}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_sources()
