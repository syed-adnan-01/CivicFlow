"""
Script: seed_knowledge_sources.py

Seeds the database with verified demo/test knowledge sources and indexes them into ChromaDB.
Used to bootstrap local development and demo environments.
"""

import json
import os
import sys
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge_document import VerificationStatus
from app.services.rag.chunker import GeneratedChunk
from app.services.rag.vector_store import VectorStore


def main():
    print("Seeding demo knowledge sources...")

    # Ensure tables exist (especially in local SQLite)
    Base.metadata.create_all(bind=engine)

    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "fixtures",
        "verified_sources",
        "synthetic_test_source.json",
    )

    if not os.path.exists(fixture_path):
        print(f"Fixture not found at {fixture_path}")
        return

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    vector_store = VectorStore()

    try:
        doc_id = UUID(data["id"])
        existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

        if existing:
            print(f"Source '{existing.title}' already exists in database. Updating...")
            doc = existing
        else:
            doc = KnowledgeDocument(
                id=doc_id,
                title=data["title"],
                authority=data["authority"],
                source_url=data["source_url"],
                service_scope=data["service_scope"],
                verification_status=data["verification_status"],
                active=data["active"],
                content_hash=data.get("content_hash"),
                version=1,
            )
            db.add(doc)
            db.commit()

        # Delete existing chunks
        db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_document_id == doc_id).delete()
        db.commit()

        # Add chunks
        chunks_to_index = []
        for c in data.get("chunks", []):
            chunk_index = c["chunk_index"]
            chunk_id = f"{doc_id}_chunk_{chunk_index}"
            chunk_text = c["chunk_text"]

            chunk_obj = KnowledgeChunk(
                knowledge_document_id=doc_id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                page_number=c.get("page_number", 1),
                section_heading=c.get("section_heading", ""),
                content_hash="synthetic_hash",
                embedding_model="mock-synthetic",
                active=True,
            )
            db.add(chunk_obj)

            metadata = {
                "knowledge_document_id": str(doc_id),
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "page_title": doc.title,
                "canonical_url": doc.source_url,
                "authority": doc.authority,
                "service_scope": doc.service_scope,
                "verification_status": doc.verification_status,
                "active": doc.active,
                "retrieved_at": "2026-10-30T00:00:00Z",
                "last_checked_at": "2026-10-30T00:00:00Z",
                "content_hash": "synthetic_hash",
                "page_number": c.get("page_number", 1),
                "section_heading": c.get("section_heading", ""),
            }

            chunks_to_index.append(
                GeneratedChunk(
                    chunk_id=chunk_id,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    page_number=c.get("page_number", 1),
                    section_heading=c.get("section_heading", ""),
                    content_hash="synthetic_hash",
                    metadata=metadata,
                )
            )

        db.commit()

        # Index into ChromaDB
        mock_embeddings = [[0.1] * 768 for _ in chunks_to_index]
        vector_store.upsert_chunks(chunks_to_index, mock_embeddings)

        print(f"Successfully seeded '{doc.title}' with {len(chunks_to_index)} chunks.")

    finally:
        db.close()


if __name__ == "__main__":
    main()

