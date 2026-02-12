# PayRails – Project Status & Roadmap

## 1. Project Goal

PayRails is a **real-time B2B payments platform** built on a **sponsor-bank-led model**. The core premise is that businesses today suffer from slow, expensive payment infrastructure (ACH batching, wire fees, multi-day settlement). PayRails aims to solve this by providing:

- **Instant settlement** via FedNow and/or RTP (Real-Time Payments) rails
- **Sponsor bank compliance** — the platform operates under a sponsor bank's charter, meaning PayRails itself does not hold funds or require a banking license. The sponsor bank handles regulatory obligations (BSA/AML, KYC/KYB) while PayRails provides the technology layer
- **Rail abstraction** — merchants and businesses interact with a single API regardless of whether the underlying payment moves over FedNow, RTP, or falls back to ACH. The platform selects the optimal rail based on amount, availability, and cost
- **No custody** — funds flow directly between the sponsor bank and end parties. PayRails never takes custody of funds, reducing regulatory burden

**Target users:**
- Businesses (merchants, vendors, suppliers) that need to send or receive payments in real time
- The sponsor bank partner that provides the banking infrastructure and compliance umbrella

**Technical architecture:**
- A **FastAPI (Python) backend** that exposes payment APIs, manages merchant accounts, orchestrates transactions, and integrates with bank/payment rails
- A **Flutter mobile/web frontend** that provides a dashboard for merchants to initiate payments, view transaction history, manage accounts, and onboard

---

## 2. What Has Been Completed

### Backend (`backend/`)
- **FastAPI application scaffold** — app initializes, CORS middleware configured, runs via Uvicorn
- **Health check endpoint** — `GET /` returns `{"status": "ok"}`
- **Database layer** — SQLAlchemy configured with SQLite (`local.db`), engine and session factory created, declarative base defined
- **Environment configuration** — `.env.example` template with `JWT_SECRET` placeholder; real `.env` properly gitignored
- **Python virtual environment** — `payrails.app.venv` set up locally with dependencies installed

### Frontend (`mobile_flutter/`)
- **Flutter project initialized** — multi-platform support scaffolded for Android, iOS, Web, Windows, Linux, macOS
- **App entry point** — `main.dart` renders a MaterialApp with a static placeholder label ("Instant Pay – Flutter Web OK")
- **Dart SDK constraint** — configured for SDK >=3.10.0

### Repository
- **Git repo** on GitHub (`OnlineGBC/ai4org-payrails-app`)
- **`.gitignore`** properly configured (Python artifacts, `.env`, venvs, `_sdk/`, Flutter build outputs, IDE files, OS files)
- **Documentation** — `README.md`, `ARCHITECTURE.md`, `RUNBOOK.md`, `VC_OVERVIEW.md` committed
- **Bundled Flutter SDK** — available locally in `_sdk/` (gitignored)

### Summary
The project has a **working development environment** and **runnable skeletons** for both backend and frontend, but **no business logic, data models, or integrations exist yet**.

---

## 3. What Needs to Be Completed

### 3.1 Backend — Data Models & Database

| Item | Description |
|---|---|
| **Merchant model** | Business entity with name, EIN/tax ID, contact info, bank account details, onboarding status, KYB verification status |
| **User model** | Individual users tied to a merchant, with email, hashed password, role (admin/operator/viewer) |
| **Transaction model** | Payment records with sender, receiver, amount, currency, rail used (FedNow/RTP/ACH/Card), status (pending/processing/completed/failed), timestamps, reference IDs |
| **Bank account model** | Linked bank accounts with routing number, account number (encrypted), account type, verification status |
| **Webhook/event log** | Audit trail of all inbound and outbound events (bank callbacks, status changes, API calls) |
| **Ledger model** | Embedded ledger for tracking debits, credits, and balances per merchant account with full audit trail |
| **Bank/rail configuration model** | Sponsor bank connection details, supported rails, limits, and routing preferences — supports multi-bank architecture |
| **Database migrations** | Alembic setup for schema versioning. Migration from SQLite to PostgreSQL (Azure) for production |

### 3.2 Backend — Authentication & Authorization

