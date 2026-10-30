> **AUTHENTICATION DECISION UPDATE (QueueLess 2.3, 30 October 2026)**
>
> **This decision supersedes every earlier reference in this document to QueueLess-managed citizen OTP challenges, custom access-token issuance, custom refresh-token rotation, and the `otp_challenges` (not implemented; superseded by Firebase Authentication) / `refresh_tokens` tables.** QueueLess uses **Firebase Authentication** for citizen identity verification and client session management. FastAPI verifies Firebase ID tokens with the Firebase Admin SDK. PostgreSQL remains the source of truth for QueueLess user profiles, roles, office assignments, appointments, QR references, audit records, and all business data.
>
> - Citizen phone sign-in and SMS OTP verification are performed by the Firebase client SDK. QueueLess does not generate, store, send, or verify citizen OTP codes.
> - The frontend obtains a Firebase ID token and sends it as `Authorization: Bearer <Firebase-ID-token>` to protected REST endpoints.
> - FastAPI verifies the token signature, issuer, audience, expiry, and Firebase project. It then resolves `firebase_uid` to the internal QueueLess user record.
> - Do not trust role, office, or counter values supplied by the browser. Enforce roles and resource scope from PostgreSQL on every protected operation.
> - Do not create a QueueLess refresh-token table or `/auth/refresh` endpoint. The Firebase client SDK manages refresh of its ID token.
> - Keep the QueueLess short-lived, single-use WebSocket-ticket design. Do not put Firebase ID tokens in WebSocket URLs.
> - Firebase Admin credentials must be supplied through secure environment/secret management and must never be committed.
>
> The detailed setup and implementation requirements are in the Firebase Authentication section of the updated Member 1 plan. Any older custom-OTP instructions retained below are historical text and must not be implemented.

# QueueLess 2.3

## Implementation-Ready Technical Specification

**Version:** 2.2\
**Date:** 30 October 2026\
**Status:** Hackathon implementation baseline\
**Product owner:** QueueLess project team

------------------------------------------------------------------------

## 1. Executive summary

QueueLess is a citizen-visit preparation and physical-office queue
coordination layer that works alongside Karnataka's official service
portals. It helps citizens understand a service, prepare a preliminary
document checklist, reserve a visit, check in using a QR reference, and
follow their live queue status. It helps office staff coordinate
counters and understand demand.

QueueLess is **not** a government application-submission or
certificate-approval platform. It does not determine legal eligibility,
authenticate the legal validity of documents, or replace official
portals, officers, or government systems. Unless an authorized
integration is implemented, citizens must use the relevant official
portal or office for the actual application and official status.

The hackathon objective is one reliable, demonstrable journey:

**Citizen signs in → finds a service → checks readiness → books a slot →
checks in → receives a token → officer serves the citizen → citizen sees
live updates → admin sees operational analytics.**

## 2. Product positioning and boundaries

### 2.1 Positioning

QueueLess complements existing government service channels such as Seva
Sindhu, Nadakacheri centres and DigiLocker. Its proposed differentiator
is connecting three stages in one workflow:

1.  **Before the visit:** understandable service guidance and a
    preliminary checklist.
2.  **During the visit:** appointment check-in, token coordination and
    live queue status.
3.  **Office operations:** counter activity and aggregate demand
    information.

This is a product hypothesis to validate through an office pilot, not a
claim that no existing system provides any individual feature.

### 2.2 Scope boundary

QueueLess does not:

-   Submit or approve a certificate application.
-   Decide whether a citizen is legally eligible for a government
    service.
-   Declare that an uploaded document is genuine, legally valid or
    officially accepted.
-   Replace Seva Sindhu, Nadakacheri, DigiLocker or an authorized
    government workflow.
-   Use predictions to cancel, penalize, or deprioritize a citizen.
-   Claim live queue functionality during an office network outage.

### 2.3 MVP tiers

  ---------------------------------------------------------------------------
  Tier                    Included capabilities       Acceptance outcome
  ----------------------- --------------------------- -----------------------
  P0: core journey        Demo phone OTP, service     Full citizen-to-officer
                          catalogue, slots, booking,  journey works in two
                          QR check-in, token          browser sessions
                          creation, officer           
                          call-next/start/complete,   
                          citizen live updates        

  P1: citizen             RAG assistant with          Grounded answer and
  intelligence            citations; OCR-assisted     visible preliminary
                          checklist report with       readiness result
                          manual fallback             

  P1: operational proof   PostgreSQL-based admin      Admin sees bookings,
                          analytics                   walk-ins, waiting
                                                      queue, completed tokens
                                                      and wait metrics

  P2: optional            Email reminders,            Added only after P0/P1
                          transparent wait estimate,  are stable
                          basic eligible-counter      
                          rules                       

  Roadmap only            Voice, no-show ML, advanced Clearly labelled future
                          optimization, multi-office, scope; not represented
                          WhatsApp, waitlists         as implemented
  ---------------------------------------------------------------------------

Everything outside the delivered tier must be labelled as planned,
mocked or unavailable.

## 3. Roles and permissions

Only three roles are in the hackathon MVP.

  -----------------------------------------------------------------------
  Role                                Allowed actions
  ----------------------------------- -----------------------------------
  Citizen                             Browse services, ask assistant,
                                      upload own sample documents, manage
                                      own appointments, view own
                                      QR/token/status

  Officer                             View assigned counter queue,
                                      perform check-in, call next, start
                                      service, place a token on hold,
                                      complete or mark a called token
                                      no-show

  Office admin                        Configure demo services, checklist
                                      versions, slots, counters,
                                      assignments, queue policy and
                                      knowledge sources; view office
                                      analytics
  -----------------------------------------------------------------------

Authorization must be enforced by the backend on every request. Hiding a
button in the frontend is not authorization.

A citizen must never access another citizen's appointments, document
files, OCR results or private profile data. An officer must be
restricted to the assigned office/counter and the minimum citizen data
required for service. Platform administrator and supervisor roles are
future scope.

## 4. Technology architecture

  ----------------------------------------------------------------------------
  Layer                   MVP choice              Notes
  ----------------------- ----------------------- ----------------------------
  Frontend                React + Vite + Tailwind Citizen, officer and admin
                          CSS                     experiences

  Backend                 One FastAPI application Modular monolith; no
                          organized into modules  microservice overhead

  Database                PostgreSQL              Transactions, constraints
                                                  and relational integrity

  Live updates            Native WebSockets       Office/counter/user-scoped
                                                  events

  Authentication          Firebase Phone Auth     Firebase ID tokens are
                                                  verified by FastAPI

  RAG                     Chosen LLM +            Retrieval from curated,
                          embeddings + ChromaDB   verified sources

  OCR                     PaddleOCR or Tesseract, Preliminary extraction only
                          selected after a test   
                          gate                    

  Background work         FastAPI BackgroundTasks Do not rely on in-process
                          for noncritical work    background tasks for durable
                                                  jobs

  File storage            Private persistent      Local private storage
                          object storage          acceptable for local demo

  Notifications           In-app first; email     SMS and WhatsApp are roadmap
                          only if time remains    

  Waiting estimate        Transparent             No ML performance claims
                          deterministic formula   from synthetic data
  ----------------------------------------------------------------------------

Redis, Celery/RQ, Socket.IO, separate AI microservices, voice providers
and deployed ML models are outside the MVP. A single backend instance is
assumed for the hackathon WebSocket implementation. Multi-instance
deployment requires shared event distribution or a message broker and is
future infrastructure work.

### 4.1 Backend module boundaries

