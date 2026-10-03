"""Executor abstraction — run scanner commands locally or via Tailscale SSH.

The pipeline orchestrates tools (nmap, httpx, nuclei, dnsx) through a common
interface.  ``LocalExecutor`` runs commands as local subprocesses (used by the
MacBook worker container).  ``SSHExecutor`` runs commands on a remote host via
``tailscale ssh`` (used for the ASUS / medusa worker).

Both executors return the same ``RunResult`` so the pipeline does not care
where the tool actually ran.
"""
from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """Result of running a scanner tool."""
    tool: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class Executor:
    """Abstract command executor."""

    def build_command(self, command: list[str]) -> list[str]:
        """Wrap *command* for this executor's execution context."""
        raise NotImplementedError

    def run(
        self,
        tool: str,
        command: list[str],
        stdin: str | None = None,
        timeout: int = 300,
        on_cancel: Callable[[], bool] | None = None,
    ) -> RunResult:
        """Run *command* and return a ``RunResult``."""
        raise NotImplementedError


class LocalExecutor(Executor):
    """Run commands as local subprocesses."""

    def build_command(self, command: list[str]) -> list[str]:
        return list(command)

    def run(self, tool, command, stdin=None, timeout=300, on_cancel=None):
        full_cmd = self.build_command(command)
        logger.info("[%s] local: %s", tool, " ".join(shlex.quote(c) for c in full_cmd))
        return _run_process(tool, full_cmd, stdin, timeout, on_cancel)


class SSHExecutor(Executor):
    """Run commands on a remote host via ``tailscale ssh``.

    Requires the Tailscale binary and socket to be available in the container
    (both are already mounted/copied for the control panel).  Tailscale SSH
    must be enabled in the tailnet ACLs.
    """

    def __init__(self, host: str, user: str | None = None) -> None:
        self.host = host
        self.user = user
        self._ts_bin = shutil.which("tailscale") or "/usr/local/bin/tailscale"

    @property
    def target(self) -> str:
        return f"{self.user}@{self.host}" if self.user else self.host

    def build_command(self, command: list[str]) -> list[str]:
        return [self._ts_bin, "ssh", self.target, *command]

    def run(self, tool, command, stdin=None, timeout=300, on_cancel=None):
        full_cmd = self.build_command(command)
        logger.info("[%s] ssh %s: %s", tool, self.host, " ".join(shlex.quote(c) for c in command))
        return _run_process(tool, full_cmd, stdin, timeout, on_cancel)

    def check_tool(self, tool: str, timeout: int = 15) -> bool:
        """Return True if *tool* exists on the remote host."""
        result = self.run("preflight", ["command", "-v", tool], timeout=timeout)
        return result.returncode == 0 and bool(result.stdout.strip())


# ── Shared process runner ─────────────────────────────────────────────────────

def _run_process(
    tool: str,
    command: list[str],
    stdin: str | None,
    timeout: int,
    on_cancel: Callable[[], bool] | None,
) -> RunResult:
    """Run *command* with timeout, cancellation, and optional stdin piping."""
    start = time.monotonic()

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE if stdin is not None else None,
            text=True,
        )
    except FileNotFoundError as exc:
        return RunResult(
            tool=tool, command=command, returncode=127,
            stdout="", stderr=str(exc), duration=0.0,
        )

    timed_out = False
    try:
        while True:
            poll_interval = 0.5
            try:
                stdout, stderr = proc.communicate(
                    input=stdin, timeout=poll_interval,
                )
                break
            except subprocess.TimeoutExpired:
                if on_cancel and on_cancel():
                    logger.info("[%s] cancellation requested — terminating", tool)
                    proc.terminate()
                    try:
                        stdout, stderr = proc.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        stdout, stderr = proc.communicate()
                    return RunResult(
                        tool=tool, command=command,
                        returncode=proc.returncode, stdout=stdout or "",
                        stderr=stderr or "", duration=time.monotonic() - start,
                        timed_out=True,
                    )
                elapsed = time.monotonic() - start
                if elapsed > timeout:
                    logger.warning("[%s] timeout after %.1fs — terminating", tool, timeout)
                    proc.terminate()
                    try:
                        stdout, stderr = proc.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        stdout, stderr = proc.communicate()
                    timed_out = True
                    break
    except Exception as exc:
        proc.kill()
        return RunResult(
            tool=tool, command=command, returncode=1,
            stdout="", stderr=str(exc), duration=time.monotonic() - start,
        )

    return RunResult(
        tool=tool, command=command,
        returncode=proc.returncode, stdout=stdout or "",
        stderr=stderr or "", duration=time.monotonic() - start,
        timed_out=timed_out,
    )
