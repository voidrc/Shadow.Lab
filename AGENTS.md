# Project commands

- Validate core Compose: `SEARXNG_SECRET=test TAILSCALE_AUTHKEY=test docker compose config --quiet`
- Run control-panel tests: `PYTHONPATH=control-panel pytest control-panel/tests`
- Add-ons must share `network_mode: service:tailscale`, use a unique port, define a healthcheck, and carry `shadow.lab.manage=true` to appear in the panel.
- Scanner workers use the same image as the control panel but run `python -m app.worker` as their command.
- Scanner tools (nmap, httpx, nuclei, dnsx) are pinned in the Dockerfile and downloaded at build time — never during scans.
- The Scope Manager (`app/scope.py`) is the central safety gate; every worker target is checked against the authorised scope before any outbound network operation.
