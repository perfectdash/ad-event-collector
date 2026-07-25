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

# Compile wheels in a local directory to avoid copying compile-time tools to final image
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================================
# STAGE 2: Lightweight Production Runtime
# ==========================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed user packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY app/ /app/app/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Run as non-privileged system user for container security compliance
USER 65534:65534

EXPOSE 8000

# Run with uvloop event-loop and warning log level to reduce output logging overhead during benchmarks
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--log-level", "warning"]
