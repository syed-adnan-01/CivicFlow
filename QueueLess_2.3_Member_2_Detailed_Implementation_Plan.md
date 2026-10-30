# QueueLess 2.3 — Member 2 Detailed Implementation Plan

**Workstream:** Queue Engine, Check-in Orchestration, Counter Operations and Real-time Queue Updates  
**Project:** QueueLess 2.3  
**Primary owner:** Member 2  
**Backend stack:** FastAPI, Python, PostgreSQL, SQLAlchemy, Alembic, native WebSockets  
**Authentication:** Firebase Authentication on the client; Firebase Admin SDK token verification in the shared FastAPI authentication layer  
**Timezone:** `Asia/Kolkata` for office operating dates and display; timestamps stored as timezone-aware instants (UTC)  
**Document purpose:** A practical, implementation-level work plan for Member 2, including ownership boundaries, data model, transaction design, API contracts, queue algorithms, real-time delivery, testing, integration and delivery milestones.

---

## 1. Executive summary

Member 2 builds the operational heart of QueueLess: the part that turns an appointment or walk-in arrival into a queue token, decides which eligible citizen should be served next, lets an authorized officer operate a counter, and keeps dashboards synchronized with committed queue changes.

The workstream has five major responsibilities:

1. **Check-in orchestration:** accept a QR scan or officer-assisted manual check-in, validate the appointment and check-in window, consume the QR reference through Member 1's service boundary, and create exactly one queue token atomically.
2. **Walk-in registration:** create a walk-in queue token for an eligible office/service without inventing an appointment record.
3. **Queue state machine:** enforce valid token transitions, record timestamps and actor/reason metadata, and maintain a reliable event history.
4. **Counter operations:** let an assigned officer call the next eligible token, start service, hold/resume, complete, withdraw a call or mark a confirmed no-show.
5. **Live queue updates:** publish committed, correctly scoped events over authenticated WebSockets and provide REST resynchronization after reconnects or missed messages.

Member 2 must not duplicate Member 1's appointment or QR-reference implementation. Member 1 owns appointment persistence, booking/cancellation/rescheduling, Firebase-backed user identity mapping, authorization primitives, and QR reference creation/rotation/storage. Member 2 owns the actual consumption/check-in flow and queue token creation. The two members must agree on the check-in transaction boundary before either implementation is finalized.

The system must treat PostgreSQL as the source of truth. WebSocket messages are notifications, not authoritative state. A token must never be created twice for one appointment, a counter must not have two active called/serving tokens, and a token must not move through an invalid state transition.

## 2. Product and technical context

QueueLess is a citizen-visit preparation and physical-office queue coordination layer alongside official service portals. It helps citizens understand visit preparation, book an appointment where supported, check in at the office, and follow queue progress. It helps officers coordinate counters and helps administrators understand aggregate office demand.

QueueLess does **not** submit or approve government applications, decide legal eligibility, replace an official portal, or replace an officer's decision. A successful check-in only means that the citizen has been registered into the QueueLess office queue. It is not proof of identity or approval of the underlying government service.

### 2.1 Relevant architecture

- **Frontend:** React, Vite and Tailwind CSS.
- **Backend:** FastAPI modular monolith.
- **Database:** PostgreSQL.
- **ORM/migrations:** SQLAlchemy and Alembic.
- **Authentication:** Firebase Phone Authentication on the frontend; Firebase Admin SDK verifies ID tokens in FastAPI. Member 2 consumes the shared authenticated request context and must not implement a separate login system.
- **Real-time:** native FastAPI WebSockets with a short-lived, single-use WebSocket ticket. Never put Firebase ID tokens or other credentials in a WebSocket URL.
- **AI/document assistance:** separate workstream. It must not be a dependency for core check-in or queue operations.

### 2.2 Queue-related service modules

Suggested logical modules:

```text
backend/app/
  api/v1/
    checkin.py
    walkins.py
    queue.py
    counters.py
    realtime.py
  models/
    queue_token.py
    queue_event.py
    counter.py
    officer_assignment.py
    websocket_ticket.py
    outbox_event.py
  schemas/
    checkin.py
    walkin.py
    queue.py
    counter.py
    realtime.py
  services/
    checkin_service.py
    queue_state_service.py
    token_number_service.py
    call_next_service.py
    counter_service.py
    wait_estimate_service.py
    event_publisher.py
    websocket_ticket_service.py
  repositories/
    queue_repository.py
    counter_repository.py
    event_repository.py
  workers/
    outbox_publisher.py
  tests/
    unit/
    integration/
    concurrency/
    api/
```

Adapt this to the repository's existing structure rather than creating duplicate folders or parallel abstractions.

## 3. Member 2 ownership and boundaries

### 3.1 Member 2 owns

- `queue_tokens` persistence and queue-specific migrations, in coordination with Member 1.
- `queue_events` or equivalent immutable queue transition history.
- Walk-in token creation.
- QR check-in endpoint `POST /checkin` and the check-in orchestration service.
- Manual officer check-in endpoint `POST /appointments/{appointment_id}/check-in/manual`.
- Atomic coordination with Member 1's appointment and QR-reference services.
- Token numbering and operating-date sequence behavior.
- Queue token state machine and transition validation.
- Counter availability checks, counter locking and call-next selection.
- Counter actions: call next, start service, hold, resume, complete, withdraw call, no-show confirmation and authorized counter transfer.
- Walk-in fairness and overdue-walk-in promotion.
- Queue position and estimated-wait calculations, with transparent assumptions.
- WebSocket ticket consumption, scoped subscriptions, event publishing and reconnect/resync behavior, subject to shared authentication foundations.
- Queue-specific audit events and operational metrics.
- Unit, integration, concurrency, API and real-time tests for this workstream.

### 3.2 Member 2 does not own

| Capability | Owner | Member 2 integration responsibility |
|---|---|---|
| Firebase client sign-in and Firebase Admin token verification | Member 1/shared backend foundation | Use the shared authenticated principal; do not add custom OTP/JWT logic |
| Internal user profile, role, office and counter assignment records | Member 1/shared foundation | Use shared authorization dependencies; never trust client-supplied role/scope |
| Appointment booking, cancellation, rescheduling and slot capacity | Member 1 | Read/lock appointment data through agreed model/service contract |
| QR reference generation, hashing, storage and rotation | Member 1 | Ask the shared QR service to validate/consume a reference within the agreed transaction boundary |
| Frontend citizen/officer/admin screens | Member 3 | Publish stable API and WebSocket contracts; provide sample payloads |
| RAG, OCR, document intelligence and source verification | Member 4 | Do not block queue operations on AI/OCR availability |
| Overall QA coordination and integrated release | Member 4 / team lead as agreed | Supply tests, fixtures, logs and defect fixes for queue scope |

### 3.3 Non-negotiable ownership rule

Member 1 stores and rotates the QR reference. Member 2 consumes a currently valid reference and creates the queue token. Do not build two check-in implementations or allow two code paths to independently create queue tokens. QR and manual check-in must call the same internal transactional check-in service.

## 4. Normative QueueLess 2.3 rules Member 2 must implement

The following are product rules, not optional implementation suggestions:

