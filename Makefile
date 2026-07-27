.PHONY: up down seed logs test

up:
	docker compose up -d --build
	@echo "waiting for the API..."
	@until curl -sf http://localhost:8000/health > /dev/null; do sleep 1; done
	$(MAKE) seed
	@echo "up: http://localhost:8000 (console at /)"

down:
	docker compose down -v

seed:
	docker compose exec api python -m search_api.seed

logs:
	docker compose logs -f api

test:
	pip install -e ".[dev]" > /dev/null
	pytest -q
