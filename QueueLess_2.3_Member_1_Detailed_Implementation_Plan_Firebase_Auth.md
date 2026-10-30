> **FIREBASE AUTH UPDATE (30 October 2026):** This revised plan uses Firebase Authentication for citizen phone OTP and client session refresh. FastAPI verifies Firebase ID tokens with Firebase Admin SDK; PostgreSQL stores the internal user profile and authoritative roles. This update supersedes any legacy custom-OTP/custom-JWT/refresh-token instructions retained elsewhere in the source text. Do not implement `otp_challenges`, `refresh_tokens`, `/auth/otp/request`, `/auth/otp/verify`, or `/auth/refresh`. Follow Section 6 below for the implementation contract.

# QueueLess 2.3
## Member 1 Detailed Implementation Plan
### Backend Foundation, Authentication, Database, Appointment Booking, Slot Capacity and QR Reference Management

**Owner:** Member 1  
**Project:** QueueLess 2.3  
**Baseline:** QueueLess 2.3 Implementation-Ready Technical Specification and QA Test Plan  
**Primary responsibility:** Build the trusted backend foundation and the complete citizen appointment lifecycle, from authentication and slot discovery through booking, cancellation, rescheduling and QR-reference recovery.

---

# 1. Mission and definition of done

Member 1 owns the backend foundation that the other members depend on. The work must provide stable database models, migrations, authentication/authorization services, appointment APIs and transactional guarantees.

The module is complete when a citizen can:

1. Sign in through Firebase Phone Authentication and obtain a Firebase ID token.
2. Receive a valid authenticated session with the correct role.
3. Browse available offices, services and appointment slots.
4. Book a slot without exceeding capacity, including under concurrent requests.
5. View their own appointment and appointment history.
6. Cancel or reschedule an eligible appointment without corrupting slot capacity.
7. Display a QR reference when the booking is created.
8. Recover a QR after page reload through authenticated QR rotation.
9. Be prevented from viewing or modifying another citizen's appointment.
10. Receive predictable API errors and safe retry behavior.

Member 1 must also expose the backend contracts needed by Member 2 for officer check-in. Member 1 owns authentication, appointment records, QR-reference records and the shared authorization primitives. Member 2 owns the actual queue token creation, check-in transaction orchestration, queue state machine, counters and call-next algorithm.

**Product boundary:** QueueLess coordinates visits. It does not submit government applications, approve certificates, determine legal eligibility or claim that an uploaded document is genuine or officially accepted.

---

# 2. Exact ownership and boundaries

## 2.1 Member 1 owns

- FastAPI application foundation and shared configuration.
- PostgreSQL connection, SQLAlchemy models and Alembic migrations.
- User, role, office, service and office/service policy foundations.
- Firebase ID-token verification in FastAPI and internal user-profile provisioning.
- Shared role, ownership, office-scope and counter-assignment authorization helpers.
- Firebase project configuration and secure Admin SDK initialization. (Firebase manages client session refresh.)
- Shared role, ownership, office-scope and counter-assignment authorization helpers.
- Appointment slot generation and persisted slot capacity.
- Slot listing and availability APIs.
- Appointment booking, listing, detail, cancellation and rescheduling.
- Appointment state and appointment history.
- Idempotency-key middleware/service for Member 1's write APIs.
- QR opaque-reference generation, hashing, storage, initial issue and rotation.
- Appointment audit events for actions Member 1 owns.
- Unit, integration, concurrency and security tests for these modules.
- API documentation and integration handoff to Members 2 and 3.

## 2.2 Member 1 does not own

| Module | Owner | Member 1's responsibility |
|---|---|---|
| Queue token creation and token numbering | Member 2 | Provide appointment and citizen identifiers; agree on transaction boundary |
| QR scan check-in `POST /checkin` | Member 2 | Provide reference lookup/validation service and appointment lock contract |
| Manual officer check-in | Member 2 | Provide appointment data and shared officer authorization |
| Queue token state machine | Member 2 | No queue-state implementation |
| Counter assignment and call-next | Member 2 | Provide office/service/counter base data as agreed |
| WebSocket event delivery | Member 2 | Provide committed appointment events/outbox contract if appointment updates need broadcasting |
| Citizen/officer/admin screens | Member 3 | Publish OpenAPI contract and sample responses |
| RAG, ChromaDB, LLM and citations | Member 4 | No AI pipeline implementation |
| OCR and document checklist comparison | Member 4 | Provide authenticated API conventions if document module needs them |
| End-to-end QA coordination | Member 4 | Supply testable endpoints and fix Member 1 defects |

**Important coordination rule:** Member 1 must not independently create a second check-in implementation. QR rotation and reference storage belong to Member 1; consuming a reference and creating a queue token belongs to Member 2. Agree on a shared service interface before either side implements the final check-in transaction.

---

# 3. Technology and engineering decisions

Use the stack already selected for QueueLess:

- Python and FastAPI.
- PostgreSQL.
- SQLAlchemy 2.x for ORM/database access.
- Alembic for schema migrations.
- Pydantic v2 for request/response validation.
- `psycopg` or the team's chosen PostgreSQL driver.
- A secure password-hashing library such as Argon2id for staff passwords, if password login is enabled.
- Python's cryptographically secure `secrets` module for QR references. Firebase handles citizen OTP generation and verification.
- Pytest, HTTPX and a real PostgreSQL test database for integration tests.

Do not introduce microservices, Redis, Celery, RQ or a second database for this member's scope. QueueLess 2.3 is a modular monolith. Use one FastAPI application and clear module boundaries.

## 3.1 Configuration

Use environment variables and a typed settings class. Never hard-code secrets.

Required configuration:

- `DATABASE_URL`
- `FIREBASE_PROJECT_ID`
- `GOOGLE_APPLICATION_CREDENTIALS` or the deployment platform's secure service-account/Workload Identity configuration
- `FIREBASE_CHECK_REVOKED` (documented policy; enable for sensitive routes or globally if latency permits)
- `APP_ENV` (`development`, `test`, `production`)
- `DEFAULT_TIMEZONE=Asia/Kolkata`
- `QR_ROTATION_LIMIT`
- `QR_ROTATION_WINDOW_SECONDS`
- `IDEMPOTENCY_RETENTION_HOURS`
- `APP_ENV` (`development`, `test`, `production`)
- `DEFAULT_TIMEZONE=Asia/Kolkata`
- `QR_ROTATION_LIMIT`
- `QR_ROTATION_WINDOW_SECONDS`
- `IDEMPOTENCY_RETENTION_HOURS`

