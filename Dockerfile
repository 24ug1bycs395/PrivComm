# syntax=docker/dockerfile:1
# Privcomm — multi-stage image (Vite SPA + FastAPI/Uvicorn)

# -----------------------------------------------------------------------------
# Stage 1: Frontend builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Backend runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    SECURITY_POLICY_PATH=/app/config/security_policy.yaml

WORKDIR /app

RUN echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections \
    && apt-get update && apt-get install -y --no-install-recommends \
    tshark \
    wireshark-common \
    tcpdump \
    libpcap-dev \
    libgomp1 \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc python3-dev \
    && rm -rf /root/.cache/pip

COPY main.py index.html style.css script.js ./
COPY analyzer ./analyzer
COPY ml ./ml
COPY security ./security
COPY routers ./routers
COPY services ./services
COPY reports ./reports
COPY db ./db
COPY models ./models
COPY utils ./utils
COPY config ./config
COPY samples ./samples

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/results /app/captures \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home --shell /usr/sbin/nologin appuser \
    && (getent group wireshark >/dev/null && usermod -aG wireshark appuser || true) \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
