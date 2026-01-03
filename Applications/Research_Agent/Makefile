.PHONY: help install setup run test lint format clean docker-up docker-down

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)Research Agent - Development Commands$(NC)"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies with Poetry"
	@echo "  make setup         - Complete setup (install + migrate + seed)"
	@echo ""
	@echo "Development:"
	@echo "  make run           - Run Django development server"
	@echo "  make run-asgi      - Run ASGI server for WebSocket support"
	@echo "  make ingest        - Run paper ingestion workflow"
	@echo "  make shell         - Django interactive shell"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint          - Run linting and type checks"
	@echo "  make format        - Format code with black"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         - Remove cache and temporary files"
	@echo "  make migrate       - Run database migrations"
	@echo "  make env           - Create .env from .env.example"

# Installation and setup
install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install poetry
	poetry install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup: install migrate
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "Run '$(BLUE)make run$(NC)' to start the development server"

# Development commands
run:
	@echo "$(BLUE)Starting Django development server...$(NC)"
	cd src/web && python manage.py runserver

run-asgi:
	@echo "$(BLUE)Starting ASGI server with Daphne...$(NC)"
	cd src/web && daphne -b 0.0.0.0 -p 8001 webapp.asgi:application

ingest:
	@echo "$(BLUE)Running paper ingestion...$(NC)"
	cd src/web && python manage.py run_ingestion --days 7 --max_results 100

shell:
	@echo "$(BLUE)Starting Django shell...$(NC)"
	cd src/web && python manage.py shell

migrate:
	@echo "$(BLUE)Running migrations...$(NC)"
	cd src/web && python manage.py migrate
	@echo "$(GREEN)✓ Migrations complete$(NC)"

# Testing and quality
test:
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest -v --cov=src/backend src/tests/

test-unit:
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -v src/tests/unit/

test-integration:
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -v src/tests/integration/

lint:
	@echo "$(BLUE)Running linting and type checks...$(NC)"
	black --check src/
	flake8 src/
	mypy src/backend/
	@echo "$(GREEN)✓ Linting passed$(NC)"

format:
	@echo "$(BLUE)Formatting code with black...$(NC)"
	black src/
	@echo "$(GREEN)✓ Code formatted$(NC)"

# Docker commands
docker-up:
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started:$(NC)"
	@echo "  - Web:      http://localhost:8000"
	@echo "  - ASGI:     http://localhost:8001"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   http://localhost:6333"
	@echo "  - Redis:    localhost:6379"

docker-down:
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs:
	docker-compose logs -f

docker-rebuild:
	@echo "$(BLUE)Rebuilding Docker images...$(NC)"
	docker-compose build --no-cache

# Utility commands
clean:
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

env:
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created. Please configure it with your settings.$(NC)"; \
	else \
		echo "$(RED).env already exists$(NC)"; \
	fi

# Quick health check
health:
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/api/health/ | python -m json.tool || echo "$(RED)Web service not responding$(NC)"

# Development shortcuts
dev: install run

prod: install migrate
	@echo "$(GREEN)✓ Production setup complete$(NC)"
	@echo "Run with: gunicorn -w 4 -b 0.0.0.0:8000 webapp.wsgi:application"