| Item | Description |
|---|---|
| **JWT authentication** | Token-based auth using the JWT_SECRET. Login endpoint issuing access + refresh tokens |
| **Password hashing** | bcrypt or argon2 for stored passwords |
| **Role-based access control** | Middleware enforcing permissions per role (admin, operator, viewer) |
| **API key auth** | For programmatic/M2M access from merchant systems |
| **Rate limiting** | Per-endpoint throttling to prevent abuse |

### 3.3 Backend — Core Payment APIs

| Item | Description |
|---|---|
| **POST /payments** | Initiate a payment — validate inputs, select rail, submit to sponsor bank, return transaction ID |
| **GET /payments/{id}** | Retrieve payment status and details |
| **GET /payments** | List payments with filters (date range, status, amount, rail) and pagination |
| **POST /payments/{id}/cancel** | Cancel a pending payment if the rail supports it |
| **POST /webhooks/bank** | Receive status callbacks from the sponsor bank (payment completed, failed, returned) |
| **GET /balance** | Retrieve current balance/available funds from the sponsor bank |
| **POST /payouts** | Initiate outbound payout to a merchant's linked bank account |

### 3.4 Backend — Merchant Onboarding APIs

| Item | Description |
|---|---|
| **POST /merchants** | Register a new merchant (business details, beneficial owners) |
| **POST /merchants/{id}/kyb** | Submit KYB (Know Your Business) verification data to the sponsor bank or compliance provider |
| **GET /merchants/{id}/status** | Check onboarding/verification status |
| **POST /merchants/{id}/bank-accounts** | Link a bank account (micro-deposit verification or instant verification via Plaid/MX) |
| **PUT /merchants/{id}** | Update merchant profile |

### 3.5 Backend — Bank & Rail Integration

> **Note:** No sponsor bank API documentation is available yet. Phase 1 will be built against a **mock bank API** that simulates realistic FedNow/RTP/ACH behavior. The mock assumes the following based on publicly available FedNow specifications and common BaaS patterns:
>
> **Mock Bank API Assumptions:**
> - **Protocol:** REST/JSON over HTTPS (as confirmed in chat — the sponsor bank abstracts ISO 20022 internally)
> - **Authentication:** OAuth 2.0 client credentials flow (standard for BaaS providers like Cross River, Synapse, etc.)
> - **Endpoints mocked:**
>   - `POST /transfers` — initiate a credit transfer (FedNow/RTP/ACH)
>   - `GET /transfers/{id}` — check transfer status
>   - `POST /rfp` — send a Request for Payment
>   - `GET /balance` — retrieve account balance
>   - `GET /transfers` — list transfers with filters
>   - `POST /ach/originate` — initiate ACH transfer
> - **Webhooks:** Bank sends POST callbacks to a PayRails webhook URL for status changes (pending → processing → completed/failed/returned)
> - **FedNow limits:** Up to $500,000 per transaction (default FedNow limit; $10M is the max configurable by the bank)
> - **RTP limits:** Up to $1,000,000 per transaction (TCH default)
> - **ACH limits:** No per-transaction limit, but subject to daily/monthly caps set by the bank
> - **Settlement:** FedNow and RTP settle in real time (seconds). ACH settles next business day
> - **Idempotency:** Mock supports idempotency keys via `X-Idempotency-Key` header
> - **Error codes:** Standardized error responses (insufficient_funds, account_closed, invalid_routing, timeout, rail_unavailable)
>
> When a real bank partner is secured, the mock layer will be replaced with the actual bank API client. The abstraction layer is designed to make this swap straightforward.

| Item | Description |
|---|---|
| **Mock bank API service** | In-process mock that simulates bank responses with realistic delays, statuses, and error scenarios |
| **Bank API abstraction layer** | Interface/adapter pattern so the mock can be swapped for a real bank client without changing business logic |
| **FedNow integration (mock)** | Simulates credit transfer initiation and status callbacks via the mock |
| **RTP integration (mock)** | Simulates RTP payments with appropriate limits and timing |
| **ACH fallback (mock)** | Simulates ACH origination with next-business-day settlement |
| **Card fallback** | Direct integration with Visa/Mastercard debit rails as the final fallback option |
| **Rail selection logic** | Routing engine that picks FedNow → RTP → ACH → Card based on: amount limits, recipient bank availability, time of day, cost |
| **Idempotency** | Ensure duplicate payment requests don't result in duplicate transactions via `X-Idempotency-Key` |
| **Reconciliation** | End-of-day reconciliation between PayRails records and bank settlement reports (mock generates simulated settlement files) |