Firebase Phone Authentication must be configured for the correct project and authorized domains. Do not log Firebase ID tokens, service-account credentials, QR references or secrets. Never commit service-account JSON files.

---

# 4. Repository structure

Use a structure similar to this. If the team already has a repository convention, adapt names while preserving the boundaries.

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   └── time.py
│   ├── common/
│   │   ├── dependencies.py
│   │   ├── pagination.py
│   │   ├── idempotency.py
│   │   └── permissions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── office.py
│   │   ├── service.py
│   │   ├── queue_policy.py
│   │   ├── appointment_slot.py
│   │   ├── appointment.py
│   │   ├── checkin_reference.py
│   │   ├── firebase_auth.py
│   │   ├── user_provisioning.py
│   │   ├── idempotency_key.py
│   │   └── audit_event.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── catalogue.py
│   │   ├── appointment.py
│   │   └── common.py
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── catalogue/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── appointments/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── slot_generator.py
│   │   │   ├── repository.py
│   │   │   └── policies.py
│   │   └── qr_references/
│   │       ├── service.py
│   │       ├── repository.py
│   │       └── crypto.py
│   └── integrations/
│       └── firebase_admin.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── concurrency/
│   └── security/
├── scripts/
│   ├── seed_demo_data.py
│   └── create_demo_users.py
├── alembic.ini
├── pyproject.toml
└── .env.example
```

Keep route handlers thin. Route handlers should validate input, call a service, and return a schema. Business rules and transactions belong in service/repository code, not in React and not scattered across route handlers.

---

# 5. Database design and migration plan

Member 1 owns the initial migration foundation and the appointment/authentication tables. Coordinate with Member 2 before finalizing shared tables such as `offices`, `services`, `counters`, `queue_policy` and `audit_events`.

## 5.1 Core tables

### `users`

Purpose: citizen and staff identity.

Suggested fields:

- `id` UUID primary key (internal QueueLess identifier).
- `firebase_uid` unique and non-null; maps the verified Firebase identity to this internal account.
- `phone_number` nullable/normalized according to the team's privacy decision; populate only from a trusted verified Firebase claim where available.
- `display_name`.
- `role` enum/string constrained to approved values: `CITIZEN`, `OFFICER`, `OFFICE_ADMIN` (and `PLATFORM_ADMIN` only if the project requires it).
- `is_active`.
- `created_at`, `updated_at`, `last_login_at`.
- `office_id` / staff assignment relations as required by the shared office model. Staff mappings are provisioned by a trusted process.

Rules:

- Never expose internal database IDs as a substitute for authorization.
- A citizen can access only their own profile and appointments.
- Officer access must be scoped to office/counter assignments.
- Admin access must be scoped to the office they administer.
- Avoid collecting Aadhaar or unnecessary sensitive identity data.

### `offices`

Purpose: physical service locations.

Suggested fields:

- `id` UUID.
- `name`.
- `address`.
- `timezone`, default `Asia/Kolkata`.
- `is_active`.
- `created_at`, `updated_at`.

### `services`

Purpose: services offered by an office.

Suggested fields:

- `id` UUID.
- `office_id` foreign key.
- `name`.
- `description`.
- `average_service_duration_minutes`.
- `is_active`.
- `created_at`, `updated_at`.

Use a unique constraint appropriate to the product, such as `(office_id, normalized_name)`.

### `queue_policy`

Purpose: versioned office/service operating rules.

Required 2.3 fields:

- `id`.
- `office_id`.
- `service_id`, nullable for office-wide defaults.
- `slot_duration_minutes`.
- `walk_in_share`.
- `max_walk_in_wait_minutes`.
- `checkin_open_minutes`.
- `checkin_close_minutes`.
- `policy_version`.
- `effective_from`.
- `updated_by`.
- `updated_at`.

Member 1 owns persistence and policy read access needed by slot generation. Member 2 owns queue-engine use of fairness and token-selection policy. Admin policy mutation should be restricted to office admins and audited. If policy editing is not ready for P0, seed a versioned demo policy and keep the write API behind an admin-only route.

### `appointment_slots`

Required fields:

- `id` UUID.
- `office_id`.
- `service_id`.
- `starts_at` and `ends_at` as UTC `TIMESTAMPTZ`.
- `operating_date` as local office date.
- `block_start_at`.
- `capacity` integer, non-negative.
- `booked_count` integer, non-negative.
- `status`: `OPEN`, `FULL`, `CLOSED`.
- `capacity_policy_version`.
- `created_at`, `updated_at`.

Constraints:

- `booked_count >= 0`.
- `capacity >= 0`.
- `booked_count <= capacity`.
- `ends_at > starts_at`.
- Unique slot identity, for example `(office_id, service_id, starts_at)`.
- A zero-capacity generated slot must be `CLOSED`.
- `FULL` means `booked_count >= capacity` for an otherwise bookable slot.
- Preserve an administrative/out-of-hours `CLOSED` state. Do not automatically reopen such a slot during cancellation.

### `appointments`

Suggested fields:

- `id` UUID.
- `citizen_id` foreign key to `users`.
- `office_id`, `service_id`, `slot_id`.
- `status`: at minimum `BOOKED`, `CHECKED_IN`, `CANCELLED`, `RESCHEDULED`, `NO_SHOW`.
- `booking_reference` non-sequential public reference if required.
- `slot_start_at`, or join the slot consistently.
- `check_in_open_at`, `check_in_close_at`.
- `rescheduled_from_id`, `rescheduled_to_id`, nullable self-references.
- `cancelled_at`, `cancellation_reason`.
- `no_show_at`, `no_show_reason`.
- `reminder_status`.
- `qr_rotated_at`.
- `created_at`, `updated_at`.

Use database constraints and indexes for common citizen/office/date lookups. Define active appointment statuses explicitly. Prevent duplicate active reservations for the same citizen, service, office and slot with a partial unique index or an equivalent database constraint.

### `checkin_references`

Purpose: store QR references without storing the raw secret.

Suggested fields:

- `id` UUID.
- `appointment_id` foreign key.
- `reference_hash` unique.
- `created_at`.
- `expires_at`.
- `used_at`, nullable.
- `invalidated_at`, nullable.
- `invalidation_reason`, nullable (`ROTATED`, `CANCELLED`, `RESCHEDULED`, `EXPIRED`, etc.).
- Optional `created_by_user_id` for audit context.

Store only a cryptographic hash of the raw reference. Never store the raw QR reference.


### `idempotency_keys`

Required fields:

- `id`.
- `actor_id`.
- `scope`.
- `key_hash`.
- `request_hash`.
- `response_status`.
- `response_body`.
- `created_at`.
- `expires_at`.

Unique constraint: `(actor_id, scope, key_hash)`.

Behavior:
- Same key and same request hash: return the original response.
- Same key and different request hash: `409 IDEMPOTENCY_KEY_REUSED`.
- Different key: treat as a new request, subject to business uniqueness constraints.
- Hash the canonical method, route, actor and normalized body.
- Do not store raw OTPs, QR references, passwords or access tokens in this table.

### `audit_events`

Append-only event table for sensitive actions.

At minimum record:
- actor ID and role;
- office ID where relevant;
- action name;
- resource type and ID;
- timestamp;
- reason where required;
- safe metadata without secrets.

Member 1 actions to audit include booking, cancellation, rescheduling, QR rotation, login security events and admin policy changes. Coordinate a common event schema with Member 2.

## 5.2 Database migration order

Create migrations in this order to reduce foreign-key and integration conflicts:

1. Extensions/enums and base identity tables.
2. Offices and services.
3. Office/service assignments and queue policy.
4. Appointment slots.
5. Appointments and appointment history constraints.
6. QR check-in references.
7. Firebase UID mapping and the required appointment/QR support tables. No QueueLess OTP or refresh-token tables.
8. Idempotency keys.
9. Audit events and supporting indexes.

Do not edit an already-applied migration in a shared environment. Create a new forward migration. Run migrations against a clean database and an existing database before merging.

---

# 6. Firebase Authentication and authorization implementation

## 6.1 Architecture and responsibility split

- **Firebase Authentication:** citizen phone-number verification, SMS OTP delivery/verification, client sign-in state and refresh-token lifecycle.
- **React/Vite client:** Firebase client SDK integration; obtains an ID token with `getIdToken()` and sends it as a Bearer token.
- **FastAPI:** verifies Firebase ID tokens with Firebase Admin SDK, maps verified `uid` to an internal QueueLess user, and enforces application authorization.
- **PostgreSQL:** source of truth for internal user UUID, active status, role, office/counter assignment, and all application data.

Do not implement citizen OTP request/verify endpoints, `otp_challenges`, custom citizen JWT issuance, `/auth/refresh`, or a QueueLess `refresh_tokens` table.

## 6.2 Firebase project setup

1. Create/select the QueueLess Firebase project and record its project ID.
2. Enable Phone provider in Firebase Authentication.
3. Configure authorized domains for local development and the deployed frontend.
4. Configure SMS region policy and quotas. Use Firebase test phone numbers for automated testing and rehearsals.
5. Install the Firebase client SDK in the frontend and Firebase Admin SDK in the backend.
6. Configure Admin SDK credentials through the platform's secret manager or workload identity. Never commit service-account JSON.
7. Keep development, staging and production Firebase configuration separate.

## 6.3 Frontend sign-in contract

1. Initialize Firebase using public client configuration supplied through frontend environment variables.
2. Use Firebase Phone Authentication, including the required reCAPTCHA/app-verification mechanism.
3. Complete OTP verification using Firebase SDK APIs.
4. After sign-in, call `await user.getIdToken()` when an authenticated API request is made.
5. Send `Authorization: Bearer <id-token>` to FastAPI. Do not put tokens in query strings, local logs, analytics, or URLs.
6. Let the Firebase SDK manage token refresh. Do not build a custom refresh-token flow.
7. On sign-out, call Firebase sign-out and clear client application state.

## 6.4 Backend Firebase Admin verification

Create one shared authentication module and initialize Firebase Admin once during application startup. Do not initialize the SDK on every request. A minimal verification pattern is:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

bearer = HTTPBearer(auto_error=False)

def get_verified_firebase_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        claims = auth.verify_id_token(
            credentials.credentials,
            check_revoked=settings.FIREBASE_CHECK_REVOKED,
        )
        if claims.get("aud") != settings.FIREBASE_PROJECT_ID:
            raise ValueError("Unexpected Firebase audience")
        return claims
    except Exception:
        # In production, catch Firebase Admin exception classes explicitly
        # and distinguish revoked/expired/invalid tokens without leaking details.
        raise HTTPException(status_code=401, detail="Invalid or expired authentication")
```

