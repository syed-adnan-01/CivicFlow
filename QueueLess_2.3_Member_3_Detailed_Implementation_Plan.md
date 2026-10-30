# QueueLess 2.3 — Member 3 Detailed Implementation Plan
## Frontend Engineering: React, Vite, TypeScript, Tailwind CSS, Firebase Client Authentication, REST Integration and Live Queue Experience

**Document purpose:** A practical, implementation-ready plan for the frontend owner (Member 3). It defines screens, component architecture, frontend state, API integration, authentication behavior, WebSocket handling, validation, testing, milestones, ownership boundaries and handoff requirements.

**Baseline:** QueueLess 2.3 Implementation-Ready Technical Specification, Firebase Authentication amendment, Member 1 Firebase-updated Implementation Plan, and Member 2 Detailed Implementation Plan.

---

# 1. Mission and definition of done

Member 3 builds the complete browser experience that connects citizens, officers and office administrators to the QueueLess backend. The frontend must make the core workflow understandable and reliable without implementing business rules that belong in FastAPI.

The core experience is:

1. A citizen signs in through Firebase Authentication.
2. The citizen discovers a service and reviews its guidance/checklist.
3. The citizen chooses an office and available appointment slot.
4. The citizen books and receives a confirmation with a QR check-in reference.
5. At the office, an officer signs in and uses the officer interface to scan or manually enter the reference.
6. The backend validates the reference and creates one queue token.
7. The officer calls the next eligible token, starts service, and completes, holds or otherwise updates the token through permitted actions.
8. The citizen sees their queue status update live without manually refreshing.
9. The office administrator views basic operational analytics and configuration screens exposed by the backend.

The frontend is complete when the demo journey can be performed in two browser sessions without editing the database, using mock data in production-facing screens, or relying on optimistic state changes that can misrepresent backend state.

## 1.1 Member 3 success criteria

- React + Vite application runs from a documented command and has a reproducible build.
- Firebase client sign-in works with the configured Firebase project and the backend accepts its ID token.
- Route guards improve navigation, while backend authorization remains authoritative.
- Citizen can browse services, view details/checklists, see slots, book, view appointment details and display/rotate a QR reference.
- Officer can view their assigned queue, scan a QR or enter a reference manually, and operate tokens using the backend's allowed actions.
- Citizen queue tracking receives scoped live events and resynchronizes from REST after reconnect.
- Admin can view the agreed analytics and office configuration pages that are actually supported by backend endpoints.
- RAG/OCR pages consume Member 4's APIs and show citations, uncertainty and preliminary status correctly. They never present AI/OCR as official eligibility or legal validation.
- All important screens include loading, empty, error, permission-denied and stale-data states.
- No frontend path bypasses backend validation, invents queue state, or trusts a role supplied by the browser.

---

# 2. Product context and frontend scope

QueueLess is a citizen-visit preparation and physical-office queue coordination layer that complements official Karnataka service portals. It does not submit or approve government applications, determine legal eligibility, or replace official portals/officers without an authorized integration.

The frontend must communicate this boundary clearly. Service guidance and document checks are preliminary. The actual government application and official status remain with the relevant official portal or office.

## 2.1 Delivery tiers

| Tier | Frontend responsibility | Delivery rule |
|---|---|---|
| P0 core journey | Sign-in, service catalogue, appointment slots, booking, QR confirmation, officer check-in UI, queue operations UI, citizen live tracking | Must work end to end |
| P1 showcase | RAG assistant with citations; OCR document readiness report; basic admin analytics | Implement when stable APIs are supplied; show uncertainty and preliminary labels |
| P2 if time remains | Transparent waiting-time range, basic eligible-counter explanation, email notification preferences | Do not block P0 |
| Roadmap/mock only | Voice, advanced ML predictions, WhatsApp, waitlists, multi-office/district optimization | Label as future capability; do not imply it is implemented |

## 2.2 Technology choices

- React with Vite.
- TypeScript strongly recommended for API contracts and state safety.
- Tailwind CSS for styling.
- React Router (or the routing solution agreed by the team) for role-aware navigation.
- Firebase Web SDK for client authentication.
- A small typed `fetch`/Axios API layer. Choose one and use it consistently.
- Native WebSocket API for live queue updates.
- A QR rendering package for showing the opaque QR reference.
- Browser camera/QR scanning support where reliable, with manual-entry fallback.
- Vitest + React Testing Library for component/unit tests; Playwright or an equivalent browser test runner for end-to-end journeys if time permits.

Avoid adding Redux, a UI component framework, Socket.IO, a second backend, or a large state-management dependency unless a concrete need is agreed. Start with React Context for authentication and a small query/cache layer or explicit hooks for server data.

---

# 3. Ownership and boundaries

## 3.1 Member 3 owns

1. Frontend repository setup, build configuration, environment configuration and application shell.
2. Routing, layouts, navigation, responsive behavior and shared UI components.
3. Firebase client SDK integration and authenticated frontend session lifecycle.
4. Citizen sign-in and sign-out screens.
5. Citizen service catalogue, service detail, checklist and guidance views.
6. Appointment slot selection, booking form, confirmation and appointment history/detail screens.
7. QR display and QR rotation user experience using Member 1's API.
8. Citizen queue tracking and live updates using Member 2's APIs and WebSocket events.
9. Officer dashboard, queue list, counter status, check-in scanner/manual entry and action controls.
10. Admin dashboard and configuration UI for backend-supported features.
11. RAG assistant and OCR readiness UI by consuming Member 4's documented APIs.
12. Client-side input validation, error presentation, accessibility, responsive layouts and loading/empty states.
13. Frontend tests, integration verification, demo data presentation and UI documentation.
14. Coordination with backend members to freeze API contracts and report mismatches.

## 3.2 Member 3 does not own

| Capability | Owner | Member 3 responsibility |
|---|---|---|
| Firebase project setup, Admin SDK verification, internal user provisioning and authoritative roles | Member 1 / shared backend foundation | Use Firebase Web SDK and call the shared backend; do not create backend identities or roles |
| Appointment slot generation, booking capacity, cancellation/rescheduling transactions | Member 1 | Render backend availability and submit requests; never calculate authoritative capacity in the browser |
| QR reference generation, hashing, persistence and rotation rules | Member 1 | Display the returned raw reference/QR and invoke the rotation endpoint; never generate or store a replacement reference locally |
| QR consumption, manual check-in orchestration and queue-token creation | Member 2 | Capture/submit the reference to the check-in API; do not create tokens in the frontend |
| Queue state machine, call-next selection, fairness, counter locking and token numbering | Member 2 | Display server state and expose only permitted actions |
| WebSocket ticket issuance, authorization, event publication and queue state | Member 2 / shared backend | Request a ticket, connect, handle events and resync via REST |
| RAG retrieval, source verification, LLM prompts and answer policy | Member 4 | Display the returned answer, citations and uncertainty without inventing content |
| OCR extraction, classification, confidence and checklist result | Member 4 | Upload supported files and display the returned preliminary result |
| Firebase Admin service-account credentials | Member 1 | Never place credentials in Vite variables or frontend bundles |
| Database schema, SQL, migrations and direct database access | Members 1 and 2 | Use APIs only |

## 3.3 Non-negotiable frontend rules