### 3.6 Backend — Infrastructure & Security

> **Decision:** Azure is the cloud provider for production infrastructure.

| Item | Description |
|---|---|
| **CORS lockdown** | Replace `allow_origins=["*"]` with specific allowed origins |
| **HTTPS enforcement** | TLS termination via Azure Application Gateway or Azure Front Door |
| **Encryption at rest** | Encrypt sensitive fields (bank account numbers, SSNs) in the database |
| **Logging & monitoring** | Structured logging, error tracking (Sentry or Azure Monitor/Application Insights), metrics |
| **Environment config** | Migrate from `.env` to Azure Key Vault for production secrets management |
| **Database** | Azure Database for PostgreSQL (Flexible Server) for production; SQLite remains for local dev |
| **Compute** | Azure App Service or Azure Container Apps for the FastAPI backend |
| **Pinned dependencies** | Add version pins to `requirements.txt` (e.g., `fastapi==0.115.0`) |
| **Tests** | Unit tests for models/services, integration tests for API endpoints, mock tests for bank integrations |
| **CI/CD** | GitHub Actions with deployment to Azure |

### 3.7 Frontend — Screens & Navigation

| Screen | Description |
|---|---|
| **Login / Register** | Email + password authentication, token storage |
| **Dashboard** | Overview of recent transactions, balance, quick-send |
| **Send Payment** | Form to initiate a payment (recipient, amount, memo, rail preference) |
| **Transaction History** | Searchable, filterable list of past payments with status indicators |
| **Transaction Detail** | Full detail view of a single payment including rail, timestamps, status history |
| **Merchant Profile** | View/edit business details, onboarding status |
| **Bank Accounts** | Link, verify, and manage connected bank accounts |
| **Settings** | User preferences, API keys, notification settings |

### 3.8 Frontend — Architecture & Integration

| Item | Description |
|---|---|
| **State management** | Provider, Riverpod, or Bloc for app state |
| **HTTP client** | `dio` or `http` package for API calls to the FastAPI backend |
| **Secure token storage** | `flutter_secure_storage` for JWT tokens |
| **Routing** | `go_router` or Navigator 2.0 for named routes and deep linking |
| **Form validation** | Input validation for payment amounts, bank account numbers, etc. |
| **Error handling** | User-facing error messages, retry logic, offline detection |
| **Push notifications** | Payment status updates via Firebase Cloud Messaging or similar |
| **Fix stale test** | `test/widget_test.dart` tests the removed counter template — needs to be updated or removed |

---

## 4. Information Needed for Integrations

### 4.1 Sponsor Bank Partner (Critical)

This is the most important dependency. PayRails cannot process real payments without a sponsor bank.

| Need | Detail |
|---|---|
| **Sponsor bank identity** | Which bank will serve as the sponsor? (e.g., a community bank, BaaS provider like Cross River, Evolve, etc.) |
| **FedNow access** | Does the sponsor bank have FedNow connectivity? What is their gateway/API format? Do they expose a direct API or require ISO 20022 XML message construction? |
| **RTP access** | Does the sponsor bank participate in The Clearing House RTP network? What is their integration method? |
| **ACH origination** | How does the sponsor bank handle ACH? Nacha file upload, API-based (e.g., Moov, Modern Treasury), or proprietary? |
| **API credentials & documentation** | Sandbox/test environment credentials, API docs, endpoint URLs, authentication method (mTLS, OAuth, API key) |
| **Webhook/callback setup** | How will the bank notify PayRails of payment status changes? Push (webhook) or pull (polling)? |
| **Settlement model** | How and when does settlement occur? Real-time, end-of-day batch, or pre-funded? |
| **Amount limits** | Per-transaction and daily limits for each rail |
| **Operating hours** | FedNow is 24/7; RTP is 24/7; ACH has cutoff times — confirm specifics with sponsor bank |

