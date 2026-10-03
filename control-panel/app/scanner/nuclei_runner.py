"""Nuclei runner — template-based vulnerability assessment.

Only safe, non-destructive templates are used.  The runner restricts nuclei to
the authorised scope and collects JSONL findings for normalisation.
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
class NucleiFinding:
    template_id: str
    template_name: str
    severity: str
    confidence: str | None = None
    host: str
    url: str
    matched_at: str
    type: str | None = None
    description: str | None = None
    reference: list[str] = field(default_factory=list)
    cve: str | None = None
    cwe: str | None = None
    cvss_score: float | None = None
    cvss_vector: str | None = None
    extracted_results: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@dataclass
class NucleiResult:
    findings: list[NucleiFinding] = field(default_factory=list)
    raw: RunResult | None = None


# Templates that are explicitly excluded because they are destructive or
# require exploitation.  We also pass -severity to limit to safe levels.
_EXCLUDED_TAGS = ["dos", "exploit", "brute-force", "fuzz"]


class NucleiRunner(BaseRunner):
    tool_name = "nuclei"

    def scan(
        self,
        urls: list[str],
        severities: list[str] | None = None,
        on_cancel=None,
    ) -> NucleiResult:
        """Run nuclei against a list of URLs (http/https).

        Only URLs whose host is in scope are probed.
        """
        in_scope_urls = []
        for url in urls:
            # Extract host from URL for scope check
            host = self._extract_host(url)
            if host and self.sm.is_in_scope(self.scope, host):
                in_scope_urls.append(url)
            else:
                logger.warning("Skipping out-of-scope nuclei target %s", url)

        if not in_scope_urls:
            return NucleiResult()

        sev_arg = ",".join(severities) if severities else "info,low,medium,high,critical"

        cmd = [
            "nuclei",
            "-json",
            "-silent",
            "-severity", sev_arg,
            "-exclude-tags", ",".join(_EXCLUDED_TAGS),
            "-concurrency", str(self.max_concurrency),
            "-rate-limit", str(self.rps),
            "-timeout", str(settings.connect_timeout),
            "-no-color",
            "-nc",  # no color
        ]

        logger.info("[nuclei] scanning %d URLs with severities=%s", len(in_scope_urls), sev_arg)
        result = self.run(cmd, stdin="\n".join(in_scope_urls), on_cancel=on_cancel)
        findings = self._parse_jsonl(result.stdout)
        # Final scope check
        findings = [f for f in findings if self.sm.is_in_scope(self.scope, f.host)]
        return NucleiResult(findings=findings, raw=result)

    def _extract_host(self, url: str) -> str:
        """Extract the host portion from a URL for scope checking."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ""
        return host

    def _parse_jsonl(self, jsonl: str) -> list[NucleiFinding]:
        findings = []
        for line in jsonl.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Nuclei JSON format
            host = d.get("host", "") or d.get("ip", "")
            url = d.get("matched-at", "") or d.get("url", "")
            matched_at = d.get("matched-at", url)

            finding = NucleiFinding(
                template_id=d.get("template-id", "") or d.get("templateID", ""),
                template_name=d.get("info", {}).get("name", "") if isinstance(d.get("info"), dict) else "",
                severity=str(d.get("info", {}).get("severity", "info")).upper() if isinstance(d.get("info"), dict) else "INFO",
                confidence=d.get("confidence"),
                host=host,
                url=d.get("url", url),
                matched_at=matched_at,
                type=d.get("type"),
                raw=d,
            )

            info = d.get("info", {})
            if isinstance(info, dict):
                finding.description = info.get("description")
                finding.reference = info.get("reference", [])
                finding.cve = info.get("classification", {}).get("cve-id") if isinstance(info.get("classification"), dict) else None
                finding.cwe = info.get("classification", {}).get("cwe-id") if isinstance(info.get("classification"), dict) else None
                cvss = info.get("classification", {}).get("cvss-score") if isinstance(info.get("classification"), dict) else None
                finding.cvss_score = float(cvss) if cvss is not None else None
                finding.cvss_vector = info.get("classification", {}).get("cvss-vector") if isinstance(info.get("classification"), dict) else None

            er = d.get("extracted-results", [])
            if isinstance(er, list):
                finding.extracted_results = er

            findings.append(finding)
        return findings
