"""Scan profiles — declarative descriptions of what each scan mode does.

Profiles are data, not code.  The pipeline reads the profile to decide which
stages to run and which tool flags to use.  New profiles can be added by
appending to ``PROFILES``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models import ScanProfile


@dataclass(frozen=True)
class StageConfig:
    name: str
    enabled: bool = True
    timeout: int = 300
    extra_args: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileDef:
    key: str
    label: str
    description: str
    stages: list[StageConfig]
    # Nmap timing template (0-5: polite=3, normal=4, aggressive=5)
    nmap_timing: int = 3
    # Nuclei severity tags to run (empty = all safe)
    nuclei_severities: list[str] = field(default_factory=list)
    # Whether to run vulnerability assessment at all
    run_vuln: bool = True


# ── Stage names (shared across profiles) ────────────────────────────────────

HOST_DISCOVERY = "host_discovery"
PORT_DISCOVERY = "port_discovery"
SERVICE_DETECTION = "service_detection"
HTTP_DISCOVERY = "http_discovery"
TECH_FINGERPRINT = "tech_fingerprint"
DNS_ENRICH = "dns_enrich"
VULN_ASSESSMENT = "vuln_assessment"
NORMALIZATION = "normalization"


SAFE_PROFILE = ProfileDef(
    key=ScanProfile.SAFE.value,
    label="Safe",
    description=(
        "Low-impact reconnaissance and vulnerability assessment.  "
        "Host discovery, TCP service discovery, HTTP/HTTPS discovery, "
        "technology fingerprinting, safe vulnerability templates, TLS checks, "
        "exposed-service checks, and version detection."
    ),
    stages=[
        StageConfig(HOST_DISCOVERY, timeout=300),
        StageConfig(PORT_DISCOVERY, timeout=600),
        StageConfig(SERVICE_DETECTION, timeout=600),
        StageConfig(HTTP_DISCOVERY, timeout=300),
        StageConfig(TECH_FINGERPRINT, timeout=300),
        StageConfig(DNS_ENRICH, timeout=120, enabled=False),
        StageConfig(VULN_ASSESSMENT, timeout=1800),
        StageConfig(NORMALIZATION, timeout=120),
    ],
    nmap_timing=3,  # polite
    nuclei_severities=["info", "low", "medium", "high", "critical"],
    run_vuln=True,
)

THOROUGH_PROFILE = ProfileDef(
    key=ScanProfile.THOROUGH.value,
    label="Thorough",
    description=(
        "Comprehensive authenticated-free assessment, still non-destructive.  "
        "Everything in Safe plus broader service enumeration, deeper HTTP "
        "discovery, additional vulnerability templates, configuration analysis, "
        "and additional fingerprinting."
    ),
    stages=[
        StageConfig(HOST_DISCOVERY, timeout=600),
        StageConfig(PORT_DISCOVERY, timeout=1200),
        StageConfig(SERVICE_DETECTION, timeout=1200),
        StageConfig(HTTP_DISCOVERY, timeout=600),
        StageConfig(TECH_FINGERPRINT, timeout=600),
        StageConfig(DNS_ENRICH, timeout=180),
        StageConfig(VULN_ASSESSMENT, timeout=3600),
        StageConfig(NORMALIZATION, timeout=180),
    ],
    nmap_timing=3,  # still polite — thorough means more ports, not faster
    nuclei_severities=["info", "low", "medium", "high", "critical"],
    run_vuln=True,
)

RECON_PROFILE = ProfileDef(
    key=ScanProfile.RECON.value,
    label="Recon",
    description=(
        "Discovery and enumeration only.  No vulnerability templates.  "
        "Host discovery, port/service discovery, HTTP discovery, and "
        "technology fingerprinting."
    ),
    stages=[
        StageConfig(HOST_DISCOVERY, timeout=300),
        StageConfig(PORT_DISCOVERY, timeout=600),
        StageConfig(SERVICE_DETECTION, timeout=600),
        StageConfig(HTTP_DISCOVERY, timeout=300),
        StageConfig(TECH_FINGERPRINT, timeout=300),
        StageConfig(DNS_ENRICH, timeout=120),
        StageConfig(VULN_ASSESSMENT, enabled=False),
        StageConfig(NORMALIZATION, timeout=120),
    ],
    nmap_timing=3,
    nuclei_severities=[],
    run_vuln=False,
)

PROFILES: dict[str, ProfileDef] = {
    SAFE_PROFILE.key: SAFE_PROFILE,
    THOROUGH_PROFILE.key: THOROUGH_PROFILE,
    RECON_PROFILE.key: RECON_PROFILE,
}


def get_profile(key: str) -> ProfileDef:
    if key not in PROFILES:
        raise ValueError(f"Unknown scan profile '{key}'.  Available: {list(PROFILES)}")
    return PROFILES[key]