Implementation requirements:
- Validate the expected Firebase project; never accept tokens from an unintended project.
- Catch specific Firebase Admin exceptions in production code and return controlled errors. Do not expose raw exception messages.
- Decide and document revocation-check policy. `check_revoked=True` provides stronger revocation enforcement but adds a network round trip; use it globally only if the latency/availability trade-off is acceptable, otherwise apply it to sensitive routes and document the residual window.
- Fail closed if Firebase verification cannot be performed. Never bypass verification because Firebase is unavailable.
- Never log the Bearer token or full decoded claims if they contain personal information.

## 6.5 Internal user provisioning and role resolution

Create/maintain `users` with at least:
- `id` (internal UUID primary key)
- `firebase_uid` (unique, non-null)
- `phone_number` (nullable/verified value from trusted Firebase claims where available)
- `display_name` (nullable)
- `role` (database enum/string constrained to approved roles)
- `is_active`
- `created_at`, `updated_at`, `last_login_at`

On each authenticated request:
1. Verify Firebase ID token.
2. Read the verified `uid` and verified phone claim, if present.
3. Find the QueueLess user by `firebase_uid`.
4. If first-time citizen provisioning is enabled, create a citizen profile transactionally with the least-privilege `CITIZEN` role. Otherwise return a controlled onboarding response.
5. Never accept role or office/counter assignment from the client during provisioning.
6. Reject inactive QueueLess users even if their Firebase token is valid.
7. Load the role and office/counter scope from PostgreSQL and attach the internal user to request context.

Staff and admin identities must be pre-provisioned through a trusted process. A Firebase account does not automatically become an officer or administrator. Role changes must be audited.

## 6.6 Authorization dependencies

Implement reusable dependencies/services such as:
- `get_current_user`: verified Firebase claims plus active internal QueueLess user.
- `require_role(*roles)`: database-backed role check.
- `require_office_scope(office_id)`: verifies the user's assigned office.
- `require_counter_assignment(counter_id)`: verifies officer-counter assignment.
- `require_appointment_owner(appointment_id)`: verifies citizen ownership or an explicitly authorized staff scope.

Every protected endpoint must enforce both authentication and resource authorization. Never rely on hidden frontend controls.

## 6.7 Authentication acceptance tests

- Valid Firebase ID token from the configured project resolves the correct internal user.
- Missing, malformed, expired, tampered, wrong-project and revoked tokens are rejected.
- A first-time Firebase UID receives only a citizen role or a controlled onboarding response.
- Repeated sign-in does not create duplicate QueueLess users.
- A client cannot self-assign staff/admin roles or office/counter scope.
- Inactive QueueLess users are denied even with valid Firebase tokens.
- A citizen cannot access another citizen's appointments or QR references.
- Firebase token refresh through the client SDK works without a QueueLess refresh endpoint.
- Firebase verification outage fails closed.
- No ID token or service-account secret appears in logs.


