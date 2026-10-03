"""Scan API — create, list, show, and cancel scans."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import (
    Finding,
    Host,
    Scan,
    ScanLog,
    ScanStatus,
    Scope,
    Service,
    WebTarget,
)
from app.profiles import PROFILES, get_profile
from app.queue import enqueue_scan, set_cancelled
from app.scope import ScopeError, ScopeManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scans", tags=["scans"])
sm = ScopeManager()


# ── Request / response models ──────────────────────────────────────────────

class ScanCreate(BaseModel):
    scope: str
    profile: str = "safe"
    name: Optional[str] = None
    creator: Optional[str] = None
    max_concurrency: Optional[int] = None
    requests_per_second: Optional[int] = None

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        if v not in PROFILES:
            raise ValueError(f"Unknown profile '{v}'.  Available: {list(PROFILES.keys())}")
        return v


class ScanConfirm(BaseModel):
    """Second step — user confirms the normalised scope."""
    scope_id: str
    profile: str = "safe"
    name: Optional[str] = None
    creator: Optional[str] = None
    worker: Optional[str] = None
    max_concurrency: Optional[int] = None
    requests_per_second: Optional[int] = None


class ScanSummary(BaseModel):
    id: str
    scope_id: str
    profile: str
    status: str
    name: Optional[str] = None
    creator: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    worker: Optional[str] = None
    progress: int = 0
    hosts_discovered: int = 0
    ports_discovered: int = 0
    web_targets_discovered: int = 0
    findings_critical: int = 0
    findings_high: int = 0
    findings_medium: int = 0
    findings_low: int = 0
    findings_info: int = 0
    error: Optional[str] = None


class ScopeValidateResponse(BaseModel):
    valid: bool
    scope_id: Optional[str] = None
    name: str
    cidrs: list[str]
    address_count: int
    error: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _scan_to_summary(scan: Scan) -> ScanSummary:
    return ScanSummary(
        id=scan.id,
        scope_id=scan.scope_id,
        profile=scan.profile,
        status=scan.status,
        name=scan.name,
        creator=scan.creator,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        finished_at=scan.finished_at.isoformat() if scan.finished_at else None,
        worker=scan.worker,
        progress=scan.progress,
        hosts_discovered=scan.hosts_discovered,
        ports_discovered=scan.ports_discovered,
        web_targets_discovered=scan.web_targets_discovered,
        findings_critical=scan.findings_critical,
        findings_high=scan.findings_high,
        findings_medium=scan.findings_medium,
        findings_low=scan.findings_low,
        findings_info=scan.findings_info,
        error=scan.error,
    )


def _generate_scan_id(session: Session) -> str:
    """Generate a sequential scan ID like scan-2026-000042."""
    year = settings.scan_id_year
    prefix = settings.scan_id_prefix
    count = session.execute(
        select(func.count()).select_from(Scan).where(Scan.id.like(f"{prefix}-{year}-%"))
    ).scalar() or 0
    return f"{prefix}-{year}-{count + 1:06d}"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/validate-scope", response_model=ScopeValidateResponse)
def validate_scope(body: ScanCreate, db: Session = Depends(get_db)):
    """Validate and normalise a scope without starting a scan.

    Returns the resolved CIDR list so the UI can show it for confirmation.
    """
    try:
        scope = sm.parse(body.scope, name=body.name or body.scope)
    except ScopeError as exc:
        return ScopeValidateResponse(
            valid=False, name="", cidrs=[], address_count=0, error=str(exc)
        )

    scope_model = Scope(
        name=scope.name,
        cidrs=scope.to_json(),
    )
    scope_model.cidr_list = scope.cidr_list
    db.add(scope_model)
    db.commit()
    db.refresh(scope_model)

    return ScopeValidateResponse(
        valid=True,
        scope_id=scope_model.id,
        name=scope.name,
        cidrs=scope.cidr_list,
        address_count=scope.address_count,
    )


@router.post("", response_model=ScanSummary, status_code=201)
def create_scan(body: ScanConfirm, db: Session = Depends(get_db)):
    """Create and enqueue a scan after scope confirmation."""
    scope_model = db.get(Scope, body.scope_id)
    if scope_model is None:
        raise HTTPException(404, "Scope not found — call /validate-scope first")

    # Re-validate the scope from the stored CIDRs
    try:
        scope = sm.parse(scope_model.cidr_list, name=scope_model.name)
    except ScopeError as exc:
        raise HTTPException(400, f"Stored scope is invalid: {exc}") from exc

    profile = get_profile(body.profile)
    scan_id = _generate_scan_id(db)

    scan = Scan(
        id=scan_id,
        scope_id=scope_model.id,
        profile=body.profile,
        status=ScanStatus.PENDING.value,
        creator=body.creator,
        name=body.name,
        worker=body.worker or settings.worker_remote_host,
        max_concurrency=body.max_concurrency,
        requests_per_second=body.requests_per_second,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Enqueue for the worker
    enqueue_scan(scan_id, {
        "profile": body.profile,
        "scope_cidrs": scope.cidr_list,
    })

    return _scan_to_summary(scan)


@router.get("", response_model=list[ScanSummary])
def list_scans(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = select(Scan).order_by(desc(Scan.created_at)).limit(limit)
    if status:
        query = query.where(Scan.status == status.upper())
    scans = db.execute(query).scalars().all()
    return [_scan_to_summary(s) for s in scans]


@router.get("/{scan_id}")
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "Scan not found")

    scope = db.get(Scope, scan.scope_id)
    stages = [
        {
            "seq": s.seq,
            "name": s.name,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            "detail": s.detail,
            "error": s.error,
        }
        for s in scan.stages
    ]
    logs = [
        {"timestamp": l.timestamp.isoformat(), "level": l.level, "message": l.message}
        for l in scan.logs
    ]
    return {
        **_scan_to_summary(scan).model_dump(),
        "scope": {"id": scope.id, "name": scope.name, "cidrs": scope.cidr_list} if scope else None,
        "stages": stages,
        "logs": logs,
    }


@router.post("/{scan_id}/cancel")
def cancel_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "Scan not found")

    terminal = {ScanStatus.COMPLETE.value, ScanStatus.FAILED.value, ScanStatus.CANCELLED.value}
    if scan.status in terminal:
        raise HTTPException(409, f"Scan is already in terminal state: {scan.status}")

    set_cancelled(scan_id)
    scan.status = ScanStatus.CANCELLED.value
    scan.finished_at = datetime.now(timezone.utc)
    db.commit()
    return {"scan_id": scan_id, "status": scan.status}


@router.get("/preflight/{worker}")
def preflight_check(worker: str, profile: str = Query("safe")):
    """Check that required scanner tools exist on the target worker.

    Returns a list of missing tools with install instructions.  The scan
    should not be started if any tools are missing.
    """
    from app.preflight import preflight
    result = preflight(worker, profile)
    return result.to_dict()