1. Appointment check-in opens **15 minutes before** the appointment slot start and closes **15 minutes after** the slot start, unless a versioned office/service policy explicitly changes these values.
2. A citizen arriving after the appointment check-in window closes is not an on-time appointment check-in. The officer may offer the next available appointment or register the citizen as a walk-in at the actual arrival time.
3. QR check-in is a convenience reference, not proof of identity. Manual check-in requires an officer to confirm the citizen against the booking profile and record the officer and reason.
4. A valid appointment can create **at most one** queue token. A queue token linked to an appointment must have a unique non-null appointment link.
5. QR reference consumption and queue-token creation must be atomic. A duplicate scan must not create a second token.
6. A zero-capacity appointment slot is closed for appointment booking. Queue operations must not infer availability from theoretical capacity or create appointments themselves.
7. Queue token transitions must be validated server-side and recorded with actor, timestamp, event type and relevant reason/context.
8. A counter can have at most one token in `CALLED` or `SERVING` at a time. The counter row must be locked during call-next and relevant counter transitions.
9. A token in `CALLED` stays called while configured call attempts are made. It must not be silently changed to no-show merely because a timer elapsed.
10. A called token can become `NO_SHOW` only after the configured retry policy is exhausted and an officer confirms the no-show.
11. A counter transfer is an event, not a token status. Record old counter, new counter, actor, timestamp and reason.
12. `ON_HOLD` represents service that has already started. It must retain the assigned counter unless an authorized reassignment flow explicitly releases it. Do not implement `ON_HOLD → WAITING` as an ordinary transition.
13. WebSocket events are hints for fast UI updates, not the source of truth. REST resynchronization is required on connect/reconnect and after a detected event gap.
14. Use the versioned queue policy for walk-in fairness. Default maximum walk-in wait is **45 minutes**. The oldest overdue walk-in is promoted ahead of ordinary appointment candidates.
15. All office operating dates and token-number resets use the office's local date in `Asia/Kolkata`, not the server machine's local timezone.
16. AI, OCR, RAG, external messaging or WebSocket availability must not prevent the core database transaction for check-in or queue transitions from succeeding.

## 5. Data model and database responsibilities

Member 2 must review shared tables with Member 1 before migrations are merged. Do not independently redefine `offices`, `services`, `queue_policy`, `counters`, `users` or `appointments` if they already exist.

### 5.1 `queue_tokens`

Recommended fields:

| Field | Type / intent | Notes |
|---|---|---|
| `id` | UUID primary key | Internal token identifier |
| `public_token_number` | String | Human-readable display value, e.g. `A-023`; never use as authorization secret |
| `office_id` | UUID FK | Required |
| `service_id` | UUID FK | Required |
| `operating_date` | Date | Derived using office timezone (`Asia/Kolkata`) |
| `source` | Enum | `APPOINTMENT` or `WALK_IN` |
| `appointment_id` | UUID FK nullable | Non-null for appointment source; unique when non-null |
| `citizen_user_id` | UUID FK nullable | May be nullable for a walk-in without an account, subject to product policy |
| `citizen_display_name` | String nullable | Minimize stored personal data; use a snapshot only if required by operational UI |
| `status` | Enum | `WAITING`, `CALLED`, `SERVING`, `ON_HOLD`, `COMPLETED`, `NO_SHOW`, `CANCELLED` |
| `priority_class` | Enum/string | Appointment or walk-in classification; not a user-controlled priority |
| `checked_in_at` | timestamptz | Actual check-in time |
| `created_at` | timestamptz | Server timestamp |
| `updated_at` | timestamptz | Server timestamp |
| `called_at` | timestamptz nullable | Latest call time |
| `first_called_at` | timestamptz nullable | First call, retained across retries |
| `last_called_at` | timestamptz nullable | Latest call attempt |
| `call_attempt_count` | integer | Starts at zero; increments atomically on call/retry according to agreed policy |
| `service_started_at` | timestamptz nullable | First actual service start |
| `last_resumed_at` | timestamptz nullable | Latest resume time |
| `hold_started_at` | timestamptz nullable | Current hold start |
| `total_hold_seconds` | integer | Accumulated hold duration |
| `completed_at` | timestamptz nullable | Completion time |
| `assigned_counter_id` | UUID FK nullable | Current counter, if any |
| `promoted_for_fairness` | boolean | True if selected due to overdue walk-in policy |
| `policy_version` | integer/string | Snapshot of relevant policy version at check-in |
| `created_by_user_id` | UUID FK nullable | Officer/system actor for walk-in or check-in |
| `version` | integer | Optional optimistic version for clients; DB locking remains authoritative |

Recommended constraints/indexes:

- Unique partial index on `appointment_id WHERE appointment_id IS NOT NULL`.
- Index `(office_id, service_id, operating_date, status, checked_in_at)` for queue selection.
- Index `(assigned_counter_id, status)` for active counter-token checks.
- Check constraints for non-negative call count and hold seconds.
- Foreign keys with deliberate deletion behavior. Do not cascade-delete historical queue records when a user or counter is deactivated.
- Avoid storing full QR raw references on queue tokens.

### 5.2 `queue_events`

Append-only event history. Suggested fields:

- `id` UUID primary key.
- `queue_token_id` UUID FK.
- `office_id`, `service_id`, `counter_id` nullable context.
- `event_type` string/enum, such as `TOKEN_CREATED`, `TOKEN_CALLED`, `SERVICE_STARTED`, `TOKEN_HELD`, `TOKEN_RESUMED`, `TOKEN_COMPLETED`, `TOKEN_NO_SHOW`, `CALL_WITHDRAWN`, `COUNTER_TRANSFERRED`, `WALK_IN_PROMOTED`.
- `from_status`, `to_status` nullable.
- `actor_user_id` nullable for system-generated events.
- `reason` nullable, required for selected administrative/manual actions.
- `metadata` JSONB for bounded, non-sensitive event details.
- `created_at` timestamptz.

Events should be immutable after insertion. Correct mistakes with a compensating event, not by rewriting history. Do not put raw QR references, Firebase ID tokens, OTPs or unnecessary personal data in metadata.

### 5.3 `counters` and assignments

Coordinate with Member 1 for shared table ownership. Queue engine needs:

- `id`, `office_id`, `name/code`, `is_active`, service compatibility, operating availability and optional display order.
- `counter_services` relation to represent which services a counter can handle.
- `officer_assignments` relation connecting officer user to office/counter and effective dates/status.
- A database-enforced or transaction-enforced rule preventing a counter from having more than one active `CALLED`/`SERVING` token.

A counter is eligible only when active, staffed/assigned as required, open for the current operating block, and compatible with the token's service.

### 5.4 `queue_policy`

Member 1 owns the shared policy foundation. Member 2 consumes it. Required fields include:

- `office_id`, optional `service_id`.
- `slot_duration_minutes`.
- `walk_in_share`.
- `max_walk_in_wait_minutes` (default 45).
- `checkin_open_minutes` (default 15).
- `checkin_close_minutes` (default 15).
- call retry settings and no-show confirmation rules, if configured.
- `policy_version`, `effective_from`, `updated_by`, `updated_at`.

Queue token should snapshot the policy version applied at check-in so that later policy edits do not silently rewrite historical fairness decisions.

### 5.5 `outbox_events` (recommended)

Use a transactional outbox for reliable real-time event publication. The queue transaction writes the state change, immutable queue event and outbox row in the same database transaction. A background publisher delivers outbox rows to WebSocket subscribers and marks them published/retryable. This avoids the failure mode where a DB commit succeeds but an in-process WebSocket send fails and the update is lost.

