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
| **Transaction model** | Payment records with sender, receiver, amount, currency, rail used (FedNow/RTP/ACH), status (pending/processing/completed/failed), timestamps, reference IDs |
| **Bank account model** | Linked bank accounts with routing number, account number (encrypted), account type, verification status |
| **Webhook/event log** | Audit trail of all inbound and outbound events (bank callbacks, status changes, API calls) |
| **Database migrations** | Alembic setup for schema versioning. Migration from SQLite to PostgreSQL for production |

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

| Item | Description |
|---|---|
| **FedNow integration** | Connect to the sponsor bank's FedNow gateway to send/receive ISO 20022 messages (pacs.008 for credit transfers, pacs.002 for status) |
| **RTP integration** | Connect to the sponsor bank's RTP (The Clearing House) gateway for real-time payments |
| **ACH fallback** | For cases where real-time rails are unavailable or amount exceeds limits — Nacha file generation or API-based ACH via sponsor bank |
| **Rail selection logic** | Routing engine that picks FedNow vs RTP vs ACH based on: amount limits, recipient bank availability, time of day, cost |
| **Idempotency** | Ensure duplicate payment requests don't result in duplicate transactions |
| **Reconciliation** | End-of-day reconciliation between PayRails records and sponsor bank settlement reports |

### 3.6 Backend — Infrastructure & Security

| Item | Description |
|---|---|
| **CORS lockdown** | Replace `allow_origins=["*"]` with specific allowed origins |
| **HTTPS enforcement** | TLS termination in production |
| **Encryption at rest** | Encrypt sensitive fields (bank account numbers, SSNs) in the database |
| **Logging & monitoring** | Structured logging, error tracking (Sentry or similar), metrics |
| **Environment config** | Migrate from `.env` to a secrets manager for production (AWS Secrets Manager, Vault, etc.) |
| **Pinned dependencies** | Add version pins to `requirements.txt` (e.g., `fastapi==0.115.0`) |
| **Tests** | Unit tests for models/services, integration tests for API endpoints, mock tests for bank integrations |
| **CI/CD** | GitHub Actions or similar for automated testing and deployment |

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

### 4.3 Bank Account Verification

| Need | Detail |
|---|---|
| **Verification method** | Micro-deposits (slow, 2-3 days), or instant verification via aggregator? |
| **Aggregator choice** | If instant: Plaid, MX, Finicity, or Yodlee? Need API credentials and docs |
| **Account validation** | Does the sponsor bank provide account/routing number validation, or should PayRails use a third-party service? |

### 4.4 Infrastructure & Deployment

| Need | Detail |
|---|---|
| **Cloud provider** | AWS, GCP, Azure — or on-prem? Affects database, secrets management, deployment pipeline choices |
| **Database** | PostgreSQL is the likely production choice — hosted (RDS, Cloud SQL) or self-managed? |
| **Domain & SSL** | Production domain name, SSL certificate provisioning (ACM, Let's Encrypt) |
| **App distribution** | Will the Flutter app be distributed via App Store / Play Store, or web-only initially? |

### 4.5 Business Logic Decisions

| Need | Detail |
|---|---|
| **Fee structure** | Does PayRails charge per transaction? Flat fee, percentage, or tiered? This affects the transaction model and reporting |
| **Multi-currency** | USD only, or multi-currency support needed? |
| **Payment types** | Credit push only? Or also request-for-payment (RfP) / debit pull? |
| **Refunds/returns** | What is the refund policy and flow? How are returned payments handled? |
| **Notifications** | Email, SMS, push, or in-app only for payment status updates? |
| **Reporting** | What reports do merchants need? (Daily settlement, monthly statements, tax documents) |

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
| Bank integration | Not started (blocked on sponsor bank info) |
| Compliance/KYB | Not started (blocked on provider choice) |
| Frontend scaffold | Done |
| Frontend screens | Not started |
| Frontend API integration | Not started |
| Tests | Not started (1 stale test exists) |
| CI/CD | Not started |
| Deployment | Not started |
