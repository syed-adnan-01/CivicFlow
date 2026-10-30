"""
Script: ingest_source.py

CLI utility to ingest a single official source document by URL or local file path.

Usage:
    python scripts/ingest_source.py --id <UUID> [--file <path>]
"""

import argparse
import sys
import os
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.knowledge_documents.service import KnowledgeDocumentService


def main():
    parser = argparse.ArgumentParser(description="Ingest a verified source document into ChromaDB.")
    parser.add_argument("--id", required=True, help="UUID of the knowledge_document in database")
    parser.add_argument("--file", required=False, help="Optional local snapshot file path")

    args = parser.parse_args()

    try:
        doc_id = UUID(args.id)
    except ValueError:
        print(f"Error: Invalid UUID '{args.id}'")
        sys.exit(1)

    db = SessionLocal()
    service = KnowledgeDocumentService(db)

    try:
        print(f"Ingesting document {doc_id}...")
        chunk_count = service.ingest_source(doc_id, local_file_path=args.file)
        print(f"Success: Indexed {chunk_count} chunks into vector store.")
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