Suggested fields: `id`, `aggregate_type`, `aggregate_id`, `office_id`, `event_type`, `payload` JSONB, `created_at`, `published_at`, `attempt_count`, `last_error` (redacted and bounded).

If the team decides not to implement a full outbox for the demo, at minimum publish only after commit and ensure clients always resync via REST. Document that process-local publication is not durable across restarts or multiple backend instances.

### 5.6 Migration order

Coordinate with Member 1. A safe order is:

1. Shared offices/services/users/policy/counters/assignments tables confirmed.
2. Queue token and queue event tables.
3. Appointment foreign key on queue token and unique partial constraint.
4. Counter active-token constraints/indexes.
5. Outbox table and supporting indexes.
6. Optional WebSocket ticket storage if the shared realtime implementation persists tickets in PostgreSQL/Redis.

Do not run separate Alembic heads from different members. Each migration must be reviewed and merged into the team's single migration chain.

## 6. Queue token lifecycle and state machine

### 6.1 States

| State | Meaning |
|---|---|
| `WAITING` | Citizen is checked in and waiting for an officer to call them |
| `CALLED` | Token has been called to a counter; retry attempts may be in progress |
| `SERVING` | Officer has started handling the citizen's service |
| `ON_HOLD` | Service began but is temporarily paused; counter remains assigned unless explicitly released by authorized transfer |
| `COMPLETED` | Service interaction at the office is finished |
| `NO_SHOW` | Officer confirmed the citizen did not respond after configured call attempts, or other explicitly defined no-show path |
| `CANCELLED` | Token was cancelled through an authorized operational path; preserve the reason and actor |

### 6.2 Allowed transitions

```text
                 call-next
   WAITING ----------------------> CALLED
      ^                              |  \
      |                              |   \ retries exhausted + officer confirms
      | explicit withdraw/reset      |    \
      +------------------------------+     v
                                     |   NO_SHOW
                                     |
                              officer starts
                                     v
                                  SERVING
                                  /     \
                           hold /       \ complete
                                v         v
                             ON_HOLD   COMPLETED
                                |
                             resume
                                v
                             SERVING
```

Rules:

- `WAITING → CALLED`: only through the atomic call-next operation.
- `CALLED → WAITING`: only through an explicit call withdrawal/reset with reason and audit event. This is not an automatic retry side effect.
- `CALLED → SERVING`: officer starts service at the assigned counter.
- `CALLED → NO_SHOW`: only after configured retry attempts are exhausted and officer confirms.
- `SERVING → ON_HOLD`: officer action with optional/required reason according to policy.
- `ON_HOLD → SERVING`: officer resumes the same service.
- `SERVING → COMPLETED`: officer completes service.
- `ON_HOLD → COMPLETED`: allowed only if the officer is explicitly completing a held service, with event history preserved.
- Counter transfer is a separate event and assignment change, not a status transition.
- No ordinary transition may resurrect `COMPLETED`, `NO_SHOW` or `CANCELLED` tokens. If correction is necessary, use a privileged, audited administrative correction workflow.

### 6.3 Central transition service

All state changes must go through one service, for example:

```python
transition_token(
    db,
    token_id,
    target_status,
    actor,
    reason=None,
    counter_id=None,
    expected_status=None,
)
```

The service should:

1. Load and lock the token row (`SELECT ... FOR UPDATE`).
2. Confirm current status and requested transition are compatible.
3. Confirm actor authorization and office/counter scope.
4. Confirm counter invariants if a counter is involved.
5. Apply timestamp updates consistently.
6. Update accumulated hold duration where appropriate.
7. Insert immutable `queue_events` row.
8. Insert outbox event row in the same transaction.
9. Commit before any external WebSocket delivery.
10. Return the authoritative updated token representation.

Do not scatter raw `token.status = ...` assignments across route handlers.

## 7. Check-in orchestration

Check-in is the most sensitive integration boundary between Member 1 and Member 2. It must guarantee one current QR reference can be consumed once and one appointment can produce at most one queue token.

### 7.1 QR check-in API

`POST /api/v1/checkin`

Request:

```json
{
  "reference": "<opaque-raw-reference>"
}
```

The QR path intentionally does not require the officer to know or submit an appointment ID. The backend resolves the appointment from the hashed opaque reference through Member 1's QR service. Require an authenticated officer and enforce office assignment server-side.

Success response example:

```json
{
  "token": {
    "id": "<uuid>",
    "public_token_number": "A-023",
    "status": "WAITING",
    "source": "APPOINTMENT",
    "service_id": "<uuid>",
    "office_id": "<uuid>",
    "checked_in_at": "2026-10-30T04:30:00Z"
  },
  "appointment_status": "CHECKED_IN"
}
```

Do not return the raw QR reference or internal security metadata.

### 7.2 Manual officer check-in API

`POST /api/v1/appointments/{appointment_id}/check-in/manual`

Request:

```json
{
  "confirmation": true,
  "reason": "Citizen identity and booking details checked at counter"
}
```

Requirements:

- Officer must be assigned to the appointment's office.
- `confirmation` must be true.
- Reason must be non-empty and bounded in length.
- Officer confirms the citizen against the booking profile using the operational process.
- Record officer actor, reason, timestamp and audit event.
- Both QR and manual paths call the same internal transactional service.

### 7.3 Check-in transaction sequence

The desired logical transaction is:

1. Authenticate officer using the shared Firebase-backed FastAPI request principal.
2. Confirm officer is active and has check-in permission for the appointment's office.
3. Begin database transaction.
4. For QR path, lock and validate the QR reference using Member 1's agreed service/repository boundary. For manual path, lock appointment directly.
5. Lock appointment row.
6. Confirm appointment belongs to the office/service and is in `BOOKED` state.
7. Confirm check-in window is open using server time and the office policy. It opens 15 minutes before and closes 15 minutes after slot start by default.
8. Confirm appointment is not already checked in and no queue token already references it.
9. Validate any QR reference has not expired, been rotated, been consumed or been revoked.
10. Allocate the next token number for the office/service/operating date.
11. Create one `queue_tokens` row with source `APPOINTMENT`, status `WAITING`, appointment link and policy version.
12. Mark QR reference consumed and appointment `CHECKED_IN` through the shared agreed transaction boundary.
13. Insert queue event, audit event and outbox event.
14. Commit.
15. Publish the committed event asynchronously.

**Critical:** A sequence that performs step 11 in one committed transaction and step 12 in another is not acceptable. If Member 1 and Member 2 use separate service functions, they must share the same SQLAlchemy session/transaction or use a rigorously designed database-level transaction boundary. Avoid an HTTP call from one backend module to another for a same-process database operation.

### 7.4 Duplicate and concurrent scans

Two officers may scan the same QR nearly simultaneously. Protect against this at multiple levels:

- Lock the QR-reference row.
- Lock the appointment row.
- Enforce unique `queue_tokens.appointment_id` where non-null.
- Enforce one-time reference consumption.
- Catch `IntegrityError` and map it to a stable `ALREADY_CHECKED_IN` response after rolling back the failed transaction.
- Return the existing token only if the product contract explicitly permits idempotent replay to the same authorized office. Otherwise return a conflict with a safe message. Agree this behavior with Member 1 and Member 3 before frontend implementation.