# 7. Appointment slot generation

This is one of Member 1's most important correctness responsibilities.

## 7.1 Inputs

For each office, service, operating date and 60-minute block, obtain:

- office opening hours;
- office timezone;
- service duration;
- active eligible counters/staffing for that block;
- breaks and unavailable intervals;
- slot duration from the effective queue policy;
- walk-in share;
- policy version.

Do not assume every counter supports every service. Only count eligible, active counters.

## 7.2 Capacity calculation

For each 60-minute block:

```text
block_capacity = active_counters
                 × floor(60 / service_duration_minutes)

walk_in_reserve = floor(block_capacity × walk_in_share)

appointment_block_capacity = block_capacity - walk_in_reserve

base = floor(appointment_block_capacity / slots_in_block)
remainder = appointment_block_capacity % slots_in_block
```

Distribute appointment capacity chronologically:
- first `remainder` slots receive `base + 1`;
- remaining slots receive `base`.

Persist each slot's capacity. Do not recompute capacity during booking.

Example: two active counters, 10-minute service duration, 20% walk-in share:
- theoretical block capacity = 12;
- walk-in reserve = 2;
- appointment capacity = 10;
- six slot capacities = `2, 2, 2, 2, 1, 1`.

Example: one active counter:
- theoretical block capacity = 6;
- walk-in reserve = 1;
- appointment capacity = 5;
- six slot capacities = `1, 1, 1, 1, 1, 0`;
- the zero-capacity slot is `CLOSED`.

The walk-in reserve is a planning allocation, not a promise that a fixed number of walk-ins will be served. The default release rule permits unused reserve to be released to appointments 10 minutes before the block ends. Implement this only if the team is including the release behavior in the demo; otherwise leave the reserve unavailable to appointments and document that simplification.

## 7.3 Generation algorithm

1. Load effective policy and office timezone.
2. Convert the requested operating date to the office-local date.
3. Load office hours and eligible counter availability.
4. Divide the day into operating blocks.
5. For each block, calculate theoretical capacity and appointment capacity.
6. Divide the block into the configured slot intervals.
7. Apply quotient/remainder distribution in chronological order.
8. Mark slots outside hours, during breaks or with zero capacity as `CLOSED`.
9. Insert or update generated slots idempotently using the unique slot identity.
10. Persist the policy version used for every slot.
11. If confirmed bookings exist, never silently reduce capacity below `booked_count`.
12. If staffing changes would make existing bookings exceed the new safe capacity, raise an admin-visible conflict requiring explicit resolution.

Generation must be deterministic. Running the generator twice with the same inputs and policy version must not create duplicates or alter already-booked capacity unexpectedly.

## 7.4 Slot APIs

Recommended contracts:

`GET /offices`
- Public or authenticated according to team decision.
- Returns active office summaries.

`GET /offices/{office_id}/services`
- Returns active services and basic guidance.

`GET /offices/{office_id}/services/{service_id}/slots?date=YYYY-MM-DD`
- Returns persisted slot capacity, booked count, remaining availability and status.
- Never expose citizen names or appointment IDs in public slot results.

Admin-only generation endpoint, if required:

`POST /admin/offices/{office_id}/services/{service_id}/slots/generate`

Body includes operating date and an optional explicit regeneration mode. Require office-admin authorization and audit the action. Do not permit destructive regeneration of slots with confirmed bookings.

---

# 8. Appointment APIs and business logic

## 8.1 API contract overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| Firebase client SDK | Phone sign-in | Public Firebase flow | Verify phone and obtain Firebase ID token |
| GET/POST | Protected application APIs | Firebase ID token | FastAPI verifies Bearer token and resolves internal user |
| POST | `/auth/logout` | Authenticated | Revoke session |
| GET | `/me` | Authenticated | Current profile and role |
| GET | `/offices` | Public/authenticated | List active offices |
| GET | `/offices/{office_id}/services` | Public/authenticated | List office services |
| GET | `/offices/{office_id}/services/{service_id}/slots` | Public/authenticated | List available persisted slots |
| POST | `/appointments` | Citizen | Book appointment |
| GET | `/appointments` | Citizen | List only own appointments |
| GET | `/appointments/{appointment_id}` | Owner or authorized staff | Appointment details |
| POST | `/appointments/{appointment_id}/cancel` | Owner/authorized staff | Cancel appointment |
| POST | `/appointments/{appointment_id}/reschedule` | Citizen | Reschedule appointment |
| POST | `/appointments/{appointment_id}/qr/rotate` | Appointment owner | Rotate and return a new raw QR reference |

All write endpoints must validate role, resource ownership, current state and request schema. Use typed error responses consistently.

## 8.2 Booking request

Example:

```json
{
  "slot_id": "UUID",
  "service_id": "UUID"
}
```

The citizen ID must come from the authenticated session, never from the request body.

Require an `Idempotency-Key` header for booking and other non-repeatable writes.

## 8.3 Booking transaction

Inside one database transaction:

1. Validate authenticated actor is an active citizen.
2. Resolve the requested slot and lock it using `SELECT ... FOR UPDATE`.
3. Confirm slot is `OPEN`, in the future and has `booked_count < capacity`.
4. Confirm slot belongs to the selected office/service.
5. Confirm the policy version and operating window are valid.
6. Enforce the duplicate active-reservation rule.
7. Insert appointment with `BOOKED` status.
8. Calculate and persist `check_in_open_at` and `check_in_close_at` from policy.
9. Generate a cryptographically random 256-bit QR reference.
10. Hash the reference and store only the hash in `checkin_references`.
11. Increment `booked_count`.
12. Set slot to `FULL` if the new count reaches capacity; otherwise keep `OPEN`.
13. Write audit event and idempotency response record in the same transaction.
14. Commit.
15. Return appointment response and raw QR reference once, with `Cache-Control: no-store`.

If any step fails, roll back all changes. Never create an appointment without reserving capacity or reserve capacity without creating the appointment.

## 8.4 Cancellation transaction

Allowed only while the appointment is in a cancellable state, normally `BOOKED` and before the configured cutoff.

1. Lock appointment row.
2. Verify citizen ownership or authorized officer/admin role.
3. Validate current appointment state and cancellation policy.
4. Lock the associated slot row.
5. Set appointment `CANCELLED`, timestamp and reason.
6. Decrement slot `booked_count`.
7. Reopen the slot only if `booked_count < capacity` and the slot is not administratively closed or outside operating hours.
8. Invalidate all unused QR references with reason `CANCELLED`.
9. Write audit event and idempotency result.
10. Commit.