- The backend is the source of truth for identity role, office assignment, booking availability, QR validity, check-in, token state, counter assignment and analytics.
- Hiding a button is not authorization. Every protected API call must still be authorized by FastAPI.
- Never accept a `role`, `user_id`, `office_id` or `counter_id` from a browser form as proof of permission. The backend derives or validates scope from the authenticated user and database assignments.
- Never create a queue token, mark an appointment checked in, call a token, or mark service complete by editing local state alone.
- Do not place Firebase ID tokens or WebSocket tickets in query strings, logs, analytics or error reports.
- Do not store raw QR references in localStorage, sessionStorage, analytics or console output. Render only as long as needed for the confirmation view and allow backend rotation if it is lost.
- Never put name, phone, Aadhaar number, document text or other personal data inside a QR code.
- Do not broadcast or display document contents, OCR text, phone numbers or full profile information in shared office queue views.
- Clearly label synthetic/demo data and preliminary AI/OCR outputs.

---

# 4. Application architecture

## 4.1 High-level flow

```text
React + Vite browser application
  |
  |-- Firebase Web SDK ----------------------> Firebase Authentication
  |       |                                      |
  |       | Firebase ID token                    | authenticated user session
  |       v                                      |
  |-- Typed REST client ------------------------+
  |       | Authorization: Bearer <ID token>
  |       v
  |    FastAPI /api/v1
  |       |-- Member 1: users, services, slots, appointments, QR reference issue/rotation
  |       |-- Member 2: check-in, queue tokens, counters, queue actions, WebSocket ticket/events
  |       |-- Member 4: assistant, documents, OCR and RAG APIs
  |       v
  |    PostgreSQL + private object storage + AI components
  |
  |-- Authenticated REST request for one-time WebSocket ticket
  |       v
  |    Native WebSocket (ticket only, no Firebase token in URL)
  |       v
  |    Scoped queue/appointment events
  |
  +-- On connect/reconnect/event gap: fetch authoritative REST snapshot
```

## 4.2 Frontend layers

1. **Presentation layer:** pages, layouts, design primitives, forms, tables and status components.
2. **Routing layer:** public routes, citizen routes, officer routes and office-admin routes.
3. **Session layer:** Firebase session observer, ID-token retrieval, sign-out and current-user profile loading.
4. **API layer:** typed request client, error normalization, endpoint modules and request cancellation.
5. **Feature layer:** service catalogue, appointments, QR, queue, check-in, analytics, assistant and documents.
6. **Realtime layer:** ticket request, WebSocket lifecycle, event validation, stale indicator and REST resync.
7. **Test layer:** unit, component, API-contract and end-to-end tests.

## 4.3 Suggested repository structure

```text
frontend/
├── public/
│   ├── favicon.svg
│   └── demo-assets/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   ├── providers.tsx
│   │   └── route-config.ts
│   ├── assets/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ErrorState.tsx
│   │   ├── layout/
│   │   │   ├── PublicLayout.tsx
│   │   │   ├── CitizenLayout.tsx
│   │   │   ├── OfficerLayout.tsx
│   │   │   └── AdminLayout.tsx
│   │   └── shared/
│   │       ├── PageHeader.tsx
│   │       ├── ConfirmDialog.tsx
│   │       ├── StatusBadge.tsx
│   │       ├── LoadingButton.tsx
│   │       └── LastUpdated.tsx
│   ├── features/
│   │   ├── auth/
│   │   │   ├── AuthProvider.tsx
│   │   │   ├── firebase.ts
│   │   │   ├── SignInPage.tsx
│   │   │   ├── useAuth.ts
│   │   │   └── auth.types.ts
│   │   ├── catalogue/
│   │   ├── assistant/
│   │   ├── documents/
│   │   ├── appointments/
│   │   ├── qr/
│   │   ├── citizen-queue/
│   │   ├── officer-queue/
│   │   ├── checkin/
│   │   └── admin/
│   ├── hooks/
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── errors.ts
│   │   │   ├── auth.api.ts
│   │   │   ├── catalogue.api.ts
│   │   │   ├── appointments.api.ts
│   │   │   ├── queue.api.ts
│   │   │   ├── checkin.api.ts
│   │   │   ├── admin.api.ts
│   │   │   ├── assistant.api.ts
│   │   │   └── documents.api.ts
│   │   ├── realtime/
│   │   │   ├── ticket.api.ts
│   │   │   ├── socket.ts
│   │   │   ├── event.types.ts
│   │   │   └── useQueueRealtime.ts
│   │   ├── validation/
│   │   ├── date-time.ts
│   │   └── format.ts
│   ├── types/
│   │   ├── api.ts
│   │   ├── user.ts
│   │   ├── appointment.ts
│   │   ├── queue.ts
│   │   └── service.ts
│   ├── styles/
│   │   └── index.css
│   └── main.tsx
├── tests/
│   ├── e2e/
│   ├── fixtures/
│   └── mocks/
├── .env.example
├── package.json
├── tsconfig.json
└── vite.config.ts
```

This is a suggested structure, not a requirement to create every file on day one. Keep modules feature-oriented and avoid one giant `App.tsx` or a single file containing all API calls.

---

# 5. UX flows and page inventory

## 5.1 Public and authentication pages

| Route | Page | Purpose |
|---|---|---|
| `/` | Landing page | Explain QueueLess and direct users to sign in or explore public services |
| `/sign-in` | Sign-in | Firebase phone authentication flow configured by Member 1/team |
| `/access-denied` | Access denied | Explain that the signed-in account lacks the required office role/assignment |
| `/not-found` | Not found | Friendly fallback |

Sign-in must not offer a role selector that can create an officer/admin. A new Firebase identity must receive the backend's default citizen role or controlled onboarding response. Officer/admin access is provisioned through trusted backend/database administration.

## 5.2 Citizen pages

| Route | Page | Key functions |
|---|---|---|
| `/citizen` | Citizen home | Upcoming appointment, current token if checked in, service shortcuts and notifications |
| `/citizen/services` | Service catalogue | Search/filter services and offices |
| `/citizen/services/:serviceId` | Service detail | Description, office information, checklist, official portal guidance |
| `/citizen/assistant` | Service assistant | Ask a question and inspect source citations |
| `/citizen/documents` | Document checklist | Upload sample document and see preliminary readiness status |
| `/citizen/appointments/new` | Book appointment | Choose office, service, date and available slot; confirm booking |
| `/citizen/appointments` | Appointment history | Upcoming, past, cancelled and rescheduled records |
| `/citizen/appointments/:appointmentId` | Appointment detail | Booking information, QR, rotate QR, cancel/reschedule when permitted |
| `/citizen/queue/:tokenId` | Live queue tracking | Token status, public queue information, last-updated state and wait estimate if supported |
| `/citizen/profile` | Profile | Show editable profile fields only when backend supports them |

## 5.3 Officer pages

| Route | Page | Key functions |
|---|---|---|
| `/officer` | Officer home | Assigned office/counter, counter state and queue summary |
| `/officer/queue` | Queue board | Waiting, called, serving, on-hold and completed views as authorized |
| `/officer/check-in` | Check-in | Camera QR scan and manual reference entry |
| `/officer/counters/:counterId` | Counter workspace | Call next, start, hold/resume, complete, missed-call/no-show and permitted transfer actions |
| `/officer/queue/:tokenId` | Token detail | Minimal citizen/appointment information required for the officer's task and action history |

Only display counters and queues returned for the signed-in officer's authorized scope. Do not let a user type an arbitrary office ID to gain access to another office.

## 5.4 Office-admin pages

| Route | Page | Key functions |
|---|---|---|
| `/admin` | Admin overview | Bookings, walk-ins, waiting count, completed tokens and average wait |
| `/admin/analytics` | Analytics | Date-filtered operational aggregates and service-level summaries |
| `/admin/services` | Service configuration | View/edit supported service metadata and checklist configuration |
| `/admin/counters` | Counter configuration | View counters, status, service mapping and assignments if supported |
| `/admin/queue-policy` | Queue policy | Display and edit only policy fields exposed by backend |
| `/admin/knowledge-sources` | Knowledge source administration | Optional P1 source status/deactivation UI if Member 4/backend provides APIs |

