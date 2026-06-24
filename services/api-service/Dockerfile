# ─── Builder stage ────────────────────────────────────────────────────────────
# Install all Python dependencies into /install so the runtime image stays lean.
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --upgrade pip --quiet

# Install the shared contracts package first (other services depend on it too).
COPY packages/contracts /build/packages/contracts
RUN pip install --quiet --no-cache-dir --prefix=/install /build/packages/contracts

# Install the API service dependencies.
# We copy pyproject.toml and a stub app/ so pip can resolve deps without
# needing the full source tree during the dependency-install layer.
COPY services/api-service/pyproject.toml /build/pyproject.toml
RUN mkdir -p /build/app && touch /build/app/__init__.py
RUN pip install --quiet --no-cache-dir --prefix=/install "/build[dev]"

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

# curl is needed for the Docker health check command.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security.
RUN useradd --system --create-home --shell /bin/bash appuser

WORKDIR /service

# Copy installed packages from builder.
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin

# Copy the application source.
COPY services/api-service/app ./app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
