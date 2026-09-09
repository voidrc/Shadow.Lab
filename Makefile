CORE_SERVICES := tailscale socket-proxy searxng control-panel
ADDON_FILES := $(filter-out services/example/docker-compose.yml,$(wildcard services/*/docker-compose.yml))
COMPOSE := docker compose -f docker-compose.yml $(addprefix -f ,$(ADDON_FILES))

.PHONY: up build catalog down logs config services start stop restart hermes-setup hermes-terminal example-up

up: build
	$(COMPOSE) up -d --no-build $(CORE_SERVICES)
	$(MAKE) catalog

build:
	$(COMPOSE) build

catalog:
	@for service in $$($(COMPOSE) config --services); do \
		case " $(CORE_SERVICES) " in *" $$service "*) continue ;; esac; \
		if [ -z "$$($(COMPOSE) ps -q --all "$$service")" ]; then \
			$(COMPOSE) create --no-build "$$service"; \
		fi; \
	done

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

config:
	$(COMPOSE) config

services:
	@for file in $(ADDON_FILES); do echo $$file; done

start:
	@test -n "$(SERVICE)" || (echo "Usage: make start SERVICE=<compose-service-name>" && exit 1)
	$(COMPOSE) up -d --build $(SERVICE)

stop:
	@test -n "$(SERVICE)" || (echo "Usage: make stop SERVICE=<compose-service-name>" && exit 1)
	$(COMPOSE) stop $(SERVICE)

restart:
	@test -n "$(SERVICE)" || (echo "Usage: make restart SERVICE=<compose-service-name>" && exit 1)
	$(COMPOSE) restart $(SERVICE)

hermes-setup:
	$(COMPOSE) run --rm --no-deps hermes setup

hermes-terminal:
	$(COMPOSE) run --rm --no-deps hermes hermes

example-up:
	docker compose -f docker-compose.yml -f services/example/docker-compose.yml up -d --build example