Never rely only on an in-memory mutex. It fails across processes and restarts.

### 7.5 Check-in window and late arrivals

- Use the appointment slot start instant and configured policy offsets.
- Compare timezone-aware timestamps.
- If before opening, return `CHECKIN_NOT_OPEN`.
- If after closing, return `CHECKIN_WINDOW_CLOSED` and guide officer to offer next slot or register walk-in.
- Do not silently convert an expired appointment into a walk-in without officer confirmation and a separate walk-in creation request.

### 7.6 Walk-in creation API

`POST /api/v1/queue/tokens`

Request example:

```json
{
  "office_id": "<uuid>",
  "service_id": "<uuid>",
  "citizen": {
    "display_name": "Citizen name"
  },
  "reason": "Walk-in visit"
}
```

Only an authorized officer/front-desk role may create walk-ins. The backend must:

- Derive actor, office scope and permissions from the authenticated principal/database.
- Validate the office and service are active and available.
- Validate the service is supported by the office and at least one eligible counter exists for current operations.
- Enforce any configured walk-in intake rules. The 20% walk-in share is a planning allocation used for appointment slot capacity and reporting, not a promise that a fixed number of walk-ins will be served.
- Allocate token number atomically for the operating date.
- Create `WAITING` token with source `WALK_IN`, actual `checked_in_at`, actor and policy version.
- Record event/audit/outbox row.
- Return the created token.

Do not block walk-in intake solely because the appointment planning reserve is used up unless the office policy explicitly defines a hard intake cap. The policy describes planning share and fairness; it is not automatically a hard rejection threshold.

## 8. Token numbering and operating date

### 8.1 Requirements

- Token number is a human-facing queue label, not a security credential.
- Sequence scope must be agreed: recommended `(office_id, service_id, operating_date)` or `(office_id, operating_date)` with service prefixes. Do not let each API worker generate numbers independently.
- Operating date is computed in `Asia/Kolkata` from the authoritative check-in instant.
- Reset sequence by operating date, not UTC date.
- Number allocation must be concurrency-safe.

### 8.2 Recommended implementation

Use a `token_sequences` table with a unique key over the sequence scope and an atomic upsert/increment, or use a PostgreSQL sequence per scope only if lifecycle management is acceptable. A row-based counter is easier to reason about for per-office/per-day numbering.

Pseudo-flow:

```sql
INSERT INTO token_sequences (office_id, service_id, operating_date, last_value)
VALUES (:office_id, :service_id, :operating_date, 1)
ON CONFLICT (office_id, service_id, operating_date)
DO UPDATE SET last_value = token_sequences.last_value + 1
RETURNING last_value;
```

The allocation must occur inside the same transaction that creates the token. If token creation fails, sequence gaps are acceptable unless the product explicitly requires gapless numbers. Prefer operational correctness over gapless numbering.

## 9. Counter operations

### 9.1 Counter eligibility

A counter is eligible only when all relevant conditions hold:

- Counter is active.
- Counter belongs to the target office.
- Counter supports the token's service.
- Counter is currently within operating hours and not in a configured break/unavailable period.
- Officer is active and assigned to that counter/office for the current period.
- Counter has no token in `CALLED` or `SERVING`.
- Any service-specific or staffing constraints are satisfied.

Do not count a counter simply because its row exists. Use current eligibility, not stale frontend data.

### 9.2 Call-next endpoint

`POST /api/v1/counters/{counter_id}/call-next`

Request may include optional service filter only if the counter supports multiple services and the policy permits officer selection. Do not accept arbitrary token ID from the client as the call-next candidate.

Transaction algorithm:

1. Authenticate officer and validate assignment to the counter.
2. Begin transaction.
3. Lock counter row using `SELECT ... FOR UPDATE`.
4. Confirm counter active, staffed, available and service-compatible.
5. Confirm no token is currently `CALLED` or `SERVING` on this counter.
6. Select eligible `WAITING` tokens in the counter's office/service scope.
7. Apply overdue walk-in fairness rule (Section 10).
8. Lock the selected token row (`FOR UPDATE SKIP LOCKED` may be used for safe parallel candidate selection, but must not weaken counter locking or fairness semantics).
9. Revalidate selected token remains `WAITING` and eligible.
10. Change token to `CALLED`, assign counter, set call timestamps and increment attempt count.
11. Insert queue event and outbox event, including whether fairness promotion occurred and policy version.
12. Commit.
13. Publish event asynchronously.

If no eligible token exists, return `NO_WAITING_TOKENS` with a clear, non-error operational response. If counter is occupied, return `COUNTER_BUSY`.

### 9.3 Avoid double calls

The counter row lock serializes two officers/requests trying to call next on the same counter. Also consider a partial unique index or exclusion strategy to prevent multiple active tokens per counter. Use both transactional logic and database constraints where possible.

### 9.4 Call attempts and missed-call handling

- A call creates/updates `first_called_at`, `last_called_at` and `call_attempt_count`.
- Retry policy must be explicit and configurable; do not invent an unapproved retry count or timeout.
- A token remains `CALLED` while retries are attempted.
- If the citizen appears, officer starts service.
- If the citizen does not respond after retries, officer explicitly confirms no-show. Then transition to `NO_SHOW` and release counter.
- If officer withdraws a call for a reason, transition `CALLED → WAITING` and record the reason.
- Do not automatically mark no-show just because `last_called_at` is old.

### 9.5 Start service

`POST /api/v1/queue/tokens/{token_id}/start`

- Token must be `CALLED` and assigned to the officer's counter.
- Officer must be assigned to that counter.
- Lock token and counter.
- Change to `SERVING`; set `service_started_at` once; insert event/outbox.

### 9.6 Hold and resume

`POST /api/v1/queue/tokens/{token_id}/hold`

`POST /api/v1/queue/tokens/{token_id}/resume`

Hold:
- Only from `SERVING`.
- Record `hold_started_at`, reason where required, actor and event.
- Keep counter assigned by default.

Resume:
- Only from `ON_HOLD`.
- Calculate held duration and add to `total_hold_seconds`.
- Clear `hold_started_at`, set `last_resumed_at`, return to `SERVING`.
- Preserve the counter assignment.

If a real operational case requires releasing the counter while a token is on hold, implement a separate privileged reassignment/release workflow with explicit events. Do not silently detach the token.

### 9.7 Complete service

`POST /api/v1/queue/tokens/{token_id}/complete`

- Allowed from `SERVING`, and optionally `ON_HOLD` only through an explicit officer completion action.
- Record `completed_at` and finalize any open hold interval.
- Release counter assignment.
- Insert `TOKEN_COMPLETED` event and outbox row.
- Return authoritative token and counter status.

### 9.8 Withdraw call and confirm no-show

`POST /api/v1/queue/tokens/{token_id}/withdraw-call`

`POST /api/v1/queue/tokens/{token_id}/no-show`

Both require an assigned officer, reason or confirmation data as specified by policy, row locks and audit events. No-show must validate the retry policy and that the token is still `CALLED`.

### 9.9 Counter transfer

Implement only if required for the demo, but design the event schema now. Transfer should:

