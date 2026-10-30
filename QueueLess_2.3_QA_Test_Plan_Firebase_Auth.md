> **AUTHENTICATION UPDATE (30 October 2026):** Firebase Authentication is the sole citizen phone-OTP identity provider. The Firebase client SDK performs phone verification and manages ID-token refresh; FastAPI verifies Firebase ID tokens with Firebase Admin SDK; PostgreSQL stores QueueLess profiles and roles. The Firebase QA addendum below is normative and supersedes legacy demo-OTP, custom JWT issuance, and custom refresh-token test cases retained in older sections. Do not implement `otp_challenges`, QueueLess OTP endpoints, or a QueueLess refresh-token table.

# QueueLess 2.3

## QA Plan, Test Matrix and Acceptance Criteria

**Version:** 1.0\
**Date:** 30 October 2026\
**Companion document:** QueueLess 2.3 Implementation-Ready Technical Specification (Firebase Auth update)

------------------------------------------------------------------------

## 1. Purpose

This document defines the minimum tests required to demonstrate that
QueueLess works safely and consistently. It focuses on the high-risk
areas identified in the specification review:

-   Appointment capacity and concurrency.
-   QR check-in and replay protection.
-   Queue selection and token state transitions.
-   Authorization and document privacy.
-   RAG citations and refusal behavior.
-   OCR failure and manual fallback.
-   WebSocket reconnect and state recovery.
-   Offline manual reconciliation.
-   Analytics correctness.

A feature is not complete merely because its screen renders. Its backend
rules, failure paths and audit records must also behave correctly.



## Firebase Authentication QA addendum (normative)

The following cases replace the legacy demo-OTP and QueueLess-managed refresh-token tests. QueueLess must not implement its own citizen OTP challenge store or refresh-token rotation.

| ID | Test | Expected result |
|---|---|---|
| FB-AUTH-01 | Sign in with a configured Firebase test phone number | Firebase completes verification; client receives an authenticated Firebase user |
| FB-AUTH-02 | Call a protected API with a valid ID token from the configured Firebase project | FastAPI verifies the token and resolves the internal QueueLess user |
| FB-AUTH-03 | Call a protected API without an Authorization header | `401`; no protected data is returned |
| FB-AUTH-04 | Send a malformed, expired, or tampered ID token | `401`; token details are not exposed |
| FB-AUTH-05 | Send a valid ID token issued by a different Firebase project | `401`; wrong issuer/audience/project is rejected |
| FB-AUTH-06 | Send a revoked token when revocation checking is enabled for that route | `401`; access is denied |
| FB-AUTH-07 | Firebase UID has no QueueLess user profile | Safe citizen provisioning or controlled onboarding response; never grant staff role |
| FB-AUTH-08 | Existing Firebase UID signs in again | Same internal QueueLess user is resolved; no duplicate profile is created |
| FB-AUTH-09 | Citizen attempts to submit `OFFICER` or `ADMIN` in profile payload | Role assignment is ignored/rejected; database role remains unchanged |
| FB-AUTH-10 | Citizen requests another user's appointment | `403` or non-disclosing `404`, according to API convention |
| FB-AUTH-11 | Inactive QueueLess user presents a valid Firebase ID token | `403`; inactive application account is blocked |
| FB-AUTH-12 | Client obtains a refreshed ID token through Firebase SDK and calls API | Request succeeds; no QueueLess refresh endpoint is involved |
| FB-AUTH-13 | Inspect application logs and telemetry during sign-in/API calls | No ID token, service-account secret, OTP or raw QR reference is logged |
| FB-AUTH-14 | Staff Firebase identity has no pre-provisioned staff mapping | Staff endpoints deny access |
| FB-AUTH-15 | Firebase Admin SDK is unavailable or misconfigured | Protected APIs fail closed with controlled `503`/`401` behavior; never bypass verification |
| FB-AUTH-16 | WebSocket ticket is requested through authenticated REST API | Ticket is short-lived, single-use and scoped to authorized topics |
| FB-AUTH-17 | Attempt WebSocket connection using Firebase ID token in URL | URL-token authentication is not supported; ticket flow is required |

### Firebase test setup

