# QueueLess 2.3 — Frontend Engineering

Client browser application for QueueLess: a physical-visit preparation and queue coordination layer that complements Karnataka citizen service portals.

Built by **Member 3 (Frontend Engineering Lead)**.

---

## Tech Stack
* **Framework:** React 18 + Vite 5 + TypeScript
* **Styling:** Tailwind CSS + Lucide Icons
* **Routing:** React Router 6 (with role-aware protected layouts)
* **Auth:** Firebase Web Client SDK + backend authoritative `/users/me` sync
* **API Client:** Shared typed `fetch` client injecting `Authorization: Bearer <ID-Token>`
* **Realtime:** Native WebSockets with single-use tickets & REST snapshot fallback
* **Hardware Integrations:** Camera QR scanning (`html5-qrcode`) with manual entry fallback, QR generation (`qrcode.react`)

---

## Getting Started

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/realtime/ws
VITE_FIREBASE_API_KEY=your-firebase-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=your-app-id
```

### 3. Start Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 4. Build for Production
```bash
npm run build
```

---

## Role Portals & Demo Walkthrough

The application features 3 role-isolated portals:
1. **Citizen Portal (`/citizen`):**
   - Service discovery with mandatory/optional document checklists.
   - Slot selection (operating hours in `Asia/Kolkata`).
   - Appointment confirmation with opaque check-in QR code.
   - Live WebSocket-powered queue tracking (`/citizen/queue/:tokenId`).
   - AI Service Assistant with verified citations & preliminary Document OCR check.
2. **Officer Portal (`/officer`):**
   - Check-in desk with camera QR scanning & manual lookup (`/officer/check-in`).
   - Counter workspace (`Call Next`, `Start Service`, `Put on Hold`, `Resume`, `Complete`, `No-Show`).
3. **Admin Portal (`/admin`):**
   - Operational throughput metrics, wait time analytics, and counter utilization.

> **Developer Tip:** The `/sign-in` screen includes one-click **Demo Shortcuts** to test Citizen, Officer, and Admin workflows immediately without requiring live SMS OTP credits during development.

