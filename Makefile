# Makefile for Remnawave Admin Bot

# Variables
DOCKER_IMAGE = ghcr.io/dignezzz/remna-telegram-bot
DOCKER_TAG = latest
COMPOSE_FILE_DEV = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose-prod.yml

.PHONY: help build run stop logs clean deploy pull health test

# Default target
help: ## Show this help message
	@echo "Remnawave Admin Bot - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
build: ## Build Docker image for development
	docker-compose -f $(COMPOSE_FILE_DEV) build

run: ## Run bot in development mode
	docker-compose -f $(COMPOSE_FILE_DEV) up -d

stop: ## Stop development containers
	docker-compose -f $(COMPOSE_FILE_DEV) down

logs: ## Show development logs
	docker-compose -f $(COMPOSE_FILE_DEV) logs -f

restart: stop run ## Restart development environment

# Production commands
prod-pull: ## Pull latest production image
	docker pull $(DOCKER_IMAGE):$(DOCKER_TAG)

prod-deploy: ## Deploy to production
	docker-compose -f $(COMPOSE_FILE_PROD) down --remove-orphans
	docker-compose -f $(COMPOSE_FILE_PROD) pull
	docker-compose -f $(COMPOSE_FILE_PROD) up -d

prod-stop: ## Stop production containers
	docker-compose -f $(COMPOSE_FILE_PROD) down

prod-logs: ## Show production logs
	docker-compose -f $(COMPOSE_FILE_PROD) logs -f

prod-status: ## Show production container status
	docker-compose -f $(COMPOSE_FILE_PROD) ps

# Utility commands
health: ## Check container health
	@echo "Development containers:"
	@docker-compose -f $(COMPOSE_FILE_DEV) ps 2>/dev/null || echo "Not running"
	@echo ""
	@echo "Production containers:"
	@docker-compose -f $(COMPOSE_FILE_PROD) ps 2>/dev/null || echo "Not running"

clean: ## Clean up Docker resources
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	docker system prune -af
	docker volume prune -f

# Setup commands
setup: ## Initial setup - copy environment template
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.example .env; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

setup-prod: ## Setup production environment
	@if [ ! -f .env ]; then \
		echo "Creating .env from production template..."; \
		cp .env.production .env; \
		echo "Please edit .env file with your production configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Testing and validation
test-syntax: ## Test Python syntax
	python -m py_compile main.py
	python -c "import ast; [ast.parse(open(f).read()) for f in ['main.py']]"

test-imports: ## Test if all imports work
	python -c "from modules.config import *; print('✅ Config imports OK')"
	python -c "from modules.api.client import *; print('✅ API client imports OK')"
	python -c "from modules.handlers.user_handlers import *; print('✅ Handlers imports OK')"

validate-env: ## Validate environment variables
	@python -c "import os; from dotenv import load_dotenv; load_dotenv(); required=['API_BASE_URL','REMNAWAVE_API_TOKEN','TELEGRAM_BOT_TOKEN','ADMIN_USER_IDS']; missing=[k for k in required if not os.getenv(k)]; print('✅ All required env vars present' if not missing else f'❌ Missing: {missing}')"

# Information commands
info: ## Show current configuration
	@echo "🐳 Docker Images:"
	@docker images | grep remna || echo "No local images found"
	@echo ""
	@echo "📊 Container Status:"
	@make health
	@echo ""
	@echo "📁 Files:"
	@ls -la *.yml *.env* 2>/dev/null || echo "No config files found"

version: ## Show version information
	@echo "Remnawave Admin Bot v2.0"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose: $(shell docker-compose --version 2>/dev/null || echo 'Not installed')"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'Not installed')"

# GitHub commands (require gh CLI)
gh-release: ## Create GitHub release
	@read -p "Enter version (e.g., v2.0.1): " version; \
	git tag $$version && \
	git push origin $$version && \
	gh release create $$version --generate-notes

gh-workflow: ## Trigger GitHub workflow
	gh workflow run docker-publish.yml

# Quick shortcuts
dev: run ## Alias for 'run' - start development
prod: prod-deploy ## Alias for 'prod-deploy' - deploy production