- Use Firebase Authentication test phone numbers in development/staging where possible; avoid sending real SMS during automated test runs.
- Keep Firebase project configuration and service-account credentials in environment/secret management, never in source control.
- Test both a valid Firebase identity with an existing QueueLess profile and a first-time identity requiring safe profile provisioning.
- Test citizen, officer, office-admin, inactive-user and unknown-user mappings.
- The PostgreSQL role and office/counter assignment must be checked independently of Firebase authentication.
- Firebase provider quotas, authorized domains, phone sign-in configuration and SMS region policy must be verified before the live demo.


## 2. Test environments and data

### 2.1 Environments

  -----------------------------------------------------------------------
  Environment             Purpose                 Data
  ----------------------- ----------------------- -----------------------
  Local development       Unit and integration    Synthetic
                          tests                   

  Staging/demo            End-to-end and judge    Synthetic only
                          rehearsal               

  Pilot environment       Only after formal       Lawfully collected,
                          approval                minimized data
  -----------------------------------------------------------------------

### 2.2 Seed data

Create deterministic seed data:

-   One fictional office.
-   One Income Certificate service.
-   Two active counters, both supporting the service.
-   Two officer accounts, each assigned to a counter.
-   One office admin.
-   At least five fictional citizens.
-   Several 10-minute appointment slots.
-   A mix of appointment and walk-in tokens.
-   Synthetic document images/PDFs in English and Kannada if Kannada OCR
    is claimed.
-   A small, manually verified source corpus.

Do not use real Aadhaar numbers or real citizen documents.

## 3. Acceptance criteria by feature

### 3.1 P0 core journey

  -----------------------------------------------------------------------
  ID                                  Acceptance criterion
  ----------------------------------- -----------------------------------
  P0-01                               Citizen can sign in through Firebase Phone Authentication and obtain a valid Firebase ID token

  P0-02                               Citizen can browse an active
                                      service and its current checklist

  P0-03                               Citizen can see only available
                                      future appointment slots

  P0-04                               Citizen can book a slot without
                                      exceeding capacity

  P0-05                               Booking returns a QR reference that
                                      contains no personal data

  P0-06                               Authorized officer can check in the
                                      citizen inside the configured
                                      window

  P0-07                               Exactly one queue token is created
                                      for one appointment

  P0-08                               Officer can call next, start and
                                      complete the token

  P0-09                               Citizen receives live queue updates

  P0-10                               Reconnecting the citizen client
                                      restores the latest state from REST

  P0-11                               Admin dashboard reflects the final
                                      token and booking data

  P0-12                               The complete demo works without
                                      direct database edits
  -----------------------------------------------------------------------

### 3.2 P1 RAG and OCR

  -----------------------------------------------------------------------
  ID                                  Acceptance criterion
  ----------------------------------- -----------------------------------
  P1-01                               Every authoritative RAG claim
                                      includes a verified source citation

  P1-02                               Unverified/inactive sources are not
                                      used as authoritative evidence

  P1-03                               Assistant refuses or qualifies
                                      answers not supported by retrieved
                                      sources

  P1-04                               Assistant does not invent fees,
                                      eligibility, deadlines or
                                      processing time

  P1-05                               OCR result is labelled preliminary
                                      and includes uncertainty

  P1-06                               OCR failure does not block
                                      appointment booking

  P1-07                               Citizen can manually confirm
                                      document category/checklist status

  P1-08                               Citizen cannot access another
                                      citizen's uploaded file or OCR
                                      result

  P1-09                               No real sensitive identity data
                                      appears in logs or demo artifacts
  -----------------------------------------------------------------------

