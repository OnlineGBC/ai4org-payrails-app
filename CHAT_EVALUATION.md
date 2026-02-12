# FedNow Chat Evaluation

This document evaluates the decisions and information captured in `FedNowChat.txt` and maps them against the 8 workstreams and 5 blocker categories defined in `PROJECT_STATUS.md`.

---

## Decisions Already Made (Extracted from Chat)

### Business & Strategy
- **Target users:** All businesses, initial focus on SMBs (line 12)
- **Regulatory approach:** Partner with a regulated institution — no money transmitter licenses (line 14)
- **Compliance:** KYC/KYB and AML outsourced to the bank partner (line 13)
- **Payment direction:** Both sending and receiving (line 11)
- **Target scale:** 50,000 B2B customers, 10 million transactions/year (line 8)
- **Market:** $27T U.S. B2B payments, TAM $200B+ by 2027, initial wedge 5M SMBs

### Business Model
- **SaaS:** Monthly fee per active account
- **Transaction markup:** $0.01–$0.05 per transaction
- **Premium tier:** API access, ERP/batch payments

### Product Features Committed
- 24/7 instant credit transfers via FedNow
- Request-for-Payment (RFP) / real-time invoicing
- Smart routing: FedNow → RTP → ACH → Card fallback (line 88)
- Single app supporting multiple sponsor banks (line 89)
- ~~Healthcare vertical: HIPAA-compliant ledger tagging, provider remittance (line 87)~~ **Deferred to Phase 2**
- QR Code and NFC-based payments on mobile (lines 106-107)
- Real-time balance, notifications, reconciliation
- Embedded ledger, permissions, audit trail

### Technical Decisions
- **Backend:** Python with FastAPI (line 126)
- **Frontend:** Flutter, targeting Android phone + emulator initially (line 126)
- **Bank API format:** REST/JSON (line 127)
- **Authentication:** Email/password only for now (line 130)
- **Bank integration:** Will use the sponsor bank's own FedNow API (line 126)

### Candidate Sponsor Banks Identified
Primary list (line 18): Sunrise Banks, Cross River Bank, Carver Federal Savings Bank, M&F Bank, Sutton Bank, OneUnited

Extended list evaluated (line 121): Piermont Bank, Bank Southern, Liberty Bank, Central Bank KC, Lead Bank

The chat references checking these banks against official FedNow and RTP participant datasets (line 122), but results were not captured in this transcript.

### Development Environment (Confirmed Working)
- Windows 11 (25H2)
- Flutter 3.38.9 stable at `C:\flutter`
- Dart 3.10.8
- Android SDK 36.1.0 with emulator
- Chrome and Edge for web
- Visual Studio Community 2019 for Windows desktop
- Python 3.10 with FastAPI in venv

---

## Impact on the 8 Workstreams

### 3.1 Data Models & Database

**What the chat resolves:**
- Transaction model needs fields for: rail used (FedNow/RTP/ACH/Card), RFP support
- Multi-bank support means the merchant model needs a sponsor bank association (or the ability to route through different banks)
- Ledger model needed — the pitch references an "embedded ledger" for permissions and audit

**What remains open:**
- No specific schema decisions were made in the chat
- Multi-bank routing adds complexity — need a bank/rail configuration model

### 3.2 Authentication & Authorization

**What the chat resolves:**
- Email/password only for now (line 130) — simplifies initial implementation
- JWT-based (from .env.example with JWT_SECRET)

**What remains open:**
- Role-based access control not discussed — pitch mentions "permissions" but no specifics
- API key auth for programmatic access not discussed
- No MFA or SSO requirements mentioned

### 3.3 Core Payment APIs

**What the chat resolves:**
- Both send and receive payments confirmed
- Request-for-Payment (RFP) is a confirmed feature — this is a FedNow-native capability
- Real-time balance queries needed
- Reconciliation endpoint needed
- QR Code payments imply a payment-link or payment-request encoding scheme

**What remains open:**
- RFP flow details: who initiates, approval workflow, expiration
- QR Code payload format — likely encode a payment request URL or FedNow RFP reference
- NFC payment flow — tap-to-pay implies proximity payments, needs device integration
- Batch/ERP payment API (mentioned as premium feature) not detailed

