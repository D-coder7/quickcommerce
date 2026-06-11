.PHONY: up down build logs migrate seed test

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api

migrate:
	docker compose exec api alembic upgrade head

makemigration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec api python -m app.scripts.seed

test:
	docker compose exec api pytest tests/ -v

shell:
	docker compose exec api python
