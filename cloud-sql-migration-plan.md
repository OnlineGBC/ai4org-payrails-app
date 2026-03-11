# Cloud SQL Migration Plan

## Goal
Migrate from ephemeral SQLite (data lost on every Cloud Run restart/deploy) to persistent Cloud SQL PostgreSQL.

## Current State (Already Done)
- `psycopg2-binary` already in `backend/requirements.txt`
- Alembic already configured with 6 migration files in `backend/alembic/versions/`
- `alembic upgrade head` already runs on startup in `entrypoint.sh`
- `DATABASE_URL` already configurable via env var in `backend/app/config.py`
- `SEED_DATA` already controlled by env var in `entrypoint.sh`

## Steps (COMPLETED)

### Step 1 — Create Cloud SQL PostgreSQL Instance (one-time) ✅
```bash
gcloud services enable sqladmin.googleapis.com --project=fednowrtppayrails
gcloud sql instances create payrails-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-east1 \
  --project=fednowrtppayrails

gcloud sql databases create payrails --instance=payrails-db --project=fednowrtppayrails
gcloud sql users create payrails-user --instance=payrails-db --password=REDACTED_SEE_SECRET_MANAGER --project=fednowrtppayrails
```

### Step 2 — Grant Cloud Run Access to Cloud SQL (one-time IAM) ✅
```bash
gcloud projects add-iam-policy-binding fednowrtppayrails \
  --member="serviceAccount:1090496405720-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### Step 3 — Deploy Command (use going forward) ✅
**IMPORTANT: Avoid special characters in the password — they cause shell interpolation and
URL parsing issues. Use alphanumeric passwords only.**
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

### Step 4 — Code Fix in main.py (remove SQLite-only create_all)
Remove `Base.metadata.create_all(bind=engine)` from the startup handler.
Alembic handles schema creation — `create_all` bypasses Alembic and causes conflicts with PostgreSQL.

### Step 5 — Turn Off SEED_DATA After First Deploy
Change `SEED_DATA=true` → `SEED_DATA=false` in the deploy command once the
database is seeded and working, so re-deploys don't overwrite real data.

## Future Workflow (After Migration)
- Deploy command is the same as Step 3 above (with SEED_DATA=false)
- For model/schema changes: run `alembic revision --autogenerate -m "description"` before deploying
- Local dev continues to use SQLite — no change needed

## Cloud SQL Instance Details
- Project: fednowrtppayrails
- Instance name: payrails-db
- Region: us-east1
- Database: payrails
- User: payrails-user
- Connection name: fednowrtppayrails:us-east1:payrails-db
