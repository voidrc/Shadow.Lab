# Shadow.Lab

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
make config
make up
```

`make config` validates the core stack together with every discovered add-on under `services/`. `make up` builds the complete stack, starts only the core services, and creates stopped containers for add-ons so they immediately appear in the control panel. Use these Make targets instead of bare `docker compose` commands so add-on files are included automatically.

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
6. Run `make up`.

The Makefile automatically merges every `services/*/docker-compose.yml` except the example. `make up` builds all discovered services, starts only Tailscale, the socket proxy, SearXNG, and the control panel, then creates each add-on container without starting it. Because the stopped container carries its management labels, it appears in the control panel and can be started there immediately.

```sh
make services                         # show discovered add-on files
make up                               # build all, start core, catalog stopped add-ons
make catalog                          # create any missing stopped add-on containers
make start SERVICE=<compose-service>  # build and start one add-on
make stop SERVICE=<compose-service>
make restart SERVICE=<compose-service>
```

The `SERVICE` value is the service key inside the add-on Compose file. Add-ons already running are not stopped by `make up`. `make down`, `make logs`, and `make config` also include all discovered add-ons.

The excluded template can be launched separately with `make example-up`. Use the Make targets rather than bare `docker compose` commands when add-ons are present, because Docker Compose itself does not discover nested files.

### Hermes setup

Run the core stack before launching either interactive Hermes command:

```sh
make up
make hermes-setup       # run the first-time `hermes setup` wizard
make hermes-terminal    # open interactive Hermes chat; slash commands such as /setup work here
make start SERVICE=hermes
```

Both interactive commands use the same persistent `/opt/data` mount as the gateway. Complete setup before starting the background service. The dashboard is then available over the tailnet at `http://shadow-lab:9119/`.

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
