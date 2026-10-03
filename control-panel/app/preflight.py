"""Pre-flight tool checks — verify scanner tools exist before starting a scan.

For the local MacBook worker, tools are inside the container image.  For the
remote ASUS worker (medusa), tools run natively on CachyOS and are installed
via ``pacman``.  This module checks that each required tool is available on
the target worker and returns clear install instructions if any are missing.
"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field

from app.executor import Executor, LocalExecutor, SSHExecutor

logger = logging.getLogger(__name__)

# Tool → pacman package name on CachyOS/Arch
PACMAN_PACKAGES = {
    "nmap": "nmap",
    "httpx": "httpx-git (AUR) or download from https://github.com/projectdiscovery/httpx/releases",
    "nuclei": "nuclei-git (AUR) or download from https://github.com/projectdiscovery/nuclei/releases",
    "dnsx": "dnsx-git (AUR) or download from https://github.com/projectdiscovery/dnsx/releases",
}

# Tools required by each scan profile
PROFILE_TOOLS = {
    "safe": ["nmap", "httpx", "nuclei", "dnsx"],
    "thorough": ["nmap", "httpx", "nuclei", "dnsx"],
    "recon": ["nmap", "httpx", "dnsx"],
}


@dataclass
class PreflightResult:
    ok: bool
    missing: list[str] = field(default_factory=list)
    available: list[str] = field(default_factory=list)
    worker: str = ""
    instructions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "worker": self.worker,
            "missing": self.missing,
            "available": self.available,
            "instructions": self.instructions,
        }


def check_local(tools: list[str]) -> PreflightResult:
    """Check that *tools* exist in the local PATH (MacBook worker container)."""
    missing, available = [], []
    for tool in tools:
        if shutil.which(tool):
            available.append(tool)
        else:
            missing.append(tool)
    instructions = [
        f"  {t}: install inside the control-panel Docker image (Dockerfile)"
        for t in missing
    ]
    return PreflightResult(
        ok=not missing,
        missing=missing,
        available=available,
        worker="local",
        instructions=instructions,
    )


def check_remote(ssh: SSHExecutor, tools: list[str]) -> PreflightResult:
    """Check that *tools* exist on the remote host via Tailscale SSH."""
    missing, available = [], []
    for tool in tools:
        if ssh.check_tool(tool):
            available.append(tool)
        else:
            missing.append(tool)
    instructions = []
    for t in missing:
        pkg = PACMAN_PACKAGES.get(t, t)
        instructions.append(f"  sudo pacman -S {pkg}")
    return PreflightResult(
        ok=not missing,
        missing=missing,
        available=available,
        worker=ssh.host,
        instructions=instructions,
    )


def preflight(worker: str, profile: str) -> PreflightResult:
    """Run pre-flight checks for a given worker and profile.

    *worker* is either "local" or a remote hostname (e.g. "medusa").
    *profile* is a scan profile key (safe, thorough, recon).
    """
    tools = PROFILE_TOOLS.get(profile, PROFILE_TOOLS["safe"])

    if worker == "local":
        return check_local(tools)

    # Remote worker — use Tailscale SSH
    from app.config import settings
    user = settings.worker_remote_user
    ssh = SSHExecutor(host=worker, user=user)
    return check_remote(ssh, tools)