- Require authorized officer/supervisor permission for both counters.
- Lock old and new counter rows in deterministic UUID order to avoid deadlocks.
- Lock token row.
- Validate token state and new counter eligibility.
- Ensure target counter is not busy.
- Update `assigned_counter_id`.
- Insert `COUNTER_TRANSFERRED` event with old counter, new counter, actor, timestamp and reason.
- Not create a fake token status called `TRANSFERRED`.

## 10. Walk-in fairness and next-token selection

### 10.1 Policy

Default `max_walk_in_wait_minutes = 45`. If any eligible walk-in has waited at least that long, the oldest overdue walk-in is promoted ahead of ordinary appointment candidates. This prevents walk-ins from waiting indefinitely behind a continuous stream of appointments.

### 10.2 Candidate ordering

Within the locked counter transaction:

1. Filter waiting tokens to same office, service compatibility and operating date/current queue scope.
2. Identify eligible walk-ins where `now - checked_in_at >= max_walk_in_wait_minutes`.
3. If one or more overdue walk-ins exist, select the oldest by `checked_in_at`, then `created_at`, then stable token ID. Mark `promoted_for_fairness = true` and record `WALK_IN_PROMOTED`/call event metadata.
4. Otherwise select the next eligible appointment token according to appointment slot order and check-in order. Confirm exact tie-break order with Member 1/3 and encode it in tests.
5. If no eligible appointment exists, select the oldest walk-in by `checked_in_at`, then `created_at`, then token ID.
6. If no eligible token exists, return no-waiting result.

The event and dashboard should expose `walk_in_wait_minutes`, `promoted_for_fairness` and policy version. If an office disables the cap, the UI must show an explicit warning that strict appointment priority can create unbounded walk-in waits. Do not claim a guaranteed wait time.

### 10.3 Fairness edge cases

Test:
- Several overdue walk-ins: oldest first.
- A walk-in crosses the 45-minute threshold between calls: eligible on the next call-next transaction.
- Appointment and walk-in tie timestamps: deterministic tie-break.
- Token belongs to a service the counter cannot handle: excluded.
- Token cancelled/no-show/completed: excluded.
- Policy version changes during the day: tokens retain the policy snapshot/version agreed for their queue decision.
- Counter busy: no candidate is assigned until the counter becomes available.

## 11. Queue position and estimated wait

Queue position and estimated wait are estimates, not guarantees. Keep the calculation transparent and deterministic.

A reasonable baseline is:

`estimated_wait_minutes = total_expected_work_of_eligible_tokens_ahead / active_eligible_counters`

Implementation guidance:

- Count only tokens eligible for the same service/counter pool.
- Exclude cancelled, completed and no-show tokens.
- Account for tokens already being served and their expected remaining time only if a reliable duration estimate exists; otherwise label the estimate as a rough queue estimate.
- Exclude counters unavailable or unable to serve the service.
- Include the configured average service duration and any explicit policy adjustment.
- Return `estimated_wait_minutes`, `queue_position`, `active_eligible_counters` and `last_updated_at`.
- Do not expose other citizens' full names or personal data in public queue views.
- Do not present a precise arrival guarantee. UI wording should say “estimated” and display last-updated time.

If the team has no defensible service-duration baseline, ship queue position first and label wait time as approximate or unavailable. Do not fabricate accuracy.

## 12. Real-time updates and WebSockets

### 12.1 Events to publish

At minimum:

- `queue.token_created`
- `queue.token_called`
- `queue.service_started`
- `queue.token_held`
- `queue.token_resumed`
- `queue.token_completed`
- `queue.token_no_show`
- `queue.call_withdrawn`
- `queue.counter_transferred`
- `queue.counter_status_changed`
- `queue.wait_estimate_updated` (only if the team implements recalculation)

Each event should include:

- Stable event ID and monotonically increasing office/stream sequence if implemented.
- Event type and schema version.
- `office_id`, optional `service_id`, optional `counter_id`.
- Queue token public ID/reference safe for the recipient.
- Changed status and event timestamp.
- Minimal metadata required by that audience.

Never broadcast Firebase tokens, raw QR references, internal secrets, or full citizen profiles.

### 12.2 Authentication

- REST request authenticates through the shared Firebase ID-token verification dependency.
- Client requests a short-lived, single-use WebSocket ticket through an authenticated REST endpoint.
- Ticket is scoped to user, role, office and allowed counter/service subscriptions.
- Ticket expires quickly and is consumed once.
- WebSocket URL must not contain Firebase ID token or other credentials.
- On connection, consume ticket, validate scope and bind socket to authorized rooms.
- Close or reauthorize sockets when user is deactivated or assignment scope changes, according to the team's session policy.

### 12.3 Event publication

Preferred:

1. API transaction writes queue state, queue event and outbox event.
2. Commit.
3. Publisher reads pending outbox rows.
4. Publisher sends event to relevant office/counter/user subscribers.
5. Publisher marks row published or schedules retry.

If using process-local connection managers for the hackathon, document that multiple worker instances require a shared broker (e.g. Redis pub/sub) or another cross-process fan-out. Do not assume in-memory connection maps work across multiple Uvicorn workers.

### 12.4 Reconnect and resynchronization

On socket connect/reconnect:

- Client fetches authoritative queue snapshot through REST.
- Client subscribes to the authorized stream using the one-time ticket.
- If event IDs/sequences reveal a gap, client fetches REST snapshot again.
- If socket drops, UI marks data stale and shows last-updated time.
- WebSocket is not used to mutate queue state; mutations go through REST APIs.

### 12.5 Suggested WebSocket ticket endpoint

`POST /api/v1/realtime/tickets`

Request:

```json
{
  "scope": {
    "office_id": "<uuid>",
    "counter_id": "<uuid>"
  }
}
```

The server derives the user's maximum allowed scope and rejects any requested scope outside it. The returned ticket is short-lived, single-use and opaque. Keep ticket persistence/consumption atomic. Never trust the browser's requested scope without checking the database assignment.

## 13. API contract summary

Exact prefixes and naming should be aligned with the shared API convention before frontend integration.

