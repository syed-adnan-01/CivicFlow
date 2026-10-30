# QueueLess 2.3 — Member 4 to Member 1 Backend Integration Contract
## Database Models, Shared Authentication & Storage Boundaries

This document defines the backend integration boundaries between **Member 4** (RAG, OCR & AI Coordination) and **Member 1** (Core FastAPI backend, Firebase Admin Auth, and Database Foundations).

---

## 1. Database Table Alignments & Foreign Keys

Member 4 has created models for AI knowledge documents, OCR jobs, and document readiness checks. To prevent duplicate migration conflicts, table ownership is divided as follows:

| Table | Purpose | Defined In | Foreign Key Dependencies |
|---|---|---|---|
| `knowledge_documents` | Curated RAG source register | `app/models/knowledge_document.py` | `reviewed_by` (UUID, optional link to `users.id`) |
| `knowledge_chunks` | Chunk-level text & citation metadata | `app/models/knowledge_chunk.py` | `knowledge_document_id` -> `knowledge_documents.id` |
| `citizen_documents` | Uploaded file records & processing state | `app/models/citizen_document.py` | `citizen_id` (UUID, link to `users.id`), `service_id` (UUID, link to `services.id`) |
| `document_processing_jobs` | OCR execution tracking | `app/models/document_processing_job.py` | `citizen_document_id` -> `citizen_documents.id` |
| `document_checks` | Top-level readiness comparison | `app/models/document_check.py` | `citizen_document_id` -> `citizen_documents.id`, `checklist_version_id` (UUID, link to `service_checklist_versions.id`) |
| `document_check_items` | Item-level matching results | `app/models/document_check_item.py` | `check_id` -> `document_checks.id`, `checklist_item_id` (UUID) |

### Key Shared Ownership Rules
1. **No Duplicate User Table:** Member 4 consumes `users.id` via `citizen_id` and does not define a competing users table.
2. **Authoritative Checklists:** PostgreSQL service checklists owned by Member 1 remain the single authoritative source of truth. Vector store (ChromaDB) stores ONLY verified knowledge excerpts, never checklist rules or citizen data.
3. **Soft Deletion & Cascade:** When a citizen deletes their document, derived check items and storage files are purged per retention policies.

---

## 2. Authentication Dependency Contract

* **Import Path:** `from app.common.dependencies import get_current_user, AuthenticatedUser`
* **Resolved User Object:**
  ```python
  class AuthenticatedUser(BaseModel):
      id: UUID
      firebase_uid: str
      role: str  # "CITIZEN" | "OFFICE_ADMIN"
      is_active: bool
      display_name: Optional[str]
      email: Optional[str]
  ```
* **Authorization Rules:**
  * Citizen endpoints (`/api/v1/documents/*`, `/api/v1/assistant/chat`) allow `CITIZEN` or `OFFICE_ADMIN`.
  * Admin endpoints (`/api/v1/admin/knowledge-documents/*`) strictly require role `OFFICE_ADMIN`.

---

## 3. Storage Interface Boundaries

* **Private Storage Class:** `from app.services.ocr.storage import PrivateStorage`
* **Access Policy:**
  * Files are stored under non-guessable paths (`citizens/{citizen_id}/{document_id}_{hash}.{ext}`).
  * No public buckets or guessable URLs are exposed.
  * Signed tokens expire after a configured duration (default: 3600 seconds).

---

## 4. Coordination with Member 2 (Queue Operations)

* **Zero Queue Payload Bleed:** Uploaded document contents, raw OCR text, and citizen identity numbers are NEVER broadcast over public or counter WebSocket channels.
* **Core Non-Blocking Guarantee:** Appointment check-in and queue token issuance do not depend on OCR success. If OCR fails or is pending, the queue system proceeds with manual document verification at the counter.

