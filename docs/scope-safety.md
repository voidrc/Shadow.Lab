# Scope Safety

Scope enforcement is the most important safety component in Shadow.Lab. This document explains why it exists and how it works.

## Why scope enforcement exists

Shadow.Lab is an authorised vulnerability-assessment platform. It is designed for operators who have explicit written authorization to assess specific networks. Without technical scope enforcement, a typo or misunderstanding could cause the scanner to touch systems outside the authorised boundary — potentially violating laws, contracts, or trust.

**The UI is not the enforcement boundary.** The backend enforces scope independently. Even if the UI is compromised or bypassed, the worker rejects out-of-scope targets.

## How scope enforcement works

### Layer 1: API validation

When a user submits a scan, the API (`POST /api/scans/validate-scope`) validates the scope:

1. **Parsing**: CIDR ranges, single IPs, and IP ranges are parsed using Python's `ipaddress` module.
2. **Normalisation**: Overlapping and adjacent ranges are collapsed using `ipaddress.collapse_addresses()`.
3. **Blocked networks**: The following are always rejected:
   - `0.0.0.0/8` — "this network"
   - `127.0.0.0/8` — loopback
   - `169.254.0.0/16` — link-local
   - `224.0.0.0/4` — multicast
   - `240.0.0.0/4` — reserved
   - `100.64.0.0/10` — Tailscale CGNAT (management plane)
   - `::1/128` — IPv6 loopback
   - `fe80::/10` — IPv6 link-local
   - `ff00::/8` — IPv6 multicast
4. **Prefix length**: Minimum /16 for IPv4, /48 for IPv6. This prevents accidental full-internet scans.
5. **Address count**: Total IPv4 addresses must not exceed `SCANNER_MAX_HOSTS` (default 65536).
6. **IPv6**: Disabled by default. Enable with `ENABLE_IPV6=true`.

The validated scope is stored in the database and associated with the scan via a `scope_id`.

### Layer 2: Worker enforcement

Before the worker touches any target, it calls `ScopeManager.is_in_scope(scope, target)`:

- **Host discovery**: Only in-scope CIDRs are passed to nmap.
- **Port scanning**: Only in-scope IPs (discovered in the host discovery stage) are scanned.
- **HTTP probing**: Each (host, port) pair is scope-checked before httpx probes it.
- **Vulnerability assessment**: Each URL is scope-checked before nuclei scans it.
- **DNS enrichment**: Each IP is scope-checked before dnsx queries it.

After each tool runs, the results are filtered again to ensure no out-of-scope data enters the database.

### Layer 3: Tool-level restrictions

Scanner tools receive only in-scope targets via their input mechanisms:
- nmap: targets passed as command-line arguments
- httpx: targets passed via stdin
- nuclei: URLs passed via stdin
- dnsx: IPs passed via stdin

No tool is given a broader target list and asked to self-filter.

## What happens when a target is out of scope

1. The API rejects the scan request with an error message explaining why.
2. If a somehow out-of-scope target reaches a worker, the worker logs a warning and skips it.
3. The `ScopeManager.assert_in_scope()` method raises a `ScopeError` if called with an out-of-scope target.

## Scope logging

Every scope is logged when authorised:
```
Scope authorised: 10.10.20.0/24 (1 networks, 256 addresses)
```

Every scan is associated with a `scope_id` in the database. The exact authorised CIDRs are stored and can be reviewed at any time.

## Configuration

| Environment variable | Default | Purpose |
|---------------------|---------|---------|
| `SCANNER_MAX_HOSTS` | 65536 | Maximum IPv4 addresses per scope |
| `ENABLE_IPV6` | true | Allow IPv6 scopes |
| `SCANNER_EGRESS_NETWORK` | egress | Docker network for scanning traffic |
| `SCANNER_RPS` | 5 | Rate limit (requests per second) |
| `SCANNER_MAX_CONCURRENCY` | 8 | Maximum concurrent scanner threads |
| `SCANNER_CONNECT_TIMEOUT` | 5 | Connection timeout in seconds |
| `SCANNER_COMMAND_TIMEOUT` | 300 | Per-tool timeout in seconds |
| `SCANNER_SCAN_TIMEOUT` | 3600 | Overall scan timeout in seconds |

## What the system does NOT do

- No credential attacks or password spraying
- No destructive payloads
- No persistence mechanisms
- No shell deployment
- No data exfiltration
- No evasion mechanisms
- No exploit chaining
- No arbitrary shell command execution from the dashboard
- No arbitrary Docker API operations beyond inspect/start/stop/restart on labeled containers

The goal is assessment and evidence, not compromise.