| Method | Endpoint | Purpose | Primary authorization |
|---|---|---|---|
| `POST` | `/api/v1/checkin` | QR scan check-in | Active officer assigned to appointment office |
| `POST` | `/api/v1/appointments/{id}/check-in/manual` | Manual officer check-in | Active officer assigned to appointment office |
| `POST` | `/api/v1/queue/tokens` | Create walk-in token | Authorized front-desk/officer role and office scope |
| `GET` | `/api/v1/queue/tokens/{id}` | Read token detail | Citizen owner or authorized office staff |
| `GET` | `/api/v1/offices/{office_id}/queue` | Office queue snapshot | Authorized office staff; citizen view must be privacy-filtered |
| `GET` | `/api/v1/counters/{counter_id}/queue` | Counter queue/active token | Assigned officer or supervisor |
| `POST` | `/api/v1/counters/{counter_id}/call-next` | Call next eligible token | Officer assigned to counter |
| `POST` | `/api/v1/queue/tokens/{id}/start` | Start service | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/hold` | Hold active service | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/resume` | Resume held service | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/complete` | Complete service | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/withdraw-call` | Return called token to waiting | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/no-show` | Confirm no-show after retries | Officer assigned to token counter |
| `POST` | `/api/v1/queue/tokens/{id}/transfer` | Transfer to another counter | Authorized officer/supervisor for both counters |
| `GET` | `/api/v1/queue/tokens/{id}/position` | Position and wait estimate | Citizen owner or authorized staff |
| `POST` | `/api/v1/realtime/tickets` | Create one-time WebSocket ticket | Authenticated user, server-validated scope |

### 13.1 Standard error codes

Use stable machine-readable error codes and consistent response shape:

```json
{
  "error": {
    "code": "COUNTER_BUSY",
    "message": "This counter already has an active token.",
    "request_id": "<correlation-id>"
  }
}
```

Recommended codes:

- `UNAUTHENTICATED`
- `FORBIDDEN`
- `OFFICE_SCOPE_DENIED`
- `COUNTER_ASSIGNMENT_REQUIRED`
- `INVALID_QR_REFERENCE`
- `QR_REFERENCE_EXPIRED`
- `QR_REFERENCE_ALREADY_USED`
- `APPOINTMENT_NOT_FOUND`
- `APPOINTMENT_NOT_BOOKED`
- `CHECKIN_NOT_OPEN`
- `CHECKIN_WINDOW_CLOSED`
- `ALREADY_CHECKED_IN`
- `WALKIN_NOT_ALLOWED`
- `NO_ELIGIBLE_COUNTER`
- `COUNTER_BUSY`
- `COUNTER_UNAVAILABLE`
- `NO_WAITING_TOKENS`
- `INVALID_TOKEN_TRANSITION`
- `TOKEN_NOT_ASSIGNED_TO_COUNTER`
- `CALL_RETRY_POLICY_NOT_MET`
- `IDEMPOTENCY_CONFLICT`
- `WEBSOCKET_TICKET_EXPIRED`
- `WEBSOCKET_TICKET_ALREADY_USED`

Use appropriate HTTP status codes: 400 for malformed input, 401 for invalid/missing authentication, 403 for authenticated but unauthorized, 404 where resource disclosure policy allows, 409 for state/concurrency conflicts, 422 for schema validation, and 5xx for unexpected failures. Do not expose raw SQL errors or Firebase verification details.

## 14. Authorization and privacy

Member 2 must use shared authorization dependencies from Member 1. Authentication proves who the caller is; database-backed authorization proves what they can do.

Rules:

- Citizen may read only their own token/appointment information, subject to privacy policy.
- Officer may operate only assigned office/counter resources.
- Supervisor/admin privileges must be explicitly represented in PostgreSQL and scoped to the correct office.
- Do not accept `role`, `office_id`, `counter_id`, `actor_user_id` or `is_admin` as authoritative client values.
- For a walk-in, office scope comes from the officer's authorized assignment or an explicitly allowed office selection validated by the server.
- Do not include citizen phone numbers, document details or full identity data in office-wide WebSocket events.
- Do not expose queue token IDs as authorization credentials.
- Rate-limit check-in and state-mutating endpoints where appropriate; log actor, route, result and request ID without logging raw QR values or auth tokens.

## 15. Idempotency, concurrency and reliability

### 15.1 Idempotency

For check-in and walk-in creation, support an `Idempotency-Key` header if the team has standardized this mechanism. Store key, actor, endpoint/scope, request hash, response reference and expiry. Reusing a key with a different payload must return `IDEMPOTENCY_CONFLICT`. Idempotency complements database constraints; it does not replace them.

### 15.2 Concurrency safeguards

| Race condition | Required safeguard |
|---|---|
| Two QR scans for same appointment | Lock QR ref + appointment; unique appointment link; one-time consumption |
| QR rotation while old QR is scanned | Serialize on QR reference/appointment row; only current unused ref may be consumed |
| Two officers call next on same counter | Lock counter row; enforce one active token per counter |
| Two counters select same waiting token | Lock candidate token; revalidate status; use safe candidate selection |
| Two walk-ins receive same number | Atomic token sequence row/upsert |
| Complete and hold happen together | Lock token; validate current status before transition |
| Counter transfer overlaps call-next | Lock both counters in deterministic order and token row |
| DB commit succeeds but socket send fails | Transactional outbox and REST resync |
| Worker restarts during event send | Outbox retry; idempotent event delivery or client event de-duplication |

### 15.3 Transaction boundaries

Keep each business action in a single database transaction wherever possible:

- Check-in: QR consume + appointment status update + queue token + queue event + outbox.
- Walk-in: token sequence + queue token + event + outbox.
- Call-next: counter lock + token selection/lock + state update + event + outbox.
- Start/hold/resume/complete/no-show: token/counter locks + state/timing update + event + outbox.
- Transfer: both counter locks + token lock + assignment update + event + outbox.

Never hold database locks while sending WebSocket messages, calling external APIs or running AI/OCR operations.

## 16. Observability and audit

Every mutating request should carry a request/correlation ID. Log:

- Request ID, actor internal user ID, office/counter scope, endpoint, action, result code and duration.
- Token ID and appointment ID where permitted.
- State transition from/to and event ID.
- Lock wait/transaction duration for concurrency-sensitive operations.
- Outbox publish attempts and failures.
- WebSocket connection, ticket consumption, subscription scope and disconnect reason.

Do not log raw QR references, Firebase ID tokens, phone OTPs, passwords, full document contents or sensitive citizen details.

Metrics worth collecting:

- Check-ins by QR/manual path and success/failure reason.
- Walk-ins created.
- Duplicate check-in attempts.
- Average/median wait time and service duration, with clear inclusion rules.
- Call attempts and confirmed no-shows.
- Walk-ins promoted for fairness.
- Counter utilization and unavailable time.
- Queue event publication lag and outbox backlog.
- WebSocket reconnect count and resync frequency.

Report appointment no-shows separately from queue-token no-shows. Do not include cancelled/no-show tokens in completed-service duration metrics. Define whether wait-time averages use first call or actual service start; recommended waiting time ends at `service_started_at`, so repeated calls do not understate waiting.

## 17. Testing strategy and acceptance criteria

### 17.1 Unit tests

- Every allowed and forbidden state transition.
- Timestamp updates for call/start/hold/resume/complete.
- Hold duration accumulation.
- Walk-in overdue threshold and tie-breaking.
- Counter eligibility rules.
- Token-number formatting and operating-date calculation in `Asia/Kolkata`.
- Queue position and estimated-wait calculation with documented assumptions.
- Event payload privacy filtering.

### 17.2 Integration tests

- QR reference valid and appointment in window creates one token.
- QR reference invalid/expired/rotated/used is rejected.
- Manual check-in requires officer assignment, confirmation and reason.
- Appointment outside check-in window is rejected with the correct code.
- Already checked-in appointment cannot create another token.
- Walk-in creation validates office/service/actor scope.
- Call-next only chooses tokens for eligible counters.
- Officer cannot operate another officer's counter.
- Hold/resume preserves counter assignment.
- Completion releases counter.
- No-show requires retry policy and officer confirmation.
- Transfer records old/new counter and reason.
- WebSocket ticket is single-use, short-lived and scope-limited.
- Reconnect obtains a fresh snapshot and does not rely on replaying every socket event.

### 17.3 Concurrency tests (mandatory)

Run actual concurrent transactions against PostgreSQL, not only mocked repository calls:

1. Fire at least 10 concurrent QR check-ins for one appointment. Exactly one queue token must exist.
2. Rotate QR while another transaction attempts to consume the old reference. Only the valid serialized outcome may succeed; no duplicate token or partial state.
3. Send multiple simultaneous call-next requests to one counter. At most one token becomes `CALLED`/`SERVING` on that counter.
4. Send simultaneous call-next requests to different counters with one waiting token. That token is assigned to at most one counter.
5. Create many walk-ins concurrently. Token numbers must be unique within the agreed scope.
6. Race complete against hold/resume. Exactly one valid transition succeeds; the other receives a conflict.
7. Race transfer against call-next. No counter ends with multiple active tokens and no token is assigned to two counters.

### 17.4 Real-time tests

- Event emitted only after DB commit.
- Rollback emits no event.
- Outbox retries failed publication.
- Unauthorized user cannot subscribe to another office/counter.
- Expired/replayed WebSocket ticket is rejected.
- Client can resync after socket disconnect or missed event.
- Sensitive fields are absent from payloads.

### 17.5 Acceptance checklist

- [ ] QR check-in endpoint does not accept appointment ID as a substitute for opaque QR reference.
- [ ] Manual check-in is a separate officer-confirmed endpoint.
- [ ] QR and manual check-in share one transactional service.
- [ ] Check-in window defaults to -15/+15 minutes from slot start.
- [ ] Appointment can create at most one queue token, enforced by DB constraint.
- [ ] Walk-in token creation is office/service scoped and audited.
- [ ] Token number generation is concurrency-safe and uses `Asia/Kolkata` operating date.
- [ ] Queue state transitions are centralized and validated.
- [ ] Counter call-next locks the counter and selected token.
- [ ] Counter cannot have two active called/serving tokens.
- [ ] Overdue walk-in fairness defaults to 45 minutes and is deterministic.
- [ ] No-show requires configured retry policy and officer confirmation.
- [ ] Hold/resume preserves the counter by default.
- [ ] Counter transfer is an event with old/new counter and reason.
- [ ] Queue events and outbox rows are written in the state-change transaction.
- [ ] WebSocket authentication uses short-lived single-use tickets, never Firebase token in URL.
- [ ] REST snapshot/resync works after reconnect.
- [ ] Role, office and counter permissions are read from PostgreSQL, not browser payload.
- [ ] No raw QR reference or Firebase token appears in logs or events.
- [ ] Concurrency tests pass against PostgreSQL.

## 18. Suggested 20-working-day implementation schedule

Adjust to the team's actual hackathon calendar. Do not skip the integration and concurrency days to add cosmetic features.

| Day | Focus | Deliverable / exit condition |
|---|---|---|
| 1 | Ownership and API agreement | Signed-off boundary with Member 1; check-in transaction contract; shared IDs/status enums agreed |
| 2 | Schema design | Queue token/event/counter/sequence/outbox ERD and migration review |
| 3 | Migrations and models | Alembic migration merged into shared chain; SQLAlchemy models and constraints |
| 4 | State machine core | Central transition service and unit tests for all allowed/forbidden transitions |
| 5 | Token numbering | `Asia/Kolkata` operating date and concurrent-safe token sequence tests |
| 6 | QR check-in integration | `POST /checkin` with shared QR consume service and transaction boundary |
| 7 | Manual check-in | Manual endpoint, reason/audit handling and office-scope tests |
| 8 | Walk-in intake | Walk-in token creation and validation; event/outbox integration |
| 9 | Call-next core | Counter locking, candidate selection, counter-busy checks |
| 10 | Fairness | 45-minute overdue walk-in promotion, deterministic ordering and tests |
| 11 | Service actions | Start, hold, resume and complete endpoints with timing fields |
| 12 | Retry/no-show | Call withdrawal, retry count and officer-confirmed no-show flow |
| 13 | Counter transfer | Transfer workflow if in demo scope; otherwise document deferred state |
| 14 | Queue read APIs | Office/counter snapshots, token detail, queue position and estimated wait |
| 15 | Realtime auth | Single-use WebSocket ticket and scope validation |
| 16 | Realtime delivery | Event publisher/outbox, room routing and payload privacy |
| 17 | Reconnect/resync | REST snapshot recovery and event gap handling |
| 18 | Concurrency/security | PostgreSQL race tests, authorization tests, rate limits and log redaction |
| 19 | Frontend integration | Member 3 integration, API payload fixes, officer/citizen demo workflow |
| 20 | Stabilization/handoff | QA run, bug fixes, API docs, seed data, deployment notes and handoff |

### Priority guidance

**P0 (must work for demo):** QR/manual check-in, walk-in registration, one-token-per-appointment, token numbering, `WAITING → CALLED → SERVING → COMPLETED`, counter locking, 45-minute walk-in fairness, authorization, basic REST queue snapshot, WebSocket ticket and essential live events.

**P1 (should work if schedule permits):** hold/resume, retry/no-show, durable outbox, detailed wait estimates, counter transfer, richer queue analytics.

**P2 (defer unless explicitly required):** multi-instance Redis fan-out, sophisticated predictive wait estimation, automated no-show inference, voice notifications, ML-based queue optimization. Never replace the explicit rules with ML guesses.

## 19. Integration contract with other members

### 19.1 With Member 1

Before implementation, agree on:

- SQLAlchemy session/transaction sharing for QR consume + appointment update + token creation.
- QR-reference service function signature and lock semantics.
- Whether QR reference is marked consumed by Member 1's repository function inside the caller's transaction.
- Appointment fields exposed to Member 2: ID, office/service IDs, citizen user ID, status, slot start, check-in open/close instants, policy version and timezone.
- Appointment state update to `CHECKED_IN` and allowed status transition.
- Shared authorization dependencies: current user, role, office scope, counter assignment.
- Ownership and migration strategy for shared `counters`, `queue_policy`, `audit_events` and `officer_assignments` tables.
- Duplicate QR scan response behavior.

Suggested internal interface (illustrative; agree exact naming):

```python
# Must use the caller's SQLAlchemy session and current transaction.
appointment = await appointment_service.lock_for_checkin(
    db=db,
    appointment_id=appointment_id,
)

