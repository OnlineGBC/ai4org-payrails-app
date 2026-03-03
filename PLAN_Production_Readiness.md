# Plan: Production Readiness

## Goal
Migrate the PayRails platform from local-development mode to a production-grade Azure deployment. This plan is purely infrastructure and configuration — no new product features.

---

## Prerequisites (information needed before starting)

| Item | Status | Notes |
|---|---|---|
| Azure subscription | Required | Resource Group, region chosen |
| Production domain name | Required | e.g. `api.payrails.io` |
| Azure PostgreSQL credentials | Required | Flexible Server, db name, admin user |
| Azure Key Vault name | Required | For secrets |
| GitHub Actions service principal | Required | For CI/CD deploy permission |
| CORS allowed origins | Required | Frontend domain(s) |

---

## Step 1 — Database: SQLite → Azure PostgreSQL

### Backend changes (`backend/`)

**`backend/requirements.txt`** — add:
```
psycopg2-binary>=2.9
```

**`backend/app/config.py`** — `DATABASE_URL` is already env-driven; no code change needed.
Set in Azure App Service configuration:
```
DATABASE_URL=postgresql://user:pass@host:5432/payrails
```

**Alembic migration** — run once against the new PostgreSQL instance:
```bash
alembic upgrade head
```

**Seed data** — production seed script should create:
- At minimum one active `BankConfig` record (the mock bank)
- Admin user account

**Test locally with PostgreSQL first:**
```bash
DATABASE_URL=postgresql://... uvicorn app.main:app --reload
```

---

## Step 2 — Secrets: Hardcoded defaults → Azure Key Vault

### Secrets to move out of code / `.env`

| Secret | Current default | Key Vault secret name |
|---|---|---|
| `JWT_SECRET` | `"changeme"` | `payrails-jwt-secret` |
| `ENCRYPTION_KEY` | `""` (auto-gen) | `payrails-encryption-key` |
| `DATABASE_URL` | SQLite path | `payrails-database-url` |
| `SMTP_PASSWORD` | `""` | `payrails-smtp-password` |
| `BREVO_API_KEY` | `""` | `payrails-brevo-api-key` |
| `ANTHROPIC_API_KEY` | `""` | `payrails-anthropic-api-key` |

### Integration approach
Use **Azure App Service "Key Vault references"** — no SDK changes needed in Python. Set App Service environment variables as:
```
JWT_SECRET=@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/payrails-jwt-secret/)
```
App Service resolves these at startup. The FastAPI app reads them as normal env vars via `pydantic_settings`.

### Generate production `ENCRYPTION_KEY` once
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Store the output in Key Vault. **Never regenerate** — doing so invalidates all encrypted bank account numbers in the database.

---

## Step 3 — CORS: Lock down allowed origins

**`backend/app/config.py`** — `CORS_ORIGINS` already defaults to a localhost list (not `"*"`).

For production, set in Azure App Service configuration:
```
CORS_ORIGINS=https://app.payrails.io,https://payrails.io
```

No code changes needed — `main.py` already reads this env var correctly.

---

## Step 4 — HTTPS / TLS

Use **Azure Application Gateway** or **Azure Front Door** in front of App Service:
- Managed TLS certificate (auto-renew)
- HTTP → HTTPS redirect enforced at gateway
- App Service runs plain HTTP internally (gateway terminates TLS)

Add to `main.py` if terminating TLS at App Service directly instead:
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
if settings.ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

Add `ENV: str = "development"` to `config.py`.

---

## Step 5 — CI/CD: GitHub Actions

### File: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ --tb=short

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - uses: azure/webapps-deploy@v3
        with:
          app-name: payrails-backend
          package: ./backend

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: "3.x"
      - run: flutter build web --dart-define=API_BASE_URL=https://api.payrails.io
        working-directory: mobile_flutter
      - uses: azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_TOKEN }}
          action: upload
          app_location: mobile_flutter/build/web
```

### GitHub Secrets to configure
| Secret | Value |
|---|---|
| `AZURE_CREDENTIALS` | JSON from `az ad sp create-for-rbac` |
| `AZURE_STATIC_WEB_APPS_TOKEN` | From Azure Static Web Apps resource |

---

## Step 6 — Structured Logging & Monitoring

**Add to `backend/requirements.txt`:**
```
azure-monitor-opentelemetry>=1.0
```

**`backend/app/main.py`** — add near top:
```python
import os
from azure.monitor.opentelemetry import configure_azure_monitor

if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()
```

Set in Azure App Service configuration:
```
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

This gives: request traces, exception tracking, response time metrics — all in Azure Monitor / Application Insights.

---

## Step 7 — Production Checklist (run before go-live)

- [ ] `JWT_SECRET` is a 32+ char random string (not `"changeme"`)
- [ ] `ENCRYPTION_KEY` is set and matches the value used when bank accounts were enrolled
- [ ] `DATABASE_URL` points to PostgreSQL (not SQLite)
- [ ] `alembic upgrade head` run against production database
- [ ] `CORS_ORIGINS` set to production frontend domain only
- [ ] HTTPS enforced at gateway level
- [ ] All Key Vault references resolve (check App Service → Configuration → Key Vault references tab)
- [ ] GitHub Actions pipeline passes on a test push to `main`
- [ ] Application Insights showing live telemetry
- [ ] At least one smoke test: register → login → view balance → make payment
- [ ] Admin account seeded with a strong password (not `password123`)
- [ ] Rotate any test API keys (Brevo, Anthropic) to production keys

---

## Effort Estimate

| Step | Effort | Blocker |
|---|---|---|
| Step 1 — PostgreSQL | Small — config only | Need DB credentials |
| Step 2 — Key Vault | Small — config only | Need Key Vault provisioned |
| Step 3 — CORS | None — already done in code | Just set env var |
| Step 4 — HTTPS | Small — gateway config | Need domain + cert |
| Step 5 — CI/CD | Medium — ~1 day | Need service principal |
| Step 6 — Monitoring | Small — 1 package + 3 lines | Need App Insights connection string |

**Total:** approximately 1–2 days of configuration and pipeline work, assuming Azure resources are already provisioned.
