"""SQLAlchemy models for the shadow.lab asset graph.

    Scope
      └── Host
            └── Service
                  └── WebTarget
                        └── Finding
"""
from __future__ import annotations

import enum
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────

class ScanStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    DISCOVERING = "DISCOVERING"
    ENUMERATING = "ENUMERATING"
    ASSESSING = "ASSESSING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScanProfile(str, enum.Enum):
    SAFE = "safe"
    THOROUGH = "thorough"
    RECON = "recon"


class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class FindingStatus(str, enum.Enum):
    OPEN = "OPEN"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FIXED = "FIXED"
    ACCEPTED = "ACCEPTED"


class ServiceState(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"


class StageStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


# ── Models ─────────────────────────────────────────────────────────────────

class Scope(Base):
    __tablename__ = "scopes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cidrs: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of CIDR/IP strings
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    scans: Mapped[list["Scan"]] = relationship(back_populates="scope", cascade="all, delete-orphan")
    hosts: Mapped[list["Host"]] = relationship(back_populates="scope", cascade="all, delete-orphan")

    @property
    def cidr_list(self) -> list[str]:
        return json.loads(self.cidrs)

    @cidr_list.setter
    def cidr_list(self, value: list[str]) -> None:
        self.cidrs = json.dumps(value)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scope_id: Mapped[str] = mapped_column(ForeignKey("scopes.id", ondelete="CASCADE"))
    profile: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ScanStatus.PENDING.value)
    creator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    worker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Safety overrides
    max_concurrency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requests_per_second: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Aggregate counters (denormalised for quick dashboard reads)
    hosts_discovered: Mapped[int] = mapped_column(Integer, default=0)
    ports_discovered: Mapped[int] = mapped_column(Integer, default=0)
    web_targets_discovered: Mapped[int] = mapped_column(Integer, default=0)
    findings_critical: Mapped[int] = mapped_column(Integer, default=0)
    findings_high: Mapped[int] = mapped_column(Integer, default=0)
    findings_medium: Mapped[int] = mapped_column(Integer, default=0)
    findings_low: Mapped[int] = mapped_column(Integer, default=0)
    findings_info: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scope: Mapped["Scope"] = relationship(back_populates="scans")
    stages: Mapped[list["ScanStage"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", order_by="ScanStage.seq"
    )
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    logs: Mapped[list["ScanLog"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", order_by="ScanLog.id"
    )


class ScanStage(Base):
    __tablename__ = "scan_stages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=StageStatus.PENDING.value)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="stages")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    scan: Mapped["Scan"] = relationship(back_populates="logs")


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    scope_id: Mapped[str] = mapped_column(ForeignKey("scopes.id", ondelete="CASCADE"))
    scan_id: Mapped[Optional[str]] = mapped_column(ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    os_guess: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scope: Mapped["Scope"] = relationship(back_populates="hosts")
    services: Mapped[list["Service"]] = relationship(
        back_populates="host", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_hosts_scope_ip", "scope_id", "ip"),)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    host_id: Mapped[str] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"))
    protocol: Mapped[str] = mapped_column(String(16), default="tcp")
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), default=ServiceState.OPEN.value)
    service_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    banner: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    host: Mapped["Host"] = relationship(back_populates="services")
    web_target: Mapped[Optional["WebTarget"]] = relationship(
        back_populates="service", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("host_id", "protocol", "port", name="uq_services_host_proto_port"),
    )


class WebTarget(Base):
    __tablename__ = "web_targets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    scheme: Mapped[str] = mapped_column(String(16), default="http")
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    server_header: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technologies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    redirect_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tls_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    service: Mapped["Service"] = relationship(back_populates="web_target")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="web_target", cascade="all, delete-orphan"
    )

    @property
    def technology_list(self) -> list[str]:
        return json.loads(self.technologies) if self.technologies else []

    @technology_list.setter
    def technology_list(self, value: list[str]) -> None:
        self.technologies = json.dumps(value)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    scan_id: Mapped[Optional[str]] = mapped_column(ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    host_id: Mapped[Optional[str]] = mapped_column(ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True)
    service_id: Mapped[Optional[str]] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    web_target_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("web_targets.id", ondelete="SET NULL"), nullable=True
    )

    # Dedup key — findings with the same key are merged across scans
    dedup_key: Mapped[str] = mapped_column(String(512), nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Normalised classification
    severity: Mapped[str] = mapped_column(String(16), default=Severity.INFO.value)
    confidence: Mapped[str] = mapped_column(String(16), default=Confidence.UNKNOWN.value)

    # Original scanner classification (kept separate from normalised)
    source_severity: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)  # nmap, httpx, nuclei, etc.
    template_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # External references
    cve: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cwe: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cvss_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Evidence
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    affected_asset: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    affected_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Remediation
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list

    # Lifecycle
    status: Mapped[str] = mapped_column(String(32), default=FindingStatus.OPEN.value)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scan: Mapped[Optional["Scan"]] = relationship(back_populates="findings")
    web_target: Mapped[Optional["WebTarget"]] = relationship(back_populates="findings")
    notes: Mapped[list["FindingNote"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="FindingNote.id"
    )
    history: Mapped[list["FindingStatusChange"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="FindingStatusChange.id"
    )

    __table_args__ = (
        Index("ix_findings_dedup", "dedup_key"),
        Index("ix_findings_severity", "severity"),
        Index("ix_findings_scan", "scan_id"),
    )


class FindingNote(Base):
    __tablename__ = "finding_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)

    finding: Mapped["Finding"] = relationship(back_populates="notes")


class FindingStatusChange(Base):
    """Audit trail for finding status changes."""
    __tablename__ = "finding_status_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    old_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    finding: Mapped["Finding"] = relationship(back_populates="history")