Never decrement below zero. Use one shared slot-release helper for cancellation and rescheduling.

## 8.5 Rescheduling transaction

Rescheduling creates a new appointment record and preserves the old appointment's history.

1. Lock old appointment.
2. Verify owner, state and rescheduling cutoff.
3. Lock old and new slot rows in deterministic slot-ID order to avoid deadlocks.
4. Verify the new slot is open and has capacity.
5. Reserve the new slot.
6. Create new appointment with `BOOKED` status and `rescheduled_from_id`.
7. Mark old appointment `RESCHEDULED` and set `rescheduled_to_id`.
8. Decrement old slot `booked_count`.
9. Recalculate old slot state without reopening admin-closed slots.
10. Invalidate all unused QR references for the old appointment with reason `RESCHEDULED`.
11. Create a new QR reference for the new appointment.
12. Record audit events for both appointment records.
13. Commit as one transaction.

If any operation fails, roll back the whole transaction. Never overwrite the old appointment row.

---

# 9. QR reference generation and rotation

## 9.1 Reference format

- Generate at least 256 bits of cryptographically secure randomness.
- Encode as URL-safe Base64 or another QR-friendly opaque representation.
- QR contains only the opaque reference and, if required, a harmless version marker.
- Do not encode names, phone numbers, Aadhaar, document data or predictable database IDs.
- Store only a SHA-256 or keyed cryptographic hash of the reference. A keyed HMAC is appropriate if the team manages a separate server secret.
- Do not log the raw reference or include it in analytics/error telemetry.

## 9.2 QR rotation endpoint

`POST /appointments/{appointment_id}/qr/rotate`

Authorization:
- Authenticated citizen.
- Citizen must own the appointment.
- Appointment must be `BOOKED`.
- Appointment must not be checked in, cancelled, rescheduled or expired.
- Check-in window must not have closed.

Transaction:
1. Lock appointment row.
2. Verify ownership and state.
3. Apply rotation rate limit (prototype example: 3 rotations per 10 minutes).
4. Invalidate all existing unused references with reason `ROTATED`.
5. Generate a new 256-bit raw reference.
6. Store its hash and metadata.
7. Set `qr_rotated_at`.
8. Write audit event.
9. Commit.
10. Return raw reference exactly once with `Cache-Control: no-store`.

The invalidation and new-reference insert must be atomic. If the transaction fails, the old reference must remain valid.

The endpoint is deliberately a rotation endpoint, not a read endpoint. The raw reference is not recoverable from the database. The frontend's **Show QR** button calls this endpoint whenever it needs to redisplay a QR after reload.

## 9.3 Member 2 check-in integration contract

Member 2 implements:
- `POST /checkin` with body `{ "reference": "<opaque-raw-reference>" }`.
- `POST /appointments/{appointment_id}/check-in/manual` with body `{ "confirmation": true, "reason": "<required reason>" }`.

Member 1 supplies a service contract such as:

```python
class QRReferenceService:
    def resolve_and_lock_reference(self, db, raw_reference):
        # Hash raw reference, find and lock matching record.
        # Return reference and appointment context. Do not create a token.

    def mark_reference_used(self, reference_record):
        # Mark used inside the caller's transaction. The caller commits
        # check-in and queue-token creation atomically.
```

This is an interface sketch, not a requirement to use these exact method names. Member 1 and Member 2 must agree on transaction ownership before coding. The check-in transaction must guarantee one token per appointment and one-time QR use. A unique constraint on the queue-token appointment link is owned by Member 2's queue schema.

---

# 10. Timezone and operating-date handling

- Store timestamps as UTC `TIMESTAMPTZ`.
- Use the office timezone (`Asia/Kolkata` for Karnataka deployment) to determine operating dates.
- Never use the server's naive local time.
- Convert the current instant to office timezone before selecting `operating_date`.
- Check-in windows are absolute instants stored/derived consistently from the slot and policy.
- A booking around midnight IST must be assigned to the correct local operating date.
- Do not derive token numbers in Member 1; Member 2 owns token sequence allocation. However, Member 1 must provide `operating_date` and office timezone consistently in the appointment/slot contract.
- Test a request at 23:59:59 IST and another at 00:00:01 IST.

Use timezone-aware datetime objects end-to-end. Reject naive datetimes at API boundaries unless the API explicitly defines the timezone.

---

# 11. Idempotency implementation

Create a reusable idempotency service for appointment booking, cancellation, rescheduling and QR rotation.

Algorithm:
1. Read the `Idempotency-Key` header.
2. Validate format and length.
3. Hash the key before storage.
4. Build a canonical request fingerprint from HTTP method, route, actor ID and normalized request body.
5. Attempt to claim the unique `(actor_id, scope, key_hash)` record.
6. If an existing record has the same request hash and completed response, return the stored response.
7. If the existing record has a different request hash, return `409 IDEMPOTENCY_KEY_REUSED`.
8. If another request is still processing, wait/retry briefly or return a typed conflict according to the agreed policy.
9. Store response status/body only after the operation succeeds, in the same transaction where practical.
10. Apply retention/expiry cleanup through a safe maintenance job or periodic cleanup command.

Idempotency does not replace business uniqueness constraints. For example, a citizen must not create duplicate active bookings merely by using a new idempotency key.

---

# 12. Error contract

Use a consistent shape:

```json
{
  "error": {
    "code": "SLOT_FULL",
    "message": "This appointment slot is no longer available.",
    "details": {}
  }
}
```

Suggested error codes:

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request |
| 401 | `UNAUTHENTICATED` | Missing/invalid session |
| 403 | `FORBIDDEN` | Wrong role or resource scope |
| 404 | `APPOINTMENT_NOT_FOUND` | No visible matching appointment |
| 404 | `SLOT_NOT_FOUND` | Slot does not exist |
| 409 | `SLOT_FULL` | Slot capacity exhausted |
| 409 | `DUPLICATE_ACTIVE_APPOINTMENT` | Active duplicate reservation |
| 409 | `APPOINTMENT_NOT_CANCELLABLE` | Current state/cutoff blocks cancellation |
| 409 | `APPOINTMENT_NOT_RESCHEDULABLE` | Current state/cutoff blocks reschedule |
| 409 | `IDEMPOTENCY_KEY_REUSED` | Same key used with a different payload |
| 409 | `QR_NOT_ROTATABLE` | Appointment state does not allow QR rotation |
| 429 | `RATE_LIMITED` | OTP or QR rotation rate limit |
| 500 | `INTERNAL_ERROR` | Unexpected error; no secrets in response |