Do not invent controls for backend features that do not exist. If an admin operation is not implemented, hide it or label it clearly as unavailable/future work rather than simulating success.

---

# 6. Design system and shared components

Build a small, consistent UI kit before implementing every page independently.

## 6.1 Core components

- `Button`: primary, secondary, danger and disabled/loading variants.
- `Input`, `PhoneInput`, `Textarea`, `Select`, `DatePicker` and `FilePicker`.
- `Modal` and `ConfirmDialog` for destructive or irreversible actions.
- `Alert` and `Toast` for request outcomes.
- `StatusBadge` for appointment, token, counter, OCR and document states.
- `Skeleton` for loading layouts.
- `EmptyState` for no appointments/no queue/no search results.
- `ErrorState` with retry action.
- `PageHeader` with title, description and primary action.
- `DataTable` or responsive card list for admin/officer data.
- `LastUpdated` and `ConnectionStatus` for live data freshness.
- `ProtectedRoute` for navigation convenience, not security enforcement.

## 6.2 Status labels

Use human-readable labels while preserving backend enum values internally.

| Backend value | Suggested UI label |
|---|---|
| `BOOKED` | Booked |
| `CHECKED_IN` | Checked in |
| `RESCHEDULED` | Rescheduled |
| `CANCELLED` | Cancelled |
| `NO_SHOW` | No-show |
| `WAITING` | Waiting |
| `CALLED` | Please proceed to counter |
| `SERVING` | Service in progress |
| `ON_HOLD` | Temporarily on hold |
| `COMPLETED` | Completed |

The backend may have additional internal states. Render unknown states safely as a neutral label and log a sanitized development warning rather than crashing.

## 6.3 Accessibility requirements

- Every form control has a visible label and accessible error message.
- Keyboard navigation works for menus, dialogs, forms and action buttons.
- Focus is moved into dialogs and returned to the triggering control on close.
- Color is never the only indicator of status.
- Text contrast is readable; interactive targets are large enough for touch use.
- QR scanning has a manual-entry fallback.
- Camera denial or unavailable hardware does not block check-in.
- Live updates are announced politely where useful; avoid announcing every queue event in a way that overwhelms screen-reader users.
- Layout works at mobile, tablet and desktop widths.

---

# 7. Firebase client authentication

Member 1 owns Firebase project setup, Firebase Admin SDK verification and PostgreSQL user/role provisioning. Member 3 implements only the browser-side Firebase flow.

## 7.1 Firebase project setup dependencies

Obtain from Member 1/team:

- Firebase project ID and approved web-app configuration.
- Enabled sign-in provider (phone authentication if phone OTP is the agreed sign-in method).
- Authorized development and deployment domains.
- Test phone numbers or approved demo test method, if configured.
- Backend API base URL.
- Expected behavior for unknown users and deactivated users.

The Firebase web configuration is client configuration, not the Admin service-account private key. Never request or commit the Admin service-account JSON in the frontend repository.

## 7.2 Environment variables