Suggested FastAPI modules:

-   `auth`: OTP, sessions, role checks.
-   `catalogue`: offices, services and checklist versions.
-   `appointments`: slots, booking, cancellation and rescheduling.
-   `checkin`: QR references and officer check-in.
-   `queue`: token creation, selection, transitions and counter
    assignment.
-   `documents`: upload validation, OCR and checklist comparison.
-   `assistant`: retrieval, answer generation and citations.
-   `analytics`: aggregate queries and metric definitions.
-   `notifications`: in-app and optional email.
-   `realtime`: WebSocket authentication, subscriptions and event
    delivery.
-   `audit`: append-only accountability events.

Queue ordering and appointment eligibility are backend domain rules.
They must not be implemented as frontend-only logic.

## 5. Queue policy and deterministic next-token algorithm

This is a configurable prototype policy, **not a statement of Karnataka
government rules**. The defaults below are starting values for a demo
and must be approved by the participating office before any real pilot.

### 5.1 Configurable defaults

  Setting                                          Prototype default
  ----------------------------- ------------------------------------
  Slot duration                                           10 minutes
  Appointment check-in opens            15 minutes before slot start
  Appointment check-in closes            15 minutes after slot start
  Walk-in planning share          20% of theoretical hourly capacity
  Missed-call retries                             2 additional calls
  Delay between retries                                    2 minutes
  Time zone                                           `Asia/Kolkata`

Store these values in an office-level `queue_policy` configuration
record, with who changed them and when. Do not hard-code them throughout
the application.

### 5.2 Capacity calculation

For a service with `C` active eligible counters and an average planned
service duration of `D` minutes:

`theoretical_capacity_per_hour = C × floor(60 / D)`

`walk_in_planning_target = floor(theoretical_capacity_per_hour × walk_in_share)`

`appointment_planning_capacity = theoretical_capacity_per_hour - walk_in_planning_target`

Example: two counters, ten-minute service slots:

-   Theoretical capacity: `2 × floor(60 / 10) = 12` visits/hour.
-   Walk-in planning target at 20%: `floor(12 × 0.20) = 2`.
-   Appointment planning capacity: `12 - 2 = 10`.

If one counter is unavailable:

-   Theoretical capacity: 6 visits/hour.
-   Walk-in planning target: 1.
-   Appointment planning capacity: 5.

These are planning estimates, not guaranteed throughput. Subtract
breaks, setup time, staff absence and service-specific variation. The
system must not generate bookable slots for closed or unstaffed periods.

### 5.3 Resolve the walk-in/appointment ambiguity

For the MVP, the 20% figure is a **planning target**, not a promise that
walk-ins will be called ahead of an eligible appointment. This avoids an
unclear mixture of strict appointment priority and hard walk-in
reservation.

The call-next algorithm is:

1.  Lock the selected counter row inside a database transaction.
2.  Confirm the counter is active, staffed and assigned to the officer.
3.  Confirm it has no token currently in `CALLED` or `SERVING`.
4.  Find eligible `WAITING` tokens for services supported by that
    counter.
5.  Appointment tokens are eligible only if the appointment was checked
    in inside its valid window.
6.  If any eligible appointment token exists, choose the earliest
    appointment `slot_start`; break ties by `checked_in_at`, then stable
    token creation time and token ID.
7.  If no eligible appointment token exists, choose the oldest walk-in
    token by `checked_in_at`, then token creation time and token ID.
8.  If no token is eligible, return `204 No Content` or a typed
    `NO_ELIGIBLE_TOKEN` response.
9.  Atomically change the selected token from `WAITING` to `CALLED`,
    assign the counter and record a queue event.
10. Commit before publishing the live event.

The walk-in planning target is used to expose appointment capacity and
measure the walk-in share. Unused appointment capacity is not left idle
when there are waiting walk-ins. The admin dashboard should display
actual walk-in share against the target.

If a pilot office requires strict walk-in reservation, that must be a
separately configured and tested policy, not an undocumented variation
of the MVP algorithm.

### 5.4 Appointment eligibility and late arrivals

-   Appointment check-in opens 15 minutes before slot start and closes
    15 minutes after slot start.
-   Adjacent windows may overlap. The ordering rule in section 5.3
    resolves the eligible appointment order.
-   A citizen checking in after the window closes is not treated as an
    on-time appointment check-in. The officer may offer the next
    available slot or register the citizen as a walk-in at the actual
    arrival time.
-   An appointment not checked in by the close of its window is marked
    `NO_SHOW` only after the system has attempted the configured
    reminder. If no reminder channel is configured, record
    `reminder_status = NOT_CONFIGURED`; do not falsely claim a reminder
    was sent.
-   Appointment no-show is an operational label only and does not block
    future bookings in the MVP.

### 5.5 Missed officer call

A token in `CALLED` remains in that state while retry attempts are made.
Store `call_attempt_count`, `last_called_at` and the officer actor.
After the initial call plus two configured retries, the officer may mark
it `NO_SHOW` with a reason. The citizen can be registered again as a
walk-in. Do not silently move a called token to no-show based only on a
client-side timer.

### 5.6 Priority and fairness

Any accessibility or legally mandated priority must be explicitly
configured by the office, applied according to the office's approved
policy, visible to authorized staff and audit-logged. Never infer
priority from personal attributes or sensitive data. Priority policy is
not required for the hackathon demo.

## 6. Appointment booking and capacity integrity

### 6.1 Appointment slot model

Create an `appointment_slots` table rather than calculating availability
only in the frontend.

Suggested fields:

-   `id`
-   `office_id`
-   `service_id`
-   `starts_at`
-   `ends_at`
-   `capacity`
-   `booked_count`
-   `status` (`OPEN`, `FULL`, `CLOSED`)
-   `created_at`, `updated_at`

A slot's capacity must be generated from active staffing, counter
availability, service duration and office hours. Admin changes to
counter availability must not silently overbook already confirmed
appointments.

### 6.2 Atomic booking transaction

Booking must lock the slot row and reserve capacity in the same
transaction as appointment creation. A safe implementation pattern is:

``` sql
BEGIN;

SELECT id, capacity, booked_count, status
FROM appointment_slots
WHERE id = :slot_id
FOR UPDATE;

-- Application checks:
-- status = 'OPEN'
-- booked_count < capacity
-- slot is still in the future
-- citizen is eligible to book this slot under the product's duplicate rule

INSERT INTO appointments (..., status)
VALUES (..., 'BOOKED');

UPDATE appointment_slots
SET booked_count = booked_count + 1,
    status = CASE
      WHEN booked_count + 1 >= capacity THEN 'FULL'
      ELSE 'OPEN'
    END
WHERE id = :slot_id;

COMMIT;
```

The application must roll back if any check or insert fails. Use an
idempotency key for booking requests so a network retry does not create
duplicate appointments.

Add a partial unique index or equivalent constraint to prevent duplicate
active reservations for the same citizen, service, office and slot.
Define active statuses explicitly, for example `BOOKED` and
`CHECKED_IN`.

### 6.3 Cancellation and rescheduling

Cancellation and rescheduling must update appointment history and slot
capacity transactionally.

Rescheduling procedure:

1.  Lock the old appointment and new slot rows in a consistent order.
2.  Verify the old appointment is still active and the new slot has
    capacity.
3.  Reserve the new slot.
4.  Create a new appointment row with `rescheduled_from_id`.
5.  Mark the old row `RESCHEDULED` and set `rescheduled_to_id`.
6.  Decrement the old slot's `booked_count`.
7.  Invalidate every unused QR reference for the old appointment.
8.  Create a new QR reference for the new appointment.
9.  Commit all changes together.

