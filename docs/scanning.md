# Scanning Workflow

Shadow.Lab performs authorised reconnaissance and vulnerability assessment through a multi-stage pipeline. This document explains the complete workflow.

**Important**: Only scan networks for which you have explicit written authorization.

## Scan profiles

| Profile | Description | Vulnerability templates |
|---------|-------------|------------------------|
| **Safe** | Low-impact recon + safe vuln assessment | info, low, medium, high, critical |
| **Thorough** | Comprehensive non-destructive assessment | all severities, broader enumeration |
| **Recon** | Discovery and enumeration only | none |

Profiles are defined in `control-panel/app/profiles.py`. New profiles can be added by appending to the `PROFILES` dictionary.

## Pipeline stages

Scanner tools run either locally (MacBook worker container) or on the remote ASUS (medusa) via Tailscale SSH. The pipeline orchestration, result parsing, normalization, and storage all happen locally on the MacBook. Only the tool execution is remote.

### 1. Scope Validation
- Parses CIDR ranges, single IPs, and IP ranges
- Normalises and collapses overlapping ranges
- Rejects blocked infrastructure (loopback, link-local, Tailscale CGNAT, multicast)
- Enforces minimum prefix length (/16 IPv4, /48 IPv6)
- Stores the authorised scope and associates it with the scan

### 2. Host Discovery (nmap -sn)
- Ping scan to identify live hosts
- Only in-scope targets are passed to nmap
- Every discovered host is re-checked against the scope

### 3. Port Discovery (nmap -sV)
- TCP connect scan with service/version detection
- Safe profile: top 1000 ports
- Thorough profile: all 65535 ports
- Rate-limited via `SCANNER_RPS`

### 4. Service Detection
- Performed as part of the nmap -sV scan
- Service name, product, version, and banner are captured

### 5. HTTP Discovery (httpx)
- Probes HTTP/HTTPS for discovered web ports
- Captures: status code, title, content type, server header, redirects, technologies, TLS certificate info
- Only in-scope hosts are probed

### 6. Technology Fingerprinting
- Performed by httpx -tech-detect
- Technologies are stored on the WebTarget model

### 7. DNS Enrichment (dnsx)
- Reverse DNS lookup for discovered IPs
- Enriches hosts with hostnames
- Optional in Safe, enabled in Thorough and Recon

### 8. Vulnerability Assessment (nuclei)
- Template-based vulnerability detection
- Excludes destructive tags: dos, exploit, brute-force, fuzz
- Severity-filtered per profile
- Only in-scope URLs are scanned

### 9. Exposure Checks
- Detects dangerous exposed services (Telnet, FTP, RDP, Redis, MongoDB, Docker API, etc.)
- Generates findings with appropriate severity and remediation guidance

### 10. Normalization and Deduplication
- All findings are normalised to a canonical Finding model
- Severity and confidence are mapped separately
- Findings with the same dedup key (source + template + asset + title) are merged
- Higher severity wins on merge

### 11. Evidence Storage
- Evidence is stored as JSON in the Finding.evidence column
- Includes: tool, template ID, matched URL, extracted results, response metadata
- Sensitive response bodies are not stored by default
- Configurable retention via `EVIDENCE_RETENTION_DAYS`

## Starting a scan

### Via dashboard

1. Open `http://shadow-lab:8080/`
2. Click "New Scan"
3. Enter the authorised scope (e.g., `10.10.20.0/24`)
4. Select a profile
5. Click "Validate scope"
6. Review the normalised scope
7. Click "Start scan"

### Via CLI

```sh
make scan SCOPE=10.10.20.0/24 PROFILE=safe
# or directly:
docker compose exec control-panel python -m app.cli scan create --scope 10.10.20.0/24 --profile safe --yes
```

### Via API

```sh
# Step 1: validate scope
curl -X POST http://shadow-lab:8080/api/scans/validate-scope \
  -H "Content-Type: application/json" \
  -d '{"scope": "10.10.20.0/24", "profile": "safe"}'

# Step 2: create scan (use scope_id from step 1)
curl -X POST http://shadow-lab:8080/api/scans \
  -H "Content-Type: application/json" \
  -d '{"scope_id": "<id>", "profile": "safe"}'
```

## Monitoring progress

- Dashboard: `http://shadow-lab:8080/scans/<scan-id>` — live progress with polling
- CLI: `shadow scan show <scan-id>`
- API: `GET /api/scans/<scan-id>` — includes stages and logs

## Cancellation

Scans can be cancelled at any time. Cancellation propagates to the worker via a Redis key. The worker checks for cancellation between stages and during tool execution.

```sh
shadow scan cancel <scan-id>
# or via API:
curl -X POST http://shadow-lab:8080/api/scans/<scan-id>/cancel
```

## Findings

### Severity and confidence

Severity and confidence are stored separately:
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Confidence**: HIGH, MEDIUM, LOW, UNKNOWN

The original scanner classification (`source_severity`) is preserved alongside the normalised classification.

### Finding states

| State | Meaning |
|-------|---------|
| OPEN | Newly discovered, not yet reviewed |
| CONFIRMED | Manually verified as a real vulnerability |
| FALSE_POSITIVE | Determined to not be a real issue |
| FIXED | The vulnerability has been remediated |
| ACCEPTED | Known and accepted risk |

All status changes are recorded in an audit trail.

### External references

Findings can include:
- CVE IDs (from Nuclei templates)
- CWE IDs
- CVSS score and vector
- Template IDs
- References (URLs)

Shadow.Lab does not invent CVEs or vulnerability classifications. It only stores what the scanner tools report.

## Reports

Reports can be generated in Markdown, JSON, and HTML:

```sh
make report SCAN=scan-2026-000042 FORMAT=markdown
# or:
shadow report generate scan-2026-000042 --format markdown --output report.md
```

Reports include: scope, scan configuration, time, assets, services, technologies, findings, evidence, and recommendations.
