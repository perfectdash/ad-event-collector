# ==========================================================
# STAGE 1: Build Dependencies
# ==========================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile wheels and install to a shared /install prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================================
# STAGE 2: Lightweight Production Runtime
# ==========================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed packages from the builder stage to /usr/local (globally readable/executable)
COPY --from=builder /install /usr/local
COPY app/ /app/app/

ENV PYTHONPATH=/app

# Run as non-privileged system user for container security compliance
USER 65534:65534

EXPOSE 8080

# Run with uvloop event-loop and warning log level to reduce output logging overhead during benchmarks
# Uses sh -c to expand the $PORT environment variable dynamically injected by Cloud Run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --loop uvloop --log-level warning"]


