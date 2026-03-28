#!/usr/bin/env bash
# restore-env.sh — Rebuild backend/.env from Google Secret Manager
#
# Usage:
#   cd C:/Users/raja/ai4org_payrails
#   bash backend/restore-env.sh
#
# Prerequisites:
#   - gcloud CLI authenticated (gcloud auth login)
#   - Correct project active (gcloud config set project YOUR_PROJECT_ID)
#
# Secret naming convention: payrails-<env-var-lowercase-with-hyphens>
#
# Label reference: environment=local or environment=cloudrun
#   LOCAL ONLY  : DATABASE_URL (sqlite), SEED_DATA
#   CLOUD RUN   : DATABASE_URL (postgresql+Cloud SQL), SEED_DATA (false for prod)
#   BOTH        : all other secrets below

set -e

OUTPUT_FILE="$(dirname "$0")/.env"

echo "Fetching secrets from Google Secret Manager..."
echo ""

fetch() {
  local secret_name="$1"
  gcloud secrets versions access latest --secret="$secret_name" 2>/dev/null \
    || { echo "  WARNING: secret '$secret_name' not found — leaving blank"; echo ""; }
}

cat > "$OUTPUT_FILE" <<EOF
JWT_SECRET=$(fetch payrails-jwt-secret)
ENCRYPTION_KEY=$(fetch payrails-encryption-key)

# For LOCAL development use sqlite; for Cloud Run use the PostgreSQL URL from payrails-database-url-cloudrun
DATABASE_URL=sqlite:///./local.db

# Set to true for local dev to seed demo data; use false in production
SEED_DATA=true

# Email via SMTP relay (Brevo) — used in both local and Cloud Run
SMTP_HOST=$(fetch payrails-smtp-host)
SMTP_PORT=$(fetch payrails-smtp-port)
SMTP_USERNAME=$(fetch payrails-smtp-username)
SMTP_PASSWORD=$(fetch payrails-smtp-password)
SMTP_USE_TLS=$(fetch payrails-smtp-use-tls)
FROM_ADDR=$(fetch payrails-from-addr)
SENDER_NAME=$(fetch payrails-sender-name)

# SMS via Brevo REST API — used in both local and Cloud Run
BREVO_API_KEY=$(fetch payrails-brevo-api-key)
BREVO_SMS_SENDER=$(fetch payrails-brevo-sms-sender)

# Claude API (AI-generated transaction descriptions) — used in both local and Cloud Run
ANTHROPIC_API_KEY=$(fetch payrails-anthropic-api-key)
EOF

echo ""
echo "Written to: $OUTPUT_FILE"
echo ""
echo "NOTE: DATABASE_URL is set to SQLite for local dev."
echo "For Cloud Run, retrieve the PostgreSQL URL with:"
echo "  gcloud secrets versions access latest --secret=payrails-database-url"
