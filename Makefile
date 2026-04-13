.PHONY: up down dev prod logs test clean help

# Default target
help: ## Show this help
	@echo ""
	@echo "  DB Assessment — Multi-Database Integration Platform"
	@echo "  =================================================="
	@echo ""
	@echo "  make up        Start all services (production mode)"
	@echo "  make dev       Start all services (dev mode with hot-reload)"
	@echo "  make prod      Start all services (hardened production mode)"
	@echo "  make down      Stop all services"
	@echo "  make logs      Tail logs from all services"
	@echo "  make test      Run backend test suite"
	@echo "  make clean     Remove all containers, volumes, and build cache"
	@echo ""
	@echo "  Demo Credentials:"
	@echo "    Admin:  admin / admin123"
	@echo "    User:   demo / demo1234"
	@echo ""

up: ## Start all services (production mode)
	docker-compose up --build -d
	@echo ""
	@echo "  ✓ Services starting..."
	@echo "  Frontend:  http://localhost:3000"
	@echo "  API:       http://localhost:8000/api/v1/"
	@echo "  Admin:     admin / admin123"
	@echo "  User:      demo / demo1234"
	@echo ""
	@echo "  Run 'make logs' to watch startup progress"

dev: ## Start all services (dev mode with hot-reload)
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
	@echo ""
	@echo "  ✓ Dev services starting (hot-reload enabled)..."
	@echo "  Frontend:  http://localhost:3000"
	@echo "  API:       http://localhost:8000/api/v1/"
	@echo ""

prod: ## Start all services (hardened production mode)
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
	@echo ""
	@echo "  ✓ Production services starting..."
	@echo "  Frontend:  http://localhost:3000"
	@echo "  API:       http://localhost:8000/api/v1/"
	@echo "  Logs:      backend/logs/ (app.log, error.log, security.log)"
	@echo ""
	@echo "  ⚠  Ensure .env has production values (DEBUG=False, real SECRET_KEY)"
	@echo ""

down: ## Stop all services
	docker-compose down

logs: ## Tail logs from all services
	docker-compose logs -f

test: ## Run backend test suite
	cd backend && python manage.py test --verbosity 2

clean: ## Remove all containers, volumes, and build cache
	docker-compose down -v --remove-orphans
	docker system prune -f
