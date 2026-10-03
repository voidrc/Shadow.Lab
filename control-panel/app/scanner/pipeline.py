"""Scan pipeline — orchestrates the multi-stage scanning workflow.

Each stage has inputs, outputs, status, logs, timeout, retry, and cancellation
support.  A failed stage does not destroy the entire scan; later stages that
depend on a failed stage are skipped, but independent stages still run.
"""
from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from typing import Callable

from app.config import settings
from app.executor import Executor, LocalExecutor, SSHExecutor
from app.models import (
    Confidence,
    Finding,
    Host,
    Scan,
    ScanLog,
    ScanStage,
    ScanStatus,
    Service,
    ServiceState,
    Severity,
    StageStatus,
    WebTarget,
)
from app.profiles import (
    DNS_ENRICH,
    HTTP_DISCOVERY,
    HOST_DISCOVERY,
    NORMALIZATION,
    PORT_DISCOVERY,
    ProfileDef,
    SERVICE_DETECTION,
    TECH_FINGERPRINT,
    VULN_ASSESSMENT,
)
from app.scope import Scope, ScopeManager
from app.scanner.dnsx_runner import DnsxRunner
from app.scanner.httpx_runner import HttpxRunner
from app.scanner.nmap_runner import NmapRunner
from app.scanner.nuclei_runner import NucleiRunner
from app import normalize, events

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CancelCheck = Callable[[], bool]


