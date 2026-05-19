.DEFAULT_GOAL := help

help: ## Show available make targets
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS=":.*?##"} {printf "%-20s %s\n", $$1, $$2}'

dev: ## Run docker compose in the foreground
	@docker compose up --build

up: ## Run docker compose in the background
	@docker compose up -d --build

down: ## Stop docker compose services
	@docker compose down

clean: ## Stop services and remove volumes/orphans
	@docker compose down -v --remove-orphans

logs: ## Tail logs from all services
	@docker compose logs -f

test: ## Run backend pytest suite
	@cd backend && pytest tests/ -v

lint: ## Run ruff checks on backend
	@ruff check backend/ && ruff format --check backend/

format: ## Format backend code with ruff
	@ruff format backend/

build-backend: ## Build the backend Docker image
	@docker build -t devops-agent-backend ./backend

build-frontend: ## Build the frontend Docker image
	@docker build -t devops-agent-frontend ./frontend

shell-backend: ## Open a shell inside the running backend container
	@docker compose exec backend /bin/sh

redis-cli: ## Open a redis-cli session inside the running redis container
	@docker compose exec redis redis-cli
