# QueueLess 2.3 — Member 4 to Member 3 Frontend Integration Contract
## AI Assistant & Document Readiness Integration Specification

This document provides the frontend development contract for **Member 3** (React + Vite + Tailwind CSS) to integrate the RAG Service Assistant and the OCR Document Readiness pipeline.

---

## 1. Authentication & API Base Configuration

* **Base URL:** `/api/v1`
* **Authorization Header:** `Authorization: Bearer <FIREBASE_ID_TOKEN>`
* All citizen-specific routes require the user to be authenticated with Firebase Auth.

---

## 2. RAG Service Assistant API

### 2.1 Chat Endpoint
`POST /api/v1/assistant/chat`

#### Request Payload (`AssistantChatRequest`)
```typescript
interface AssistantChatRequest {
  message: string;          // Required. 1-2000 characters.
  service_id?: string;     // Optional UUID. Scopes retrieval to a specific civic service.
  language?: string;       // Optional. Default 'en'. Supported: 'en' | 'kn' | 'hi'.
  conversation_id?: string;// Optional UUID. Session grouping identifier.
}
```

#### Response Payload (`AssistantChatResponse`)
```typescript
interface CitationSchema {
  chunk_id: string;        // Unique identifier of the verified chunk.
  title: string;           // Official source title.
  authority: string;       // Issuing government authority (e.g. "Revenue Department").
  url: string;             // Canonical verified URL (e.g. "https://nadakacheri.karnataka.gov.in").
  page_number?: number;    // Page number if source is a PDF.
  retrieved_at: string;    // ISO timestamp.
  last_checked_at: string; // ISO timestamp.
}

interface AssistantChatResponse {
  answer: string;          // Grounded answer text containing citation badges like [1], [2].
  status: "ANSWERED" | "INSUFFICIENT_EVIDENCE" | "SOURCE_CONFLICT" | "TEMPORARILY_UNAVAILABLE" | "INVALID_REQUEST";
  language: string;        // "en" | "kn" | "hi"
  citations: CitationSchema[];
  limitations: string[];   // Notice scope and disclaimer notes.
  request_id: string;      // UUID for tracing and audit.
}
```

#### UI Behavior Matrix for Assistant Status
| Status | Meaning | Recommended UI Rendering |
|---|---|---|
| `ANSWERED` | Grounded answer with active verified sources | Render answer with clickable `[1]`, `[2]` citation pills that expand source title, authority, and official link. |
| `INSUFFICIENT_EVIDENCE` | Official corpus lacks verified data to answer | Display message with fallback badge: *"Official portals or office counters should be consulted for statutory verification."* |
| `SOURCE_CONFLICT` | Conflicting rules found across official notices | Display warning alert advising citizen to consult the issuing authority directly. |
| `TEMPORARILY_UNAVAILABLE` | LLM or ChromaDB temporary failure | Render temporary offline banner: *"AI assistant temporarily unavailable. Standard checklists and booking remain active."* |

### 2.2 Health Check Endpoint
`GET /api/v1/assistant/health` (No authentication required)

#### Response Payload (`AssistantHealthResponse`)
```typescript
interface AssistantHealthResponse {
  llm_configured: boolean;
  embedding_configured: boolean;
  vector_store_reachable: boolean;
  status: "healthy" | "degraded" | "unavailable";
}
```

---

## 3. Document Readiness & OCR Pipeline API

### 3.1 Upload Document
`POST /api/v1/documents/upload`

* **Content-Type:** `multipart/form-data`
* **Form Fields:**
  * `file`: Binary file (`.pdf`, `.jpg`, `.jpeg`, `.png`). Max 10 MB.
  * `service_id`: Optional UUID.
  * `checklist_version_id`: Optional UUID.

#### Response Payload (`DocumentUploadResponse`)
```typescript
interface DocumentUploadResponse {
  document_id: string;     // UUID of the created citizen document.
  processing_status: "RECEIVED" | "VALIDATING" | "OCR_PENDING" | "OCR_COMPLETE" | "VALIDATION_FAILED" | "OCR_FAILED";
  file_name: string;
  message: string;
}
```

### 3.2 List Citizen Documents
`GET /api/v1/documents`

#### Response Payload (`CitizenDocumentList`)
```typescript
interface CitizenDocumentRead {
  document_id: string;
  file_name: string;
  service_id?: string;
  processing_status: string;
  created_at: string;
}

interface CitizenDocumentList {
  items: CitizenDocumentRead[];
  total: number;
}
```

### 3.3 Fetch Document Readiness Report
`GET /api/v1/documents/{document_id}/check-result`

#### Response Payload (`DocumentCheckResult`)
```typescript
interface ChecklistItemRead {
  checklist_item_id: string;
  label: string;            // e.g. "Identity Proof (Aadhaar Card)"
  result: "PRESENT_CANDIDATE" | "MISSING" | "NEEDS_REVIEW" | "REPLACEMENT_REQUESTED" | "USER_CONFIRMED";
  confidence_band?: "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
  message?: string;
}

interface DocumentCheckResult {
  document_id: string;
  processing_status: string;
  checklist_version_id?: string;
  items: ChecklistItemRead[];
  overall_status: "READY_FOR_REVIEW" | "NEEDS_REVIEW" | "UNAVAILABLE";
  disclaimer: string;      // Non-negotiable citizen disclaimer.
}
```

### 3.4 Delete Citizen Document
`DELETE /api/v1/documents/{document_id}`

#### Response Payload (`DocumentDeleteResponse`)
```typescript
interface DocumentDeleteResponse {
  document_id: string;
  status: "DELETED";
  message: string;
}
```

---

## 4. Non-Negotiable UI Disclaimers & Core Safeguards

1. **Assistant Disclaimer:**  
   QueueLess complements physical office visits. Display the footer note:  
   *"QueueLess provides procedural guidance and does not submit, decide, or approve government applications."*
2. **OCR Readiness Disclaimer:**  
   Always display the disclaimer returned in `DocumentCheckResult.disclaimer`:  
   *"Preliminary readiness check only. Confirm current requirements on the official service portal or with the relevant office."*
3. **Core Workflow Independence:**  
   Never block appointment booking or queue token creation if OCR extraction fails or returns `NEEDS_REVIEW`. Allow the citizen to proceed manually.