### 3.4 Merchant Onboarding APIs

**What the chat resolves:**
- KYB outsourced to bank partner
- SMB focus means simpler onboarding initially

**What remains open:**
- Exact data required for onboarding depends on the sponsor bank's requirements
- No compliance provider chosen (Alloy, Middesk, etc.) — or is the bank handling it entirely?
- Multi-bank support raises the question: does a merchant onboard with one bank or multiple?

### 3.5 Bank & Rail Integration

**What the chat resolves:**
- REST/JSON API format (not ISO 20022 XML directly — the bank abstracts this)
- Smart routing order: FedNow → RTP → ACH → Card fallback
- Will use the bank's own FedNow API
- FedNow supports up to $10M per transaction
- FedNow and RTP are 24/7
- Multi-bank architecture — single app connects to multiple sponsor banks

**What remains open (unblocked via mock assumptions):**
- No API documentation from any sponsor bank yet (line 126: "we dont have the API documentation yet")
- No sandbox/test credentials
- No confirmed bank partnership — only a candidate list
- Webhook/callback mechanism unknown
- Settlement model unknown

**Phase 1 decisions:**
- **Mock bank API** will be built to simulate FedNow/RTP/ACH behavior (REST/JSON, OAuth 2.0, webhook callbacks)
- **Card fallback:** Direct Visa/Mastercard debit rails
- **Healthcare/HIPAA:** Deferred to Phase 2

Development is **unblocked** — the mock bank layer allows all workstreams to proceed. The mock will be swapped for a real bank client when a partnership is secured.

### 3.6 Infrastructure & Security

**What the chat resolves:**
- Development is on Windows (confirmed working)
- Local SQLite for development

**Resolved:**
- **Cloud provider:** Microsoft Azure
- **Database:** Azure Database for PostgreSQL (Flexible Server)
- **Secrets:** Azure Key Vault
- **Monitoring:** Azure Monitor + Application Insights
- **Healthcare/HIPAA:** Deferred to Phase 2

**What remains open:**
- CORS lockdown, HTTPS, domain name still needed
- CI/CD not discussed
- App distribution plan (App Store / Play Store / web-only) TBD

### 3.7 Frontend Screens

**What the chat resolves:**
- QR Code scanning screen needed
- NFC tap-to-pay screen needed
- Dashboard with real-time balance
- Payment sending flow
- Notification display
- Android is the primary target platform

**What remains open:**
- No wireframes or UI designs exist
- RFP approval/review screen not defined
- Multi-bank selection UI not defined
- Batch payment UI for premium tier not defined

### 3.8 Frontend Architecture

**What the chat resolves:**
- Flutter confirmed, SDK 3.10+
- Multi-platform scaffolding exists (Android, iOS, Web, Windows, Linux, macOS)
- Android emulator and physical device are available for testing

**What remains open:**
- State management choice (Provider, Riverpod, Bloc)
- HTTP client choice (dio, http)
- QR Code package (e.g., `mobile_scanner`, `qr_flutter`)
- NFC package (e.g., `nfc_manager`)
- Secure storage for JWT tokens
- Push notification setup
- Stale test still needs fixing

---

## Impact on the 5 Blocker Categories

### 4.1 Sponsor Bank Partner — PARTIALLY RESOLVED

**Resolved:**
- Six primary candidate banks identified: Sunrise Banks, Cross River Bank, Carver Federal Savings Bank, M&F Bank, Sutton Bank, OneUnited
- Five additional banks evaluated: Piermont Bank, Bank Southern, Liberty Bank, Central Bank KC, Lead Bank
- Decision to use the bank's own FedNow REST/JSON API
- Decision to partner (not self-operate as regulated entity)

**Still needed:**
- A signed partnership agreement with at least one bank
- API documentation, sandbox credentials, endpoint URLs
- Webhook/callback specifications
- Settlement model and timing
- Per-transaction cost from the bank (to validate the $0.01–$0.05 markup model)
- RTP access confirmation (not all FedNow banks also do RTP)
- ACH origination method from the chosen bank

### 4.2 KYC/KYB Compliance Provider — PARTIALLY RESOLVED

**Resolved:**
- Compliance will be outsourced (not built in-house)
- The bank partner is expected to handle or provide compliance

