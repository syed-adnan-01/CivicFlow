from app.models.user import User
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.idempotency_key import IdempotencyKey
from app.models.audit_event import AuditEvent
from app.models.counter import Counter
from app.models.queue_token import QueueToken, TokenStatus, TokenSource
from app.models.queue_event import QueueEvent, EventType

# Member 4 — RAG knowledge and document models (imported lazily to avoid
# hard dependency on SQLite-only dev setups).
try:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.knowledge_chunk import KnowledgeChunk
    from app.models.citizen_document import CitizenDocument
    from app.models.document_processing_job import DocumentProcessingJob
    from app.models.document_check import DocumentCheck
    from app.models.document_check_item import DocumentCheckItem
except ImportError:
    pass

__all__ = [
    "User",
    "Office",
    "Service",
    "QueuePolicy",
    "AppointmentSlot",
    "Appointment",
    "CheckinReference",
    "IdempotencyKey",
    "AuditEvent",
    "Counter",
    "QueueToken",
    "TokenStatus",
    "TokenSource",
    "QueueEvent",
    "EventType",
    # Member 4
    "KnowledgeDocument",
    "KnowledgeChunk",
    "CitizenDocument",
    "DocumentProcessingJob",
    "DocumentCheck",
    "DocumentCheckItem",
]