If any step fails, roll back the entire transaction. Never overwrite the
original appointment row or its audit history.

## 7. QR check-in and replay protection

### 7.1 QR reference design

-   Generate a cryptographically secure random opaque reference with at
    least 128 bits of entropy; 256 bits is preferred.
-   The QR contains only the opaque reference and a non-sensitive
    version/route marker if required.
-   Never place a name, phone number, Aadhaar number, document content
    or predictable database ID in the QR.
-   Store only a cryptographic hash of the reference in
    `checkin_references`.
-   Store `appointment_id`, `expires_at`, `used_at`, `created_at`, and
    invalidation reason.
-   The raw reference is returned to the citizen once at booking and is
    not logged.

### 7.2 Atomic check-in transaction

The officer submits the reference through the authenticated check-in
endpoint.

Inside one transaction:

1.  Hash the submitted reference and locate the matching record.
2.  Lock the reference and appointment rows.
3.  Verify officer authorization for the appointment's office.
4.  Verify appointment status is `BOOKED`.
5.  Verify current server time is within the configured check-in window.
6.  Verify `used_at IS NULL` and reference is not expired or
    invalidated.
7.  Atomically set `used_at`.
8.  Change appointment status to `CHECKED_IN`.
9.  Create exactly one queue token for the appointment.
10. Record audit and queue events.
11. Commit, then publish the event.

Enforce a unique constraint on `queue_tokens.appointment_id` when
non-null. If two officers scan the same QR simultaneously, only one
transaction may create the token. The second receives a clear
`ALREADY_CHECKED_IN` response.

QR check-in is a convenience reference, not proof of identity. Manual
lookup by booking reference must require officer authorization and
confirmation against the citizen's demo profile.

## 8. Appointment and token state machines

Keep appointment state separate from queue-token state.

### 8.1 Appointment states

  -----------------------------------------------------------------------
  Current state           Allowed next state      Trigger
  ----------------------- ----------------------- -----------------------
  `BOOKED`                `CHECKED_IN`            Valid officer QR/manual
                                                  check-in

  `BOOKED`                `CANCELLED`             Citizen or authorized
                                                  officer cancels

  `BOOKED`                `RESCHEDULED`           New linked appointment
                                                  created

  `BOOKED`                `NO_SHOW`               Check-in window closes
                                                  without check-in and
                                                  reminder attempt/status
                                                  is recorded

  `CHECKED_IN`            `COMPLETED`             Linked queue token is
                                                  completed

  `CHECKED_IN`            `CANCELLED`             Authorized office
                                                  cancellation with
                                                  reason
  -----------------------------------------------------------------------

`RESCHEDULED`, `CANCELLED`, `NO_SHOW` and `COMPLETED` are terminal
appointment states. A rescheduled booking is a new appointment record.

### 8.2 Queue-token states

  Current state   Allowed next state   Trigger
  --------------- -------------------- ---------------------------------------------
  `WAITING`       `CALLED`             Atomic officer call-next
  `WAITING`       `CANCELLED`          Authorized cancellation with reason
  `CALLED`        `SERVING`            Officer starts service
  `CALLED`        `NO_SHOW`            Retry policy exhausted and officer confirms
  `CALLED`        `WAITING`            Officer withdraws call with reason
  `SERVING`       `COMPLETED`          Officer completes service
  `SERVING`       `ON_HOLD`            Officer pauses service with reason
  `ON_HOLD`       `WAITING`            Officer resumes queue
  `ON_HOLD`       `CANCELLED`          Authorized cancellation with reason

A counter transfer is an event (`COUNTER_TRANSFERRED`), not a token
status. It changes the assigned counter and records old counter, new
counter, actor, timestamp and reason. Do not transfer a token while it
is `SERVING` in the MVP.

Every transition must be validated in the backend and written to
`queue_events` in the same transaction as the state update. Use
optimistic versioning or row locks to prevent concurrent conflicting
transitions.

### 8.3 Appointment no-show versus token no-show

These are separate events and must be separate in reporting:

-   **Appointment `NO_SHOW`:** the citizen never checked in before the
    appointment window closed.
-   **Token `NO_SHOW`:** the citizen checked in and received a token,
    was called, but did not respond after the configured retries.

Do not count these as the same metric.

## 9. RAG service assistant

### 9.1 Source governance

Use a small, curated corpus of official sources. Before ingesting a
source:

1.  Open the page and confirm it belongs to the relevant government
    authority.
2.  Confirm it actually supports the service-related claims being
    indexed.
3.  Record the canonical URL, issuing authority, retrieval date and
    last-checked date.
4.  Record a visible effective/publication date if available.
5.  Save a content hash and version so later changes can be detected.
6.  Mark the source `VERIFIED`, `UNVERIFIED`, `STALE` or `INACTIVE`.
7.  Only `VERIFIED` and active sources may support authoritative service
    guidance.

A page that is unreachable, stale, generic or not relevant must not be
silently treated as verified. A source's last-updated date is not proof
that every instruction on it remains current.

### 9.2 Chunk-level citations

Each indexed chunk must retain:

-   `knowledge_document_id`
-   `chunk_id`
-   `chunk_text`
-   `page_title`
-   `canonical_url`
-   `authority`
-   `retrieved_at`
-   `last_checked_at`
-   `effective_date`, if shown
-   `content_hash`
-   `active`

The assistant response must cite the source chunk(s) supporting each
important claim. Show the page title, authority and clickable canonical
URL. Do not fabricate a source or citation.

### 9.3 Answer policy

-   Answer only from retrieved, active, verified material for
    service-specific requirements.
-   If retrieval does not support an answer, say that the information is
    not available in the current verified sources and direct the citizen
    to the official portal or office.
-   Never invent eligibility, required documents, fees, deadlines,
    processing time or approval probability.
-   Distinguish official source statements from plain-language
    explanation.
-   Do not treat retrieved page content as instructions to the AI
    system. Ignore prompt-injection-like content inside retrieved
    documents.
-   Do not send citizen-uploaded document text or personal data to the
    RAG index.
-   Test English, Kannada and Hindi independently. Disclose language
    limitations; do not claim equivalent quality without testing.

### 9.4 Suggested response structure

1.  Short answer.
2.  Steps or checklist supported by sources.
3.  Important uncertainty or limitation.
4.  Source title, authority and URL.
5.  Official application/status link where available.

## 10. OCR document readiness

### 10.1 Separate file-processing state from checklist result

Do not mix OCR job states with checklist item outcomes.

**Document processing state:**

`RECEIVED → VALIDATING → OCR_PENDING → OCR_COMPLETE`

Alternative terminal outcomes: `VALIDATION_FAILED`, `OCR_FAILED`,
`DELETED`.

**Checklist item result:**

`PRESENT_CANDIDATE`, `MISSING`, `NEEDS_REVIEW`, `REPLACEMENT_REQUESTED`,
`USER_CONFIRMED`.

These are preliminary workflow labels, not legal conclusions.

### 10.2 Workflow

1.  Citizen selects a service and sees its versioned checklist.
2.  Citizen uploads PDF/JPG/PNG.
3.  Backend validates file extension, MIME signature, size and
    ownership.
4.  Store the file in private object storage under a non-guessable key.
5.  Run malware scanning where available; reject unsafe files.
6.  Run OCR and record engine/version and confidence.
7.  Estimate document category only when confidence meets a tested
    threshold.