**Still needed:**
- Confirmation: does the sponsor bank handle KYB end-to-end, or does PayRails need a third-party provider?
- If third-party: which provider? (Alloy, Middesk, Persona)
- OFAC/sanctions screening — bank or PayRails?

### 4.3 Bank Account Verification — MOCK ASSUMPTIONS FOR PHASE 1

**Phase 1 mock assumptions:**
- Simulated micro-deposit verification flow (instant approval in mock)
- Mock Plaid-like instant verification stub (prepares UI/API for real integration later)
- Format-only validation: routing number checksum (9 digits), account number length (4-17 digits)
- Real aggregator integration (Plaid/MX) deferred to Phase 2 when bank partner is secured

### 4.4 Infrastructure & Deployment — RESOLVED

**Decisions:**
- **Cloud provider:** Microsoft Azure
- **Database:** Azure Database for PostgreSQL (Flexible Server); SQLite for local dev
- **Compute:** Azure App Service or Azure Container Apps
- **Secrets:** Azure Key Vault
- **Monitoring:** Azure Monitor + Application Insights
- **SSL/TLS:** Azure-managed certificates

**Still needed:** Production domain name, app distribution plan (App Store / Play Store / web-only)

### 4.5 Business Logic Decisions — MOSTLY RESOLVED

**Resolved:**
- Fee structure: SaaS monthly + $0.01–$0.05 per transaction + premium API tier
- Payment types: Credit push + Request-for-Payment (RFP)
- Smart routing: FedNow → RTP → ACH → Card fallback
- Multi-bank support: yes
- Verticals: general SMB (healthcare deferred to Phase 2)
- Mobile payment methods: QR Code + NFC
- USD only (line 8: "all transactions are US or USD-based")

**Newly resolved:**
- Card fallback: **Direct Visa/Mastercard debit rails** (not via Stripe/Adyen)
- Healthcare/HIPAA: **Deferred to Phase 2**

**Still needed:**
- Refund/return policy and flow
- Notification channels: email, SMS, push, or in-app? (pitch says "notifications" but no specifics)
- Reporting requirements for merchants
- Batch/ERP payment details (premium feature — what formats? CSV, API?)

---

## Summary: What the Chat Changes

| Category | Before Chat | After Chat + Latest Decisions |
|---|---|---|
| Sponsor bank | Unknown | 6 candidates identified, no partnership signed; **mock API for Phase 1** |
| Bank API format | Unknown | REST/JSON confirmed, no docs yet; **mock assumes OAuth 2.0 + webhooks** |
| Bank account verification | Unknown | **Mock micro-deposit + Plaid-like stub for Phase 1** |
| Compliance approach | Unknown | Outsourced to bank partner |
| Payment types | Unknown | Send + receive, credit push + RFP |
| Routing strategy | Unknown | FedNow → RTP → ACH → Card (**direct Visa/MC debit**) |
| Business model | Unknown | SaaS + per-txn markup + premium API |
| Mobile payments | Unknown | QR Code + NFC confirmed |
| Healthcare vertical | Not considered | **Deferred to Phase 2** |
| Multi-bank | Not considered | Single app for multiple sponsor banks confirmed |
| Auth method | JWT_SECRET existed | Email/password only, JWT confirmed |
| Target scale | Unknown | 50K customers, 10M txns/year |
| Currency | Unknown | USD only |
| Infrastructure | Unknown | **Microsoft Azure** (PostgreSQL, Key Vault, App Service) |
| Dev environment | Assumed | Fully confirmed and working |

### Critical Path

With mock assumptions in place, **all 8 workstreams are unblocked for Phase 1 development**. The mock bank API layer, mock account verification, and Azure infrastructure decisions remove the previously identified blockers.

**Phase 1** can deliver a fully functional prototype with mock bank integrations.

**Phase 2** (requires real bank partnership) will:
- Replace mock bank API with real sponsor bank integration
- Replace mock account verification with Plaid/MX or bank-provided verification
- Add healthcare/HIPAA-compliant ledger tagging
- Add real Visa/Mastercard direct debit integration

The recommended parallel track is to continue pursuing a sandbox agreement with one of the candidate banks (Cross River is the most likely to have a developer-friendly API program) while Phase 1 development proceeds.
