# Architecture

Shadow.Lab is an authorised bug-bounty reconnaissance and vulnerability-assessment platform built on top of a Docker Compose + Tailscale home-lab stack.

## Two-host model

| Host | Role | RAM | Responsibilities |
|------|------|-----|-----------------|
| **ASUS** (medusa) | Scanner worker | ~16 GB | Runs scanner tools (nmap, httpx, nuclei, dnsx) natively on CachyOS. Accessed via Tailscale SSH — no container needed. |
| **MacBook Air** | Control plane | ~16 GB | Shadow.Lab control panel, dashboard, job submission, report viewing, Redis, SQLite DB, optional local worker, development/admin |

Both hosts share the same Tailscale tailnet. The control panel is reachable only through the tailnet at `http://shadow-lab:8080/`.

## Execution model — hybrid

The MacBook runs the control panel, Redis, and an optional local scanner-worker container. When a scan targets the ASUS (hostname `medusa` via MagicDNS), the control panel runs scanner tools on the ASUS via **Tailscale SSH** (`tailscale ssh medusa <command>`). No worker container, Redis, or database needs to run on the ASUS — tools execute natively on CachyOS and results come back over SSH for local parsing and storage.

Workers are designed to be moved between hosts. Adding a worker to a new machine requires:
1. Install scanner tools on the host (nmap via pacman, httpx/nuclei/dnsx from GitHub releases or AUR)
2. Join the host to the tailnet
3. Enable Tailscale SSH in the tailnet ACLs
4. Set `WORKER_REMOTE_HOST=<hostname>` in the control panel's .env

## Network architecture

### Management network (Tailscale)

- Carries all administrative traffic: dashboard access, API calls, job submission, progress updates.
- Tailscale owns the shared network namespace (`network_mode: service:tailscale`).
- No ports are published to the host or public interfaces.
- Tailnet ACLs restrict which users/devices can reach ports 8080 (control panel) and 8081 (SearXNG).

### Scanning network (Docker egress)

- Carries all outbound scanning traffic to authorised targets.
- Uses the Docker `egress` bridge network — the default route for containers.
- Scanning traffic does **not** route through Tailscale. Tailscale is only used for tailnet addresses (100.x.y.z).
- The `SCANNER_EGRESS_NETWORK` configuration value explicitly identifies this network.

### Internal management bridge

- The `management` network (internal: true) carries:
  - Docker socket proxy ↔ control panel
  - Redis ↔ control panel and workers
- Not routable externally.

### Interface selection and routing

```
┌─────────────────────────────────────────────────┐
│  Docker host (ASUS or MacBook)                   │
│                                                   │
│  ┌─────────┐   egress    ┌──────────────┐         │
│  │ Tailscale│◄──────────►│  scanner-     │         │
│  │ sidecar  │  mgmt      │  worker      │         │
│  └────┬─────┘            └──────┬───────┘         │
│       │                         │                  │
│       │    ┌─────────┐          │                  │
│       ├───►│ control- │◄────────┘                  │
│       │    │ panel    │                            │
│       │    └────┬─────┘                            │
│       │         │                                  │
│  ┌────▼─────┐   │   ┌──────────┐                  │
│  │  redis   │◄──┴──►│ socket-   │                  │
│  └──────────┘       │ proxy    │                  │
│                      └──────────┘                  │
└─────────────────────────────────────────────────┘
         │                          │
         │ Tailscale (100.x.y.z)   │ Docker egress (LAN)
         │ Management traffic      │ Scanning traffic
```

## Service architecture

### Core services (docker-compose.yml)

| Service | Image | RAM | Purpose |
|---------|-------|-----|---------|
| tailscale | tailscale/tailscale:v1.84.3 | ~20 MB | Tailnet gateway, shared namespace |
| socket-proxy | tecnativa/docker-socket-proxy:0.3.0 | ~10 MB | Read-only Docker API proxy |
| redis | redis:7.4-alpine | ~10–128 MB | Job queue + progress pub/sub |
| searxng | searxng/searxng | ~50 MB | Private metasearch (existing) |
| control-panel | built from control-panel/ | ~80 MB | FastAPI dashboard + API + SQLite |
| scanner-worker | built from control-panel/ | ~80 MB | Worker process running scanner tools |

### Scanner tools (inside scanner-worker)

| Tool | Version | Purpose | Output format |
|------|---------|---------|---------------|
| nmap | system package | Host discovery, port scan, service detection | XML |
| httpx | v1.6.9 | HTTP/HTTPS probing, tech fingerprinting | JSONL |
| nuclei | v3.3.7 | Template-based vulnerability detection | JSONL |
| dnsx | v1.2.2 | DNS reverse lookup enrichment | JSONL |

All tools are pinned at build time. No tools are downloaded dynamically during scans.

## Data model

```
Scope
  └── Host
        └── Service
              └── WebTarget
                    └── Finding
                          ├── FindingNote
                          └── FindingStatusChange (audit trail)
```

- **Database**: SQLite with WAL mode (default). Swappable to PostgreSQL via `DATABASE_URL`.
- **Persistence**: The `shadow-data` Docker volume survives container restarts.
- **Evidence**: Stored as JSON in the Finding.evidence column. Configurable retention via `EVIDENCE_RETENTION_DAYS`.

## Job queue and worker architecture

```
Control Panel ──► Redis Queue ──► Worker ──► Scanner Tools
     ▲                                  │
     └──── Progress pub/sub ◄───────────┘
```

1. User submits a scan via the dashboard or CLI.
2. Control panel validates the scope, creates a Scan record, and enqueues a job in Redis.
3. The scanner worker dequeues the job, runs the pipeline, and writes results to the database.
4. Progress is published to a Redis pub/sub channel; the dashboard polls for updates.

Workers never execute arbitrary shell commands. They run a fixed pipeline of scanner tools with scope-checked targets.

## Scan pipeline

```
Scope Validation → Host Discovery → Port Discovery → Service Detection
  → HTTP Discovery → Tech Fingerprint → DNS Enrich → Vuln Assessment
  → Normalization → Deduplication → Evidence Storage → Reporting
```

Each stage has:
- Inputs and outputs
- Status tracking (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED)
- Timeout
- Cancellation support
- Error isolation (a failed stage does not destroy the scan)

## Security boundaries

- The control panel does **not** mount the raw Docker socket.
- The socket proxy allow-lists only CONTAINERS, INFO, PING, and POST.
- The panel only accepts actions against explicitly labeled containers.
- Workers enforce scope at every target before touching it.
- No arbitrary shell execution from the dashboard.
- No credential attacks, password spraying, destructive payloads, persistence, shell deployment, data exfiltration, evasion, or exploit chaining.

## Event system

Events are emitted for scan lifecycle, host/service discovery, and finding creation. Initially logged. Designed for future email/Discord/Slack/webhook integrations.

Events: `scan.started`, `scan.completed`, `scan.failed`, `host.discovered`, `service.discovered`, `finding.created`, `finding.updated`, `findings.stored`.
