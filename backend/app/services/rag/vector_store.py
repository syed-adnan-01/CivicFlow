"""
Vector store integration using ChromaDB.
Handles upserting chunks with embeddings, deleting chunks on source deactivation,
and querying with strict active/verified and service-scope metadata filters.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.services.rag.chunker import GeneratedChunk

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised when ChromaDB operations fail."""
    pass


class VectorStore:
    """Manages persistent ChromaDB vector storage for verified source chunks."""

    def __init__(self, persist_directory: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION
        self._client = None
        self._collection = None

    def _get_collection(self):
        """Lazily connects to ChromaDB."""
        if self._collection is not None:
            return self._collection

        try:
            import chromadb  # type: ignore

            self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "QueueLess verified official sources"},
            )
            return self._collection
        except ImportError as exc:
            logger.warning("chromadb not installed — vector store operating in fallback mode.")
            return None
        except Exception as exc:
            logger.error("Failed to connect to ChromaDB at %s: %s", self.persist_directory, exc)
            raise VectorStoreError("Vector store is temporarily unreachable.") from exc

    def upsert_chunks(self, chunks: List[GeneratedChunk], embeddings: List[List[float]]) -> None:
        """
        Upserts document chunks with their precomputed embeddings and metadata.
        """
        if not chunks:
            return

        collection = self._get_collection()
        if collection is None:
            logger.info("Mock ChromaDB: would upsert %d chunks.", len(chunks))
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.chunk_text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("Upserted %d chunks into ChromaDB collection '%s'", len(chunks), self.collection_name)
        except Exception as exc:
            logger.error("ChromaDB upsert failed: %s", exc)
            raise VectorStoreError("Failed to store chunks in vector store.") from exc

    def delete_chunks_by_document(self, document_id: UUID) -> None:
        """
        Removes all chunks belonging to a document (used on deactivation or re-indexing).
        """
        collection = self._get_collection()
        if collection is None:
            return

        try:
            collection.delete(where={"knowledge_document_id": str(document_id)})
            logger.info("Deleted chunks for document %s from ChromaDB.", document_id)
        except Exception as exc:
            logger.error("Failed to delete chunks for document %s: %s", document_id, exc)
            raise VectorStoreError("Failed to remove chunks from vector store.") from exc

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        service_scope: Optional[str] = None,
        only_verified: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for the closest chunks matching query_embedding.
        Enforces verified=True and active=True filters.
        """
        collection = self._get_collection()
        if collection is None:
            return []

        # Build filter conditions
        where_conditions: List[Dict[str, Any]] = []
        if only_verified:
            where_conditions.append({"verification_status": "VERIFIED"})
            where_conditions.append({"active": True})

        if service_scope:
            where_conditions.append({"service_scope": service_scope})

        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}
        else:
            where = None

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            formatted: List[Dict[str, Any]] = []
            if not results or not results.get("ids"):
                return formatted

            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else []
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i in range(len(ids)):
                # ChromaDB distance: cosine distance is 1 - similarity.
                # Convert to rough similarity score: 1.0 - distance
                dist = distances[i] if i < len(distances) else 0.0
                similarity = max(0.0, 1.0 - dist)

                formatted.append({
                    "chunk_id": ids[i],
                    "text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "score": similarity,
                })

            return formatted

        except Exception as exc:
            logger.error("ChromaDB query failed: %s", exc)
            raise VectorStoreError("Vector store query failed.") from exc

    def is_healthy(self) -> bool:
        """Returns True if the vector store is reachable."""
        try:
            collection = self._get_collection()
            return collection is not None
        except Exception:
            return False