Do not reveal whether another citizen's appointment exists. For cross-citizen access, return a consistent not-found or forbidden policy approved by the team.

---

# 13. API documentation and handoff requirements

Before Member 3 begins full integration, provide:

- OpenAPI/Swagger route list.
- Request and response examples for every Member 1 endpoint.
- Authentication header/cookie convention.
- Role requirements.
- Error codes.
- Pagination and date/time format.
- Idempotency header behavior.
- Sample seed accounts for citizen, officer and admin.
- Test environment URL and database reset instructions.
- A clear note that QR rotation returns a new reference and invalidates the previous one.

Before Member 2 integrates check-in, provide:

- QR reference table/model and migration.
- Reference hashing function.
- A transaction-safe reference lookup/lock interface.
- Appointment status and check-in-window fields.
- Office assignment authorization helper.
- Agreed shared transaction boundary.
- Expected errors for expired, rotated, used and unknown references.

Do not send raw QR references or OTP values through team chat or issue trackers. Use synthetic local test data.

---

# 14. Implementation phases and day-by-day plan

This schedule assumes a four-week project and can be compressed or expanded depending on the hackathon deadline.

## Phase 0: Contract and setup (Day 1)

Tasks:
- Meet Members 2 and 3 to agree on endpoint and model boundaries.
- Confirm exact backend package versions.
- Create FastAPI app and health endpoint.
- Configure PostgreSQL connection and Alembic.
- Add `.env.example`, settings validation and structured logging.
- Agree on UUID usage, enum naming, UTC timestamp conventions and error response shape.
- Create a shared API contract document.

Deliverable:
- Backend starts locally.
- Database connection works.
- `/health` returns healthy status.
- OpenAPI docs are available.
- Initial project structure is merged.

Exit criteria:
- Other members can clone and run the backend.
- No secret is committed to Git.

## Phase 1: Database foundation (Days 2–3)

Tasks:
- Implement base models: users, offices, services and queue policy.
- Implement appointment slots, appointments and QR-reference models.
- Implement Firebase ID-token verification, internal user provisioning, idempotency keys and audit events. Do not create OTP-challenge or refresh-token tables.
- Add foreign keys, unique constraints, check constraints and indexes.
- Create ordered Alembic migrations.
- Write seed script for one demo office, two services and demo roles.
- Test migration from an empty database.

Deliverable:
- Database schema and seed data.
- Repeatable migration command.
- Entity relationship diagram or schema notes.

Exit criteria:
- Fresh database can be created from migrations.
- All constraints are enforced by PostgreSQL, not just Pydantic.

## Phase 2: Authentication and authorization (Days 4–5)

Tasks:
- Configure Firebase Phone Authentication and authorized frontend domains.
- Initialize Firebase Admin SDK securely in FastAPI.
- Implement Firebase ID-token verification and expected-project validation.
- Implement `firebase_uid` to internal-user lookup and safe citizen provisioning.
- Implement database-backed role, ownership, office-scope and counter-assignment dependencies.
- Implement current-user endpoint and audit events for account provisioning/role changes.
- Verify Firebase test-phone flow and fail-closed behavior when verification is unavailable.

Deliverable:
- Working citizen login.
- Seeded officer/admin login path.
- Protected endpoints and shared auth dependencies.

Exit criteria:
- Auth acceptance tests pass.
- Citizen cannot self-upgrade role.
- Cross-user appointment access is blocked.

## Phase 3: Catalogue and slot generation (Days 6–8)

Tasks:
- Implement office and service listing.
- Implement office-local operating date conversion.
- Implement slot generator using active counters, service duration, office hours and breaks.
- Implement block-level reserve calculation and quotient/remainder distribution.
- Persist policy version on generated slots.
- Implement idempotent generation.
- Implement slot listing and availability response.
- Implement conflict handling when staffing changes would overbook existing bookings.

Deliverable:
- Office/service catalogue APIs.
- Generated persisted slots for demo dates.
- Slot capacity tests.

Exit criteria:
- CAP-01 through CAP-06 in the QueueLess QA plan pass, or any intentionally deferred case is documented with an owner and reason.
- Re-running generation does not duplicate slots or drift capacity.

## Phase 4: Appointment lifecycle (Days 9–11)

Tasks:
- Implement appointment booking request/response schemas.
- Implement transactional booking with row lock.
- Add idempotency-key handling.
- Enforce duplicate active booking constraint.
- Implement appointment list and detail endpoints with citizen ownership.
- Implement cancellation and shared slot-release helper.
- Implement rescheduling with deterministic slot lock order.
- Preserve appointment history and QR invalidation during cancellation/reschedule.
- Add audit events.

Deliverable:
- Complete citizen appointment API.
- Booking, cancellation and rescheduling integration tests.

Exit criteria:
- Concurrent bookings cannot exceed slot capacity.
- Cancellation reopens eligible slots correctly.
- Rescheduling is all-or-nothing.
- Same idempotency key cannot create duplicate side effects.

## Phase 5: QR reference lifecycle (Days 12–13)

Tasks:
- Implement secure 256-bit opaque reference generation.
- Implement reference hashing and lookup.
- Issue initial QR reference in booking response.
- Implement authenticated QR rotation endpoint.
- Implement rotation rate limit and audit event.
- Add `Cache-Control: no-store`.
- Ensure raw reference is never persisted or logged.
- Agree on reference locking/consumption contract with Member 2.

Deliverable:
- QR reference service.
- QR rotation API.
- Member 2 check-in integration interface.

Exit criteria:
- QR-11 through QR-16 pass.
- Old reference is rejected after rotation.
- Failed rotation transaction leaves previous reference valid.
- Only appointment owner can rotate.

## Phase 6: Integration and hardening (Days 14–16)

Tasks:
- Integrate Member 2's check-in service with Member 1's reference service.
- Integrate Member 3's frontend with appointment APIs.
- Verify token/refresh behavior in browser.
- Add pagination and consistent error responses.
- Review logs for secret leakage.
- Test timezone edge cases.
- Review migration and deployment instructions.
- Fix integration defects.

Deliverable:
- Citizen booking and QR flow works in browser.
- Member 2 can consume QR references through the agreed service boundary.
- Stable API contract for frontend.

Exit criteria:
- Complete citizen sign-in → service → slot → booking → show QR journey works.
- No raw secrets in logs.
- API docs match implementation.

## Phase 7: Release candidate (Days 17–20)

