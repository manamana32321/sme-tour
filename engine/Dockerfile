# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

# System deps needed by gurobipy + pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Copy source + data
COPY src/ ./src/
COPY data/processed/ ./data/processed/

# Non-root user
RUN useradd -m -u 1000 engine && chown -R engine:engine /app
USER engine

EXPOSE 8000

# Gurobi WLS credentials are injected via K8s env vars:
# GUROBI_LICENSE_ID, GUROBI_WLS_ACCESS_ID, GUROBI_WLS_SECRET

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
