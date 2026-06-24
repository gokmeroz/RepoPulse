.PHONY: up down logs build ps test test-api shell-api shell-ingestion shell-recommender

# ─── Docker Compose ────────────────────────────────────────────────────────────

up:
	docker compose up --build

up-detached:
	docker compose up --build -d

down:
	docker compose down

down-volumes:
	docker compose down -v

build:
	docker compose build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api-service

logs-ingestion:
	docker compose logs -f ingestion-service

logs-recommender:
	docker compose logs -f recommender-service

ps:
	docker compose ps

# ─── Testing ───────────────────────────────────────────────────────────────────

test:
	docker compose run --rm api-service python -m pytest tests/ -v

test-local:
	cd services/api-service && python -m pytest tests/ -v

# ─── Shell access ──────────────────────────────────────────────────────────────

shell-api:
	docker compose exec api-service /bin/bash

shell-ingestion:
	docker compose exec ingestion-service /bin/bash

shell-recommender:
	docker compose exec recommender-service /bin/bash

# ─── Database ──────────────────────────────────────────────────────────────────

psql:
	docker compose exec postgres psql -U repopulse -d repopulse

# ─── RabbitMQ ──────────────────────────────────────────────────────────────────

rabbitmq-ui:
	@echo "RabbitMQ management UI: http://localhost:15672"
	@echo "Default credentials: repopulse / repopulse (from .env)"
