"""Base runner — shared execution with scope enforcement and safety.

Uses an ``Executor`` abstraction so commands can run locally (MacBook worker
container) or via Tailscale SSH on a remote host (ASUS / medusa).
"""
from __future__ import annotations

import logging
from typing import Callable

from app.config import settings
from app.executor import Executor, LocalExecutor, RunResult
from app.scope import Scope, ScopeManager

logger = logging.getLogger(__name__)


class BaseRunner:
    """Common functionality for all scanner tool wrappers."""

    tool_name: str = "base"

    def __init__(
        self,
        scope: Scope,
        scope_manager: ScopeManager | None = None,
        max_concurrency: int | None = None,
        rps: int | None = None,
        timeout: int | None = None,
        executor: Executor | None = None,
    ) -> None:
        self.scope = scope
        self.sm = scope_manager or ScopeManager()
        self.max_concurrency = max_concurrency or settings.max_concurrency
        self.rps = rps or settings.requests_per_second
        self.timeout = timeout or settings.command_timeout
        self.executor = executor or LocalExecutor()

    def assert_scope(self, target: str) -> None:
        """Enforce that *target* is inside the authorised scope."""
        self.sm.assert_in_scope(self.scope, target)

    def filter_in_scope(self, targets: list[str]) -> list[str]:
        """Return only targets inside the scope."""
        return self.sm.filter_targets(self.scope, targets)

    def run(
        self,
        command: list[str],
        timeout: int | None = None,
        on_cancel: Callable[[], bool] | None = None,
        stdin: str | None = None,
    ) -> RunResult:
        """Execute a command via the configured executor.

        Supports timeout, cancellation polling, and optional stdin piping
        (used by httpx, nuclei, dnsx to pass target lists).
        """
        to = timeout or self.timeout
        return self.executor.run(
            tool=self.tool_name,
            command=command,
            stdin=stdin,
            timeout=to,
            on_cancel=on_cancel,
        )
