# Example scan profile: Safe

This is the built-in "Safe" profile. It is defined in `control-panel/app/profiles.py`.

```yaml
key: safe
label: Safe
description: >
  Low-impact reconnaissance and vulnerability assessment. Host discovery,
  TCP service discovery, HTTP/HTTPS discovery, technology fingerprinting,
  safe vulnerability templates, TLS checks, exposed-service checks, and
  version detection where appropriate.
stages:
  - scope_validation
  - host_discovery
  - port_discovery
  - http_discovery
  - tech_fingerprint
  - dns_enrich
  - vuln_assessment
  - exposure_checks
nmap:
  host_discovery_flags: ["-sn"]
  port_scan_flags: ["-sV", "--top-ports", "1000"]
  timing: "-T3"
httpx:
  threads: 10
  timeout: 5
nuclei:
  severity: ["info", "low", "medium", "high", "critical"]
  exclude_tags: ["dos", "exploit", "brute-force", "fuzz"]
  concurrency: 10
dnsx:
  enabled: true
  reverse: true
safety:
  max_concurrency: 8
  requests_per_second: 5
  connect_timeout: 5
  command_timeout: 300
  scan_timeout: 3600
```

## Creating a custom profile

Append a new entry to `PROFILES` in `control-panel/app/profiles.py`:

```python
"custom": ScanProfile(
    key="custom",
    label="Custom",
    description="My custom profile",
    stages=[...],
    nmap_args=[...],
    httpx_args=[...],
    nuclei_args=[...],
    dnsx_args=[...],
),
```

The profile is automatically available in the dashboard and CLI.
