"""
QueueLess 2.3 — FastAPI Application Entrypoint.
Modular monolith backend coordinating citizen visit preparation and physical office queues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.assistant.router import router as assistant_router
from app.modules.documents.router import router as documents_router
from app.modules.knowledge_documents.router import router as knowledge_docs_router

app = FastAPI(
    title="QueueLess 2.3 API",
    description="Citizen visit preparation, appointment booking, and queue coordination layer.",
    version="2.3.0",
)

# CORS configuration for local React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(assistant_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(knowledge_docs_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    """System health check."""
    return {"status": "healthy", "service": "queueless-backend", "version": "2.3.0"}

