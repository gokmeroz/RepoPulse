# ─── Builder stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --upgrade pip --quiet

COPY packages/contracts /build/packages/contracts
RUN pip install --quiet --no-cache-dir --prefix=/install /build/packages/contracts

COPY services/ingestion-service/pyproject.toml /build/pyproject.toml
RUN mkdir -p /build/app && touch /build/app/__init__.py
RUN pip install --quiet --no-cache-dir --prefix=/install /build/

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN useradd --system --create-home --shell /bin/bash appuser

WORKDIR /service

COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin

COPY services/ingestion-service/app ./app

USER appuser

CMD ["python", "-m", "app.main"]