## 4. Appointment and capacity tests

  -----------------------------------------------------------------------
  ID                      Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  AP-01                   Book a slot with        Appointment created;
                          remaining capacity      `booked_count`
                                                  increments once

  AP-02                   Book a full slot        `SLOT_FULL`; no
                                                  appointment created

  AP-03                   Two citizens            Exactly one booking
                          simultaneously request  succeeds
                          the final slot          

  AP-04                   Same booking request    Same booking result
                          retried with same       returned; no duplicate
                          idempotency key         row

  AP-05                   Same citizen submits    Duplicate rejected
                          duplicate active        
                          booking for same        
                          service/office/slot     

  AP-06                   Cancel a booked         Appointment becomes
                          appointment             `CANCELLED`; slot
                                                  capacity released once

  AP-07                   Cancel request retried  No double decrement

  AP-08                   Reschedule to an        New row created; old
                          available slot          row marked
                                                  `RESCHEDULED`; both
                                                  linked

  AP-09                   Reschedule to a full    Entire transaction
                          slot                    rolls back; old booking
                                                  remains active

  AP-10                   Two citizens            Only one succeeds
                          simultaneously          
                          reschedule into the     
                          last slot               

  AP-11                   Reschedule old          Rejected unless a
                          appointment after it is specifically approved
                          already checked in      operational rule exists

  AP-12                   Admin reduces counter   Existing confirmed
                          availability below      bookings are not
                          existing bookings       silently deleted or
                                                  overbooked; conflict is
                                                  surfaced
  -----------------------------------------------------------------------

### 4.1 Capacity invariant

For every slot:

`0 <= booked_count <= capacity`

The number of active appointments for the slot must equal `booked_count`
if using a maintained counter. Add a reconciliation query/test to detect
drift.

## 5. QR and check-in tests

  -----------------------------------------------------------------------
  ID                      Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  QR-01                   Valid QR, correct       Appointment checked in
                          office, inside check-in and one token created
                          window                  

  QR-02                   Scan same QR a second   `QR_ALREADY_USED` or
                          time                    `ALREADY_CHECKED_IN`;
                                                  no new token

  QR-03                   Two officers scan same  One transaction
                          QR simultaneously       succeeds; one token
                                                  total

  QR-04                   QR has expired          `QR_EXPIRED`; no state
                                                  change

  QR-05                   QR belongs to another   Rejected; no data
                          office                  leakage

  QR-06                   Appointment is          Rejected
                          cancelled               

  QR-07                   Appointment was         Old QR rejected; new QR
                          rescheduled             works for new
                                                  appointment

  QR-08                   QR reference is         Generic
                          random/unknown          invalid-reference
                                                  response

  QR-09                   Citizen attempts        `403 Forbidden`
                          officer-only check-in   
                          endpoint                

  QR-10                   QR raw reference        Test fails; secrets
                          appears in application  must be redacted
                          logs                    
  -----------------------------------------------------------------------

### 5.1 QR invariant

For every appointment:

-   At most one successful check-in.
-   At most one linked queue token.
-   A used or invalidated QR cannot be reused.
-   A QR never contains citizen PII.

## 6. Queue policy and token state tests

### 6.1 Deterministic selection tests

  -----------------------------------------------------------------------
  ID                      Queue contents          Expected `call-next`
                                                  result
  ----------------------- ----------------------- -----------------------
  Q-01                    Two eligible            Earliest appointment
                          appointments with       slot
                          different slot start    
                          times                   

  Q-02                    Two eligible            Earlier check-in time
                          appointments with same  
                          slot time               

  Q-03                    Appointment tie on time Stable token creation
                          and check-in            time/ID tie-break

  Q-04                    No eligible             Oldest walk-in
                          appointment; two        
                          walk-ins                

  Q-05                    Appointment exists but  It is not eligible
                          is not checked in       

  Q-06                    Appointment check-in    It is not eligible as
                          window has closed       appointment

  Q-07                    No waiting tokens       Typed no-eligible-token
                                                  response

  Q-08                    Counter does not        Token is not assigned
                          support token service   

  Q-09                    Counter inactive or     Call-next rejected
                          officer unassigned      

  Q-10                    Counter already has a   Second call-next
                          called/serving token    rejected

  Q-11                    Walk-in target is below Dashboard reports
                          actual share            actual share;
                                                  appointment priority
                                                  rule remains
                                                  deterministic

  Q-12                    Appointment queue empty Oldest eligible walk-in
                          and walk-ins waiting    is selected
  -----------------------------------------------------------------------

