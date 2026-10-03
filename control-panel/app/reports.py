"""Report generation — Markdown, JSON, and HTML reports for completed scans."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Finding, Host, Scan, Scope, Service, WebTarget

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def generate_json_report(db: Session, scan_id: str) -> dict:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise ValueError(f"Scan {scan_id} not found")

    scope = db.get(Scope, scan.scope_id)
    hosts = db.query(Host).filter_by(scan_id=scan_id).all()
    services = []
    web_targets = []
    for h in hosts:
        services.extend(h.services)
        for s in h.services:
            if s.web_target:
                web_targets.append(s.web_target)
    findings = db.query(Finding).filter_by(scan_id=scan_id).all()
    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))

    return {
        "scan": {
            "id": scan.id,
            "profile": scan.profile,
            "status": scan.status,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
            "worker": scan.worker,
        },
        "scope": {
            "name": scope.name if scope else "",
            "cidrs": scope.cidr_list if scope else [],
        },
        "summary": {
            "hosts": len(hosts),
            "services": len(services),
            "web_targets": len(web_targets),
            "findings": {
                "critical": scan.findings_critical,
                "high": scan.findings_high,
                "medium": scan.findings_medium,
                "low": scan.findings_low,
                "info": scan.findings_info,
                "total": len(findings),
            },
        },
        "hosts": [
            {
                "ip": h.ip, "hostname": h.hostname, "os_guess": h.os_guess,
                "services": [
                    {"port": s.port, "protocol": s.protocol, "state": s.state,
                     "service": s.service_name, "product": s.product, "version": s.version}
                    for s in h.services
                ],
            }
            for h in hosts
        ],
        "web_targets": [
            {"url": t.url, "title": t.title, "status_code": t.status_code,
             "technologies": t.technology_list, "server": t.server_header}
            for t in web_targets
        ],
        "findings": [
            {
                "title": f.title, "severity": f.severity, "confidence": f.confidence,
                "source": f.source, "affected_asset": f.affected_asset,
                "affected_url": f.affected_url, "description": f.description,
                "evidence": json.loads(f.evidence) if f.evidence else None,
                "remediation": f.remediation,
                "references": json.loads(f.references) if f.references else None,
                "cve": f.cve, "cwe": f.cwe, "cvss_score": f.cvss_score,
                "status": f.status,
            }
            for f in findings
        ],
    }


def generate_markdown_report(db: Session, scan_id: str) -> str:
    report = generate_json_report(db, scan_id)
    lines: list[str] = []
    s = report["scan"]
    sc = report["scope"]
    summ = report["summary"]

    lines.append(f"# Scan Report — {scan_id}")
    lines.append("")
    lines.append(f"**Scope:** {sc['name']} (`{', '.join(sc['cidrs'])}`)")
    lines.append(f"**Profile:** {s['profile']}")
    lines.append(f"**Status:** {s['status']}")
    if s["started_at"]:
        lines.append(f"**Started:** {s['started_at']}")
    if s["finished_at"]:
        lines.append(f"**Finished:** {s['finished_at']}")
    lines.append(f"**Worker:** {s['worker'] or 'N/A'}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Hosts discovered: {summ['hosts']}")
    lines.append(f"- Services discovered: {summ['services']}")
    lines.append(f"- Web targets: {summ['web_targets']}")
    f = summ["findings"]
    lines.append(f"- Findings: {f['total']} (Critical: {f['critical']}, High: {f['high']}, Medium: {f['medium']}, Low: {f['low']}, Info: {f['info']})")
    lines.append("")

    if report["hosts"]:
        lines.append("## Assets")
        lines.append("")
        for h in report["hosts"]:
            lines.append(f"### {h['ip']}")
            if h["hostname"]:
                lines.append(f"Hostname: `{h['hostname']}`")
            if h["os_guess"]:
                lines.append(f"OS guess: {h['os_guess']}")
            if h["services"]:
                lines.append("")
                lines.append("| Port | Protocol | State | Service | Product | Version |")
                lines.append("|------|----------|--------|---------|---------|---------|")
                for svc in h["services"]:
                    lines.append(
                        f"| {svc['port']} | {svc['protocol']} | {svc['state']} | "
                        f"{svc['service'] or ''} | {svc['product'] or ''} | {svc['version'] or ''} |"
                    )
            lines.append("")

    if report["web_targets"]:
        lines.append("## Web Targets")
        lines.append("")
        for t in report["web_targets"]:
            lines.append(f"- **{t['url']}** — {t['title'] or 'No title'} (HTTP {t['status_code'] or '?'})")
            if t["technologies"]:
                lines.append(f"  Technologies: {', '.join(t['technologies'])}")
            if t["server"]:
                lines.append(f"  Server: {t['server']}")
        lines.append("")

    if report["findings"]:
        lines.append("## Findings")
        lines.append("")
        for f in report["findings"]:
            lines.append(f"### {f['severity']} — {f['title']}")
            lines.append("")
            lines.append(f"**Asset:** `{f['affected_asset'] or 'N/A'}`")
            if f["affected_url"]:
                lines.append(f"**URL:** {f['affected_url']}")
            lines.append(f"**Confidence:** {f['confidence']}")
            lines.append(f"**Source:** {f['source']}")
            if f["cve"]:
                lines.append(f"**CVE:** {f['cve']}")
            if f["cwe"]:
                lines.append(f"**CWE:** {f['cwe']}")
            if f["cvss_score"]:
                lines.append(f"**CVSS:** {f['cvss_score']}")
            if f["description"]:
                lines.append("")
                lines.append(f["description"])
            if f["evidence"]:
                lines.append("")
                lines.append("### Evidence")
                lines.append("```json")
                lines.append(json.dumps(f["evidence"], indent=2))
                lines.append("```")
            if f["remediation"]:
                lines.append("")
                lines.append("### Remediation")
                lines.append(f["remediation"])
            if f["references"]:
                lines.append("")
                lines.append("### References")
                for ref in f["references"]:
                    lines.append(f"- {ref}")
            lines.append("")
    else:
        lines.append("## Findings")
        lines.append("")
        lines.append("No findings recorded.")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by shadow.lab at {datetime.now(timezone.utc).isoformat()}*")
    return "\n".join(lines)


def generate_html_report(db: Session, scan_id: str) -> str:
    md = generate_markdown_report(db, scan_id)
    # Minimal HTML wrapper around the markdown content (pre-formatted)
    # A full markdown-to-HTML converter is not bundled to keep the image small.
    import html as html_mod
    escaped = html_mod.escape(md)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scan Report — {html_mod.escape(scan_id)}</title>
<style>
  body {{ font-family: "SFMono-Regular", Consolas, monospace; background: #060812; color: #d9f7ff; margin: 0; padding: 40px; }}
  pre {{ white-space: pre-wrap; word-wrap: break-word; }}
  a {{ color: #00f5ff; }}
</style>
</head>
<body>
<pre>{escaped}</pre>
</body>
</html>"""
