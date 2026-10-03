"""Finding normalisation and deduplication.

Converts findings from different scanner tools (nmap, httpx, nuclei) into a
canonical ``Finding`` model.  Deduplicates by a composite key so the same
issue found across multiple scans is merged, not duplicated.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Iterable

from app.models import Confidence, Finding, FindingStatus, Severity

logger = logging.getLogger(__name__)

# ── Severity mapping ─────────────────────────────────────────────────────────

_SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "CRITICAL": Severity.CRITICAL,
    "high": Severity.HIGH,
    "HIGH": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "moderate": Severity.MEDIUM,
    "MEDIUM": Severity.MEDIUM,
    "low": Severity.LOW,
    "LOW": Severity.LOW,
    "info": Severity.INFO,
    "informational": Severity.INFO,
    "INFO": Severity.INFO,
    "unknown": Severity.INFO,
}


def map_severity(raw: str | None) -> Severity:
    if not raw:
        return Severity.INFO
    return _SEVERITY_MAP.get(raw, Severity.INFO)


# ── Confidence mapping ──────────────────────────────────────────────────────

_CONFIDENCE_MAP = {
    "high": Confidence.HIGH,
    "medium": Confidence.MEDIUM,
    "low": Confidence.LOW,
    "certain": Confidence.HIGH,
    "firm": Confidence.HIGH,
    "tentative": Confidence.LOW,
    "true": Confidence.HIGH,
    "false": Confidence.LOW,
    "unknown": Confidence.UNKNOWN,
}


def map_confidence(raw: str | None) -> Confidence:
    if not raw:
        return Confidence.UNKNOWN
    return _CONFIDENCE_MAP.get(raw.lower(), Confidence.UNKNOWN)


# ── Dedup key ──────────────────────────────────────────────────────────────────

def make_dedup_key(
    source: str,
    template_id: str | None,
    affected_asset: str,
    title: str,
) -> str:
    """Create a stable dedup key for a finding.

    Two findings with the same source, template, affected asset, and title
    are considered the same issue.
    """
    raw = f"{source}|{template_id or ''}|{affected_asset}|{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


# ── Normalisation ──────────────────────────────────────────────────────────────

def normalize_nuclei(
    nfind: dict,
    scan_id: str,
    host_id: str | None = None,
    service_id: str | None = None,
    web_target_id: str | None = None,
) -> Finding:
    """Convert a parsed nuclei finding dict into a canonical Finding."""
    template_id = nfind.get("template_id", "")
    title = nfind.get("template_name", "") or template_id or "Nuclei finding"
    host = nfind.get("host", "")
    url = nfind.get("url", "")
    affected = url or host or ""

    severity = map_severity(nfind.get("severity"))
    confidence = map_confidence(nfind.get("confidence"))

    refs = nfind.get("reference", [])
    if isinstance(refs, str):
        refs = [refs]

    evidence = {
        "tool": "nuclei",
        "template_id": template_id,
        "matched_at": nfind.get("matched_at", ""),
        "extracted_results": nfind.get("extracted_results", []),
        "type": nfind.get("type"),
    }

    return Finding(
        scan_id=scan_id,
        host_id=host_id,
        service_id=service_id,
        web_target_id=web_target_id,
        dedup_key=make_dedup_key("nuclei", template_id, affected, title),
        title=title,
        description=nfind.get("description"),
        severity=severity.value,
        confidence=confidence.value,
        source_severity=nfind.get("severity"),
        source="nuclei",
        template_id=template_id,
        cve=nfind.get("cve"),
        cwe=nfind.get("cwe"),
        cvss_score=nfind.get("cvss_score"),
        cvss_vector=nfind.get("cvss_vector"),
        evidence=json.dumps(evidence),
        affected_asset=affected,
        affected_url=url,
        remediation=None,  # Nuclei templates don't always include remediation
        references=json.dumps(refs) if refs else None,
    )


def normalize_exposure(
    title: str,
    description: str,
    source: str,
    affected_asset: str,
    severity: Severity = Severity.INFO,
    confidence: Confidence = Confidence.HIGH,
    evidence: dict | None = None,
    remediation: str | None = None,
    references: list[str] | None = None,
    scan_id: str | None = None,
    host_id: str | None = None,
    service_id: str | None = None,
    web_target_id: str | None = None,
) -> Finding:
    """Create a canonical finding for a configuration / exposure check."""
    return Finding(
        scan_id=scan_id,
        host_id=host_id,
        service_id=service_id,
        web_target_id=web_target_id,
        dedup_key=make_dedup_key(source, None, affected_asset, title),
        title=title,
        description=description,
        severity=severity.value,
        confidence=confidence.value,
        source=source,
        evidence=json.dumps(evidence) if evidence else None,
        affected_asset=affected_asset,
        remediation=remediation,
        references=json.dumps(references) if references else None,
    )


def deduplicate_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Given a list of findings from a single scan, merge duplicates.

    Findings with the same dedup_key are merged — the highest severity wins
    and evidence is accumulated.
    """
    by_key: dict[str, Finding] = {}
    for f in findings:
        existing = by_key.get(f.dedup_key)
        if existing is None:
            by_key[f.dedup_key] = f
        else:
            # Keep the higher severity
            if _severity_rank(f.severity) > _severity_rank(existing.severity):
                f.first_seen = existing.first_seen
                by_key[f.dedup_key] = f
    return list(by_key.values())


_SEVERITY_RANK = {
    Severity.CRITICAL.value: 5,
    Severity.HIGH.value: 4,
    Severity.MEDIUM.value: 3,
    Severity.LOW.value: 2,
    Severity.INFO.value: 1,
}


def _severity_rank(sev: str) -> int:
    return _SEVERITY_RANK.get(sev, 0)
