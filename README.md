# Tailnet-only shadow.lab

A Compose stack in which Tailscale owns the shared network namespace. SearXNG, the control panel, and future add-ons bind ports inside that namespace, so Compose publishes no host ports. Tailnet clients reach the services at the Tailscale node name/IP only.

## Layout

```text
.
├── docker-compose.yml              # mandatory core stack
├── .env.example                    # configuration template
├── Makefile                        # common Compose commands
├── searxng/settings.yml
├── control-panel/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── app/                        # FastAPI UI and API
│   └── tests/
└── services/
    └── example/docker-compose.yml  # add-on template
```

## Start

Requirements: Docker Engine with Compose v2, a Tailscale account, and a reusable auth key. Create the key with the narrowest ACL tags practical; an ephemeral key is appropriate because Tailscale state persists in a Docker volume.

```sh
cp .env.example .env
# Edit .env and set TAILSCALE_AUTHKEY and SEARXNG_SECRET.
docker compose config
docker compose up -d --build
```

With MagicDNS enabled, open:

- Control panel: `http://shadow-lab:8080/`
- SearXNG: `http://shadow-lab:8081/`

Otherwise substitute the node's `100.x.y.z` Tailscale address. No `ports:` are published to the host or public interfaces. Tailnet ACLs should additionally restrict which users/devices can reach ports 8080 and 8081. The panel treats Tailscale as ready only when `tailscale status --json` reports `BackendState=Running` and a local Tailscale IP. It checks this at startup and every `TAILSCALE_CHECK_INTERVAL` seconds. Its `/healthz` also requires the Docker API proxy.

On hosts without `/dev/net/tun` support, the kernel-mode sidecar will not start. This stack deliberately uses kernel networking because all workloads share Tailscale's network namespace; enable TUN support in the Docker host rather than publishing service ports.

## Control panel

The browser UI and JSON API discover containers carrying `shadow.lab.manage=true`. No source-code changes or central registry are needed. Docker healthcheck states are shown directly. Available API routes are:

- `GET /api/services`
- `POST /api/services/{id}/start|stop|restart`
- `GET /api/services/{id}/logs?tail=200`
- `GET /healthz`

The panel has no separate login because its intended security boundary is Tailscale plus tailnet ACLs. Add application authentication before exposing it beyond a tightly controlled tailnet.

Stopping Tailscale from the panel immediately removes access to the entire node, including the panel. Recovery then requires Docker access on the host (`docker compose start tailscale`).

## Add a service

Copy `services/example/docker-compose.yml` to `services/<name>/docker-compose.yml`, then:

1. Give it a unique port; every sidecar shares one network namespace, so ports cannot overlap.
2. Set `network_mode: service:tailscale` and depend on the healthy `tailscale` service.
3. Do not add `ports:`.
4. Add a real container `healthcheck:`.
5. Add `shadow.lab.manage`, `shadow.lab.name`, `shadow.lab.description`, and optionally `shadow.lab.url` labels.
6. Merge the files when operating the stack:

```sh
docker compose -f docker-compose.yml -f services/<name>/docker-compose.yml up -d --build
```

The example can be launched with `make example-up`. Hermes can follow exactly this pattern later; once its label is present, the panel discovers it automatically.

Always include every active `-f` file in later `up`, `down`, and `config` commands. A small site-specific wrapper or Make target is useful when several add-ons are enabled.

## Docker socket permission model

The control panel does **not** mount `/var/run/docker.sock`. Only `socket-proxy` mounts it, and the proxy is attached solely to the internal `management` bridge. The proxy port is neither published to the host nor bound in the Tailscale namespace. The panel reaches it as `tcp://socket-proxy:2375` through the shared namespace's attachment to that bridge.

The proxy allow-lists only `PING`, `INFO`, and `CONTAINERS`, plus `POST`. `POST` is necessary for start, stop, and restart; the Docker API does not offer method-level proxy flags fine-grained enough to permit those actions while denying all other container POST operations. Consequently, compromise of the panel can still perform broader container operations exposed by the `CONTAINERS` API. The read-only suffix on the socket mount does not make the Docker API read-only.

Mitigations used here:

- raw socket absent from the panel;
- proxy isolated on an internal network and omitted from panel discovery;
- all other proxy API groups disabled by default;
- panel only accepts actions against explicitly labeled containers;
- panel runs as an unprivileged user.

For a stronger boundary, replace the generic socket proxy with a purpose-built privileged broker that implements only inspect, logs, start, stop, and restart and authenticates each request. Do not expose port 2375 or mount the raw socket into add-ons.

## Development checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r control-panel/requirements-dev.txt
PYTHONPATH=control-panel pytest control-panel/tests
SEARXNG_SECRET=test TAILSCALE_AUTHKEY=test docker compose config --quiet
```