Example `.env.example`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=replace-with-web-config-value
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=your-web-app-id
```

Only expose values required by the Firebase Web SDK. Do not put database URLs, private keys, Firebase Admin credentials, LLM keys, storage secrets or server-side API secrets in `VITE_` variables.

## 7.3 Firebase initialization

Create one Firebase app/auth instance. Do not initialize Firebase inside each component.

Illustrative TypeScript:

```ts
// src/features/auth/firebase.ts
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const firebaseAuth = getAuth(app);
```

Validate required configuration at startup and show a developer-friendly configuration error in development. Never print tokens or user secrets.

## 7.4 Session provider

Implement an `AuthProvider` that:

1. Subscribes once to Firebase `onAuthStateChanged`.
2. Exposes `firebaseUser`, `loading`, `signIn`, `signOut` and `getIdToken` helpers.
3. Retrieves the current backend profile through `GET /users/me` after Firebase authentication is ready.
4. Keeps Firebase identity separate from the QueueLess profile and role.
5. Handles a Firebase user who exists but has no permitted QueueLess profile/role.
6. Clears profile and cached protected data on sign-out or authentication failure.
7. Avoids rendering protected routes while initial session/profile loading is unresolved.

Do not treat Firebase display name, phone number or arbitrary custom claims as the sole source of office authorization. The backend database role and assignment are authoritative.

## 7.5 Phone sign-in UI

If phone OTP is the selected provider:

- Collect phone number in E.164 format or normalize it before sending to Firebase.
- Display the country code clearly. For the demo, default to the agreed region but do not silently change a user's number.
- Use Firebase's supported phone-auth flow and reCAPTCHA configuration required by the Web SDK.
- Show code-sent, invalid-code, expired-code, too-many-requests and network-error states.
- Disable repeated submission while a request is pending.
- Never log the OTP, confirmation result secret or Firebase ID token.
- Do not implement a custom backend OTP endpoint or custom refresh-token flow.

## 7.6 Token use in REST requests

For each protected API request, obtain the current Firebase ID token through the SDK and send:

```http
Authorization: Bearer <Firebase-ID-Token>
```

Use `user.getIdToken()` so the Firebase SDK can refresh an expired ID token when appropriate. Do not manually build a refresh-token system. Do not persist raw ID tokens in localStorage or sessionStorage.

Illustrative API helper:

```ts
import { firebaseAuth } from "../../features/auth/firebase";

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const user = firebaseAuth.currentUser;
  if (!user) return {};
  const idToken = await user.getIdToken();
  return { Authorization: `Bearer ${idToken}` };
}
```

Normalize `401` responses: attempt a controlled session refresh/retry only if the SDK session remains valid; otherwise sign out or return the user to sign-in. Avoid infinite retry loops.

## 7.7 Role-aware route handling

- Citizen routes require a valid Firebase session and citizen profile.
- Officer routes require backend role/assignment information indicating officer access.
- Admin routes require office-admin access.
- Unknown/deactivated users see an access or onboarding state.
- Never offer a client-side role switch that changes backend permissions.
- A route guard is UX only; every API call remains protected server-side.

---

# 8. Typed REST API layer

Create one shared API client. Feature components must not contain raw `fetch()` calls scattered throughout the UI.

## 8.1 API client responsibilities

- Add `/api/v1` base URL consistently.
- Add Firebase ID token to protected requests.
- Serialize JSON and `FormData` correctly.
- Apply request timeout/abort behavior where appropriate.
- Parse the backend's standard success/error envelope.
- Normalize error codes for user-friendly messages.
- Avoid logging authorization headers, raw QR references, document text or sensitive payloads.
- Support pagination and date filters consistently.
- Handle `401`, `403`, `404`, `409`, `422`, `429` and `5xx` responses distinctly.

## 8.2 Contract-first integration

Before building each page, ask the backend owner for:

- Exact request and response JSON.
- Enum values and nullable fields.
- Pagination shape.
- Error response shape and stable error codes.
- Authorization expectations.
- Timezone format and date semantics.
- Idempotency requirements.
- Whether the endpoint is implemented, in progress or only proposed.

The following endpoint list is the agreed functional surface from the QueueLess 2.3 specification. Exact payload schemas must be frozen with the respective owner before frontend integration.

| Feature | Endpoint | Owner | Frontend use |
|---|---|---|---|
| Current profile | `GET /users/me` | Member 1 | Load role and profile after Firebase sign-in |
| Offices | `GET /offices` | Member 1 | Office selection |
| Services | `GET /services` | Member 1 | Catalogue |
| Service detail | `GET /services/{id}` | Member 1 | Service details |
| Service checklist | `GET /services/{id}/checklist` | Member 1/4 as agreed | Checklist view |
| Assistant | `POST /assistant/chat` | Member 4 | Chat and source citations |
| Upload document | `POST /documents/upload` | Member 4 | Upload and progress |
| List documents | `GET /documents` | Member 4 | Citizen document list |
| Check document | `POST /documents/{id}/check` | Member 4 | Start readiness analysis |
| Check result | `GET /documents/{id}/check-result` | Member 4 | Show result/status |
| Delete document | `DELETE /documents/{id}` | Member 4 | Delete owned upload if supported |
| Appointment slots | `GET /appointments/slots` | Member 1 | Slot availability |
| Create appointment | `POST /appointments` | Member 1 | Booking |
| List appointments | `GET /appointments` | Member 1 | Appointment history |
| Appointment detail | `GET /appointments/{id}` (confirm contract) | Member 1 | Detail and resync |
| Cancel appointment | `POST /appointments/{id}/cancel` | Member 1 | Cancel with confirmation |
| Reschedule | `POST /appointments/{id}/reschedule` | Member 1 | Choose replacement slot |
| Rotate QR | `POST /appointments/{id}/qr/rotate` | Member 1 | Recover/replace QR reference |
| QR check-in | `POST /checkin` | Member 2 | Officer scan result |
| Manual check-in | `POST /appointments/{appointment_id}/check-in/manual` | Member 2 | Officer manual path |
| Walk-in token | `POST /queue/tokens` | Member 2 | Register walk-in if permitted |
| Token detail | `GET /queue/tokens/{id}` | Member 2 | Citizen/officer detail and resync |
| Office queue | `GET /queue/office/{id}` | Member 2 | Officer queue board |
| Call next | `POST /counters/{id}/call-next` | Member 2 | Officer action |
| Start service | `POST /queue/tokens/{id}/start` | Member 2 | Officer action |
| Complete | `POST /queue/tokens/{id}/complete` | Member 2 | Officer action |
| No-show | `POST /queue/tokens/{id}/no-show` | Member 2 | Officer confirmation/action |
| Hold/resume | `POST /queue/tokens/{id}/hold`, `/resume` | Member 2 | Officer action |
| Realtime ticket | `POST /realtime/tickets` | Member 2/shared backend | Obtain one-time socket ticket |
| Admin overview | `GET /admin/overview` | Member 1/2 | Admin overview |
| Admin analytics | `GET /admin/analytics/*` | Member 1/2 | Analytics pages |
| Admin services/counters | `POST /admin/services`, `POST /admin/counters` | Member 1/2 | Configuration only if supported |

If an endpoint is not implemented, keep the UI behind a feature flag or show a clear unavailable state. Do not create a fake success response to make the screen appear complete.

## 8.3 Suggested shared TypeScript types

The types below are frontend-facing examples. Replace/align them with the final OpenAPI schema from the backend. Do not assume these examples are already the exact server response.

```ts
export type AppRole = "CITIZEN" | "OFFICER" | "OFFICE_ADMIN";

export type AppointmentStatus =
  | "BOOKED"
  | "CHECKED_IN"
  | "RESCHEDULED"
  | "CANCELLED"
  | "NO_SHOW";

export type QueueTokenStatus =
  | "WAITING"
  | "CALLED"
  | "SERVING"
  | "ON_HOLD"
  | "COMPLETED"
  | "NO_SHOW"
  | "CANCELLED";

export interface CurrentUser {
  id: string;
  firebase_uid: string;
  display_name?: string | null;
  phone_number?: string | null;
  role: AppRole;
  active: boolean;
  office_ids?: string[];
  assigned_counter_ids?: string[];
}

export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, unknown>;
}
```

The backend may use lowercase enums or a different casing convention. Align the shared types to the generated OpenAPI schema if available.

---

# 9. Citizen service catalogue and guidance

## 9.1 Catalogue page

Implement:

- Search by service name and keyword.
- Filter by office/location only if the API supports it.
- Service cards with name, short description, department/authority and available office information.
- Clear loading, empty and error states.
- Pagination or incremental loading if the API returns paginated results.
- No unsupported claim that a service can be completed inside QueueLess.

## 9.2 Service detail page

Display:

- Service title and purpose.
- Issuing authority/department if returned by backend.
- Official application link when supplied and verified by backend.
- Service checklist with required/optional distinction.
- Office selection and appointment call-to-action.
- A clear notice: QueueLess offers preliminary guidance; final requirements and application submission must be confirmed through the official service portal/office.

Do not invent fees, eligibility, timelines or required documents. Display only source-backed backend content.

## 9.3 RAG assistant page (P1)

Member 4 supplies the assistant endpoint and source payload. The frontend should:

- Provide a chat input and conversation history for the current session.
- Disable repeated sends while a request is pending.
- Render answer text safely as text/approved Markdown, not arbitrary HTML.
- Display each returned source with title, issuing authority, canonical URL and relevant citation metadata.
- Show an explicit “I don't have a verified answer” or escalation message when returned by backend.
- Keep answer uncertainty visible.
- Provide links to the official portal/office when the assistant returns them.
- Avoid representing an LLM answer as a legal decision or government approval.
- Support English/Kannada/Hindi only to the extent verified by the AI member; do not claim language support solely because the UI can render those scripts.

---

# 10. Document upload and OCR readiness UI (P1)

Member 4 owns file processing and OCR. Member 3 owns the upload and result experience.

## 10.1 Upload flow

1. Citizen selects the service/checklist context.
2. Citizen chooses PDF/JPG/PNG within backend-defined size limits.
3. Frontend performs basic type/size validation for usability, but backend revalidates everything.
4. Show upload progress and allow cancellation only if the API supports it.
5. On success, show document state and action to run/check readiness.
6. Poll or refresh the result endpoint only according to the agreed backend contract. Prefer a bounded retry strategy, not an infinite loop.

## 10.2 Result states

Render the exact states returned by the backend, including the QueueLess 2.3 states:

- `UPLOADED`
- `CATEGORY_MATCHED`
- `NEEDS_REVIEW`
- `MISSING`
- `REPLACEMENT_REQUESTED`

The UI must explain that these are preliminary document-readiness signals. Never label a document “genuine”, “legally valid”, “approved” or “rejected”. Show confidence only if returned by backend and explain it in non-technical language. Hide extracted personal data unless the citizen needs to inspect it and the privacy policy allows it.

## 10.3 Failure and privacy behavior

- OCR provider outage must not prevent the citizen from booking an appointment.
- Show manual checklist confirmation if supported.
- Do not put document contents or OCR text into toast messages, analytics or logs.
- Use private download links only when returned by backend and only for the owner.
- Clear temporary file references when the user leaves or signs out where appropriate.

---

# 11. Appointment booking and QR confirmation

Member 1 owns booking capacity and QR reference lifecycle. Member 3 builds the booking flow and renders the API result.

## 11.1 Booking journey

1. Citizen opens service detail.
2. Selects office.
3. Selects date.
4. Frontend requests slots from Member 1's slot endpoint.
5. Display only returned bookable slots. Do not calculate free capacity in JavaScript.
6. Citizen chooses a slot and reviews a confirmation summary.
7. Submit booking with the backend-required idempotency key if specified.
8. Disable the submit button while pending to reduce accidental double-clicks.
9. On success, show the appointment details and QR reference if returned.
10. If the backend returns `SLOT_FULL`, `SLOT_CLOSED` or another conflict, refresh slot availability and ask the citizen to choose again.

## 11.2 Slot display

- Use the office timezone. QueueLess offices use `Asia/Kolkata` for operating-date rules.
- Preserve timezone-aware timestamps from the API.
- Show date and local time clearly, including AM/PM or 24-hour format consistently.
- Do not convert a server timestamp using an assumed browser timezone if the API supplies office timezone semantics.
- Zero-capacity slots must not be displayed as available.
- Show an empty state when no slots are returned.

## 11.3 Appointment detail and QR display

- Display booking reference, office, service, date/time and status.
- Render the opaque QR reference returned by the backend using a QR library.
- The QR must contain only the opaque reference and any explicitly approved non-sensitive marker. Never encode citizen profile or document data.
- Do not log the raw reference or store it persistently in browser storage.
- If the raw reference is no longer available, use Member 1's authenticated QR rotation endpoint.
- On rotation success, replace the currently displayed QR with the new one. The backend invalidates the prior unused reference atomically.
- Explain that QR is a check-in convenience and not proof of identity.
- If QR rotation fails, preserve the appointment view and show a retryable error. Do not invent a reference.

## 11.4 Cancel and reschedule

- Confirm destructive actions with a dialog.
- Display cancellation/rescheduling policy returned by backend if available.
- Rescheduling creates a new appointment record and preserves history. The UI should navigate to the new appointment after success and not overwrite the old appointment's details.
- Do not assume a rescheduled appointment reuses the old QR. The new booking receives its own reference according to Member 1's implementation.
- Handle stale appointment status with a fresh detail request before showing actions.

---

# 12. Officer queue dashboard and check-in UI

Member 2 owns queue business logic and APIs. Member 3 builds the operator interface around those contracts.

## 12.1 Officer home

Display:

- Signed-in officer identity and role from backend profile.
- Assigned office and assigned counter(s).
- Counter status returned by backend.
- Current called/serving token if any.
- Waiting queue count and queue list returned by backend.
- Connection status and last-updated time.

Do not let an officer choose an arbitrary counter or office unless the backend returns it as an authorized assignment.

## 12.2 Queue board

Recommended views:

- Waiting tokens.
- Called token.
- Serving token.
- On-hold tokens.
- Completed/recent history (if API supports it).

Each row/card should show only information necessary for the officer's work: public token number, service, check-in time, appointment/walk-in source and minimal profile confirmation details authorized by the API.

Provide filters by service/status only if the queue endpoint supports them. Do not infer queue order in the browser. Display the server's order.

## 12.3 QR scanner

Implement a camera-based scanner only as a frontend capture mechanism.

Behavior:

1. Officer opens check-in page.
2. Browser asks for camera permission after an explicit user action.
3. Scanner reads the QR's opaque reference.
4. Frontend sends the reference to `POST /checkin` using the authenticated API client.
5. Backend validates and consumes the reference, updates appointment and creates exactly one token in one transaction.
6. Frontend displays the returned success/token summary.
7. Frontend refreshes the queue snapshot or uses the committed event to update the queue.

Important:

- The browser must not decide whether a QR is valid or whether the appointment is within its check-in window.
- The frontend must not create the queue token itself.
- Do not persist or log the raw reference.
- Prevent repeated local submissions while a scan request is pending, but rely on backend replay protection for correctness.
- On `QR_EXPIRED`, `QR_ALREADY_USED`, `ALREADY_CHECKED_IN`, `NOT_FOUND` or authorization errors, show a clear operator message and allow an appropriate next step.
- If camera access is unavailable/denied, show manual reference entry.

## 12.4 Manual check-in

Manual check-in is a separate backend path and must not be implemented by pretending a typed booking ID is a QR reference.

- Officer searches/enters the booking reference or appointment identifier using the exact backend contract.
- Backend performs authorization and returns the minimum details needed to confirm the citizen.
- Officer confirms the citizen against the booking profile and supplies any required reason/confirmation.
- Frontend calls `POST /appointments/{appointment_id}/check-in/manual` with the agreed body.
- Backend creates the token through the same internal transactional service used by QR check-in.
- Display success and refresh queue.

Do not expose a manual check-in action to citizens.

## 12.5 Counter actions

Show action buttons only when the backend says the action is available or when the agreed state-transition table makes it safe to render. The backend still validates every action.

| Action | API | UI behavior |
|---|---|---|
| Call next | `POST /counters/{counterId}/call-next` | Confirm counter context; show returned token |
| Start service | `POST /queue/tokens/{tokenId}/start` | Update only after API success/committed event |
| Hold | `POST /queue/tokens/{tokenId}/hold` | Require reason if API policy requires it |
| Resume | `POST /queue/tokens/{tokenId}/resume` | Show assigned counter and current state |
| Complete | `POST /queue/tokens/{tokenId}/complete` | Confirm if required; display completion |
| No-show | `POST /queue/tokens/{tokenId}/no-show` | Explicit officer confirmation after backend retry policy; never automatic client timeout |
| Counter transfer | Endpoint to be frozen with Member 2 | Require reason and show old/new counter; transfer is an event, not a token state |

Do not create a frontend timer that marks someone `NO_SHOW`. The QueueLess 2.3 rule requires the configured recall process and officer confirmation after attempts are exhausted. The UI may show a countdown/reminder prompt if the backend provides call-attempt state, but it cannot independently change token status.

## 12.6 Walk-ins

If Member 2 exposes walk-in creation, show a form with the minimum required fields and call `POST /queue/tokens`. Backend determines token number, source, ordering and fairness. UI should clearly distinguish `WALK_IN` from `APPOINTMENT` and `OFFLINE_REGISTER` sources.

---

# 13. Citizen live queue tracking and WebSockets

Member 2 owns ticket issuance, authorization, event publishing and queue state. Member 3 owns the browser connection and presentation.

## 13.1 Data flow

1. Citizen loads `GET /queue/tokens/{id}` to get authoritative current state.
2. Client calls authenticated `POST /realtime/tickets` for a short-lived, single-use ticket scoped to the current user and allowed subscription.
3. Client opens the native WebSocket connection using the ticket handshake defined by Member 2.
4. Client validates incoming event schema/version and applies only events relevant to the current citizen/token.
5. Client updates the visible status and last-updated time.
6. On disconnect, mark the live data as stale and attempt bounded reconnect with backoff.
7. After reconnect, fetch the authoritative REST snapshot and replace local state before trusting future events.
8. If sequence/event IDs show a gap, resync through REST.

## 13.2 WebSocket security

- Never put Firebase ID token in the WebSocket URL.
- Never use a long-lived credential in the URL.
- Use only the short-lived, single-use WebSocket ticket returned by the backend.
- Do not invent the ticket query parameter/path. Agree on the exact handshake with Member 2.
- Subscribe only to the current citizen's own token/appointment or authorized officer office/counter scope.
- Never subscribe to a broad office stream from a citizen screen if it would expose other citizens' private information.
- Do not display or store raw event payloads in logs.

## 13.3 Event types

At minimum, Member 2 may publish:

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
- `queue.wait_estimate_updated` when implemented
- `appointment.status_changed`

Use the final event envelope agreed with Member 2. Do not assume a field exists unless it is in the agreed schema.

## 13.4 Reconnection UX

- Show a small “Reconnecting…” indicator while disconnected.
- Show “Last updated at …” when connected or stale.
- Do not show an old queue state as if it were live.
- After a bounded number of reconnect attempts, keep REST refresh available and display a non-blocking warning.
- If the socket is unavailable, the citizen can still refresh the queue status manually.
- Queue operations must remain functional through REST even when WebSocket delivery fails.

---

# 14. Admin dashboard and analytics

The 2.3 P1 operational proof includes basic PostgreSQL aggregate analytics. Member 3 presents the data; backend members define and calculate it.

## 14.1 Overview cards

Use backend-returned metrics for:

- Total appointments.
- Walk-ins.
- Citizens served/completed tokens.
- Current waiting count.
- Average wait.
- Median wait if supplied.
- Average/service duration if supplied.

## 14.2 Charts and tables

Suggested displays, depending on API support:

- Appointment volume by day.
- Queue volume by service.
- Waiting vs completed counts.
- Average wait by service.
- Counter utilization/status.

Do not derive business metrics from only the currently loaded page of paginated queue data. Use analytics endpoints.

## 14.3 Metric definitions

Ask backend owners to document the definitions. The frontend must not relabel a metric with a different meaning. Examples that require agreement:

- “Average wait” start and end timestamps.
- Whether cancelled/no-show records are excluded.
- Whether walk-ins are included in appointments.
- Which timezone controls daily grouping.
- Whether analytics are real or synthetic demo data.

Label synthetic data and demo metrics visibly. Slow-service indicators are operational signals for review, not evidence of staff fault.

---

# 15. Error handling and user feedback

## 15.1 Common API errors

Map stable backend error codes to actionable text. Examples:

| Error code | Suggested message/action |
|---|---|
| `SLOT_FULL` | “This slot was just taken. Please choose another time.” Refresh slots. |
| `SLOT_CLOSED` | “This slot is no longer available.” Refresh availability. |
| `DUPLICATE_BOOKING` | “You already have a booking for this slot/service.” Link to existing booking if returned. |
| `QR_EXPIRED` | “This QR code has expired. Refresh or rotate the QR from the appointment page.” |
| `QR_ALREADY_USED` | “This QR code has already been used.” Refresh queue/appointment state. |
| `ALREADY_CHECKED_IN` | “This appointment has already been checked in.” Show existing token if authorized. |
| `INVALID_TOKEN_TRANSITION` | “This action is no longer available because the queue status changed.” Refresh queue. |
| `COUNTER_BUSY` | “This counter is already handling another citizen.” Refresh counter state. |
| `NOT_ASSIGNED_TO_COUNTER` | “Your account is not assigned to this counter.” Contact office admin. |
| `NO_ELIGIBLE_TOKEN` | “There is no eligible token to call right now.” Refresh queue. |
| `DOCUMENT_ACCESS_DENIED` | “You do not have access to this document.” |
| `401` | Session expired/invalid. Refresh through Firebase SDK or sign in again. |
| `403` | Signed in but not authorized for this action. |
| `429` | Too many requests. Wait and retry. |
| `5xx` | Service temporarily unavailable. Preserve user input where safe and offer retry. |

## 15.2 Form validation

- Validate required fields before submission.
- Use server validation as final authority.
- Display field-level errors returned by backend where possible.
- Preserve safe form input after recoverable server errors.
- Prevent duplicate submissions while a request is pending.
- Do not use validation to claim legal eligibility or document validity.

## 15.3 Destructive action confirmation

Use explicit confirmation for cancellation, deletion and sensitive officer actions. Explain the consequence in plain language. A dialog confirmation is not a substitute for server-side authorization or transition validation.

---

# 16. Frontend security and privacy checklist

- [ ] Firebase client config is separated by environment.
- [ ] Firebase Admin credentials and backend secrets are never included in frontend build output.
- [ ] Firebase ID token is obtained from SDK and sent only in Authorization header for REST.
- [ ] ID tokens are not manually persisted in localStorage/sessionStorage.
- [ ] WebSocket uses a short-lived, single-use ticket, never Firebase ID token in URL.
- [ ] Route guards do not substitute for backend authorization.
- [ ] Role and office/counter scope come from backend profile, not client form state.
- [ ] Raw QR references are not logged or persisted.
- [ ] QR payload contains no PII or document contents.
- [ ] File upload UI restricts obvious unsupported types and backend independently validates content.
- [ ] No sensitive document content appears in toasts, logs or analytics.
- [ ] Citizen screens expose only the signed-in citizen's own appointments/tokens/documents.
- [ ] Officer screens expose only authorized office/counter records.
- [ ] Admin screens expose only the office scope granted by backend.
- [ ] All API traffic uses HTTPS in deployed environments.
- [ ] External links use safe navigation practices and are clearly marked as official portals when verified.
- [ ] Errors do not expose stack traces, SQL details or another user's records.
- [ ] User sign-out clears protected client state and closes active WebSocket connections.

---

# 17. Performance and reliability

## 17.1 Frontend performance

- Lazy-load route-level pages, especially admin charts and AI/OCR pages.
- Keep the initial citizen home bundle small.
- Avoid fetching the same catalogue/profile repeatedly from sibling components; use shared query/cache or provider state.
- Debounce search input where it triggers API requests.
- Cancel stale requests when the user changes page/filter.
- Use pagination for large tables.
- Compress/resize images client-side only if agreed; backend must still enforce upload limits.
- Avoid unnecessary polling. Use WebSocket for event notification and REST for authoritative state.

## 17.2 Resilience

- API outage should not crash the whole application.
- A failed AI/OCR request must not block booking or queue tracking.
- WebSocket failure must not block REST queue operations.
- Camera failure must not block manual check-in.
- Missing optional analytics must not block the officer/citizen P0 journey.
- Refreshing a page should restore state from backend, not depend on React memory.

## 17.3 Date/time handling

- Treat backend timestamps as timezone-aware values.
- Use office timezone for appointment slot display and operating-date semantics.
- Do not use the browser's local timezone as the source of truth for office date/token numbering.
- Show clear date/time formatting and avoid ambiguous numeric dates.
- Avoid manually adding/subtracting a fixed UTC offset; use a timezone-aware date library or `Intl.DateTimeFormat` with the explicit timezone.

---

# 18. Testing strategy

## 18.1 Unit tests

Test:

- Date/time formatting for `Asia/Kolkata`.
- Status label mapping and unknown enum fallback.
- Error-code mapping.
- API client auth header behavior.
- Token/session loading states.
- Role-based route behavior.
- QR display input handling without logging raw value.
- WebSocket event parsing and filtering.
- Reconnect backoff and stale indicator behavior.

## 18.2 Component tests

Test:

- Sign-in validation and Firebase error display.
- Service catalogue loading/empty/error/search states.
- Service detail and preliminary-guidance disclaimer.
- Slot picker loading, unavailable and selected states.
- Booking pending, success and `SLOT_FULL` conflict behavior.
- Appointment detail and QR rotation.
- Cancel/reschedule confirmation.
- Officer queue states and disabled actions.
- QR scanner permission-denied/manual fallback.
- Check-in duplicate/expired/invalid reference error messages.
- Counter action success and invalid-transition refresh.
- Assistant source citations and unknown-answer presentation.
- OCR confidence/status and manual review states.
- Admin analytics empty and synthetic-data labels.

## 18.3 API integration tests

Use the staging backend and test Firebase accounts. Verify:

- Firebase sign-in yields a token accepted by `GET /users/me`.
- Citizen cannot call officer/admin APIs.
- Officer cannot access an unassigned office/counter.
- Admin cannot access another office's analytics unless explicitly authorized.
- Citizen sees only their own appointments/documents/tokens.
- Booking success displays the returned appointment and QR.
- QR rotation updates the QR shown in UI.
- QR scan submits the reference and displays the created token.
- Manual check-in uses the distinct manual endpoint.
- Queue actions update from REST response/committed events, not optimistic assumptions.
- WebSocket reconnect triggers REST resync.
- AI/OCR outage does not block booking.

## 18.4 End-to-end demo test

Run two browser sessions:

**Session A: citizen**
1. Sign in with Firebase test account.
2. Open a service.
3. Review checklist and official portal guidance.
4. Choose office/date/slot.
5. Book appointment.
6. Open appointment detail and show QR.
7. Open live queue tracking page.

**Session B: officer**
8. Sign in with provisioned officer account.
9. Open assigned counter/queue.
10. Scan the citizen QR or use manual entry.
11. Confirm the token appears in the queue.
12. Call next.
13. Start service.
14. Complete service.

**Back in Session A**
15. Verify queue status changes without a manual page refresh.
16. Verify reconnect/resync by briefly disconnecting the network or closing/reopening the socket.

**Admin session**
17. Sign in as office admin.
18. Verify booking, waiting, walk-in and completed metrics reflect the demo records.
19. Confirm all synthetic data is labelled.

## 18.5 Test data rules

- Use synthetic citizen identities and sample documents.
- Do not use real Aadhaar numbers or real identity documents in demo fixtures.
- Use seeded Firebase test users created through the approved project process.
- Keep test credentials out of the repository.
- Reset test data through documented scripts or backend fixtures, not manual SQL edits during the demo.

---

# 19. Suggested 20-working-day implementation schedule

The exact duration can be compressed if the hackathon is shorter. Do not skip API contract alignment or end-to-end integration in order to polish visual details early.

| Day | Focus | Deliverables |
|---|---|---|
| 1 | Contract kickoff | Confirm roles, endpoint owners, OpenAPI location, Firebase config process, API error envelope and event schema |
| 2 | Frontend foundation | Vite + React + TypeScript + Tailwind, lint/format, env validation, app shell |
| 3 | Routing and layouts | Public/citizen/officer/admin layouts, route map, responsive navigation |
| 4 | Firebase client setup | Firebase initialization, AuthProvider, session observer and sign-out |
| 5 | Profile and route guards | `GET /users/me`, role-aware routes, unauthorized/deactivated states |
| 6 | API client | Shared authenticated REST client, error normalization, request cancellation and typed API modules |
| 7 | Catalogue | Office/service listing, search, service detail and checklist display |
| 8 | Booking UI | Office/date/slot selection, empty states, timezone handling |
| 9 | Appointment lifecycle | Booking submit/idempotency behavior, appointment list/detail, cancel/reschedule |
| 10 | QR confirmation | QR rendering, no-store response handling, QR rotation, privacy checks |
| 11 | Officer dashboard | Assigned office/counter view, queue board and token status components |
| 12 | Check-in | Camera scanner, manual-entry fallback, QR/manual API integration and error states |
| 13 | Counter actions | Call-next, start, hold/resume, complete, no-show confirmation and refresh behavior |
| 14 | Citizen queue view | Token detail, status timeline, last-updated state and REST snapshot |
| 15 | WebSocket | Ticket handshake, scoped connection, event handling, reconnect and REST resync |
| 16 | Admin analytics | Overview cards, tables/charts, date filters and synthetic-data labels |
| 17 | P1 AI/OCR UI | Assistant citations, document upload, readiness report and failure handling if APIs are stable |
| 18 | Integration hardening | Cross-role access tests, mobile layout, accessibility, API mismatch fixes |
| 19 | End-to-end demo | Two-session walkthrough, test fixtures, loading/error polish, defect triage |
| 20 | Release candidate | Production build, environment checklist, documentation, known limitations and handoff |

## Priority if the schedule is shortened

1. Firebase sign-in and `/users/me`.
2. Service catalogue and appointment booking.
3. Appointment confirmation and QR display.
4. Officer check-in and queue actions.
5. Citizen live queue tracking with REST resync.
6. Basic admin overview.
7. P1 RAG/OCR pages.
8. Visual polish and optional P2 features.

A working citizen-to-officer loop is more valuable than a large set of disconnected pages.

---

# 20. Integration contract with other members

## 20.1 With Member 1

Member 1 must provide:

- Firebase project configuration and enabled client sign-in provider.
- Stable `GET /users/me` response with backend role and active status.
- Office/service catalogue response shapes.
- Slot availability and appointment booking request/response schemas.
- Appointment detail/list/cancel/reschedule contracts.
- Booking idempotency requirements.
- QR response semantics: raw value returned once, no-store behavior, QR expiry and rotation contract.
- Typed errors and timezone rules.

Member 3 must provide:

- Firebase Web SDK integration and tested token transport.
- UI flow for sign-in, profile loading, access denied and sign-out.
- Booking/appointment screens tested against staging.
- QR display/rotation UI without persisting raw reference.
- A list of API mismatches with exact request/response examples.

## 20.2 With Member 2

Member 2 must provide:

- `POST /checkin` QR request/response contract.
- Manual check-in endpoint contract and officer confirmation requirements.
- Queue token response and public token-number format.
- Queue status enum and allowed action/transition matrix.
- Office/counter queue snapshot endpoint and pagination/filter behavior.
- Counter action APIs and error codes.
- WebSocket ticket endpoint and exact one-time ticket handshake.
- Event envelope, event names, sequence/version behavior and authorized subscription scope.
- REST resynchronization endpoint(s).
- Test officer account, assigned counter and synthetic queue fixtures.

Member 3 must provide:

- Camera scan/manual entry UX.
- Queue board and counter workspace.
- Citizen live queue screen.
- WebSocket lifecycle/reconnect behavior.
- Action controls that wait for backend success and resync after conflicts.
- Cross-role UI tests and integration feedback.

## 20.3 With Member 4

Member 4 must provide:

- Assistant request/response contract including answer, uncertainty and source citations.
- Verified source metadata and source link format.
- Document upload constraints and response contract.
- OCR processing/result states, confidence format and manual-review behavior.
- Error states for provider outages and unsupported files.
- Demo fixtures and expected P1 output.

Member 3 must provide:

- Chat and citations UI.
- Upload/progress/result UI.
- Clear preliminary-readiness disclaimer.
- Accessible error and retry behavior.
- No dependency from P1 AI/OCR features into P0 booking/queue pages.

## 20.4 Shared contract-freeze checklist

Before feature implementation, agree:

- [ ] Base API URL and `/api/v1` prefix.
- [ ] Firebase project ID and allowed domains.
- [ ] `GET /users/me` profile schema and role enum.
- [ ] Standard error response schema.
- [ ] Timestamp format and office timezone behavior.
- [ ] Pagination conventions.
- [ ] Appointment/queue state enums.
- [ ] QR raw-reference one-time display behavior.
- [ ] QR rotation behavior and expiry.
- [ ] QR/manual check-in request/response contracts.
- [ ] WebSocket ticket handshake and event envelope.
- [ ] Queue REST snapshot endpoint and resync semantics.
- [ ] RAG citations and OCR result schemas.
- [ ] Demo/test accounts and synthetic data reset procedure.

---

# 21. Repository and Git workflow

## 21.1 Branching

Suggested branch names:

- `feature/member3-frontend-foundation`
- `feature/member3-firebase-auth-ui`
- `feature/member3-catalogue`
- `feature/member3-appointments`
- `feature/member3-qr-ui`
- `feature/member3-officer-dashboard`
- `feature/member3-checkin-ui`
- `feature/member3-realtime`
- `feature/member3-admin-analytics`
- `feature/member3-ai-ocr-ui`

Use short-lived branches and small pull requests. Avoid committing directly to the shared main branch while backend contracts are changing.

## 21.2 Commit style

Examples:

```text
feat(auth): add Firebase phone sign-in flow
feat(appointments): add slot selection and booking confirmation
feat(qr): add appointment QR display and rotation
feat(officer): add queue board and check-in workflow
feat(realtime): add ticket-based queue WebSocket client
fix(queue): resync token state after reconnect
 test(frontend): cover citizen booking journey
```

Use the team's agreed conventional commit style; fix the example spacing if using a commit linter.

## 21.3 Pull request checklist

- [ ] Scope is limited and described.
- [ ] No backend secrets or test credentials committed.
- [ ] API calls use the shared client.
- [ ] Loading, empty, error and permission states exist.
- [ ] No optimistic state claims for queue transitions.
- [ ] TypeScript/build/lint checks pass.
- [ ] Relevant tests pass.
- [ ] Screenshots or short recording included for major UI changes.
- [ ] API contract changes are coordinated with the owner.

---

# 22. Definition of done for Member 3

## Functional

- [ ] Firebase client authentication works with the selected provider.
- [ ] Backend profile and role are loaded from `/users/me`.
- [ ] Citizen, officer and office-admin routes behave correctly.
- [ ] Citizen can browse services and view service guidance/checklists.
- [ ] Citizen can see available slots and book an appointment.
- [ ] Appointment history/detail and cancel/reschedule work with backend.
- [ ] QR is displayed from backend-provided raw reference and can be rotated through Member 1's endpoint.
- [ ] Officer can scan QR or use manual check-in and see backend result.
- [ ] Officer can view queue and perform supported counter actions.
- [ ] Citizen queue status updates through WebSocket and REST resync.
- [ ] Admin overview displays backend analytics with correct definitions.
- [ ] AI/OCR pages work only against documented Member 4 endpoints and display preliminary disclaimers.

## Security

- [ ] No custom frontend role assignment.
- [ ] No Firebase Admin credentials in browser bundle.
- [ ] No Firebase ID token in WebSocket URL.
- [ ] No raw QR reference in logs or persistent browser storage.
- [ ] No citizen PII in shared queue events or broad office views.
- [ ] Protected data cleared on sign-out.

## Quality

- [ ] Responsive layouts work on mobile and desktop.
- [ ] Keyboard and screen-reader basics are covered.
- [ ] Loading, empty, error and stale-data states are implemented.
- [ ] API conflict errors trigger appropriate refresh/resync.
- [ ] P0 two-session demo passes without manual database edits.
- [ ] Build and test commands documented.
- [ ] Known limitations and deferred features listed honestly.

---

# 23. First actions: what Member 3 should do now

1. Meet Members 1 and 2 for a 30-minute contract session. Freeze the current user profile schema, booking response, QR rotation behavior, check-in response, queue snapshot and WebSocket ticket handshake.
2. Ask Member 1 for Firebase Web configuration and the backend `/users/me` contract. Do not request or copy the Firebase Admin private key.
3. Ask Member 2 for a working officer account, assigned counter, queue fixture and exact action/event schemas.
4. Ask Member 4 for the assistant and OCR response examples. Keep P1 screens behind a feature boundary until these contracts are stable.
5. Create the React + Vite + TypeScript + Tailwind application and `.env.example`.
6. Implement the shared API client and Firebase AuthProvider before building protected pages.
7. Build the P0 citizen booking journey and officer queue journey first.
8. Test the full two-browser workflow early, not only at the end.

---

# Appendix A. Suggested frontend API module interfaces

These are internal frontend function signatures. Align names and payloads with the final OpenAPI document.

```ts
// appointments.api.ts
export const appointmentsApi = {
  getSlots: (params: SlotQuery) => api.get<SlotResponse>("/appointments/slots", { params }),
  create: (body: CreateAppointmentRequest, idempotencyKey: string) =>
    api.post<AppointmentConfirmation>("/appointments", body, {
      headers: { "Idempotency-Key": idempotencyKey },
    }),
  list: (params?: AppointmentListQuery) =>
    api.get<AppointmentListResponse>("/appointments", { params }),
  getById: (id: string) => api.get<Appointment>(`/appointments/${id}`),
  cancel: (id: string, body?: CancelAppointmentRequest) =>
    api.post<Appointment>(`/appointments/${id}/cancel`, body),
  reschedule: (id: string, body: RescheduleAppointmentRequest) =>
    api.post<Appointment>(`/appointments/${id}/reschedule`, body),
  rotateQr: (id: string) => api.post<QrRotationResponse>(`/appointments/${id}/qr/rotate`),
};
```

```ts
// queue.api.ts
export const queueApi = {
  getToken: (tokenId: string) => api.get<QueueToken>(`/queue/tokens/${tokenId}`),
  getOfficeQueue: (officeId: string, params?: QueueQuery) =>
    api.get<QueueSnapshot>(`/queue/office/${officeId}`, { params }),
  callNext: (counterId: string) => api.post<QueueActionResult>(`/counters/${counterId}/call-next`),
  start: (tokenId: string) => api.post<QueueActionResult>(`/queue/tokens/${tokenId}/start`),
  complete: (tokenId: string) => api.post<QueueActionResult>(`/queue/tokens/${tokenId}/complete`),
  hold: (tokenId: string, body: HoldRequest) => api.post<QueueActionResult>(`/queue/tokens/${tokenId}/hold`, body),
  resume: (tokenId: string) => api.post<QueueActionResult>(`/queue/tokens/${tokenId}/resume`),
};
```

```ts
// checkin.api.ts
export const checkinApi = {
  scanQr: (reference: string) => api.post<CheckinResult>("/checkin", { reference }),
  manual: (appointmentId: string, body: ManualCheckinRequest) =>
    api.post<CheckinResult>(`/appointments/${appointmentId}/check-in/manual`, body),
};
```

Do not copy these illustrative signatures blindly if backend schemas differ. The API owner and frontend owner must agree on the final shape.

---

# Appendix B. Suggested component map

| Feature | Page components | Reusable components/hooks |
|---|---|---|
| Auth | `SignInPage` | `AuthProvider`, `useAuth`, `ProtectedRoute` |
| Catalogue | `ServiceListPage`, `ServiceDetailPage` | `ServiceCard`, `ServiceFilters`, `ChecklistView` |
| Appointments | `BookAppointmentPage`, `AppointmentListPage`, `AppointmentDetailPage` | `SlotPicker`, `AppointmentCard`, `BookingSummary` |
| QR | Appointment QR panel | `QrCodeView`, `RotateQrButton`, `QrExpiryNotice` |
| Citizen queue | `CitizenQueuePage` | `TokenStatusCard`, `QueueTimeline`, `ConnectionStatus`, `useQueueRealtime` |
| Officer | `OfficerHomePage`, `OfficerQueuePage`, `CounterWorkspacePage` | `QueueTable`, `TokenActionBar`, `CounterStatusCard` |
| Check-in | `CheckinPage` | `QrScanner`, `ManualReferenceForm`, `CheckinResultPanel` |
| Assistant | `AssistantPage` | `ChatMessage`, `SourceCitationList`, `UncertaintyNotice` |
| Documents | `DocumentsPage`, `DocumentResultPage` | `FileUploader`, `ReadinessStatus`, `ConfidenceNotice` |
| Admin | `AdminOverviewPage`, `AnalyticsPage` | `MetricCard`, `DateRangeFilter`, `AnalyticsChart` |

---

# Appendix C. Integration decisions that must be recorded

1. Exact Firebase sign-in provider and phone-number test flow.
2. Whether the frontend uses React Query/SWR or local feature hooks for server state.
3. Final `/users/me` role enum and assignment fields.
4. Exact appointment booking response and one-time QR-reference return behavior.
5. QR rotation rate-limit/expiry response behavior.
6. Exact QR scanner library and browser support target.
7. Manual check-in lookup contract and what citizen fields an officer may see.
8. Counter transfer endpoint and whether it is included in the hackathon MVP.
9. WebSocket ticket handshake: path, ticket transport, expiry and reconnect policy.
10. Queue event envelope and event sequence/version behavior.
11. Admin analytics metric definitions and date-filter semantics.
12. Whether P1 RAG/OCR UI is included in the final demo based on verified source/API readiness.
13. Which routes/features are explicitly deferred so the interface does not imply they are implemented.

**Final engineering principle:** The frontend is the control panel and storyteller of QueueLess, not the authority for its business rules. It should make the correct backend workflow easy to use, explain what is happening, and recover gracefully when a request or live connection fails. The backend remains responsible for every consequential decision.
