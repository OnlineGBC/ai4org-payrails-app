# Cloud SQL Migration Plan

## Goal
Migrate from ephemeral SQLite (data lost on every Cloud Run restart/deploy) to persistent Cloud SQL PostgreSQL.

## What Was Already in Place (No Changes Needed)
- `psycopg2-binary` already in `backend/requirements.txt`
- Alembic already configured with 6 migration files in `backend/alembic/versions/`
- `alembic upgrade head` already runs on startup in `entrypoint.sh`
- `DATABASE_URL` already configurable via env var in `backend/app/config.py`
- `SEED_DATA` already controlled by env var in `entrypoint.sh`

---

## All Commands Executed (with Explanations)

### 1. Enable Cloud SQL API
```bash
gcloud services enable sqladmin.googleapis.com --project=fednowrtppayrails
```
Cloud SQL Admin API is disabled by default on new projects. This enables it so gcloud can create and manage Cloud SQL instances.

---

### 2. Create Cloud SQL Instance
```bash
gcloud sql instances create payrails-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-east1 \
  --project=fednowrtppayrails
```
Creates a PostgreSQL 15 database server named `payrails-db` in `us-east1`.
`db-f1-micro` is the smallest/cheapest tier (~$7-10/month). Takes 2-3 minutes to provision.

---

### 3. Create the Database
```bash
gcloud sql databases create payrails --instance=payrails-db --project=fednowrtppayrails
```
Creates a database named `payrails` inside the instance. The instance is the server;
the database is the schema/namespace within it (equivalent to creating a SQLite file).

---

### 4. Create the Database User
```bash
gcloud sql users create payrails-user --instance=payrails-db --password=REDACTED_SEE_SECRET_MANAGER --project=fednowrtppayrails
```
Creates a PostgreSQL user `payrails-user` with the given password.
**IMPORTANT:** Use alphanumeric passwords only — special characters like `@`, `$`, `!`
cause shell interpolation and URL parsing issues in the DATABASE_URL connection string.

---

### 5. Grant Cloud Run Access to Cloud SQL
```bash
gcloud projects add-iam-policy-binding fednowrtppayrails \
  --member="serviceAccount:1090496405720-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```
Cloud Run uses a service account (`1090496405720-compute@developer.gserviceaccount.com`)
to run your container. By default it has no access to Cloud SQL. This grants it the
`cloudsql.client` role so it can connect via the Unix socket at runtime.

---

### 6. Set Min Instances to Prevent Scale-to-Zero
```bash
gcloud run services update payrails --region us-east1 --min-instances=1
```
Cloud Run scales to zero instances when idle (~15 min), which wipes any in-memory/local
state and causes cold-start delays. Setting min-instances=1 keeps one container always
alive. Cost: ~$10-15/month extra.

---

### 7. Deploy with Cloud SQL Connected
```bash
gcloud run deploy payrails \
  --source C:/Users/raja/ai4org_payrails \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances fednowrtppayrails:us-east1:payrails-db \
  --set-env-vars "SEED_DATA=true,DATABASE_URL=postgresql+psycopg2://payrails-user:REDACTED_SEE_SECRET_MANAGER@/payrails?host=/cloudsql/fednowrtppayrails:us-east1:payrails-db" \
  --project=fednowrtppayrails
```
Builds the Docker image from source and deploys to Cloud Run with:
- `--add-cloudsql-instances` — mounts the Cloud SQL Unix socket inside the container at
  `/cloudsql/fednowrtppayrails:us-east1:payrails-db/`
- `DATABASE_URL` — tells the app to connect to PostgreSQL via that Unix socket
- `SEED_DATA=true` — on first startup, seeds all test merchants, users, and balances

On startup, `entrypoint.sh` automatically runs `alembic upgrade head` which creates all
tables in PostgreSQL, then seeds the data.

---

### 8. Code Change — Remove create_all from main.py
Removed `Base.metadata.create_all(bind=engine)` from the startup handler in `backend/app/main.py`.
Alembic handles all schema creation via migrations. Leaving `create_all` in place bypasses
Alembic and can cause conflicts with PostgreSQL (it recreates tables outside migration control).

---

## Future Deploy Command (use this going forward)
```bash
gcloud run deploy payrails \
  --source C:/Users/raja/ai4org_payrails \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances fednowrtppayrails:us-east1:payrails-db \
  --set-env-vars "SEED_DATA=false,DATABASE_URL=postgresql+psycopg2://payrails-user:REDACTED_SEE_SECRET_MANAGER@/payrails?host=/cloudsql/fednowrtppayrails:us-east1:payrails-db" \
  --project=fednowrtppayrails
```
Note: `SEED_DATA=false` — database is already seeded, no need to reseed on every deploy.
The seed script is safe to re-run (skips existing records) but `false` avoids the extra queries.

