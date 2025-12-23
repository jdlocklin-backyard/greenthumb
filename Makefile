# =============================================================================
# GreenThumb Platform - Makefile
# =============================================================================

.PHONY: help setup up down restart logs clean rebuild backend-shell agent-shell db-shell

# Default target
.DEFAULT_GOAL := help

## help: Display this help message
help:
	@echo "GreenThumb Platform - Available Commands:"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /'

## setup: Initial setup (copy .env.example to .env and create directories)
setup:
	@echo "Setting up GreenThumb platform..."
	@cp -n .env.example .env || true
	@mkdir -p data/db data/redis logs
	@chmod 600 acme.json 2>/dev/null || touch acme.json && chmod 600 acme.json
	@echo "✓ Setup complete! Edit .env file with your configuration."

## up: Start all services
up:
	@echo "Starting GreenThumb platform..."
	@docker compose up -d
	@echo "✓ Platform is running!"
	@echo "  Frontend: http://green.lab"
	@echo "  API: http://api.green.lab"
	@echo "  API Docs: http://api.green.lab/docs"
	@echo "  Traefik Dashboard: http://traefik.green.lab"

## down: Stop all services
down:
	@echo "Stopping GreenThumb platform..."
	@docker compose down

## restart: Restart all services
restart: down up

## logs: View logs from all services
logs:
	@docker compose logs -f

## logs-backend: View backend API logs
logs-backend:
	@docker compose logs -f backend

## logs-agent: View agent logs
logs-agent:
	@docker compose logs -f agent

## logs-frontend: View frontend logs
logs-frontend:
	@docker compose logs -f frontend

## clean: Stop services and remove volumes (WARNING: deletes all data!)
clean:
	@echo "WARNING: This will delete all data volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		rm -rf data/ logs/; \
		echo "✓ Cleaned up successfully"; \
	else \
		echo "Cancelled."; \
	fi

## rebuild: Rebuild all containers from scratch
rebuild:
	@echo "Rebuilding all containers..."
	@docker compose build --no-cache
	@docker compose up -d

## backend-shell: Open shell in backend container
backend-shell:
	@docker compose exec backend /bin/bash

## agent-shell: Open shell in agent container
agent-shell:
	@docker compose exec agent /bin/bash

## db-shell: Open PostgreSQL shell
db-shell:
	@docker compose exec postgres psql -U $${POSTGRES_USER:-greenthumb} -d $${POSTGRES_DB:-greenthumb}

## migrate: Run database migrations
migrate:
	@docker compose exec backend alembic upgrade head

## test-backend: Run backend tests
test-backend:
	@docker compose exec backend pytest

## format-backend: Format Python code
format-backend:
	@docker compose exec backend black .
	@docker compose exec backend isort .

## lint-backend: Lint Python code
lint-backend:
	@docker compose exec backend flake8 .
	@docker compose exec backend mypy .

## format-frontend: Format TypeScript code
format-frontend:
	@docker compose exec frontend npm run format

## lint-frontend: Lint TypeScript code
lint-frontend:
	@docker compose exec frontend npm run lint
