"""Nmap runner — host discovery, port scanning, and service detection.

Uses nmap's XML output (``-oX -``) for reliable machine parsing.
Scope is enforced by passing only in-scope targets to nmap and by
asserting each discovered host is inside the authorised scope.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterator

from app.scanner.base import BaseRunner, RunResult
from app.scope import ScopeError

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredHost:
    ip: str
    hostname: str | None = None
    mac: str | None = None
    os_guess: str | None = None
    state: str = "up"


@dataclass
class DiscoveredService:
    ip: str
    protocol: str
    port: int
    state: str
    service_name: str | None = None
    product: str | None = None
    version: str | None = None
    banner: str | None = None


@dataclass
class NmapResult:
    hosts: list[DiscoveredHost] = field(default_factory=list)
    services: list[DiscoveredService] = field(default_factory=list)
    raw: RunResult | None = None


class NmapRunner(BaseRunner):
    tool_name = "nmap"

    def discover_hosts(
        self,
        targets: list[str],
        timing: int = 3,
        on_cancel=None,
    ) -> NmapResult:
        """Host discovery only (no port scan)."""
        in_scope = self.filter_in_scope(targets)
        if not in_scope:
            return NmapResult()

        cmd = [
            "nmap",
            "-sn",            # ping scan — host discovery only
            f"-T{timing}",
            "--max-rate", str(self.rps * 100),
            "-oX", "-",        # XML to stdout
            *in_scope,
        ]
        result = self.run(cmd, on_cancel=on_cancel)
        hosts = self._parse_hosts(result.stdout)
        # Double-check every discovered host is in scope
        hosts = [h for h in hosts if self.sm.is_in_scope(self.scope, h.ip)]
        return NmapResult(hosts=hosts, raw=result)

    def scan_services(
        self,
        targets: list[str],
        timing: int = 3,
        top_ports: int = 1000,
        on_cancel=None,
    ) -> NmapResult:
        """Port scan + service detection + version detection."""
        in_scope = self.filter_in_scope(targets)
        if not in_scope:
            return NmapResult()

        cmd = [
            "nmap",
            "-sV",            # service/version detection
            f"-T{timing}",
            "--top-ports", str(top_ports),
            "--max-rate", str(self.rps * 100),
            "-oX", "-",
            *in_scope,
        ]
        result = self.run(cmd, timeout=self.timeout * 2, on_cancel=on_cancel)
        hosts, services = self._parse_full(result.stdout)
        # Enforce scope on every result
        hosts = [h for h in hosts if self.sm.is_in_scope(self.scope, h.ip)]
        services = [s for s in services if self.sm.is_in_scope(self.scope, s.ip)]
        return NmapResult(hosts=hosts, services=services, raw=result)

    # ── XML parsing ──────────────────────────────────────────────────────────

    def _parse_hosts(self, xml_str: str) -> list[DiscoveredHost]:
        if not xml_str.strip():
            return []
        hosts = []
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError as exc:
            logger.warning("nmap XML parse error: %s", exc)
            return []
        for host_el in root.findall("host"):
            if host_el.get("state") != "up":
                continue
            addr_el = host_el.find("address")
            if addr_el is None:
                continue
            ip = addr_el.get("addr", "")
            host = DiscoveredHost(ip=ip, state="up")
            # MAC address (if present)
            for a in host_el.findall("address"):
                if a.get("addrtype") == "mac":
                    host.mac = a.get("addr")
            # Hostname
            hostnames_el = host_el.find("hostnames")
            if hostnames_el is not None:
                hn = hostnames_el.find("hostname")
                if hn is not None:
                    host.hostname = hn.get("name")
            # OS guess
            os_el = host_el.find("os")
            if os_el is not None:
                match = os_el.find("osmatch")
                if match is not None:
                    host.os_guess = match.get("name")
            hosts.append(host)
        return hosts

    def _parse_full(self, xml_str: str) -> tuple[list[DiscoveredHost], list[DiscoveredService]]:
        if not xml_str.strip():
            return [], []
        hosts: list[DiscoveredHost] = []
        services: list[DiscoveredService] = []
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError as exc:
            logger.warning("nmap XML parse error: %s", exc)
            return [], []
        for host_el in root.findall("host"):
            if host_el.get("state") != "up":
                continue
            addr_el = host_el.find("address")
            if addr_el is None:
                continue
            ip = addr_el.get("addr", "")
            host = DiscoveredHost(ip=ip, state="up")
            for a in host_el.findall("address"):
                if a.get("addrtype") == "mac":
                    host.mac = a.get("addr")
            hostnames_el = host_el.find("hostnames")
            if hostnames_el is not None:
                hn = hostnames_el.find("hostname")
                if hn is not None:
                    host.hostname = hn.get("name")
            os_el = host_el.find("os")
            if os_el is not None:
                match = os_el.find("osmatch")
                if match is not None:
                    host.os_guess = match.get("name")
            hosts.append(host)

            ports_el = host_el.find("ports")
            if ports_el is None:
                continue
            for port_el in ports_el.findall("port"):
                proto = port_el.get("protocol", "tcp")
                port = int(port_el.get("portid", "0"))
                if port == 0:
                    continue
                state_el = port_el.find("state")
                state = state_el.get("state", "unknown") if state_el is not None else "unknown"
                service_el = port_el.find("service")
                svc = DiscoveredService(ip=ip, protocol=proto, port=port, state=state)
                if service_el is not None:
                    svc.service_name = service_el.get("name")
                    svc.product = service_el.get("product")
                    svc.version = service_el.get("version")
                    svc.banner = service_el.get("banner")
                services.append(svc)
        return hosts, services