Tasks:
- Run full Member 1 unit/integration/concurrency/security test suite.
- Run QA regression with Member 4.
- Fix P0 defects first.
- Verify Firebase project configuration, authorized domains, SMS policy and secret handling.
- Verify environment variables and migration instructions.
- Tag a release candidate and publish known limitations.

Deliverable:
- Member 1 module release candidate.
- Test report and deployment notes.
- Signed-off API handoff.

---

# 15. Detailed test matrix for Member 1

## 15.1 Authentication

| ID | Test | Expected |
|---|---|---|
| AUTH-01 | Valid Firebase ID token | Internal user resolved |
| AUTH-02 | Missing/invalid/expired/wrong-project token | `401` |
| AUTH-03 | Unknown Firebase UID | Safe citizen provisioning or controlled onboarding |
| AUTH-04 | Client submits elevated role | Rejected/ignored; no privilege escalation |
| AUTH-05 | Inactive QueueLess user | `403` |
| AUTH-07 | Resend before cooldown | Rate-limited |
| AUTH-08 | Citizen requests officer role | Role escalation rejected |
| AUTH-09 | Expired access token | 401 |
| AUTH-10 | Firebase SDK refreshes ID token | Protected API accepts refreshed token; no QueueLess refresh endpoint |
| AUTH-12 | Logout then refresh | Rejected |
| AUTH-13 | Firebase Admin credentials missing/invalid | Protected APIs fail closed |

## 15.2 Authorization

| ID | Test | Expected |
|---|---|---|
| AUTHZ-01 | Citizen reads own appointment | Allowed |
| AUTHZ-02 | Citizen reads another citizen's appointment | Denied without revealing private data |
| AUTHZ-03 | Citizen cancels another citizen's appointment | Denied |
| AUTHZ-04 | Officer accesses assigned office | Allowed for permitted actions |
| AUTHZ-05 | Officer accesses unassigned office | Denied |
| AUTHZ-06 | Admin changes policy for another office | Denied |

## 15.3 Slot capacity

| ID | Test | Expected |
|---|---|---|
| CAP-01 | Two counters, 10-minute service, 20% reserve | Slot capacities `2,2,2,2,1,1` |
| CAP-02 | One counter, same settings | `1,1,1,1,1,0`; zero slot is CLOSED |
| CAP-03 | Generate same block twice | No duplicate slots or capacity drift |
| CAP-04 | Counter unavailable before generation | Capacity uses active eligible counters only |
| CAP-05 | Staffing reduction below booked count | Conflict surfaced; no silent overbooking |
| CAP-06 | Policy version changes | Future/unbooked slots use new version; existing bookings are not silently rewritten |

## 15.4 Booking and lifecycle

| ID | Test | Expected |
|---|---|---|
| BOOK-01 | Citizen books open slot | Appointment created and count incremented |
| BOOK-02 | Citizen books full slot | `409 SLOT_FULL` |
| BOOK-03 | Two simultaneous requests for final place | Exactly one succeeds |
| BOOK-04 | Same idempotency key and same payload | Original response returned |
| BOOK-05 | Same key and different payload | `409 IDEMPOTENCY_KEY_REUSED` |
| BOOK-06 | New key attempts duplicate active reservation | Business uniqueness rejects duplicate |
| BOOK-07 | Citizen lists appointments | Only own appointments returned |
| BOOK-08 | Cancel eligible booking | Appointment cancelled; count decremented |
| BOOK-09 | Cancel already cancelled booking | Typed conflict; count not decremented again |
| BOOK-10 | Cancel admin-closed slot booking | Slot remains CLOSED |
| BOOK-11 | Reschedule to available slot | New appointment created; old linked and released |
| BOOK-12 | Reschedule to full slot | Entire operation rolled back |
| BOOK-13 | Concurrent reschedules | No partial update or avoidable deadlock |
| BOOK-14 | Reschedule old appointment | Old QR invalidated; new appointment has a new reference |

## 15.5 QR lifecycle

| ID | Test | Expected |
|---|---|---|
| QR-01 | Booking succeeds | Raw QR returned once; hash stored |
| QR-02 | Inspect database | No raw QR reference present |
| QR-03 | Inspect logs | No raw QR reference present |
| QR-04 | Owner rotates QR | New raw reference returned |
| QR-05 | Old reference used after rotation | Rejected |
| QR-06 | Non-owner rotates QR | 403 |
| QR-07 | Rotate after check-in/cancellation | Rejected |
| QR-08 | Exceed rotation rate limit | 429; current reference remains valid |
| QR-09 | Rotation fails before commit | Old reference remains valid |
| QR-10 | Response headers | `Cache-Control: no-store` |
| QR-11 | Two rotations race | One final current reference; no state corruption |

## 15.6 Time and database integrity

| ID | Test | Expected |
|---|---|---|
| TIME-01 | Booking near midnight IST | Correct local operating date |
| TIME-02 | Server timezone differs from office timezone | Results still use office timezone |
| TIME-03 | Naive datetime supplied | Rejected or normalized only under explicit contract |
| DB-01 | `booked_count` would exceed capacity | Database constraint/transaction prevents it |
| DB-02 | `booked_count` would become negative | Database constraint prevents it |
| DB-03 | Slot ends before it starts | Database constraint rejects it |
| DB-04 | Duplicate slot identity | Unique constraint rejects it |
| DB-05 | Migration on clean database | Succeeds |
| DB-06 | Migration on populated test database | Succeeds without data loss |

---

# 16. Concurrency tests that must use PostgreSQL

Do not validate transactional correctness only with SQLite or mocked repositories. Use PostgreSQL for concurrency tests.

Required scenarios:

1. Two citizens attempt to book the final slot simultaneously.
2. One citizen retries the same booking after a simulated network timeout.
3. Two requests use the same idempotency key with different payloads.
4. Two cancellation requests race for the same appointment.
5. Cancellation and rescheduling race for the same appointment.
6. Two reschedules lock old/new slots in opposite request order; deterministic lock ordering must prevent avoidable deadlocks.
7. Two QR rotations occur concurrently for one appointment.
8. QR rotation and QR check-in race. The system must serialize them so only a valid current reference can be consumed and no partially invalidated state is possible.

For each test, assert both the HTTP result and the final database state. A correct response with corrupted counts is still a failed test.

---

# 17. Security and privacy checklist

