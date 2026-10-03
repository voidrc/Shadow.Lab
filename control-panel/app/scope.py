"""Scope Manager — the central safety gate for all scanning.

Every scan target must pass through ``ScopeManager`` before any worker is
allowed to touch it.  The manager:

* parses and normalises CIDR ranges / single IPs (IPv4 and optionally IPv6)
* rejects invalid or private-link addresses that are never legitimate targets
* exposes the resolved set of authorised addresses to every worker
* provides ``is_in_scope()`` for per-target enforcement at the worker level
* logs exactly what was authorised

The UI is *not* the enforcement boundary.  Workers call ``is_in_scope()``
before touching any target, and the API rejects scan requests whose scope
fails validation.
"""
from __future__ import annotations

import ipaddress
import json
import logging
from dataclasses import dataclass, field
from typing import Iterable

from app.config import settings

logger = logging.getLogger(__name__)

# Addresses that must never be scanned regardless of what the operator enters.
# These are infrastructure / control-plane ranges that would indicate a
# misconfiguration rather than a legitimate target.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),       # "this network"
    ipaddress.ip_network("127.0.0.0/8"),     # loopback
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("224.0.0.0/4"),     # multicast
    ipaddress.ip_network("240.0.0.0/4"),     # reserved
    ipaddress.ip_network("100.64.0.0/10"),   # Tailscale CGNAT — management plane
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),       # IPv6 link-local
    ipaddress.ip_network("ff00::/8"),        # IPv6 multicast
]

# Maximum prefix length (smallest CIDR) we accept to prevent accidental
# full-internet scans.
_MIN_PREFIX_V4 = 16   # /16 at most — a /8 would be 16M addresses
_MIN_PREFIX_V6 = 48   # /48 at most for IPv6


class ScopeError(ValueError):
    """Raised when a scope specification is invalid or unsafe."""


@dataclass
class Scope:
    """A resolved, validated scope ready for scanning."""
    name: str
    raw_inputs: list[str]
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)

    @property
    def cidr_list(self) -> list[str]:
        return [str(n) for n in self.networks]

    @property
    def address_count(self) -> int:
        return sum(n.num_addresses for n in self.networks)

    def to_json(self) -> str:
        return json.dumps({
            "name": self.name,
            "raw_inputs": self.raw_inputs,
            "cidrs": self.cidr_list,
            "addresses": self.addresses,
            "address_count": self.address_count,
        })

    @classmethod
    def from_json(cls, data: str) -> "Scope":
        d = json.loads(data)
        s = cls(name=d["name"], raw_inputs=d["raw_inputs"])
        s.networks = [ipaddress.ip_network(c, strict=False) for c in d["cidrs"]]
        s.addresses = d.get("addresses", [])
        return s


