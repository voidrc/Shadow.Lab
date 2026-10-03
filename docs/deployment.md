# Deployment

Shadow.Lab is designed for a two-node home lab: an ASUS host for scanning workloads and a MacBook Air for the control plane. Both nodes share a Tailscale tailnet.

## Prerequisites

- Docker Engine with Compose v2 on both hosts
- A Tailscale account with MagicDNS enabled
- A reusable Tailscale auth key (ephemeral, narrow ACL tags)
- `/dev/net/tun` support on the Docker host (kernel-mode Tailscale)

## Single-host deployment (simplest)

Run the entire stack on one machine. This is the default configuration.

```sh
cp .env.example .env
# Edit .env: set TAILSCALE_AUTHKEY and SEARXNG_SECRET
make config    # validate the Compose configuration
make up        # build and start core services
```

Open `http://shadow-lab:8080/` over the tailnet.

## Two-host deployment

### MacBook Air — control plane + Redis + local worker

```sh
cp .env.example .env
# Edit .env:
#   TAILSCALE_HOSTNAME=shadow-lab
#   TAILSCALE_AUTHKEY=<your key>
#   SEARXNG_SECRET=<random>
#   WORKER_REMOTE_HOST=medusa          # ASUS hostname on the tailnet
#   WORKER_REMOTE_USER=                # leave blank for default Tailscale SSH user

make config
make up
```

The MacBook runs: Tailscale, socket-proxy, Redis, SearXNG, control-panel, and an optional local scanner-worker.

### ASUS (medusa) — remote scanner worker via Tailscale SSH

The ASUS does **not** need any Docker containers. Scanner tools run natively on CachyOS.

**Prerequisites on the ASUS:**
1. Join the ASUS to the same Tailscale tailnet: `sudo tailscale up`
2. Ensure the hostname is `medusa` (or update `WORKER_REMOTE_HOST` in the MacBook's .env)
3. Enable Tailscale SSH in the tailnet ACLs (so the control panel can SSH to `medusa`)
4. Install scanner tools:

```sh
# nmap — from the official repos
sudo pacman -S nmap

# httpx, nuclei, dnsx — from AUR or GitHub releases
# Option A: AUR (if you use an AUR helper like yay)
yay -S httpx-git nuclei-git dnsx-git

# Option B: Direct download from GitHub releases
# See https://github.com/projectdiscovery/httpx/releases
# See https://github.com/projectdiscovery/nuclei/releases
# See https://github.com/projectdiscovery/dnsx/releases
```

**Verify the control panel can reach the ASUS:**

```sh
# From the MacBook, over the tailnet:
tailscale ssh medusa nmap --version
tailscale ssh medusa httpx -version
tailscale ssh medusa nuclei -version
tailscale ssh medusa dnsx -version
```

**Pre-flight check via the API:**

```sh
curl http://shadow-lab:8080/api/scans/preflight/medusa?profile=safe
# Returns: {"ok": true, "missing": [], ...} or lists what's missing
```

When starting a scan, set the worker to `medusa` (the dashboard defaults to this). The control panel will run all scanner tools on the ASUS via Tailscale SSH and collect results locally.

## Firewall requirements

- **Tailscale**: UDP 41641 (default) for tailnet traffic
- **Scanning**: Outbound access from the worker to the authorised target network (e.g., 10.10.20.0/24)
- **Redis**: Only accessible on the internal management network (single-host) or tailnet (multi-host)
- **Control panel**: Only accessible on the tailnet at port 8080

## Verification

```sh
make health    # check control panel health
make scans     # list scans
docker compose logs scanner-worker  # check worker is polling
```

## Resource estimates

| Component | RAM (idle) | RAM (active scan) |
|-----------|-----------|-------------------|
| Tailscale | 20 MB | 20 MB |
| Socket proxy | 10 MB | 10 MB |
| Redis | 10 MB | 10–128 MB |
| SearXNG | 50 MB | 80 MB |
| Control panel | 80 MB | 120 MB |
| Scanner worker | 80 MB | 200–500 MB |
| **Total** | **~250 MB** | **~500 MB – 1 GB** |

The system is designed to operate within 16 GB RAM with significant headroom. Scanner concurrency is configurable via `SCANNER_MAX_CONCURRENCY` to scale down on weaker hardware.
