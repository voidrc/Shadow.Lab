# Project commands

- Validate core Compose: `SEARXNG_SECRET=test TAILSCALE_AUTHKEY=test docker compose config --quiet`
- Run control-panel tests: `PYTHONPATH=control-panel pytest control-panel/tests`
- Add-ons must share `network_mode: service:tailscale`, use a unique port, define a healthcheck, and carry `shadow.lab.manage=true` to appear in the panel.
