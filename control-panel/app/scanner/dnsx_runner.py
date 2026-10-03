"""dnsx runner — DNS hostname enrichment for discovered IPs.

Performs reverse DNS lookups on discovered hosts to enrich the asset graph
with hostnames.  Only in-scope IPs are queried.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.scanner.base import BaseRunner
from app.executor import RunResult

logger = logging.getLogger(__name__)


@dataclass
class DnsxResult:
    """Mapping of IP -> hostname."""
    records: dict[str, str] = field(default_factory=dict)
    raw: RunResult | None = None


class DnsxRunner(BaseRunner):
    tool_name = "dnsx"

    def reverse_lookup(
        self,
        ips: list[str],
        on_cancel=None,
    ) -> DnsxResult:
        """Reverse-DNS lookup for a list of IPs."""
        in_scope = [ip for ip in ips if self.sm.is_in_scope(self.scope, ip)]
        if not in_scope:
            return DnsxResult()

        cmd = [
            "dnsx",
            "-reverse",
            "-json",
            "-silent",
            "-rate-limit", str(self.rps),
            "-no-color",
        ]

        logger.info("[dnsx] reverse lookup for %d IPs", len(in_scope))
        result = self.run(cmd, stdin="\n".join(in_scope), on_cancel=on_cancel)
        records = self._parse_jsonl(result.stdout)
        records = {ip: hn for ip, hn in records.items() if self.sm.is_in_scope(self.scope, ip)}
        return DnsxResult(records=records, raw=result)

    def _parse_jsonl(self, jsonl: str) -> dict[str, str]:
        records = {}
        for line in jsonl.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            # dnsx reverse JSON: {"ip":"...","hostname":"..."} or {"resolver":"...","host":"...","a":["..."]}
            ip = d.get("ip") or d.get("host") or ""
            hostname = d.get("hostname") or d.get("name") or ""
            if ip and hostname:
                records[ip] = hostname
        return records