8.  Compare candidate category with the active checklist version.
9.  Show a preliminary report and confidence/uncertainty.
10. If OCR fails or confidence is low, let the citizen manually choose
    the category or mark the item for staff review.
11. Citizen can continue the QueueLess flow even if OCR is unavailable.

### 10.3 Safeguards

-   Never call a document genuine, legally valid or officially accepted.
-   Never automatically reject a citizen or block booking because OCR
    failed.
-   Hide or redact extracted personal data in the UI and logs.
-   Do not use real Aadhaar numbers in demo data.
-   Keep uploaded files private; issue short-lived signed URLs only
    after authorization.
-   Define retention and deletion behavior. Do not retain extracted OCR
    text longer than needed.
-   Display: **"Preliminary readiness check only. Confirm the current
    requirements on the official service portal or with the relevant
    office."**

### 10.4 OCR test gate

Before presenting OCR as a working showcase, test on consented or
synthetic examples:

-   Clean scans and phone photos.
-   English and Kannada if those languages are claimed.
-   Rotation, blur, shadows, compression, mixed scripts and low
    resolution.
-   Different document layouts and page counts.

Record a small test report: sample count, language, image condition,
category accuracy, failure count and manual-fallback success. Do not
claim production-grade accuracy from a small demo sample.

## 11. Waiting-time estimate and counter rules (P2)

### 11.1 Transparent waiting-time baseline

Only implement after the P0 queue works.

For the citizen's token, estimate the remaining work ahead using
historical or configured service-duration estimates:

`estimated_wait = total_expected_work_of_eligible_tokens_ahead / active_eligible_counters`

Show a range, not a false-precision timestamp, and include
`last_updated_at`. Exclude counters that are unavailable or cannot serve
the selected service. Recalculate on queue events.

If there is insufficient history, use an explicitly configured
service-duration baseline and label it as an estimate. Do not claim ML
prediction or accuracy from synthetic data.

### 11.2 Eligible-counter rules

Filter counters by service compatibility and active availability. Among
eligible counters, select the one with the lowest transparent workload
score. Store the selected counter and reason. This is deterministic
queue logic, not an AI feature. Never reassign a citizen already in
`SERVING`.

## 12. Data model

The schema below is a conceptual baseline; exact SQL types and
migrations are implementation decisions.

  -------------------------------------------------------------------------------
  Entity                         Important fields         Purpose
  ------------------------------ ------------------------ -----------------------
  `users`                        id, firebase_uid         Accounts; Firebase UID
                                 (unique), name, phone,  maps to internal user;
                                 role, is_active,        DB role is authoritative
                                 preferred_language       

  `offices`                      id, name, address,       Office configuration
                                 timezone, hours, active  

  `services`                     id, office_id, name,     Catalogue
                                 description, active,     
                                 official_url             

  `service_checklist_versions`   id, service_id, version, Versioned checklist
                                 effective_date, source,  
                                 active                   

  `service_documents`            id,                      Checklist items
                                 checklist_version_id,    
                                 name, required,          
                                 description              

  `appointment_slots`            id, office_id,           Capacity-controlled
                                 service_id, starts_at,   slots
                                 ends_at, capacity,       
                                 booked_count, status     

  `appointments`                 id, citizen_id,          Reservations and
                                 service_id, office_id,   history
                                 slot_id, status,         
                                 rescheduled_from_id,     
                                 rescheduled_to_id        

  `checkin_references`           id, appointment_id,      One-time QR references
                                 reference_hash,          
                                 expires_at, used_at,     
                                 invalidated_at           

  `counters`                     id, office_id, name,     Physical counters
                                 status                   

  `counter_services`             counter_id, service_id   Counter capability

  `officer_assignments`          officer_id, counter_id,  Authorization
                                 valid_from, valid_to     

  `queue_tokens`                 id, appointment_id,      Queue entries
                                 service_id, counter_id,  
                                 token_number, status,    
                                 source, checked_in_at,   
                                 call_attempt_count,      
                                 version                  

  `queue_events`                 id, token_id,            Immutable queue history
                                 event_type, old_status,  
                                 new_status, actor_id,    
                                 reason, created_at       

  `citizen_documents`            id, citizen_id,          Private uploads
                                 storage_key, file_type,  
                                 processing_status,       
                                 created_at               

  `document_checks`              id, document_id,         Readiness results
                                 checklist_version_id,    
                                 result, confidence,      
                                 engine_version,          
                                 reviewed_by              

  `knowledge_documents`          id, title, authority,    RAG source governance
                                 source_url,              
                                 retrieved_at,            
                                 last_checked_at,         
                                 effective_date,          
                                 content_hash,            
                                 verification_status,     
                                 active                   

  `knowledge_chunks`             id,                      Chunk-level
                                 knowledge_document_id,   retrieval/citations
                                 chunk_index, text,       
                                 embedding_ref, active    

  `notifications`                id, user_id, channel,    Delivery tracking
                                 type, status, sent_at    

  `audit_logs`                   id, actor_id, action,    Accountability
                                 entity_type, entity_id,  
                                 reason, timestamp        

  `event_outbox`                 id, event_type, payload, Reliable post-commit
                                 created_at, published_at event dispatch
  -------------------------------------------------------------------------------

### 12.1 Constraints and indexes

-   Foreign keys for all relationships.
-   Non-guessable public IDs for user-facing references.
-   Unique token number per office, service and operating date.
-   Unique non-null appointment link on queue token.
-   One-time QR reference use enforced atomically.
-   Partial unique index preventing duplicate active appointment for the
    same citizen/service/office/slot.
-   Indexes on office, service, slot time, appointment status, token
    status, queue order and actor.
-   Booking, cancellation, rescheduling, check-in, call-next and token
    transition operations use transactions.
-   Use `TIMESTAMPTZ` and store timestamps in UTC; render in the office
    timezone (`Asia/Kolkata` for the Karnataka demo).
-   Keep appointment state history and token event history; do not
    overwrite history to simplify the UI.

### 12.2 Analytics timestamps

Store at least:

-   `checked_in_at`
-   `first_called_at`
-   `service_started_at`
-   `completed_at`
-   `cancelled_at` or `no_show_at`

Definitions:

`waiting_time = service_started_at - checked_in_at`

`service_duration = completed_at - service_started_at`

For a token that is called more than once, waiting time still ends at
the actual `service_started_at`. Exclude cancelled and no-show tokens
from completed-service duration statistics. Report appointment no-shows
and token no-shows separately. State whether averages/medians use only
completed tokens and display the reporting period and sample count.

## 13. API contract

