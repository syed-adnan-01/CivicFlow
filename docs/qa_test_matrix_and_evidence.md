# QueueLess 2.3 — QA Test Matrix & Verification Evidence
## Quality Assurance Coordination & Defect Report

This document records the quality assurance results across the test pyramid, positive and negative test cases, and core independence verifications required by **Member 4** (Section 12 of the Implementation Plan).

---

## 1. Test Execution Summary

* **Total Automated Tests Executed:** 92
* **Passing Tests:** 92
* **Failed Tests:** 0
* **Skipped Tests:** 0
* **Execution Time:** ~2.5 seconds

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 92 items

backend/tests/integration/test_assistant_api.py .........               [ 9 passed ]
backend/tests/integration/test_document_pipeline.py ...........         [ 11 passed ]
backend/tests/integration/test_private_file_access.py ....              [ 4 passed ]
backend/tests/unit/test_answer_generator.py .....                      [ 5 passed ]
backend/tests/unit/test_assistant_api.py ...                           [ 3 passed ]
backend/tests/unit/test_checklist_matching.py ....                     [ 4 passed ]
backend/tests/unit/test_chunking.py ...                                [ 3 passed ]
backend/tests/unit/test_citations.py ......                            [ 6 passed ]
backend/tests/unit/test_documents_api.py ....                          [ 4 passed ]
backend/tests/unit/test_file_validation.py .............               [ 13 passed ]
backend/tests/unit/test_ocr_normalization.py .....                     [ 5 passed ]
backend/tests/unit/test_refusal.py ..........                          [ 10 passed ]
backend/tests/unit/test_retrieval.py ....                              [ 4 passed ]
backend/tests/unit/test_source_governance.py ...........               [ 11 passed ]
======================= 92 passed in 2.53s =======================
```

---

## 2. QA Test Matrix Verification (Section 12.2)

| Area | Positive Test Verified | Negative / Failure Guard Verified | Test Suite |
|---|---|---|---|
| **1. Source Governance** | Verified official source indexed and retrievable. | Unverified, stale, or inactive sources excluded from retrieval. | `test_source_governance.py` |
| **2. RAG Citations** | Clickable chunk citations mapped to verified database sources. | Model-hallucinated URLs and invented chunk IDs stripped and rejected. | `test_citations.py` |
| **3. Service Scope** | Query matching service returns authorized citations. | PSI Training notice blocked from answering general Income Certificate queries. | `test_retrieval.py` |
| **4. Refusal Policy** | Supported civic queries answered with verified sources. | Legal eligibility questions ("Will I be approved?") and out-of-scope queries refused. | `test_refusal.py` |
| **5. Multilingual** | Prompts instruct native responses in English (`en`), Kannada (`kn`), and Hindi (`hi`). | Unsupported language queries disclose limitations without fabricating translation. | `test_answer_generator.py` |
| **6. Prompt Injection** | Legitimate instructions processed normally. | Malicious overrides ("ignore previous instructions") detected and rejected. | `test_answer_generator.py` |
| **7. Upload Validation** | Valid PDF, JPEG, and PNG files accepted (202 Accepted). | MIME spoofing (HTML as JPG), oversized files (>10MB), and corrupt binaries rejected (400). | `test_file_validation.py` |
| **8. Data Privacy** | Citizen can view and delete their own documents. | Citizen A receives 403 Forbidden when attempting to view or delete Citizen B's files. | `test_document_pipeline.py` |
| **9. OCR Extraction** | Clean scans extract text, calculate confidence bands (`HIGH`/`MEDIUM`/`LOW`). | Blurry or ambiguous scans marked `NEEDS_REVIEW` without blocking the citizen. | `test_ocr_normalization.py` |
| **10. Checklist Matching** | Detected category matched to versioned checklist as `PRESENT_CANDIDATE`. | Missing checklist items explicitly identified; manual confirmation supported. | `test_checklist_matching.py` |
| **11. Provider Outages** | System operates normally when Groq/Gemini are available. | Groq quota limit switches automatically to Gemini; total outage returns `TEMPORARILY_UNAVAILABLE`. | `test_assistant_api.py` |
| **12. Core Independence** | Citizen can complete booking and check-in without AI. | OCR or LLM failure NEVER blocks appointment booking, slot reservation, or queue token issuance. | `test_document_pipeline.py` |

---

## 3. Defect Prevention & Resolution Log

* **P0 Blocker: Foreign Key / Model Dependency:** Fixed circular mapper dependency on uninstantiated Member 1 `users` and `service_checklist_versions` tables by using decoupled UUID columns with cross-platform SQLite/Postgres support.
* **P0 Blocker: Cross-Citizen Document Exposure:** Verified strict ownership checks (`doc.citizen_id == current_user.id`), guaranteeing a 403 Forbidden response on unauthorized document access.
* **P1 Major: Hallucinated URLs:** Implemented canonical URL resolution inside `CitationValidator`, replacing model-generated links with official URLs stored in PostgreSQL.
* **P1 Major: Scope Bleed Safeguard:** Enforced service scope boundary checks inside `SourceGovernance`, preventing notices intended for one process from supporting unrelated certificates.