- [ ] Firebase ID tokens are verified against the configured Firebase project.
- [ ] `firebase_uid` is unique and maps to an internal QueueLess user.
- [ ] Database roles and office/counter assignments are authoritative.
- [ ] Unknown identities receive only a citizen role or controlled onboarding response.
- [ ] Inactive users and invalid/revoked tokens are denied.
- [ ] No QueueLess OTP challenge or refresh-token table/endpoint exists.
- [ ] Firebase ID tokens and service-account credentials are never logged.
- [ ] QR references are stored only as hashes.
- [ ] QR response uses `Cache-Control: no-store`.
- [ ] QR references and OTPs are not included in analytics or error telemetry.
- [ ] Citizen ownership is enforced server-side.
- [ ] Officer office/counter assignment is enforced server-side.
- [ ] Admin office scope is enforced server-side.
- [ ] Public slot endpoints do not reveal citizen information.
- [ ] Database uses least-privilege credentials.
- [ ] Secrets are in environment configuration, not source control.
- [ ] Request logs redact authorization headers and sensitive body fields.
- [ ] Audit events are append-only and do not include secrets.
- [ ] API errors do not expose SQL, stack traces or other citizens' records.

---

# 18. Integration contract with each member

## With Member 2

Provide:
- authenticated user model and `get_current_user`;
- officer assignment authorization helper;
- office/service identifiers and timezone;
- appointment status and check-in window;
- QR reference hash/lookup/lock/consume interface;
- shared audit-event format;
- shared transaction/session convention.

Agree explicitly whether the check-in service owns one transaction that updates the QR reference, appointment status and queue-token row. The required outcome is atomic check-in and exactly one token per appointment.

## With Member 3

Provide:
- OpenAPI documentation;
- auth token storage/transport convention;
- appointment list/detail response shapes;
- slot availability response shape;
- booking/cancel/reschedule request examples;
- QR rotation response and no-store behavior;
- typed error response examples;
- pagination and timezone rules.

Frontend must never send `citizen_id` as the authority for booking. Backend derives the citizen from the session.

## With Member 4

Provide:
- common user identity and role contract;
- file/document module authentication convention;
- office/service catalogue IDs;
- test users and test fixtures;
- integration environment and database reset steps.

Member 4's OCR/RAG work must not be allowed to block appointment booking or core queue functionality.

---

# 19. Git workflow and daily working habits

Suggested branch names:

- `feature/member1-db-foundation`
- `feature/member1-auth`
- `feature/member1-slot-generation`
- `feature/member1-appointments`
- `feature/member1-qr-rotation`
- `test/member1-concurrency`

Rules:
1. Pull the latest development branch before starting a task.
2. Keep each branch focused on one feature.
3. Add migrations with the model changes they support.
4. Add tests in the same pull request.
5. Never commit `.env`, database dumps, OTP values or secrets.
6. Do not edit Member 2's queue state machine without agreement.
7. Request review from at least one teammate for shared models/migrations.
8. Merge only after tests and migration checks pass.
9. Do not rewrite shared migration history after teammates have applied it.

Daily update format:

```text
Completed:
- ...

Working on:
- ...

Blocked by:
- ...

API/schema changes for teammates:
- ...

Tests:
- Passed:
- Failing:
```

---

# 20. Priority order if time is limited

Do not attempt every feature at once. Protect the core citizen journey.

## P0: Must complete

1. PostgreSQL models and migrations.
2. Demo authentication and role authorization.
3. Office/service catalogue and seeded demo data.
4. Slot generation and persisted capacity.
5. Atomic appointment booking.
6. Appointment listing and ownership checks.
7. Cancellation and rescheduling.
8. Initial QR reference issue and QR rotation.
9. Idempotency for booking.
10. Integration contract with Member 2 and Member 3.
11. Core concurrency and security tests.

## P1: Complete after P0 is stable

1. Full refresh-token family reuse detection.
2. Admin policy management UI/API.
3. Advanced policy version migration handling.
4. Extended audit search/reporting.
5. More detailed rate-limit and abuse detection.
6. Expanded pagination/filtering.

Do not sacrifice booking transaction correctness to add optional account/profile features.

---

# 21. Final handoff checklist

Member 1 can mark the module ready only when all applicable boxes are checked.

## Backend foundation
- [ ] FastAPI app starts from documented command.
- [ ] PostgreSQL connection is configured through environment.
- [ ] Alembic migrations run on a clean database.
- [ ] Seed data creates a demo office, services and role-specific users.
- [ ] OpenAPI documentation is available.

## Authentication
- [ ] Firebase Phone Authentication works in the configured project.
- [ ] FastAPI verifies Firebase ID tokens and rejects invalid/wrong-project tokens.
- [ ] Internal user provisioning and database-backed role authorization work.
- [ ] No custom QueueLess OTP or refresh-token flow remains.
- [ ] Role and resource authorization tests pass.

## Slots and appointments
- [ ] Slot generation uses active eligible counters and policy version.
- [ ] Block-level walk-in reserve is calculated correctly.
- [ ] Quotient/remainder distribution matches the specification.
- [ ] Zero-capacity slots are CLOSED.
- [ ] Slot generation is idempotent.
- [ ] Booking is transactional and concurrency-safe.
- [ ] Duplicate active bookings are prevented.
- [ ] Cancellation releases capacity exactly once.
- [ ] Rescheduling reserves/releases capacity atomically.
- [ ] Appointment history is preserved.

## QR
- [ ] Raw QR reference is never stored.
- [ ] Raw QR reference is never logged.
- [ ] Initial reference is returned once at booking.
- [ ] Owner can rotate QR after reload.
- [ ] Rotation invalidates old unused references atomically.
- [ ] Rotation rate limit works.
- [ ] QR response is no-store.
- [ ] Member 2 has a tested reference-consumption integration contract.

## Handoff and release
- [ ] Member 2 has authorization and QR service contracts.
- [ ] Member 3 has OpenAPI examples and test credentials.
- [ ] Member 4 has test environment and seed instructions.
- [ ] PostgreSQL concurrency tests pass.
- [ ] Security checklist is complete.
- [ ] Known limitations are documented.
- [ ] Feature branch is merged after review.

---

# 22. The first five concrete actions

Start in this order:

1. **Meet Member 2 for a 30-minute API/data ownership agreement.** Finalize shared office/service IDs, appointment statuses, check-in-window fields, QR-reference interface and transaction ownership.
2. **Create the backend skeleton and PostgreSQL/Alembic setup.** Make sure every teammate can run it locally.
3. **Create the first migration for users, offices, services, policies, appointment slots and appointments.** Review the schema with Member 2 before merging.
4. **Implement and test authentication/authorization.** Do not start booking endpoints until user identity and ownership checks are reliable.
5. **Implement slot generation and atomic booking before building extra features.** This is the foundation of the citizen appointment journey.

**Member 1's success metric:** a citizen can securely sign in, book one of the persisted available slots without overbooking, recover a fresh QR after reloading, and remain unable to access another citizen's booking.
