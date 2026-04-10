# ═══════════════════════════════════════════════════════════════════════
#  WorkSim Voyager — Production Dockerfile
#  Compatible with: HuggingFace Spaces, OpenEnv push, local Docker
#  Constraints:     2 vCPU, 8 GB RAM, fast startup
# ═══════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ─────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-essential for any C-extension wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt /build/requirements.txt

# Install all dependencies into a dedicated prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 1.5: Frontend Builder ──────────────────────────────────────
FROM node:18-slim AS frontend-builder

WORKDIR /frontend-build

# Copy frontend source
COPY frontend/ /frontend-build/

# Install dependencies and build
RUN npm install && npm run build

# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.11-slim

# HuggingFace Spaces metadata
LABEL maintainer="WorkSim Voyager Team" \
      org.opencontainers.image.title="worksim-voyager" \
      org.opencontainers.image.description="Workplace simulation OpenEnv environment" \
      org.opencontainers.image.version="0.1.0"

WORKDIR /app

# Create non-root user (HF Spaces requirement for some builds)
RUN useradd -m -u 1000 appuser

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy built frontend
COPY --from=frontend-builder /frontend-build/dist /app/static

# Copy application source code
COPY app.py /app/app.py
COPY server/ /app/server/
COPY inference.py /app/inference.py
COPY openenv.yaml /app/openenv.yaml
COPY pyproject.toml /app/pyproject.toml
COPY requirements.txt /app/requirements.txt
COPY __init__.py /app/__init__.py
COPY client.py /app/client.py


COPY README.md /app/README.md

# Ensure server package is importable
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Port used by OpenEnv (must match openenv.yaml)
EXPOSE 7860

# Health check — verifies /health endpoint responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Switch to non-root user
USER appuser

# ── Startup ──────────────────────────────────────────────────────────
# Single-worker uvicorn for 2 vCPU / 8GB RAM constraint.
# --timeout-keep-alive 65 keeps connections alive for HF Spaces proxy.
# --log-level info provides enough logging for debugging without overhead.
CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--workers", "1", \
     "--timeout-keep-alive", "65", \
     "--log-level", "info"]