All REST endpoints are under `/api/v1`. Validate inputs with Pydantic,
paginate lists, use typed error responses, rate-limit
authentication/uploads/AI endpoints, and audit sensitive operations.

  ----------------------------------------------------------------------------------------
  Area                    Endpoints                               Authorization/behavior
  ----------------------- --------------------------------------- ------------------------
  Auth                    Firebase client sign-in;               FastAPI verifies
                          protected REST requests use              Firebase ID tokens;
                          `Authorization: Bearer ...`             no QueueLess OTP or
                                                                  refresh endpoint
                          `POST /auth/logout`, `GET /users/me`    

  Catalogue               `GET /offices`, `GET /services`,        Public or authenticated
                          `GET /services/{id}`,                   read as configured
                          `GET /services/{id}/checklist`          

  Assistant               `POST /assistant/chat`                  Returns answer plus
                                                                  chunk-level sources

  Documents               `POST /documents/upload`,               Citizen owns resource;
                          `GET /documents`,                       staff access limited
                          `POST /documents/{id}/check`,           
                          `GET /documents/{id}/check-result`,     
                          `DELETE /documents/{id}`                

  Appointments            `GET /appointments/slots`,              Citizen owns booking;
                          `POST /appointments`,                   idempotency key on
                          `GET /appointments`,                    create
                          `POST /appointments/{id}/reschedule`,   
                          `POST /appointments/{id}/cancel`        

  Check-in                `POST /appointments/{id}/check-in`      Officer assigned to
                                                                  office; atomic QR
                                                                  validation

  Queue                   `POST /queue/tokens` (walk-in),         Office-scoped access
                          `GET /queue/tokens/{id}`,               
                          `GET /queue/office/{id}`                

  Officer actions         `POST /counters/{id}/call-next`,        Assigned officer only;
                          `POST /queue/tokens/{id}/start`,        atomic state transitions
                          `POST /queue/tokens/{id}/complete`,     
                          `POST /queue/tokens/{id}/no-show`,      
                          `POST /queue/tokens/{id}/hold`,         
                          `POST /queue/tokens/{id}/resume`        

  Admin                   `GET /admin/overview`,                  Office admin only
                          `GET /admin/analytics/*`,               
                          `POST /admin/services`,                 
                          `POST /admin/counters`,                 
                          `POST /admin/knowledge-documents`,      
                          `POST /admin/queue/manual-entry`        
  ----------------------------------------------------------------------------------------

Use typed error codes such as `SLOT_FULL`, `SLOT_CLOSED`,
`DUPLICATE_BOOKING`, `QR_EXPIRED`, `QR_ALREADY_USED`,
`ALREADY_CHECKED_IN`, `INVALID_TOKEN_TRANSITION`, `COUNTER_BUSY`,
`NOT_ASSIGNED_TO_COUNTER`, `DOCUMENT_ACCESS_DENIED` and
`NO_ELIGIBLE_TOKEN`.

### 13.1 Concurrency rules

-   Booking: lock slot row; idempotency key; capacity update and
    appointment insert in one transaction.
-   QR check-in: lock QR reference and appointment; unique queue-token
    appointment link.
-   Call-next: lock counter row; select next token with
    `FOR UPDATE SKIP LOCKED`; assign and transition atomically.
-   Token transitions: lock token row or compare version; reject stale
    updates.
-   Rescheduling: lock old appointment and new slot; reserve new
    capacity and release old capacity atomically.
-   Manual offline entry: idempotency key or unique offline reference;
    duplicate candidates go to review.

## 14. WebSocket event delivery and recovery

### 14.1 Events

Events are scoped to an authenticated user, office or counter:

-   `queue.token_created`
-   `queue.token_called`
-   `queue.service_started`
-   `queue.service_completed`
-   `queue.token_status_changed`
-   `appointment.status_changed`

Never broadcast document contents, OCR text, phone numbers or profile
data to shared office channels. A citizen subscription may receive only
that citizen's appointment/token status and public queue information.

### 14.2 Commit before broadcast

1.  Validate and authorize the action.
2.  Commit the database state change and an `event_outbox` record in the
    same transaction.
3.  After commit, publish the event.
4.  Mark the outbox record published.
5.  Retry unpublished outbox records after a process restart.

For a single-instance hackathon deployment, the dispatcher may run
within the FastAPI process. Do not claim durable multi-instance delivery
without shared infrastructure.

### 14.3 Reconnection behavior

WebSocket events are hints for fast UI updates, not the source of truth.

On connection or reconnection:

1.  Authenticate the socket.
2.  Subscribe only to authorized topics.
3.  Fetch the latest state from REST (`GET /appointments/{id}` or
    `GET /queue/tokens/{id}`).
4.  Replace stale client state with the REST response.
5.  Resume listening for events.

Optionally include `event_id` or monotonically increasing entity
`version` so the client can detect gaps and stale updates. The UI must
remain correct if an event is missed.

## 15. Authentication, security and privacy

### 15.1 Authentication (Firebase Authentication)

QueueLess uses Firebase Authentication for citizen phone-number identity verification and client session management. FastAPI is the trusted resource server and verifies Firebase ID tokens using the Firebase Admin SDK.

**Citizen sign-in flow**
1. The React client starts Firebase Phone Authentication using the Firebase client SDK and the configured reCAPTCHA/app-verification flow.
2. Firebase sends and verifies the SMS OTP. QueueLess backend code must not generate, store, return, or verify this OTP.
3. After successful sign-in, the client obtains a Firebase ID token using the signed-in Firebase user and sends it to FastAPI as `Authorization: Bearer <token>`.
4. FastAPI verifies the token with Firebase Admin SDK, validates the expected Firebase project, and reads the verified `uid` and phone claim where present.
5. FastAPI resolves or provisions the internal QueueLess user record by unique `firebase_uid`. The internal user UUID is used for all foreign keys and ownership checks.
6. FastAPI loads the user's active status and role from PostgreSQL. The database is the source of truth for authorization.

**Required rules**
- Firebase project ID and Admin SDK configuration must be explicit per environment. Never accept tokens from an unintended Firebase project.
- Verify token signature, issuer, audience, expiry and revocation according to the selected verification policy. Use revocation checking for sensitive operations or globally if the latency trade-off is acceptable; document the chosen policy.
- Return `401` for missing, malformed, expired, revoked or invalid Firebase tokens. Do not leak token-verification details.
- Return `403` when an authenticated user lacks the required role, office scope, counter assignment or resource ownership.
- Do not allow public self-registration to assign `OFFICER`, `OFFICE_ADMIN` or `PLATFORM_ADMIN`. Staff/admin records must be provisioned through a trusted administrative process.
- Do not use client-supplied role claims as the authorization source. Firebase custom claims are optional and, if used, must be set only by trusted server-side administration; PostgreSQL role checks remain authoritative for this prototype.
- Do not implement QueueLess OTP challenge storage, custom citizen JWT issuance, custom refresh-token rotation, or a QueueLess refresh-token table.
- Firebase client SDK manages ID-token refresh. The client should call `getIdToken()` when making authenticated requests rather than persisting tokens manually.
- Never log Firebase ID tokens, service-account credentials, QR raw references or other secrets.

**Staff sign-in**
Staff may also authenticate through Firebase using the team's configured provider. Staff identity must map to a pre-provisioned QueueLess user with an approved role and office/counter assignment. A valid Firebase identity alone does not grant staff privileges.

### 15.1.1 WebSocket authentication

Do not place Firebase ID tokens or any credentials in WebSocket query strings or URLs. The authenticated REST session requests a short-lived, single-use WebSocket ticket. The socket consumes that ticket during connection establishment. Ticket expiry, single-use behavior, authorization scope and log redaction remain mandatory.

### 15.2 Authorization

-   Enforce role and resource ownership in FastAPI
    dependencies/services.
-   Verify office and counter assignment for every officer action.
-   Use least privilege for document access.
-   Avoid exposing sequential database IDs in public routes.

### 15.3 File and data security

-   HTTPS in deployed environments.
-   Private object storage and short-lived signed URLs.
-   Validate file extension, MIME signature and file size; do not trust
    browser-supplied MIME alone.
-   Malware scan where available.
-   Restrict allowed file types and maximum page/file size.
-   Keep secrets in environment/secret management, not source control.
-   Redact sensitive data from logs and notifications.
-   Define retention, deletion and backup policies before real
    deployment.
-   Use synthetic documents in demos; no real Aadhaar or sensitive
    personal data.