### 6.2 State transition tests

  -----------------------------------------------------------------------
  ID                      Transition              Expected
  ----------------------- ----------------------- -----------------------
  ST-01                   `WAITING → CALLED`      Allowed for authorized
                                                  call-next

  ST-02                   `WAITING → CANCELLED`   Allowed with reason and
                                                  authorization

  ST-03                   `CALLED → SERVING`      Allowed for assigned
                                                  officer

  ST-04                   `CALLED → NO_SHOW`      Allowed only after
                                                  retry policy and
                                                  officer confirmation

  ST-05                   `CALLED → WAITING`      Allowed only as
                                                  explicit call
                                                  withdrawal with reason

  ST-06                   `SERVING → COMPLETED`   Allowed

  ST-07                   `SERVING → ON_HOLD`     Allowed with reason

  ST-08                   `ON_HOLD → WAITING`     Allowed

  ST-09                   `ON_HOLD → CANCELLED`   Allowed with reason and
                                                  authorization

  ST-10                   `WAITING → COMPLETED`   Rejected

  ST-11                   `COMPLETED → WAITING`   Rejected

  ST-12                   `NO_SHOW → SERVING`     Rejected

  ST-13                   Counter transfer while  Rejected in MVP
                          `SERVING`               

  ST-14                   Two officers transition Only one valid
                          same token              transition succeeds
                          simultaneously          

  ST-15                   Invalid transition      No state change;
                          attempted               rejected attempt may be
                                                  security/audit logged
  -----------------------------------------------------------------------

### 6.3 No-show distinction

Test and report separately:

-   Appointment no-show: appointment was never checked in before the
    window closed.
-   Token no-show: token was checked in, called, and not answered after
    retries.

A dashboard must not combine these counts.

## 7. Authorization and privacy tests

  ---------------------------------------------------------------------------
  ID                      Scenario                    Expected result
  ----------------------- --------------------------- -----------------------
  SEC-01                  Citizen reads own           Allowed
                          appointment                 

  SEC-02                  Citizen reads another       `403` or non-disclosing
                          citizen's appointment       `404`

  SEC-03                  Citizen downloads another   Denied
                          citizen's document          

  SEC-04                  Officer views assigned      Allowed
                          office queue                

  SEC-05                  Officer views unrelated     Denied
                          office queue                

  SEC-06                  Officer acts on unassigned  Denied
                          counter                     

  SEC-07                  Citizen calls officer-only  Denied
                          endpoint                    

  SEC-08                  Non-admin changes           Denied
                          service/checklist/counter   
                          settings                    

  SEC-09                  Expired access token used   Rejected

  SEC-10                  Firebase sign-in abuse / provider rate limit    Temporarily
                                                      blocked/rate limited

  SEC-11                  Firebase SMS resend abuse             Cooldown/rate limit
                                                      enforced

  SEC-12                  Upload exceeds configured   Rejected before OCR
                          size                        

  SEC-13                  File extension and MIME     Rejected
                          signature mismatch          

  SEC-14                  User guesses another        No access
                          storage key                 

  SEC-15                  Logs inspected for Firebase tokens, QR  Sensitive values
                          raw value or document text  absent/redacted
  ---------------------------------------------------------------------------

## 8. RAG tests

Prepare a small gold set of questions whose answers are explicitly
supported by the curated corpus.

  -----------------------------------------------------------------------
  ID                      Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  RAG-01                  Question directly       Answer with matching
                          answered by verified    citation
                          source                  

  RAG-02                  Question not covered by Assistant says it
                          corpus                  cannot confirm

  RAG-03                  Only inactive source    Source is not used as
                          contains answer         authoritative

  RAG-04                  Source URL is           Source marked
                          unreachable during      unverified/failed
                          ingestion               

  RAG-05                  Source has old visible  Staleness flagged for
                          update date             human review

  RAG-06                  User asks for an        No invented value
                          unsupported             
                          fee/deadline            

  RAG-07                  Retrieved text contains Treated as untrusted
                          instruction-like prompt content, not system
                          injection               instruction

  RAG-08                  Citation URL does not   Test fails
                          match retrieved chunk   
                          metadata                

  RAG-09                  English question        Language quality
                                                  assessed against gold
                                                  answer

  RAG-10                  Kannada question, if    Kannada test set
                          claimed                 evaluated separately

  RAG-11                  Hindi question, if      Hindi test set
                          claimed                 evaluated separately

  RAG-12                  User includes personal  Data is not added to
                          document data in chat   persistent RAG corpus
  -----------------------------------------------------------------------

