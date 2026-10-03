"""Centralised configuration for the shadow.lab control panel and workers."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # --- Docker / Tailscale (existing) ---
    docker_host: str = os.getenv("DOCKER_HOST", "tcp://socket-proxy:2375")
    tailscale_socket: str = os.getenv("TAILSCALE_SOCKET", "/var/run/tailscale/tailscaled.sock")
    tailscale_check_interval: int = _env_int("TAILSCALE_CHECK_INTERVAL", 15)
    log_tail_max: int = _env_int("LOG_TAIL_MAX", 2000)

    # --- Database ---
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/shadow-lab/shadow.db")

    # --- Redis / queue ---
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    queue_name: str = os.getenv("SCAN_QUEUE_NAME", "shadow:scans")
    progress_channel: str = os.getenv("SCAN_PROGRESS_CHANNEL", "shadow:progress")

    # --- Control-panel API (used by workers to POST results) ---
    control_panel_url: str = os.getenv("CONTROL_PANEL_URL", "http://127.0.0.1:8080")
    control_panel_token: str = os.getenv("CONTROL_PANEL_TOKEN", "")

    # --- Scanner safety defaults ---
    max_concurrency: int = _env_int("SCANNER_MAX_CONCURRENCY", 8)
    requests_per_second: int = _env_int("SCANNER_RPS", 5)
    connect_timeout: int = _env_int("SCANNER_CONNECT_TIMEOUT", 5)
    command_timeout: int = _env_int("SCANNER_COMMAND_TIMEOUT", 300)
    scan_timeout: int = _env_int("SCANNER_SCAN_TIMEOUT", 3600)
    retry_limit: int = _env_int("SCANNER_RETRY_LIMIT", 2)
    max_response_size: int = _env_int("SCANNER_MAX_RESPONSE_SIZE", 10 * 1024 * 1024)
    max_hosts: int = _env_int("SCANNER_MAX_HOSTS", 65536)

    # --- Scanning network ---
    # The Docker network / host interface that scanning workers are allowed to
    # use for outbound scanning traffic.  This is a documentation and enforcement
    # hint — workers are expected to be attached to this network.
    scanner_egress_network: str = os.getenv("SCANNER_EGRESS_NETWORK", "egress")
    scanner_interface: str = os.getenv("SCANNER_INTERFACE", "auto")

    # --- Evidence retention ---
    evidence_retention_days: int = _env_int("EVIDENCE_RETENTION_DAYS", 90)
    evidence_dir: Path = Path(os.getenv("EVIDENCE_DIR", "data/shadow-lab/evidence"))

    # --- Scan ID sequence ---
    scan_id_year: int = int(os.getenv("SCAN_ID_YEAR", "2026"))
    scan_id_prefix: str = os.getenv("SCAN_ID_PREFIX", "scan")

    # --- Worker ---
    worker_poll_interval: float = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))
    worker_id: str = os.getenv("WORKER_ID", "worker-default")

    # --- Remote SSH worker (ASUS / medusa) ---
    # When a scan targets the remote worker, the control panel runs scanner
    # tools via ``tailscale ssh <host>``.  Tailscale SSH handles auth via
    # tailnet identity — no SSH keys to manage.
    worker_remote_host: str = os.getenv("WORKER_REMOTE_HOST", "medusa")
    worker_remote_user: str = os.getenv("WORKER_REMOTE_USER", "")

    # --- Feature flags ---
    enable_ipv6: bool = _env_bool("ENABLE_IPV6", True)

    @property
    def evidence_dir_path(self) -> Path:
        p = self.evidence_dir
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