## Future Workflow — Schema Changes
When you add/change a model, run this before deploying:
```bash
cd backend
alembic revision --autogenerate -m "brief description of change"
```
Review the generated file in `backend/alembic/versions/`, then deploy as normal.
Alembic applies the migration automatically on startup.

---

## Cloud SQL Instance Details
| Setting | Value |
|---|---|
| Project | fednowrtppayrails |
| Instance name | payrails-db |
| Region | us-east1-c |
| Tier | db-f1-micro |
| Database version | PostgreSQL 15 |
| Public IP | 34.26.34.254 |
| Database name | payrails |
| DB User | payrails-user |
| DB Password | REDACTED_SEE_SECRET_MANAGER |
| Connection name | fednowrtppayrails:us-east1:payrails-db |

---

## Seeded Test Data

### Banks (16 total — all support fednow, rtp, ach, card)

| Bank Config ID | Bank Name | FedNow Limit | RTP Limit | ACH Limit |
|---|---|---|---|---|
| bank-config-001 | Pinnacle BankTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-002 | American BankTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-003 | USBankTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-004 | BNYMellonTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-005 | BancorpTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-006 | SouthStateTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-007 | SimmonsTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-008 | FirstSourceTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-009 | Y12FedCredTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-010 | YakimaTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-011 | YumaTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-012 | JPMorganTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-013 | WellsFargoTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-014 | PNCTest | $500,000 | $1,000,000 | $10,000,000 |
| bank-config-015 | TruistTest | $500,000 | $1,000,000 | $10,000,000 |
| (auto) | MockBank | $500,000 | $1,000,000 | $10,000,000 |

---

### Merchants & Users (all passwords: `password123`)

| User ID | Email | Role | Merchant ID | Merchant Name | Starting Balance |
|---|---|---|---|---|---|
| user-001 | admin@acme.com | merchant_admin | merchant-001 | Acme Corp | $100,000 |
| user-002 | admin@globex.com | merchant_admin | merchant-002 | Globex Inc | $100,000 |
| user-003 | admin@walmart.testcorp | merchant_admin | merchant-003 | WalmartTestCorp | $100,000 |
| user-004 | admin@foodlion.testcorp | merchant_admin | merchant-004 | FoodLionTestCorp | $100,000 |
| user-005 | admin@target.testcorp | merchant_admin | merchant-005 | TargetTestCorp | $100,000 |
| user-006 | admin@mcdonalds.testcorp | merchant_admin | merchant-006 | McDonaldsTestCorp | $100,000 |
| user-007 | admin@costco.testcorp | merchant_admin | merchant-007 | CostcoTestCorp | $100,000 |
| user-008 | admin@westernunion.testcorp | merchant_admin | merchant-008 | WesternUnionTestCorp | $100,000 |
| user-009 | admin@netflix.testcorp | merchant_admin | merchant-009 | NetflixTestCorp | $100,000 |
| user-010 | admin@burgerking.testcorp | merchant_admin | merchant-010 | BurgerKingTestCorp | $100,000 |
| user-011 | admin@aldi.testcorp | merchant_admin | merchant-011 | AldiTestCorp | $100,000 |
| user-012 | admin@dollargeneral.testcorp | merchant_admin | merchant-012 | DollarGeneralTestCorp | $100,000 |
| user-013 | admin@subway.testcorp | merchant_admin | merchant-013 | SubwayTestCorp | $100,000 |
| user-014 | admin@nike.testcorp | merchant_admin | merchant-014 | NikeTestCorp | $100,000 |
| user-015 | admin@boostmobile.testcorp | merchant_admin | merchant-015 | BoostMobileTestCorp | $100,000 |
| user-consumer-001 | consumer1@test.com | user | merchant-consumer-001 | consumer1.test | $500 (wallet) |
| user-consumer-002 | consumer2@test.com | user | merchant-consumer-002 | consumer2.test | $500 (wallet) |

**All passwords: `password123`**

---

## Lessons Learned

- **Special characters in passwords** (`@`, `$`, `!`) cause two separate issues:
  1. Shell interpolation in bash double-quoted strings (e.g. `!` triggers history expansion, `$` expands variables)
  2. URL parsing errors — `@` is the user/host separator in connection URLs
  3. Python ConfigParser (used by Alembic) treats `%` as variable interpolation syntax, breaking URL-encoded passwords
  - **Solution:** Use alphanumeric-only passwords for database credentials in Cloud Run env vars.

- **Cloud SQL API** must be explicitly enabled before any `gcloud sql` commands will work.

- **`Base.metadata.create_all()`** must be removed from app startup when using Alembic —
  they conflict and `create_all` bypasses migration version control.