### 15.4 Responsible AI

-   AI never approves/rejects applications or determines legal
    eligibility.
-   OCR never declares authenticity or legal validity.
-   Predictions never cancel or deprioritize citizens.
-   Show citations, uncertainty and escalation route.
-   Provide manual fallback and a way to report incorrect answers.
-   Human officers remain responsible for official decisions.

## 16. Notifications

In-app notifications are the MVP default. Email may be added if time
permits. SMS and WhatsApp are roadmap items.

Notification content must not include document images, OCR text, Aadhaar
numbers or sensitive personal data. Use generic text and require the
citizen to sign in to view details. Record delivery state and avoid
claiming a reminder was sent unless the provider confirms it.

## 17. Offline fallback and reconciliation

If the office network is unavailable:

1.  Officer informs waiting citizens that live QueueLess updates and QR
    validation are temporarily unavailable.
2.  Office switches to its approved paper register.
3.  Record a temporary offline reference, arrival time, service,
    counter/desk and outcome.
4.  Do not pretend offline activity is synchronized live.
5.  When connectivity returns, an authorized officer enters records with
    source `OFFLINE_REGISTER`, preserving original event times and
    recording sync time separately.
6.  Flag likely duplicates for human review; never silently merge.
7.  Audit every manual entry and reconciliation decision.

For the hackathon, this may be a documented procedure plus a simple
admin manual-entry screen. Do not build a full offline-first
synchronization engine unless the core MVP is complete.

## 18. Admin analytics

Use PostgreSQL aggregate queries. Show reporting period, sample count
and metric definitions.

P1 metrics:

-   Total appointments booked.
-   Appointment cancellations and appointment no-shows.
-   Walk-in tokens created.
-   Current waiting tokens.
-   Tokens currently serving.
-   Completed tokens.
-   Average and median waiting time.
-   Average and median service duration.

Do not mix appointment no-shows with token no-shows. Do not interpret a
slow service as staff fault; show it as an operational signal for
review. Use aggregate data and avoid exposing individual citizen
documents or unnecessary personal data.

## 19. Demo plan and definition of done

Use a fictional citizen, one configured office, the Income Certificate
service and clearly labelled synthetic records. Do not imply that the
demo is an official government service integration.

1.  Citizen signs in using Firebase Phone Authentication; FastAPI verifies the resulting Firebase ID token.
2.  Citizen opens the service catalogue.
3.  Citizen asks the assistant a service question and sees a verified
    source citation.
4.  Citizen opens the versioned checklist and uploads synthetic sample
    documents.
5.  OCR shows a preliminary result; a missing or unreadable item can be
    manually confirmed.
6.  Citizen books an available slot and receives a one-time QR
    reference.
7.  Officer in a second browser scans/types the reference and checks the
    citizen in.
8.  A single queue token is created.
9.  Officer calls the token, starts service and completes it.
10. Citizen sees status changes without refreshing; after a simulated
    reconnect, REST resynchronization still shows the correct final
    state.
11. Admin sees bookings, waiting queue, completed token and correctly
    calculated wait metrics.

No manual database edits are permitted during the demo.

**Demo message:** QueueLess prepares citizens before they visit,
coordinates the queue while they are at the office, and gives
administrators operational information.

## 20. Implementation order

### Phase 1: Data and backend foundation

-   PostgreSQL schema and migrations.
-   Seed office, service, counters, officers and synthetic citizen.
-   Demo auth and backend role checks.
-   Appointment slot generation and transactional booking.

### Phase 2: Queue core

-   QR generation, hash storage and atomic check-in.
-   Token creation and unique constraints.
-   Queue state machine.
-   Counter lock and atomic call-next.
-   Officer actions and audit history.

### Phase 3: Frontend journey and live updates

-   Citizen booking/status screens.
-   Officer queue screen.
-   Admin overview.
-   WebSocket events and REST reconnection recovery.

### Phase 4: P1 intelligence

-   Verify and curate official source corpus.
-   RAG retrieval with chunk citations and refusal behavior.
-   OCR test gate and manual fallback.
-   Checklist versioning and readiness report.

### Phase 5: Hardening

-   Concurrency tests.
-   Authorization tests.
-   File validation tests.
-   State-machine tests.
-   Demo rehearsal and failure simulation.

Do not start P2 until the full P0 journey passes.

## 21. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Overbooking                         Slot-row lock, transaction,
                                      idempotency key, database
                                      constraints

  Duplicate QR check-in               Hashed one-time reference, atomic
                                      consume, unique token per
                                      appointment

  Duplicate call-next                 Lock counter and token selection
                                      atomically

  Invalid state transitions           Explicit backend state machine and
                                      row lock/version

  Confusing queue fairness            Publish deterministic call-next
                                      policy and reason

  Incorrect AI answer                 Verified source corpus, chunk
                                      citations, refusal when unsupported

  OCR failure                         Manual category/checklist
                                      confirmation; never block booking

  Lost WebSocket event                REST resync on connect/reconnect;
                                      outbox for post-commit events

  Unauthorized file access            Ownership checks, private storage,
                                      short-lived signed URLs

  Network outage                      Paper-register procedure and
                                      audited manual reconciliation

  Synthetic data misrepresented       Label all sample records and
                                      metrics

  Scope creep                         P0 first; P1 only after P0
                                      acceptance
  -----------------------------------------------------------------------

## 22. Verified source register for the initial corpus