class ScopeManager:
    """Parse, validate, and enforce scan scopes."""

    def __init__(
        self,
        enable_ipv6: bool | None = None,
        max_addresses: int | None = None,
    ) -> None:
        self.enable_ipv6 = settings.enable_ipv6 if enable_ipv6 is None else enable_ipv6
        self.max_addresses = settings.max_hosts if max_addresses is None else max_addresses

    # ── Parsing / validation ───────────────────────────────────────────────

    def parse(self, raw: str | Iterable[str], name: str = "") -> Scope:
        """Parse a scope from a newline/comma-separated string or iterable.

        Raises ``ScopeError`` on any invalid or unsafe input.
        """
        if isinstance(raw, str):
            tokens = [t.strip() for t in raw.replace(",", "\n").splitlines() if t.strip()]
        else:
            tokens = [str(t).strip() for t in raw if str(t).strip()]

        if not tokens:
            raise ScopeError("Empty scope — at least one CIDR or IP is required")

        networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for token in tokens:
            networks.extend(self._parse_token(token))

        # Collapse overlaps
        networks = self._collapse(networks)

        # Size check — only count IPv4 addresses; IPv6 prefix length is
        # already constrained by _MIN_PREFIX_V6.
        total_v4 = sum(n.num_addresses for n in networks if n.version == 4)
        if total_v4 > self.max_addresses:
            raise ScopeError(
                f"Scope contains {total_v4} addresses, exceeding the maximum of "
                f"{self.max_addresses}.  Narrow the scope or raise SCANNER_MAX_HOSTS."
            )

        scope = Scope(name=name or ", ".join(tokens), raw_inputs=tokens, networks=networks)
        logger.info("Scope authorised: %s (%d networks, %d addresses)",
                    scope.name, len(networks), total_v4)
        return scope

    def _parse_token(self, token: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        # Accept "10.10.20.0/24", "10.10.20.15", "10.10.20.0-10.10.20.255"
        if "-" in token and "/" not in token:
            return self._parse_range(token)

        try:
            net = ipaddress.ip_network(token, strict=False)
        except ValueError as exc:
            raise ScopeError(f"Invalid CIDR or IP '{token}': {exc}") from exc

        self._validate_network(net, token)
        return [net]

    def _parse_range(self, token: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        parts = token.split("-", 1)
        if len(parts) != 2:
            raise ScopeError(f"Invalid range '{token}'")
        try:
            start = ipaddress.ip_address(parts[0].strip())
            end = ipaddress.ip_address(parts[1].strip())
        except ValueError as exc:
            raise ScopeError(f"Invalid range '{token}': {exc}") from exc

        if start.version != end.version:
            raise ScopeError(f"Range '{token}' mixes IPv4 and IPv6")

        if int(end) < int(start):
            raise ScopeError(f"Range '{token}' end is before start")

        # Convert the range to a list of networks
        nets = list(ipaddress.summarize_address_range(start, end))
        for n in nets:
            self._validate_network(n, token)
        return nets

    def _validate_network(
        self, net: ipaddress.IPv4Network | ipaddress.IPv6Network, token: str
    ) -> None:
        if net.version == 6 and not self.enable_ipv6:
            raise ScopeError(
                f"IPv6 scope '{token}' rejected — set ENABLE_IPV6=true to allow"
            )

        # Blocked-network check (before prefix length so the user gets a
        # clear "blocked infrastructure" message even for broad ranges)
        for blocked in _BLOCKED_NETWORKS:
            if net.version == blocked.version and net.overlaps(blocked):
                raise ScopeError(
                    f"Scope '{token}' overlaps blocked infrastructure range "
                    f"{blocked} (loopback / link-local / Tailscale CGNAT / multicast)."
                )

        # Prefix length check
        min_prefix = _MIN_PREFIX_V4 if net.version == 4 else _MIN_PREFIX_V6
        if net.prefixlen < min_prefix:
            raise ScopeError(
                f"Scope '{token}' is too broad (/{net.prefixlen}).  "
                f"Minimum prefix is /{min_prefix}."
            )

    @staticmethod
    def _collapse(
        networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
    ) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        """Merge overlapping / adjacent networks and return a sorted list."""
        if not networks:
            return []
        # ipaddress.collapse_addresses handles containment and adjacency
        # correctly, but only works within the same version.
        v4 = [n for n in networks if n.version == 4]
        v6 = [n for n in networks if n.version == 6]
        collapsed: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        if v4:
            collapsed.extend(ipaddress.collapse_addresses(v4))
        if v6:
            collapsed.extend(ipaddress.collapse_addresses(v6))
        return collapsed

    # ── Enforcement ─────────────────────────────────────────────────────────

    def is_in_scope(self, scope: Scope, target: str) -> bool:
        """Return True if *target* (IP or hostname-derived IP) is inside *scope*.

        This is the per-target enforcement that workers MUST call before
        touching any host.
        """
        try:
            addr = ipaddress.ip_address(target)
        except ValueError:
            # Not a literal IP — workers should resolve hostnames and check
            # the resolved addresses.  Reject by default.
            logger.warning("Scope check on non-IP target '%s' — rejected by default", target)
            return False

        for net in scope.networks:
            if addr.version == net.version and addr in net:
                return True
        return False

    def filter_targets(self, scope: Scope, targets: Iterable[str]) -> list[str]:
        """Return only the targets that are inside *scope*."""
        return [t for t in targets if self.is_in_scope(scope, t)]

    def assert_in_scope(self, scope: Scope, target: str) -> None:
        """Raise ``ScopeError`` if *target* is outside *scope*."""
        if not self.is_in_scope(scope, target):
            raise ScopeError(
                f"Target {target} is outside the authorised scope "
                f"{scope.cidr_list}"
            )


# Module-level singleton for convenience
scope_manager = ScopeManager()