### 4.2 KYC/KYB Compliance Provider

| Need | Detail |
|---|---|
| **Compliance provider** | Will the sponsor bank handle KYB directly, or should PayRails integrate a third-party provider? (e.g., Alloy, Middesk, Persona, Onfido) |
| **Verification requirements** | What data is required for merchant onboarding? (EIN, articles of incorporation, beneficial owner SSNs, etc.) |
| **API access** | Sandbox credentials and docs for the chosen compliance provider |
| **Ongoing monitoring** | Is continuous transaction monitoring (SAR filing, OFAC screening) handled by the sponsor bank or PayRails? |

### 4.3 Bank Account Verification — MOCK ASSUMPTIONS FOR PHASE 1

> **Decision:** Phase 1 will use a mock bank account verification flow. When a real bank partner is secured, the mock will be replaced with the bank's verification method or a third-party aggregator.

**Mock Assumptions:**
- **Verification method:** Simulated micro-deposit flow — the mock instantly "sends" two small deposits (e.g., $0.12, $0.34) and the user confirms the amounts. In the mock, any amounts entered are accepted
- **Account validation:** Mock validates routing number format (9 digits, valid checksum) and account number format (4-17 digits). No real bank lookup is performed
- **Instant verification:** A mock Plaid-like flow is stubbed — user selects a bank from a list, enters test credentials, and the mock returns a verified account. This prepares the UI and API for a real Plaid/MX integration later
- **Data stored:** Routing number, last 4 digits of account number (full number encrypted), account type (checking/savings), verification status, verification method used

| Need | Status |
|---|---|
| **Verification method** | Mocked: micro-deposit simulation + instant verification stub |
| **Aggregator choice** | Deferred to Phase 2 — mock Plaid-like interface built for future swap |
| **Account validation** | Mocked: format validation only (routing number checksum, account number length) |

### 4.4 Infrastructure & Deployment — RESOLVED

> **Decision:** Azure is the cloud provider.

| Need | Decision |
|---|---|
| **Cloud provider** | **Microsoft Azure** |
| **Database** | Azure Database for PostgreSQL (Flexible Server); SQLite for local development |
| **Compute** | Azure App Service or Azure Container Apps for FastAPI backend |
| **Secrets management** | Azure Key Vault |
| **Monitoring** | Azure Monitor + Application Insights |
| **SSL/TLS** | Azure-managed certificates via Application Gateway or Front Door |
| **Domain** | Still needed — production domain name TBD |
| **App distribution** | Still needed — App Store / Play Store / web-only decision TBD |

### 4.5 Business Logic Decisions

**Resolved:**

| Need | Decision |
|---|---|
| **Fee structure** | SaaS monthly per active account + $0.01–$0.05 per transaction + premium API tier |
| **Multi-currency** | USD only |
| **Payment types** | Credit push + Request-for-Payment (RFP) |
| **Smart routing** | FedNow → RTP → ACH → Card (direct Visa/Mastercard debit rails) |
| **Card fallback** | Direct Visa/Mastercard debit rails (not via Stripe/Adyen) |
| **Healthcare/HIPAA** | **Deferred to Phase 2** — removed from Phase 1 scope |

**Still needed:**

| Need | Detail |
|---|---|
| **Refunds/returns** | What is the refund policy and flow? How are returned payments handled? |
| **Notifications** | Email, SMS, push, or in-app only for payment status updates? |
| **Reporting** | What reports do merchants need? (Daily settlement, monthly statements, tax documents) |
| **Batch/ERP payments** | Premium feature — what formats? (CSV upload, API?) |

---

## Current State at a Glance

```
[##                    ] ~10% — Project scaffolding complete, no business logic
```

| Layer | Status |
|---|---|
| Backend scaffold | Done |
| Database models | Not started |
| Authentication | Not started |
| Payment APIs | Not started |
| Bank integration | Not started (mock assumptions defined — unblocked for Phase 1) |
| Compliance/KYB | Not started (blocked on provider choice) |
| Frontend scaffold | Done |
| Frontend screens | Not started |
| Frontend API integration | Not started |
| Tests | Not started (1 stale test exists) |
| CI/CD | Not started |
| Deployment | Not started |
