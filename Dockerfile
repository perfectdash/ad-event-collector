# I did this to start Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# I did this to install compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# I did this to compile wheels and install to a shared prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# I did this to start Stage 2: Lightweight Production Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

# I did this to copy installed packages from the builder stage
COPY --from=builder /install /usr/local
COPY app/ /app/app/

ENV PYTHONPATH=/app

# I did this to run as a non-privileged system user for security compliance
USER 65534:65534

EXPOSE 8080

# I did this to run with uvloop event-loop and expand the $PORT environment variable dynamically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 8 --loop uvloop --log-level warning"]
