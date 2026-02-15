# ============================================================
# Stage 1: Build Flutter web and APK
# ============================================================
FROM ghcr.io/cirruslabs/flutter:stable AS flutter-build

ARG APK_API_URL=http://10.0.2.2:8000

WORKDIR /app
COPY mobile_flutter/ ./mobile_flutter/

WORKDIR /app/mobile_flutter

# Get dependencies
RUN flutter pub get

# Build web with empty base URL (relative paths, nginx proxies to backend)
RUN flutter build web --dart-define=API_BASE_URL=

# Build APK with configurable backend URL
RUN flutter build apk --release --dart-define=API_BASE_URL=$APK_API_URL

# ============================================================
# Stage 2: APK export (extract with: docker build --target apk-export -o out .)
# ============================================================
FROM scratch AS apk-export
COPY --from=flutter-build /app/mobile_flutter/build/app/outputs/flutter-apk/app-release.apk /app-release.apk

# ============================================================
# Stage 3: Runtime — Python + nginx serving web + API
# ============================================================
FROM python:3.10-slim AS runtime

# Install nginx
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Copy Flutter web build from Stage 1
COPY --from=flutter-build /app/mobile_flutter/build/web/ /app/web/

# Copy nginx config and entrypoint
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Remove default nginx site if present
RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