The following pages were opened during preparation of this revision.
This confirms that the pages were reachable and their visible page
descriptions were inspected; it does **not** mean every service rule is
current or that every page contains a complete document checklist.
Verify service-specific details with the responsible authority before
using them as authoritative RAG content.

  ---------------------------------------------------------------------------------------------------------------------------
  Source                                                                      What was confirmed      Corpus treatment
  --------------------------------------------------------------------------- ----------------------- -----------------------
  [Seva One, Government of Karnataka](https://sevaone.karnataka.gov.in/)      Official Karnataka      Candidate source;
                                                                              citizen-services site   verify content manually
                                                                              title was reachable;    before indexing
                                                                              readable page content   
                                                                              was not available in    
                                                                              the inspection          

  [Seva Sindhu, Bengaluru Urban                                               District page describes Verified for high-level
  District](https://bengaluruurban.nic.in/en/service/seva-sindhu/)            Seva Sindhu as a        platform description;
                                                                              Karnataka government    not a substitute for
                                                                              service-delivery        service-specific rules
                                                                              initiative and links to 
                                                                              the Seva Sindhu portal  

  [Caste and Income Certificate, Kolar                                        District page describes Candidate for
  District](https://kolar.nic.in/en/service/caste-and-income-certificate/)    Atalji Janasnehi        service-channel
                                                                              Kendras/Nadakacheri and context; page is dated
                                                                              links to the            20 Aug 2018, so
                                                                              Nadakacheri portal      re-verify current
                                                                                                      process

  [Caste Certificate, Mysuru                                                  District page describes Candidate for
  District](https://mysore.nic.in/en/service/caste-certificate/)              Nadakacheri and         service-channel
                                                                              caste/income-related    context; page is dated
                                                                              service channels        29 Jan 2021, so
                                                                                                      re-verify current
                                                                                                      process

  [Apply for Income Certificate, Tumakuru                                     Page could not be       Unverified; do not
  District](https://tumkur.nic.in/en/service/apply-for-income-certificate/)   fetched during this     ingest until manually
                                                                              review                  checked

  [DigiLocker](https://www.digilocker.gov.in/)                                Official DigiLocker     Use only for accurate
                                                                              material identifies     platform description;
                                                                              NeGD/MeitY and          do not claim QueueLess
                                                                              describes document      is integrated
                                                                              access/sharing;         
                                                                              integration material    
                                                                              requires authorized     
                                                                              onboarding              
  ---------------------------------------------------------------------------------------------------------------------------

Do not copy old or unverified document requirements into the live
checklist. The office admin must maintain the checklist version, source,
effective date and last verification date.

## 23. Open decisions before a real pilot

The hackathon defaults are implementation defaults, not official rules.
Before any office pilot, confirm:

-   Whether the office accepts appointment bookings and what capacity it
    can commit.
-   Actual service duration and staffing by time window.
-   Check-in window and walk-in handling policy.
-   Priority/accessibility rules approved by the office.
-   Approved identity confirmation procedure.
-   Official checklist and source owner for each service.
-   Data retention, hosting, security and consent requirements.
-   Whether any official API integration is authorized.

------------------------------------------------------------------------

**End of QueueLess 2.2 Technical Specification**


---

# QueueLess 2.3 Amendment: Correctness, Fairness and Operational Readiness

**Precedence:** This amendment is normative and supersedes conflicting statements in earlier sections of this document. It closes the implementation gaps identified during the 2.2 review. Existing product boundaries remain unchanged: QueueLess coordinates visits and physical queues; it does not submit or approve government applications or determine legal eligibility.

## A. Slot-level capacity and walk-in reserve

The 20% walk-in share is applied to **each generated 60-minute operating block**, not independently rounded down in every 10-minute slot. Per-slot rounding would systematically lose fractional capacity.

For each office, service, operating date and 60-minute block:

1. Calculate `block_capacity = active_counters × floor(60 / service_duration_minutes)`, adjusted for breaks and counter availability.
2. Calculate `walk_in_reserve = floor(block_capacity × walk_in_share)`.
3. Calculate `appointment_block_capacity = block_capacity - walk_in_reserve`.
4. Distribute the appointment capacity across the six 10-minute slots using the deterministic quotient/remainder rule:
   - `base = floor(appointment_block_capacity / slots_in_block)`
   - `remainder = appointment_block_capacity % slots_in_block`
   - The first `remainder` slots receive `base + 1`; the remaining slots receive `base`.
   - Slot ordering is chronological. Persist the generated capacity; do not recalculate it differently during booking.

Example: two counters, 10-minute service duration, 20% walk-in reserve:
- Theoretical block capacity = 12.
- Walk-in reserve = 2.
- Appointment block capacity = 10.
- Six slot capacities = `2, 2, 2, 2, 1, 1`.

One counter gives theoretical capacity 6, reserve 1, appointment capacity 5, and slot capacities `1, 1, 1, 1, 1, 0`. A zero-capacity slot is `CLOSED` for appointment booking, not `OPEN`.

`appointment_slots` stores the resulting integer capacity for that exact slot. `booked_count` must never exceed it. The walk-in reserve is a planning allocation, not a hard guarantee that exactly that number of walk-ins will be served. Unused walk-in capacity may be consumed by appointments only through an explicit admin-approved release rule; default behavior is to release unused reserve 10 minutes before the block ends.

## B. Authenticated QR retrieval and rotation

The citizen must be able to recover a QR after reload without storing the raw reference.

Add:

`POST /appointments/{appointment_id}/qr/rotate`

Authorization: authenticated citizen who owns the appointment; appointment must be `BOOKED`, not checked in, cancelled, rescheduled or expired.

Transaction:
1. Lock the appointment row.
2. Confirm ownership, status and that the check-in window has not closed.
3. Invalidate all existing unused references for the appointment with reason `ROTATED`.
4. Generate a new cryptographically random 256-bit opaque reference.
5. Store only its cryptographic hash and metadata.
6. Return the raw reference exactly once in the response, with `Cache-Control: no-store`; never log it.
7. Commit before returning success.

The citizen UI exposes **Show QR**. It calls the rotation endpoint each time a QR needs to be recovered or re-displayed. Rotation invalidates screenshots/older QR references. Rate-limit rotations (for example, 3 per 10 minutes) and audit them. A failed transaction must leave the previous reference valid; therefore invalidation and creation happen atomically.

## C. QR and manual check-in API separation

Replace the ambiguous QR endpoint with two distinct paths:

- `POST /checkin` body: `{ "reference": "<opaque-raw-reference>" }`. This is the QR scan path. Officer authentication and office assignment are required. Resolve the appointment from the hashed reference.
- `POST /appointments/{appointment_id}/check-in/manual` body: `{ "confirmation": true, "reason": "<required reason>" }`. This is the manual lookup path. Officer must be assigned to the appointment's office and confirm the citizen against the booking profile. Record the officer, reason and audit event.

Both paths call the same internal transactional check-in service. Both enforce one queue token per appointment, appointment state/window checks and atomic state transitions. The QR path must not require the officer to know or submit an appointment ID.

## D. Hold and resume semantics; service timing

Use the following token transitions:

- `WAITING → CALLED`
- `CALLED → WAITING` only for an explicit missed-call retry/reset action, with reason and audit event.
- `CALLED → SERVING`
- `CALLED → NO_SHOW` only after the configured call/retry policy and officer confirmation.
- `SERVING → ON_HOLD` with mandatory reason.
- `ON_HOLD → SERVING` on resume.
- `SERVING → COMPLETED`
- `ON_HOLD → CANCELLED` only with authorized cancellation and reason.

`ON_HOLD → WAITING` is not allowed. A held citizen has already started service and must retain the assigned counter unless an authorized reassignment flow explicitly releases it.

Timestamp definitions:
- `service_started_at`: first transition into `SERVING`; immutable thereafter.
- `last_resumed_at`: latest transition from `ON_HOLD` to `SERVING`.
- `hold_started_at`: start of the current hold, null when not on hold.
- `total_hold_seconds`: accumulated duration across completed hold intervals.
- `completed_at`: transition to `COMPLETED`.

Metrics:
- Gross service elapsed time = `completed_at - service_started_at`.
- Active service duration = gross service elapsed time minus `total_hold_seconds`.
- Report both when operationally useful. Do not reset `service_started_at` on resume.
- Queue waiting time ends at the first `service_started_at`; hold time is not queue waiting time.

## E. Durable no-show processing and reminders

Use a **database-backed periodic sweep**, not in-process background tasks.

Run a scheduler/worker every minute (a separate worker process or managed scheduled job). It must be safe to run more than once and across multiple instances:
1. Select due appointments where `status = BOOKED`, `check_in_close_at <= now()`, and no valid check-in exists.
2. Claim rows in bounded batches using `FOR UPDATE SKIP LOCKED`.
3. Set appointment status to `NO_SHOW`, `no_show_at`, and reason `CHECK_IN_WINDOW_CLOSED`.
4. Write an audit event and an outbox event in the same transaction.
5. Commit. A unique/conditional update prevents duplicate processing.

`call-next` and appointment-list reads must also apply a **lazy safety check** for due unprocessed appointments, so a delayed scheduler does not leave expired appointments bookable or apparently active. The periodic sweep remains the primary mechanism.

Reminders use a durable `notification_jobs` table and the event outbox. A worker claims due jobs, sends them, and records attempts/status. Do not rely on an in-memory timer. If no provider is configured, persist `NOT_CONFIGURED`; do not mark the reminder as sent.

## F. Walk-in starvation protection

Add office/service-level configurable `max_walk_in_wait_minutes`, default **45 minutes for the prototype**. This is a demo policy, not a Karnataka government rule.

Call-next selection:
1. Lock the counter and verify it is available.
2. Select eligible waiting tokens.
3. If any walk-in has waited at least `max_walk_in_wait_minutes`, promote the oldest overdue walk-in ahead of ordinary appointment candidates. Tie-break by `checked_in_at`, creation time, then token ID.
4. Otherwise, select the earliest eligible appointment using the existing appointment ordering.
5. If no appointment is eligible, select the oldest walk-in.
6. Apply approved accessibility/legal priority only through explicit office configuration and audit logging.

Expose `walk_in_wait_minutes`, `promoted_for_fairness` and policy version in the queue event. The dashboard must show overdue walk-ins and promotion count. If the office disables the cap, show an explicit warning that strict appointment priority can cause unbounded walk-in waits. Never claim a guaranteed wait time.

## G. Data model additions and corrections

Add the following tables/fields to Section 12:

| Table | Required fields / constraints | Purpose |
|---|---|---|
| `queue_policy` | `office_id`, `service_id` nullable, `slot_duration_minutes`, `walk_in_share`, `max_walk_in_wait_minutes`, `checkin_open_minutes`, `checkin_close_minutes`, `policy_version`, `effective_from`, `updated_by`, `updated_at` | Versioned office/service policy |
| `idempotency_keys` | `id`, `actor_id`, `scope`, `key_hash`, `request_hash`, `response_status`, `response_body`, `created_at`, `expires_at`; unique `(actor_id, scope, key_hash)` | Safe retry and payload-mismatch detection |
| `token_number_sequences` | `office_id`, `service_id`, `operating_date`, `last_value`; unique `(office_id, service_id, operating_date)` | Concurrency-safe daily token numbering |
| `notification_jobs` | `id`, `user_id`, `type`, `payload`, `scheduled_at`, `status`, `attempt_count`, `last_error`, `sent_at`, `created_at` | Durable reminders |
| `queue_tokens` additions | `operating_date`, `first_called_at`, `last_called_at`, `service_started_at`, `last_resumed_at`, `hold_started_at`, `total_hold_seconds`, `completed_at`, `promoted_for_fairness` | Queue timing and fairness analytics |
| `appointments` additions | `check_in_close_at`, `no_show_at`, `reminder_status`, `qr_rotated_at` | Durable lifecycle processing |
| `appointment_slots` additions | `operating_date`, `block_start_at`, `capacity_policy_version` | Auditable generated capacity |

Token number allocation must lock the relevant `token_number_sequences` row, increment `last_value`, and insert the token in the same transaction. Do not use `MAX(token_number) + 1`. Token number uniqueness must be enforced by a database unique constraint on `(office_id, service_id, operating_date, token_number)`.

Idempotency behavior:
- Same key + same request hash: return the stored original response.
- Same key + different request hash: return `409 IDEMPOTENCY_KEY_REUSED`.
- Different key: process as a new request subject to business uniqueness constraints.
- Store a canonical hash of method, route, actor, and normalized request body. Never store raw secrets in the idempotency record.

For slot cancellation/rescheduling, use one shared transactional helper to decrement `booked_count` and set `status = OPEN` when `booked_count < capacity` and the slot is not administratively closed. Preserve `CLOSED` when closed by an administrator or outside operating hours. For rescheduling, lock old and new slot rows in deterministic ID order to prevent deadlocks; reserve the new slot and release the old slot in the same transaction.

## H. Token-number and operating-date rules

The operating date is the local calendar date in the office timezone (`Asia/Kolkata` for the Karnataka deployment), not the UTC date. Convert the instant to the office timezone before selecting `operating_date` and the token sequence. Store timestamps as UTC `TIMESTAMPTZ`; derive the local date using the office timezone at transaction time.

At midnight IST, a new operating date and token-number sequence begins even if the corresponding UTC date is still the previous day. A visit spanning midnight retains the operating date assigned when its token was created. Do not re-number an active token.

## I. WebSocket authentication and authorization

Do not put Firebase ID tokens, refresh tokens, OTPs or other credentials in WebSocket query strings or URLs.

Preferred handshake:
- Browser obtains a short-lived, single-use WebSocket ticket over authenticated HTTPS (`POST /realtime/ticket`).
- Connect using the ticket in the WebSocket subprotocol or first message, according to the chosen client/server library; never put it in the URL.
- Ticket is short-lived, audience-bound, single-use and stored hashed. Consume it atomically.
- Authenticate and authorize the connection before subscribing to user/office/counter channels.
- Revalidate role/assignment on reconnect and periodically for long-lived sessions.
- Do not log ticket values or authentication frames.

## J. Authorization and reliability clarifications

- `POST /queue/tokens` (walk-in creation): officer or authorized reception staff only; must be assigned to the office. Citizen self-service walk-in creation is out of scope for P0.
- `POST /checkin`: assigned officer only.
- `POST /appointments/{id}/qr/rotate`: appointment-owning citizen only.
- Admin policy changes: office admin only, with effective date, version and audit reason.
- Add `POST /realtime/ticket` to the API contract.
- LLM and OCR provider outages must not block queue/appointment core workflows. RAG returns a clearly labelled temporary-unavailable response with official portal/contact fallback. OCR marks processing as `FAILED_RETRYABLE` or `UNAVAILABLE`; the citizen can continue manually and staff can review documents. Do not fabricate AI results.

## K. Demo source governance update

The existing Income Certificate demo question must not be presented as verified from the Tumakuru page. Replace the core RAG demo with a narrowly scoped question grounded in a primary source that can be inspected before the event.

Candidate official source located during this revision:
- Directorate of Minorities, Government of Karnataka, “Intimation and List for students for Documents Verification”, dated 6 October 2020, hosted on `dom.karnataka.gov.in`.
- The indexed document text states that PSI Training candidates must attend district-office document verification and lists original plus one set of attested copies, including SSLC/PUC marks cards, Income & Caste Certificate issued by Tahsildar, TC, driving licence/voter ID/PAN, degree marks cards/certificates, Aadhaar and photographs.
- The source is specific to **PSI Training document verification**, not a general Income Certificate application checklist. Do not generalize it to other services.
- The official PDF endpoint returned a gateway error during automated inspection, so classify it as `PRIMARY_SOURCE_PENDING_MANUAL_FETCH`, not fully verified, until a team member opens and checks the PDF directly before the event.
- If manual inspection cannot be completed, remove this source from the live RAG corpus and use a source that the team can directly open and verify. The demo question must match the source's exact service and scope.

Demo fallback question, only after manual source verification: “For the Directorate of Minorities PSI Training document verification notice dated 6 October 2020, which original documents and attested copies does the notice ask candidates to bring?” The answer must state the notice date and scope and cite the source. Do not answer “What documents are required for an Income Certificate?” from this notice.

## L. Updated acceptance requirements

The implementation is not complete until:
- Per-slot capacities are generated deterministically from a block-level reserve and persisted.
- Citizens can rotate/retrieve a QR after reload; old QR is rejected.
- QR scan and manual check-in use separate API contracts.
- Held tokens resume to `SERVING`, retaining first service start time and accumulating hold duration.
- The durable no-show sweep and notification job worker are idempotent.
- Walk-in wait-cap promotion works under appointment load.
- Token numbering remains unique under concurrent creation and midnight IST boundary tests pass.
- WebSocket credentials never appear in URLs/logs.
- Provider outage fallbacks preserve core queue functionality.
- The live RAG demo uses a directly inspected, service-specific primary source.