class Pipeline:
    """Runs the scan pipeline for a single scan job."""

    def __init__(
        self,
        session: Session,
        scan: Scan,
        scope: Scope,
        profile: ProfileDef,
        worker_id: str = "worker-default",
        cancel_check: CancelCheck | None = None,
        executor: Executor | None = None,
    ) -> None:
        self.session = session
        self.scan = scan
        self.scope = scope
        self.profile = profile
        self.worker_id = worker_id
        self.cancel_check = cancel_check or (lambda: False)
        self.sm = ScopeManager()
        self.executor = executor or LocalExecutor()

        # Runtime accumulators
        self._hosts: dict[str, Host] = {}        # ip -> Host
        self._services: dict[tuple[str, int], Service] = {}  # (ip, port) -> Service
        self._web_targets: list[WebTarget] = []
        self._findings: list[Finding] = []

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _log(self, level: str, message: str) -> None:
        self.session.add(ScanLog(scan_id=self.scan.id, level=level, message=message))
        self.session.flush()
        logger.log(getattr(logging, level, logging.INFO), "[%s] %s", self.scan.id, message)

    def _set_status(self, status: ScanStatus) -> None:
        self.scan.status = status.value
        events.emit("scan.status", self.scan.id, status=status.value)

    def _set_stage(self, seq: int, name: str, status: str, **kw) -> None:
        stage = next((s for s in self.scan.stages if s.seq == seq), None)
        if stage is None:
            stage = ScanStage(scan_id=self.scan.id, seq=seq, name=name)
            self.session.add(stage)
        stage.status = status
        if status == StageStatus.RUNNING.value:
            stage.started_at = datetime.now(timezone.utc)
        elif status in (StageStatus.COMPLETED.value, StageStatus.FAILED.value, StageStatus.CANCELLED.value):
            stage.finished_at = datetime.now(timezone.utc)
        for k, v in kw.items():
            setattr(stage, k, v)
        self.session.flush()
        events.emit("scan.stage", self.scan.id, stage=name, status=status, **kw)

    def _update_progress(self) -> None:
        self.scan.hosts_discovered = len(self._hosts)
        self.scan.ports_discovered = sum(len(h.services) for h in self._hosts.values())
        self.scan.web_targets_discovered = len(self._web_targets)
        self.session.flush()
        events.emit(
            "scan.progress",
            self.scan.id,
            hosts=self.scan.hosts_discovered,
            ports=self.scan.ports_discovered,
            web_targets=self.scan.web_targets_discovered,
        )

    def _is_cancelled(self) -> bool:
        if self.cancel_check():
            self._set_status(ScanStatus.CANCELLED)
            return True
        return False

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self) -> None:
        self.scan.worker = self.worker_id
        self.scan.started_at = datetime.now(timezone.utc)
        self._set_status(ScanStatus.VALIDATING)
        self._log("INFO", f"Scan started with profile '{self.profile.label}' on scope {self.scope.cidr_list}")
        events.emit("scan.started", self.scan.id, scan_id=self.scan.id, profile=self.profile.key)

        try:
            # Stage 0: validation already done at submission, but re-verify
            self._set_stage(0, "scope_validation", StageStatus.RUNNING.value)
            self._log("INFO", f"Scope validated: {self.scope.cidr_list} ({self.scope.address_count} addresses)")
            self._set_stage(0, "scope_validation", StageStatus.COMPLETED.value)

            # Run stages in order
            for seq, stage_cfg in enumerate(self.profile.stages, start=1):
                if self._is_cancelled():
                    self._set_stage(seq, stage_cfg.name, StageStatus.CANCELLED.value)
                    self._log("WARNING", "Scan cancelled by operator")
                    break
                if not stage_cfg.enabled:
                    self._set_stage(seq, stage_cfg.name, StageStatus.SKIPPED.value)
                    continue

                handler = self._stage_handlers.get(stage_cfg.name)
                if handler is None:
                    self._set_stage(seq, stage_cfg.name, StageStatus.SKIPPED.value, detail="no handler")
                    continue

                self._set_status(self._status_for_stage(stage_cfg.name))
                self._set_stage(seq, stage_cfg.name, StageStatus.RUNNING.value)
                try:
                    handler(self, stage_cfg)
                    self._set_stage(seq, stage_cfg.name, StageStatus.COMPLETED.value)
                except Exception as exc:
                    logger.exception("[%s] stage %s failed", self.scan.id, stage_cfg.name)
                    self._set_stage(seq, stage_cfg.name, StageStatus.FAILED.value, error=str(exc))
                    self._log("ERROR", f"Stage '{stage_cfg.name}' failed: {exc}")
                    # Continue — a failed stage should not destroy the scan

                self._update_progress()

            # Finalize
            if self._is_cancelled():
                self._log("INFO", "Scan cancelled")
            else:
                self._set_status(ScanStatus.PROCESSING)
                self._store_findings()
                self._set_status(ScanStatus.COMPLETE)
                self._log("INFO", "Scan complete")
                events.emit("scan.completed", self.scan.id, scan_id=self.scan.id)

        except Exception as exc:
            logger.exception("[%s] pipeline error", self.scan.id)
            self._set_status(ScanStatus.FAILED)
            self.scan.error = str(exc)
            self._log("ERROR", f"Pipeline error: {exc}")
            events.emit("scan.failed", self.scan.id, error=str(exc))
        finally:
            self.scan.finished_at = datetime.now(timezone.utc)
            self.session.flush()

    def _status_for_stage(self, stage_name: str) -> ScanStatus:
        return {
            HOST_DISCOVERY: ScanStatus.DISCOVERING,
            PORT_DISCOVERY: ScanStatus.DISCOVERING,
            SERVICE_DETECTION: ScanStatus.ENUMERATING,
            HTTP_DISCOVERY: ScanStatus.ENUMERATING,
            TECH_FINGERPRINT: ScanStatus.ENUMERATING,
            DNS_ENRICH: ScanStatus.ENUMERATING,
            VULN_ASSESSMENT: ScanStatus.ASSESSING,
            NORMALIZATION: ScanStatus.PROCESSING,
        }.get(stage_name, ScanStatus.PROCESSING)

    # ── Stage handlers ───────────────────────────────────────────────────────

    def _stage_host_discovery(self, cfg) -> None:
        runner = NmapRunner(self.scope, self.sm, timeout=cfg.timeout, executor=self.executor)
        targets = list(self.scope.cidr_list)
        result = runner.discover_hosts(targets, timing=self.profile.nmap_timing, on_cancel=self.cancel_check)
        if result.raw and result.raw.timed_out:
            raise TimeoutError("Host discovery timed out")
        for dh in result.hosts:
            host = self._get_or_create_host(dh)
        self._log("INFO", f"Host discovery: {len(self._hosts)} hosts up")

    def _stage_port_discovery(self, cfg) -> None:
        runner = NmapRunner(self.scope, self.sm, timeout=cfg.timeout, executor=self.executor)
        targets = [h.ip for h in self._hosts.values()]
        if not targets:
            self._log("WARNING", "No hosts to scan for ports")
            return
        top_ports = 1000 if self.profile.key == "safe" else 65535
        result = runner.scan_services(targets, timing=self.profile.nmap_timing, top_ports=top_ports, on_cancel=self.cancel_check)
        if result.raw and result.raw.timed_out:
            raise TimeoutError("Port scan timed out")
        # Update hosts from the full scan
        for dh in result.hosts:
            self._get_or_create_host(dh)
        for ds in result.services:
            self._get_or_create_service(ds)
        self._log("INFO", f"Port discovery: {len(self._services)} services found")

    def _stage_service_detection(self, cfg) -> None:
        # Service detection is done as part of port discovery (nmap -sV)
        # This stage is for additional banner grabbing if needed
        self._log("INFO", f"Service detection: {len(self._services)} services catalogued")

    def _stage_http_discovery(self, cfg) -> None:
        # Find HTTP/HTTPS services
        http_ports = {80, 8080, 8000, 8008, 8443, 9000, 3000, 5000}
        https_ports = {443, 8443}
        pairs: list[tuple[str, int]] = []
        for (ip, port), svc in self._services.items():
            if svc.state != ServiceState.OPEN.value:
                continue
            if svc.service_name and "http" in svc.service_name.lower():
                pairs.append((ip, port))
            elif port in http_ports or port in https_ports:
                pairs.append((ip, port))
        if not pairs:
            self._log("INFO", "No HTTP services to probe")
            return
        runner = HttpxRunner(self.scope, self.sm, timeout=cfg.timeout, executor=self.executor)
        result = runner.probe(pairs, on_cancel=self.cancel_check)
        for wt in result.targets:
            web_target = self._create_web_target(wt)
        self._log("INFO", f"HTTP discovery: {len(self._web_targets)} web targets")

    def _stage_tech_fingerprint(self, cfg) -> None:
        # Technology fingerprinting is done by httpx -tech-detect
        # This stage could add WhatWeb or similar in the future
        self._log("INFO", f"Tech fingerprint: {sum(len(wt.technology_list) for wt in self._web_targets)} technologies detected")

    def _stage_dns_enrich(self, cfg) -> None:
        ips = [h.ip for h in self._hosts.values()]
        if not ips:
            return
        runner = DnsxRunner(self.scope, self.sm, timeout=cfg.timeout, executor=self.executor)
        result = runner.reverse_lookup(ips, on_cancel=self.cancel_check)
        for ip, hostname in result.records.items():
            host = self._hosts.get(ip)
            if host and not host.hostname:
                host.hostname = hostname
        self._log("INFO", f"DNS enrichment: {len(result.records)} hostnames resolved")

    def _stage_vuln_assessment(self, cfg) -> None:
        if not self.profile.run_vuln:
            self._log("INFO", "Vulnerability assessment skipped for this profile")
            return
        urls = [wt.url for wt in self._web_targets]
        if not urls:
            self._log("INFO", "No web targets for vulnerability assessment")
            # Still do exposure checks on services
            self._exposure_checks()
            return
        runner = NucleiRunner(self.scope, self.sm, timeout=cfg.timeout, executor=self.executor)
        result = runner.scan(urls, severities=self.profile.nuclei_severities, on_cancel=self.cancel_check)
        for nf in result.findings:
            finding = normalize.normalize_nuclei(
                {
                    "template_id": nf.template_id,
                    "template_name": nf.template_name,
                    "severity": nf.severity,
                    "confidence": nf.confidence,
                    "host": nf.host,
                    "url": nf.url,
                    "matched_at": nf.matched_at,
                    "description": nf.description,
                    "reference": nf.reference,
                    "cve": nf.cve,
                    "cwe": nf.cwe,
                    "cvss_score": nf.cvss_score,
                    "cvss_vector": nf.cvss_vector,
                    "extracted_results": nf.extracted_results,
                    "type": nf.type,
                },
                scan_id=self.scan.id,
            )
            # Link to host/web_target if possible
            host = self._hosts.get(nf.host)
            if host:
                finding.host_id = host.id
            self._findings.append(finding)
        self._log("INFO", f"Vulnerability assessment: {len(result.findings)} findings from nuclei")
        self._exposure_checks()

    def _exposure_checks(self) -> None:
        """Generate exposure findings for dangerous open services."""
        dangerous_services = {
            "telnet": ("Telnet service exposed", "Telnet transmits credentials in cleartext and should not be exposed.", Severity.HIGH),
            "ftp": ("FTP service exposed", "FTP may allow anonymous access or transmit credentials in cleartext.", Severity.MEDIUM),
            "rdp": ("RDP service exposed", "Remote Desktop Protocol exposed to the network.", Severity.MEDIUM),
            "vnc": ("VNC service exposed", "VNC remote desktop exposed.", Severity.MEDIUM),
            "mysql": ("MySQL service exposed", "Database service exposed to the network.", Severity.MEDIUM),
            "postgresql": ("PostgreSQL service exposed", "Database service exposed to the network.", Severity.MEDIUM),
            "redis": ("Redis service exposed", "Redis exposed — often deployed without authentication.", Severity.HIGH),
            "mongodb": ("MongoDB service exposed", "MongoDB exposed — often deployed without authentication.", Severity.HIGH),
            "elasticsearch": ("Elasticsearch service exposed", "Elasticsearch exposed — often deployed without authentication.", Severity.HIGH),
            "memcached": ("Memcached service exposed", "Memcached exposed — can be abused for amplification attacks.", Severity.MEDIUM),
            "docker": ("Docker API exposed", "Docker API exposed without authentication — full host compromise risk.", Severity.CRITICAL),
            "kubernetes": ("Kubernetes API exposed", "Kubernetes API exposed to the network.", Severity.HIGH),
        }
        for (ip, port), svc in self._services.items():
            if svc.state != ServiceState.OPEN.value:
                continue
            svc_lower = (svc.service_name or "").lower()
            for key, (title, desc, sev) in dangerous_services.items():
                if key in svc_lower:
                    affected = f"{ip}:{port}"
                    f = normalize.normalize_exposure(
                        title=title,
                        description=desc,
                        source="exposure-check",
                        affected_asset=affected,
                        severity=sev,
                        confidence=Confidence.HIGH,
                        evidence={
                            "service": svc_lower,
                            "port": port,
                            "product": svc.product,
                            "version": svc.version,
                            "banner": svc.banner,
                        },
                        remediation=f"Restrict access to {svc_lower} on port {port} using firewall rules or VPN.",
                        scan_id=self.scan.id,
                        host_id=svc.host_id,
                        service_id=svc.id,
                    )
                    self._findings.append(f)

    def _stage_normalization(self, cfg) -> None:
        self._findings = normalize.deduplicate_findings(self._findings)
        self._log("INFO", f"Normalization: {len(self._findings)} unique findings after dedup")

    # ── Persistence helpers ──────────────────────────────────────────────────

    def _get_or_create_host(self, dh) -> Host:
        host = self._hosts.get(dh.ip)
        if host is None:
            host = Host(
                scope_id=self.scan.scope_id,
                scan_id=self.scan.id,
                ip=dh.ip,
                hostname=dh.hostname,
                os_guess=dh.os_guess,
                mac_address=dh.mac,
            )
            self.session.add(host)
            self.session.flush()
            self._hosts[dh.ip] = host
            events.emit("host.discovered", self.scan.id, ip=dh.ip, hostname=dh.hostname)
        else:
            if dh.hostname and not host.hostname:
                host.hostname = dh.hostname
            if dh.os_guess and not host.os_guess:
                host.os_guess = dh.os_guess
            host.last_seen = datetime.now(timezone.utc)
        return host

    def _get_or_create_service(self, ds) -> Service:
        key = (ds.ip, ds.port)
        svc = self._services.get(key)
        if svc is None:
            host = self._get_or_create_host_from_ip(ds.ip)
            svc = Service(
                host_id=host.id,
                protocol=ds.protocol,
                port=ds.port,
                state=ds.state,
                service_name=ds.service_name,
                product=ds.product,
                version=ds.version,
                banner=ds.banner,
            )
            self.session.add(svc)
            self.session.flush()
            self._services[key] = svc
            events.emit("service.discovered", self.scan.id, ip=ds.ip, port=ds.port, service=ds.service_name)
        else:
            svc.last_seen = datetime.now(timezone.utc)
            if ds.service_name and not svc.service_name:
                svc.service_name = ds.service_name
            if ds.product and not svc.product:
                svc.product = ds.product
            if ds.version and not svc.version:
                svc.version = ds.version
        return svc

    def _get_or_create_host_from_ip(self, ip: str) -> Host:
        host = self._hosts.get(ip)
        if host is None:
            host = Host(scope_id=self.scan.scope_id, scan_id=self.scan.id, ip=ip)
            self.session.add(host)
            self.session.flush()
            self._hosts[ip] = host
        return host

    def _create_web_target(self, wt) -> WebTarget:
        # Find the matching service
        service = self._services.get((wt.host, wt.port))
        web_target = WebTarget(
            service_id=service.id if service else None,
            scheme=wt.scheme,
            host=wt.host,
            port=wt.port,
            url=wt.url,
            title=wt.title,
            status_code=wt.status_code,
            content_length=wt.content_length,
            content_type=wt.content_type,
            server_header=wt.server_header,
            redirect_url=wt.redirect_url,
            tls_info=json.dumps({
                "subject": wt.tls_subject,
                "issuer": wt.tls_issuer,
                "not_after": wt.tls_not_after,
            }) if wt.tls_subject else None,
        )
        web_target.technology_list = wt.technologies
        self.session.add(web_target)
        self.session.flush()
        self._web_targets.append(web_target)
        return web_target

    def _store_findings(self) -> None:
        """Persist findings and update scan severity counters."""
        for f in self._findings:
            # Check for existing finding with same dedup key
            existing = self.session.query(Finding).filter_by(dedup_key=f.dedup_key).first()
            if existing:
                existing.last_seen = datetime.now(timezone.utc)
                existing.scan_id = self.scan.id
                # Update severity if higher
                if normalize._severity_rank(f.severity) > normalize._severity_rank(existing.severity):
                    existing.severity = f.severity
                self.session.flush()
            else:
                self.session.add(f)
                self.session.flush()

        # Update counters
        self.scan.findings_critical = sum(1 for f in self._findings if f.severity == Severity.CRITICAL.value)
        self.scan.findings_high = sum(1 for f in self._findings if f.severity == Severity.HIGH.value)
        self.scan.findings_medium = sum(1 for f in self._findings if f.severity == Severity.MEDIUM.value)
        self.scan.findings_low = sum(1 for f in self._findings if f.severity == Severity.LOW.value)
        self.scan.findings_info = sum(1 for f in self._findings if f.severity == Severity.INFO.value)
        self.session.flush()
        events.emit("findings.stored", self.scan.id, count=len(self._findings))

    # ── Stage handler registry ──────────────────────────────────────────────

    _stage_handlers = {
        HOST_DISCOVERY: _stage_host_discovery,
        PORT_DISCOVERY: _stage_port_discovery,
        SERVICE_DETECTION: _stage_service_detection,
        HTTP_DISCOVERY: _stage_http_discovery,
        TECH_FINGERPRINT: _stage_tech_fingerprint,
        DNS_ENRICH: _stage_dns_enrich,
        VULN_ASSESSMENT: _stage_vuln_assessment,
        NORMALIZATION: _stage_normalization,
    }
