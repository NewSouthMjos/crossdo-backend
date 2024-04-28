.PHONY: migrate seed server test docker-compose-server docker-compose-test


# For migrate and seed: you need to "export DATABASE_URL=..."
migrate:
	poetry run alembic upgrade head

seed:
	poetry run python db/seeds.py

flake8:
	poetry run flake8 .

server:
	poetry run serve

docker-compose-server:
	docker compose up --abort-on-container-exit
