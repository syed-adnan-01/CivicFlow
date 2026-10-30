from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.integrations.firebase_admin import init_firebase_admin

# Member 1 – Auth, catalogue, appointments
from app.modules.auth.router import router as auth_router
from app.modules.catalogue.router import router as catalogue_router
from app.modules.appointments.router import router as appointments_router
try:
    from app.modules.checkin.router import router as checkin_router
except ImportError:
    from backend.app.modules.checkin.router import router as checkin_router

# Member 4 – RAG Assistant, Documents, Knowledge Documents
try:
    from app.modules.assistant.router import router as assistant_router
    from app.modules.documents.router import router as documents_router
    from app.modules.knowledge_documents.router import router as knowledge_docs_router
    _m4_routers_available = True
except ImportError:
    _m4_routers_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    init_firebase_admin()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="QueueLess 2.3 API",
    description="QueueLess 2.3 Citizen Appointment, Slot Capacity, Office Queue, and AI-Assisted Document Readiness Backend",
    version="2.3.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production via settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
# Catch-all exception handler in non-debug mode
if settings.APP_ENV == "production":
    app.add_exception_handler(Exception, general_exception_handler)

# Member 1 & 2 Routers
app.include_router(auth_router)
app.include_router(catalogue_router)
app.include_router(appointments_router)
app.include_router(checkin_router, prefix="/api/v1")

# Member 4 Routers (RAG Assistant + Document Readiness)
if _m4_routers_available:
    app.include_router(assistant_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(knowledge_docs_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "version": "2.3.0",
    }