Record source, expected facts, actual answer, citation correctness and
reviewer outcome. Do not use model confidence alone as proof of factual
correctness.

## 9. OCR tests

  ---------------------------------------------------------------------------
  ID                      Input                       Expected behavior
  ----------------------- --------------------------- -----------------------
  OCR-01                  Clean English scan          Extract text/category
                                                      candidate where
                                                      supported

  OCR-02                  Clean Kannada scan          Evaluate separately;
                                                      disclose limitations

  OCR-03                  Blurry phone photo          Low confidence or
                                                      `NEEDS_REVIEW`

  OCR-04                  Rotated image               Correct if engine
                                                      supports it, otherwise
                                                      manual fallback

  OCR-05                  Shadowed/low-light image    Low confidence/manual
                                                      fallback

  OCR-06                  Compressed/low-resolution   Failure does not block
                          image                       booking

  OCR-07                  Mixed-script document       Manual review if
                                                      uncertain

  OCR-08                  Unsupported file type       Rejected

  OCR-09                  Oversized file or excessive Rejected with clear
                          PDF pages                   message

  OCR-10                  OCR engine unavailable      `OCR_FAILED`; manual
                                                      checklist continues

  OCR-11                  Category confidence below   `NEEDS_REVIEW`
                          threshold                   

  OCR-12                  Citizen chooses manual      Readiness workflow
                          category                    continues

  OCR-13                  Uploaded document belongs   Access denied
                          to another user             
  ---------------------------------------------------------------------------

The report must distinguish OCR extraction success from checklist
completeness. A detected document is not proof of legal validity.

## 10. WebSocket and recovery tests

  -----------------------------------------------------------------------
  ID                      Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  WS-01                   Citizen connected       Authorized status event
                          during                  received
                          `WAITING → CALLED`      

  WS-02                   Citizen disconnected    Reconnect REST fetch
                          during state change     returns latest state

  WS-03                   Client reconnects after Latest state replaces
                          multiple events         stale local state

  WS-04                   User subscribes to      Subscription denied
                          another citizen's topic 

  WS-05                   Citizen subscribes to   Denied
                          unrelated               
                          office-private channel  

  WS-06                   WebSocket event is      Test fails; event must
                          published before DB     follow commit
                          commit                  

  WS-07                   Process stops after DB  Outbox record remains
                          commit but before       for retry
                          publish                 

  WS-08                   Duplicate event         Client handles
                          delivered               idempotently using
                                                  event/entity version

  WS-09                   Event payload inspected No document contents or
                                                  unnecessary PII

  WS-10                   WebSocket unavailable   Core REST workflow
                                                  remains usable
  -----------------------------------------------------------------------

## 11. Analytics tests

Use fixed seed timestamps and assert exact outputs.

  --------------------------------------------------------------------------
  Metric                              Definition
  ----------------------------------- --------------------------------------
  Appointment bookings                Count of appointment records created
                                      in selected period, with status
                                      breakdown

  Appointment no-shows                Appointments marked `NO_SHOW` without
                                      check-in

  Walk-ins                            Tokens with source `WALK_IN`

  Current waiting                     Tokens currently in `WAITING`

  Currently serving                   Tokens currently in `SERVING`

  Completed                           Tokens in `COMPLETED`

  Waiting time                        `service_started_at - checked_in_at`

  Service duration                    `completed_at - service_started_at`

  Token no-show                       Called tokens marked `NO_SHOW` after
                                      retry process
  --------------------------------------------------------------------------

Exclude cancelled and no-show tokens from completed-service duration
statistics. Display reporting period, sample size and time zone. Verify
median calculation for both odd and even sample counts.