qr_reference = await qr_service.lock_and_validate_reference(
    db=db,
    raw_reference=raw_reference,
    appointment_id=appointment.id,
)

await qr_service.consume_reference(db=db, reference=qr_reference)
await appointment_service.mark_checked_in(db=db, appointment=appointment)
# Member 2 creates queue token + queue event + outbox in the same transaction.
```

The exact API may differ. The key requirement is one shared database transaction and no raw reference persistence in Member 2's queue tables.

### 19.2 With Member 3 (frontend)

Provide:

- OpenAPI endpoint list and example success/error payloads.
- Queue token response shape and public token number format.
- State enum and transition behavior.
- Officer permissions and counter-scoped APIs.
- WebSocket ticket request/connection handshake and event schema.
- Queue snapshot REST endpoint for initial load and reconnect.
- UI privacy rules for citizen versus officer/admin views.

Frontend must not optimistically assume a state transition succeeded. It should update from REST response or committed event, and resync when uncertain.

### 19.3 With Member 4 (AI/QA/integration)

Provide:

- Seed office/service/counter/officer/citizen data.
- Unit/integration/concurrency test commands.
- Known limitations and deferred P1/P2 features.
- Event schema and sample queue traces.
- Metrics definitions for wait/service/no-show/fairness.
- Stable staging endpoints and test credentials created through approved Firebase/project setup.

AI/OCR modules may consume appointment/queue context only through authorized service APIs. Queue state changes must not depend on AI outputs.

## 20. Repository and Git workflow

- Work on a dedicated branch, e.g. `feature/member-2-queue-engine`.
- Avoid editing Member 1's auth/appointment/QR files unless a coordinated interface change is agreed.
- Avoid editing Member 3 frontend files except for a reviewed contract example or shared type definition.
- Keep migrations small and coordinate a single Alembic head.
- Add tests with every state-changing endpoint.
- Open small PRs: schema/models, check-in, walk-in, state machine, counter operations, realtime.
- Require one teammate review for transaction/locking code.
- Before merging, run formatting, lint, unit tests, integration tests and migration upgrade/downgrade checks.
- Do not commit Firebase service account JSON, `.env`, real citizen data, raw QR references or production logs.

Suggested commit sequence:

```text
feat(queue): add queue token and event schema
feat(queue): add operating-date token sequence
feat(checkin): add atomic QR check-in orchestration
feat(checkin): add manual officer check-in
feat(queue): add walk-in token creation
feat(queue): add centralized token state machine
feat(counters): add locked call-next selection
feat(queue): enforce overdue walk-in fairness
feat(counters): add service lifecycle actions
feat(realtime): add scoped websocket tickets and events
test(queue): add postgres concurrency and authorization coverage
```

## 21. Definition of done for Member 2

Member 2's workstream is complete when:

1. All P0 queue and check-in flows are implemented and integrated with Member 1's Firebase-backed authentication and appointment/QR services.
2. Queue and counter database constraints prevent duplicate appointment tokens and multiple active tokens on one counter.
3. All state transitions go through the central transition service.
4. QR/manual check-in share a single transactional path and are covered by duplicate/concurrent request tests.
5. Walk-in fairness is deterministic and has a test for the 45-minute threshold.
6. Officer operations enforce office/counter assignments from PostgreSQL.
7. WebSocket tickets are short-lived, single-use and scoped; Firebase tokens are never placed in URLs.
8. Clients can recover authoritative state through REST after disconnect.
9. Queue events, audit history and metrics are documented and do not leak sensitive data.
10. Member 3 can complete a citizen check-in and officer counter workflow using the documented API without relying on mocked responses.
11. Member 4 can run the test suite and reproduce the acceptance checks.
12. Known limitations and deferred features are documented honestly.

## 22. First actions: what Member 2 should do now

1. **Meet Member 1 before writing check-in code.** Finalize the shared transaction contract for QR consumption, appointment locking/status update and queue token creation. This is the highest-risk integration decision.
2. **Review the current repository and existing migrations.** Confirm whether queue/counter/policy models already exist. Extend them instead of duplicating them.
3. **Write the queue ERD and state-transition table.** Get agreement from all members on status names, event names, API routes and ownership.
4. **Implement schema and constraints first.** The unique appointment-token constraint and counter-active-token protection are foundational.
5. **Build the central transition service and tests before route handlers.** This prevents inconsistent state changes across endpoints.
6. **Implement check-in and walk-in creation.** Prove that one appointment creates one token and that walk-ins receive safe token numbers.
7. **Implement call-next with database locks.** Do not use in-memory locks as the concurrency solution.
8. **Integrate WebSockets only after database events are reliable.** Use one-time tickets and REST resync; do not let socket delivery become the source of truth.
9. **Run PostgreSQL concurrency tests before declaring the queue engine complete.** Mock-only tests are insufficient for row-locking behavior.
10. **Hand Member 3 stable API contracts and Member 4 repeatable tests.** Freeze payloads early to reduce integration churn.

---

## Appendix A. Example queue event payloads

### Token created

```json
{
  "event_id": "<uuid>",
  "schema_version": 1,
  "type": "queue.token_created",
  "office_id": "<uuid>",
  "service_id": "<uuid>",
  "token": {
    "id": "<uuid>",
    "public_token_number": "A-023",
    "status": "WAITING",
    "source": "APPOINTMENT"
  },
  "occurred_at": "2026-10-30T04:30:00Z"
}
```

### Token called with fairness promotion

```json
{
  "event_id": "<uuid>",
  "schema_version": 1,
  "type": "queue.token_called",
  "office_id": "<uuid>",
  "service_id": "<uuid>",
  "counter_id": "<uuid>",
  "token": {
    "id": "<uuid>",
    "public_token_number": "W-014",
    "status": "CALLED"
  },
  "promoted_for_fairness": true,
  "walk_in_wait_minutes": 47,
  "policy_version": 3,
  "occurred_at": "2026-10-30T05:17:00Z"
}
```

### Service completed

```json
{
  "event_id": "<uuid>",
  "schema_version": 1,
  "type": "queue.token_completed",
  "office_id": "<uuid>",
  "counter_id": "<uuid>",
  "token": {
    "id": "<uuid>",
    "public_token_number": "A-023",
    "status": "COMPLETED"
  },
  "occurred_at": "2026-10-30T05:42:00Z"
}
```

Payloads are examples only. Final payloads must be versioned and privacy-reviewed before Member 3 depends on them.

## Appendix B. Example queue workflow for the demo

1. Citizen signs in through Firebase Phone Authentication.
2. Citizen books an appointment through Member 1's appointment API.
3. Member 1 creates and stores a hashed QR reference and displays the raw reference/QR to the citizen once.
4. Citizen arrives during the check-in window.
5. Officer signs in through the approved Firebase staff identity and is authorized by PostgreSQL office/counter assignment.
6. Officer scans QR. Member 2 validates the reference through Member 1's shared service, locks the appointment and atomically creates one queue token.
7. Queue screen shows the public token number and waiting status.
8. Officer presses Call Next. Member 2 locks the counter, applies appointment order and overdue walk-in fairness, assigns the token and emits a committed event.
9. Officer starts service, optionally holds/resumes, and completes it.
10. Citizen and officer dashboards update from WebSocket events. If a socket disconnects, the frontend fetches the REST queue snapshot and continues.
11. Member 4 verifies the event history and metrics. The workflow remains functional even if AI/OCR services are offline.

## Appendix C. Decisions that must be explicitly agreed before coding

| Decision | Default recommendation | Required participants |
|---|---|---|
| Queue sequence scope | Per office + service + operating date | Members 1, 2, 3 |
| Duplicate QR replay response | Conflict with safe message; optionally return existing token only if explicitly approved | Members 1, 2, 3 |
| Check-in transaction ownership | One shared SQLAlchemy session/DB transaction | Members 1, 2 |
| Appointment ordering among waiting tokens | Slot start, then check-in time, then creation time/token ID | Members 1, 2 |
| Walk-in fairness threshold | 45 minutes by default | Members 1, 2, 3 |
| Call retry count/interval | Configured policy; no invented hard-coded value | Members 1, 2, 3 |
| Counter release on hold | Retain counter by default | Members 1, 2, 3 |
| Realtime fan-out | Transactional outbox; shared broker if multi-instance | Members 2, 3, 4 |
| Wait estimate formula | Eligible work ahead / active eligible counters; label approximate | Members 2, 3, 4 |
| Counter transfer | P1 unless explicitly required for demo | Members 2, 3 |

**Final implementation principle:** protect correctness in PostgreSQL first, expose stable APIs second, and add live updates third. A slightly less animated queue that never double-books a counter is better than a dazzling dashboard showing two citizens being served at the same desk.
