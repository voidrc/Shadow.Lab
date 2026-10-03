"""httpx runner — HTTP/HTTPS probing and technology fingerprinting.

Uses projectdiscovery/httpx JSONL output.  Only HTTP/HTTPS services discovered
by nmap are probed, and every target is scope-checked before probing.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.config import settings
from app.scanner.base import BaseRunner
from app.executor import RunResult

logger = logging.getLogger(__name__)


@dataclass
class WebTargetInfo:
    scheme: str
    host: str
    port: int
    url: str
    title: str | None = None
    status_code: int | None = None
    content_length: int | None = None
    content_type: str | None = None
    server_header: str | None = None
    technologies: list[str] = field(default_factory=list)
    redirect_url: str | None = None
    tls_subject: str | None = None
    tls_issuer: str | None = None
    tls_not_after: str | None = None


@dataclass
class HttpxResult:
    targets: list[WebTargetInfo] = field(default_factory=list)
    raw: RunResult | None = None


class HttpxRunner(BaseRunner):
    tool_name = "httpx"

    def probe(
        self,
        host_port_pairs: list[tuple[str, int]],
        on_cancel=None,
    ) -> HttpxResult:
        """Probe HTTP/HTTPS for each (host, port) pair.

        Only in-scope hosts are probed.
        """
        # Build target list, scope-checking each host
        targets: list[str] = []
        for host, port in host_port_pairs:
            if not self.sm.is_in_scope(self.scope, host):
                logger.warning("Skipping out-of-scope HTTP target %s", host)
                continue
            targets.append(f"{host}:{port}")

        if not targets:
            return HttpxResult()

        cmd = [
            "httpx",
            "-json",
            "-silent",
            "-title",
            "-tech-detect",
            "-status-code",
            "-content-length",
            "-content-type",
            "-server",
            "-location",        # redirect URL
            "-tls-grab",        # TLS certificate info
            "-threads", str(self.max_concurrency),
            "-rate-limit", str(self.rps),
            "-timeout", str(settings.connect_timeout),
            "-no-color",
        ]
        # Feed targets via stdin
        logger.info("[httpx] probing %d targets", len(targets))
        result = self.run(cmd, stdin="\n".join(targets), on_cancel=on_cancel)
        web_targets = self._parse_jsonl(result.stdout)
        # Final scope check on parsed results
        web_targets = [t for t in web_targets if self.sm.is_in_scope(self.scope, t.host)]
        return HttpxResult(targets=web_targets, raw=result)

    def _parse_jsonl(self, jsonl: str) -> list[WebTargetInfo]:
        targets = []
        for line in jsonl.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = d.get("url", "")
            scheme = d.get("scheme", "http")
            host = d.get("host", "")
            port = d.get("port", 443 if scheme == "https" else 80)
            if isinstance(port, str):
                try:
                    port = int(port)
                except ValueError:
                    port = 443 if scheme == "https" else 80

            wt = WebTargetInfo(
                scheme=scheme, host=host, port=port, url=url,
                title=d.get("title"),
                status_code=d.get("status_code"),
                content_length=d.get("content_length"),
                content_type=d.get("content_type"),
                server_header=d.get("webserver"),
                redirect_url=d.get("location"),
            )
            # Technologies
            techs = d.get("tech", [])
            if isinstance(techs, list):
                wt.technologies = [str(t) for t in techs]
            # TLS info
            tls = d.get("tls")
            if isinstance(tls, dict):
                wt.tls_subject = tls.get("subject_cn")
                wt.tls_issuer = tls.get("issuer_cn")
                wt.tls_not_after = tls.get("not_after")
            targets.append(wt)
        return targets


