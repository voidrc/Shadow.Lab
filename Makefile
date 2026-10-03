CORE_SERVICES := tailscale socket-proxy redis searxng control-panel scanner-worker
ADDON_FILES := $(filter-out services/example/docker-compose.yml,$(wildcard services/*/docker-compose.yml))
COMPOSE := docker compose -f docker-compose.yml $(addprefix -f ,$(ADDON_FILES))

.PHONY: up build catalog down logs config services start stop restart hermes-setup hermes-terminal example-up worker workers scan scans test lint health report

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

# ── Scanner platform targets ────────────────────────────────────────────────

worker:
	@test -n "$(SERVICE)" || (echo "Usage: make worker SERVICE=<worker-name>" && exit 1)
	$(COMPOSE) up -d --build $(SERVICE)

workers:
	$(COMPOSE) up -d --build scanner-worker

scan:
	@test -n "$(SCOPE)" || (echo "Usage: make scan SCOPE=10.10.20.0/24 [PROFILE=safe] [WORKER=medusa]" && exit 1)
	$(COMPOSE) exec control-panel python -m app.cli scan create --scope "$(SCOPE)" --profile "$(PROFILE)" --worker "$(WORKER)" --yes

scans:
	$(COMPOSE) exec control-panel python -m app.cli scan list

preflight:
	@test -n "$(WORKER)" || (echo "Usage: make preflight WORKER=medusa [PROFILE=safe]" && exit 1)
	$(COMPOSE) exec control-panel python -m app.cli scan preflight "$(WORKER)" --profile "$(PROFILE)"

test:
	PYTHONPATH=control-panel pytest control-panel/tests

lint:
	@echo "Lint not configured — add ruff or flake8 if desired"

health:
	$(COMPOSE) exec control-panel python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/healthz').read().decode())"

report:
	@test -n "$(SCAN)" || (echo "Usage: make report SCAN=<scan-id> [FORMAT=markdown]" && exit 1)
	$(COMPOSE) exec control-panel python -m app.cli report generate "$(SCAN)" --format "$(FORMAT)"

# ── Hermes (existing add-on) ─────────────────────────────────────────────────

hermes-setup:
	$(COMPOSE) run --rm --no-deps hermes setup

hermes-terminal:
	$(COMPOSE) run --rm --no-deps hermes hermes

example-up:
	docker compose -f docker-compose.yml -f services/example/docker-compose.yml up -d --build example