## 12. Offline reconciliation tests

  -----------------------------------------------------------------------
  ID                      Scenario                Expected result
  ----------------------- ----------------------- -----------------------
  OFF-01                  Network unavailable     Officer sees/uses
                                                  documented
                                                  paper-register
                                                  procedure

  OFF-02                  Citizen checks live     UI does not falsely
                          status while system     claim real-time status
                          offline                 

  OFF-03                  Officer enters offline  Source is
                          record after reconnect  `OFFLINE_REGISTER`;
                                                  original event time
                                                  retained

  OFF-04                  Offline record          Flag as possible
                          resembles an existing   duplicate; do not
                          token                   auto-merge

  OFF-05                  Unauthorized user       Denied
                          enters offline records  

  OFF-06                  Manual reconciliation   Actor, time, reason and
                          performed               original reference
                                                  audited
  -----------------------------------------------------------------------

## 13. End-to-end demo test

Run this exact scenario before the presentation:

1.  Open citizen browser and sign in with Firebase Phone Authentication using a configured test number.
2.  Browse Income Certificate service.
3.  Ask a question that has a verified answer in the RAG corpus.
4.  Confirm the answer includes the correct source.
5.  Upload a synthetic sample document.
6.  Confirm OCR result and preliminary checklist status.
7.  Force an OCR failure or low-confidence case and demonstrate manual
    fallback.
8.  Book the final available slot.
9.  In a second browser, sign in as the assigned officer.
10. Scan the QR reference and confirm exactly one token is created.
11. Attempt to scan the same QR again and show rejection.
12. Call next, start service and complete the token.
13. Confirm citizen receives live updates.
14. Disconnect/reconnect the citizen browser and verify final state is
    restored.
15. Open admin dashboard and verify completed token and analytics.
16. Confirm no manual database edit was required.

## 14. Release gates

### Gate A: P0 can be demonstrated

-   All P0 acceptance criteria pass.
-   Appointment and QR concurrency tests pass.
-   Queue state-machine tests pass.
-   Authorization tests pass.
-   Citizen reconnect recovery works.

### Gate B: P1 can be demonstrated

-   RAG citations point to verified source chunks.
-   Unsupported questions are handled safely.
-   OCR test gate has been run and its limitations documented.
-   OCR manual fallback works.
-   No sensitive sample data is exposed.

### Gate C: demo-ready

-   End-to-end demo passes three consecutive times.
-   No database edits or manual server-side intervention are needed.
-   Synthetic data is labelled.
-   All known limitations are disclosed.
-   A backup demo path exists if external LLM/OCR provider is
    unavailable.

## 15. Defect severity

  -----------------------------------------------------------------------
  Severity                Definition              Release action
  ----------------------- ----------------------- -----------------------
  Critical                Data exposure,          Block release
                          duplicate               
                          booking/token,          
                          unauthorized state      
                          change, wrong citizen   
                          record                  

  High                    Core journey broken, QR Block affected feature
                          replay accepted,        
                          incorrect queue         
                          transition, major RAG   
                          misinformation          

  Medium                  Noncritical             Fix or disclose
                          analytics/UI            
                          inconsistency,          
                          recoverable             
                          notification failure    

  Low                     Cosmetic issue or minor May defer
                          wording                 
  -----------------------------------------------------------------------

------------------------------------------------------------------------

**End of QueueLess 2.2 QA Plan**


---

# QueueLess 2.3 QA Amendment: Additional Concurrency, Lifecycle and Resilience Coverage

**Precedence:** This amendment extends the 2.2 test plan and supersedes any conflicting expected behavior. All times below use a fixed test clock and `Asia/Kolkata` unless a test explicitly covers UTC conversion.

## 1. Slot capacity derivation

| ID | Scenario | Expected result |
|---|---|---|
| CAP-01 | Two counters, 10-minute service, 20% walk-in reserve, six slots | Block capacity 12, reserve 2, appointment capacity 10; slot capacities exactly `2,2,2,2,1,1` |
| CAP-02 | One counter, same settings | Block capacity 6, reserve 1, appointment capacity 5; slot capacities `1,1,1,1,1,0`; zero-capacity slot is `CLOSED` |
| CAP-03 | Slot generator reruns for same policy version and operating block | Idempotent result; no duplicate slots or capacity drift |
| CAP-04 | Counter becomes unavailable before slot generation | Capacity reflects active staffed counters |
| CAP-05 | Counter becomes unavailable after confirmed bookings exist | No silent overbooking; admin receives a conflict requiring explicit resolution |
| CAP-06 | Admin changes reserve or service duration | New policy version applies only to future unbooked slots unless an audited migration is explicitly approved |

