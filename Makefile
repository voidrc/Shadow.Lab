COMPOSE := docker compose -f docker-compose.yml

.PHONY: up down logs config example-up

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

config:
	$(COMPOSE) config

example-up:
	$(COMPOSE) -f services/example/docker-compose.yml up -d --build