## 2. Idempotency and token numbering

| ID | Scenario | Expected result |
|---|---|---|
| IDEM-01 | Same actor, scope, key and identical payload retried | Original response returned; one side effect |
| IDEM-02 | Same actor, scope and key reused with a different payload | `409 IDEMPOTENCY_KEY_REUSED`; no second side effect |
| IDEM-03 | Two actors use the same key | Keys are scoped by actor; requests do not collide |
| TOK-01 | 50 concurrent walk-in creations for same office/service/operating date | All successful tokens have unique sequential numbers; no duplicates |
| TOK-02 | Concurrent appointment check-ins and walk-in creation | Token numbers remain unique across both creation paths |
| TOK-03 | Token creation at 23:59:59 IST and 00:00:01 IST | First token uses prior local operating date; second uses new local operating date and sequence |
| TOK-04 | UTC date differs from IST date at token creation | `operating_date` follows office-local date, not UTC date |
| TOK-05 | A token remains active after midnight | Its original operating date and number do not change |

## 3. QR rotation and check-in API

| ID | Scenario | Expected result |
|---|---|---|
| QR-11 | Citizen reloads appointment page and selects Show QR | New QR reference returned; no raw reference is read from database |
| QR-12 | Citizen rotates QR twice | First reference invalidated; only newest reference can check in |
| QR-13 | Rotation request fails before commit | Existing QR remains valid; no partial invalidation |
| QR-14 | Non-owner attempts QR rotation | `403`; no reference changes |
| QR-15 | Citizen rotates QR after check-in or cancellation | Rejected with typed state error |
| QR-16 | Rate limit exceeded | `429`; current valid QR remains valid |
| QR-17 | Officer scans `POST /checkin` with only reference in body | Appointment is resolved from hash and checked in exactly once |
| QR-18 | QR scan endpoint receives appointment ID but no reference | Validation failure; QR route does not require appointment ID |
| QR-19 | Officer uses manual check-in endpoint with authorized appointment ID and reason | Check-in succeeds and audit event records officer and reason |
| QR-20 | Unauthorized officer attempts manual check-in for another office | `403`; no state changes |

## 4. Queue selection, multi-counter race and fairness

| ID | Scenario | Expected result |
|---|---|---|
| Q-11 | Two officers on different counters press call-next simultaneously while exactly one eligible token is waiting | Exactly one counter receives the token; the other receives `NO_ELIGIBLE_TOKEN`; no duplicate assignment |
| Q-12 | Two counters call-next with two waiting tokens | Each counter receives a different token; neither token is assigned twice |
| Q-13 | Oldest walk-in exceeds configured 45-minute cap while appointment tokens wait | Oldest overdue walk-in is promoted and event records `promoted_for_fairness=true` |
| Q-14 | Walk-in is below cap while eligible appointment waits | Appointment is selected under default appointment-first policy |
| Q-15 | Multiple overdue walk-ins | Oldest overdue walk-in wins; deterministic tie-breakers apply |
| Q-16 | Walk-in cap disabled by admin | Dashboard displays starvation-risk warning; policy change is audited |
| Q-17 | Walk-in cap changed while tokens are waiting | Effective policy version is applied consistently and recorded on subsequent call events |

## 5. Hold/resume and analytics

| ID | Scenario | Expected result |
|---|---|---|
| HOLD-01 | `SERVING → ON_HOLD → SERVING → COMPLETED` | Valid transitions; same counter retained |
| HOLD-02 | Attempt `ON_HOLD → WAITING` | Rejected with `INVALID_TOKEN_TRANSITION` |
| HOLD-03 | Resume held token | `service_started_at` remains the first start timestamp; `last_resumed_at` updates |
| HOLD-04 | Multiple hold/resume cycles | `total_hold_seconds` equals sum of completed hold intervals |
| HOLD-05 | Token completes after one hold | Gross duration and active duration match independently calculated values |
| HOLD-06 | Held token is cancelled by authorized officer | Reason required; hold interval is closed and audited |
| HOLD-07 | Analytics for held token | Queue waiting time ends at first service start; active service duration excludes holds |

## 6. Durable scheduler and operating-date boundaries

| ID | Scenario | Expected result |
|---|---|---|
| JOB-01 | Appointment check-in window closes and periodic sweep runs | Appointment becomes `NO_SHOW`; audit and outbox records created |
| JOB-02 | Sweep runs twice for same appointment | One state transition and one logical no-show event |
| JOB-03 | Two worker instances sweep same batch | Row locking/conditional update prevents duplicate processing |
| JOB-04 | Scheduler is delayed or unavailable | Lazy check on appointment read/call-next prevents expired appointment remaining eligible |
| JOB-05 | Reminder job has no provider configured | `NOT_CONFIGURED`; never marked sent |
| JOB-06 | Reminder provider transient failure | Retry metadata persists; retry does not duplicate successful delivery |
| JOB-07 | Check-in window closes at midnight IST while UTC date is previous day | No-show processing uses the correct absolute timestamp and office-local policy date |
| JOB-08 | Appointment is checked in at the last valid second | Sweep and check-in serialize safely; exactly one valid terminal outcome |

## 7. Provider outage, injection and markup safety

| ID | Scenario | Expected result |
|---|---|---|
| AI-OUT-01 | LLM provider unavailable | Assistant shows temporary-unavailable state and official portal/contact fallback; queue and booking remain operational |
| AI-OUT-02 | Embedding/vector provider unavailable | No ungrounded generated answer; retrieval failure is surfaced and logged |
| OCR-OUT-01 | OCR provider unavailable | Document state becomes `UNAVAILABLE` or `FAILED_RETRYABLE`; manual checklist path remains available |
| OCR-OUT-02 | OCR provider times out repeatedly | Bounded retries, durable failure state and no blocked appointment booking |
| INJ-01 | Prompt injection submitted in citizen chat | Treated as untrusted input; system instructions and data boundaries remain intact |
| INJ-02 | Prompt injection embedded in retrieved source text | Retrieved text cannot override system policy or cause secret disclosure |
| XSS-01 | Chat contains HTML/script markup | Rendered as escaped text; no script execution |
| XSS-02 | Citation title, URL label or source snippet contains HTML/JavaScript | Rendered safely; link destination validated; no script execution |
| XSS-03 | OCR-extracted text contains markup | Displayed as escaped text and never injected into DOM |
| SEC-WS-01 | WebSocket connection attempts token in query string | Rejected or ignored; credential is never accepted from URL |
| SEC-WS-02 | WebSocket ticket replayed | Second use rejected |
| SEC-WS-03 | Logs inspected after WebSocket authentication | No Firebase ID token, refresh token, OTP or ticket value appears |

## 8. Updated demo source gate

| ID | Scenario | Expected result |
|---|---|---|
| SRC-01 | Team opens the Directorate of Minorities PSI Training document-verification PDF directly before event | Source is marked `VERIFIED` only after direct inspection and capture of title, date, issuing authority and exact relevant text |
| SRC-02 | PDF cannot be opened or inspected before event | Source remains `PRIMARY_SOURCE_PENDING_MANUAL_FETCH`; excluded from live RAG demo |
| SRC-03 | User asks about general Income Certificate application requirements using PSI Training notice | Assistant states the source does not establish that checklist and refuses to generalize |
| SRC-04 | User asks the narrowly scoped PSI Training document-verification question | Assistant answers only from inspected notice, states date/scope and cites the source |

## 9. Release-gate additions

Gate A additionally requires CAP-01 through CAP-03, QR-11 through QR-20, IDEM-01/02, TOK-01 through TOK-05, Q-11 and HOLD-01 through HOLD-05 to pass.

Gate B additionally requires AI-OUT-01/02, OCR-OUT-01/02, INJ-01/02 and XSS-01/02 to pass.

Gate C additionally requires JOB-01 through JOB-08, Q-13, SEC-WS-01 through SEC-WS-03 and SRC-01 or the documented safe fallback from SRC-02 to pass.

A provider outage must never take down appointment booking, check-in, token calling or completion. The RAG feature may degrade independently.
