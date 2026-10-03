"""Findings API — list, show, filter, and update finding status."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Finding, FindingNote, FindingStatus, FindingStatusChange

router = APIRouter(prefix="/api/findings", tags=["findings"])


class FindingStatusUpdate(BaseModel):
    status: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class NoteCreate(BaseModel):
    note: str
    author: Optional[str] = None


_VALID_STATUSES = {s.value for s in FindingStatus}


@router.get("")
def list_findings(
    severity: Optional[str] = None,
    confidence: Optional[str] = None,
    host_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    cve: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = select(Finding).order_by(Finding.severity, Finding.last_seen.desc()).limit(limit)
    if severity:
        query = query.where(Finding.severity == severity.upper())
    if confidence:
        query = query.where(Finding.confidence == confidence.upper())
    if host_id:
        query = query.where(Finding.host_id == host_id)
    if scan_id:
        query = query.where(Finding.scan_id == scan_id)
    if source:
        query = query.where(Finding.source == source)
    if status:
        query = query.where(Finding.status == status.upper())
    if cve:
        query = query.where(Finding.cve == cve)

    findings = db.execute(query).scalars().all()
    return [_finding_dict(f) for f in findings]


@router.get("/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    f = db.get(Finding, finding_id)
    if f is None:
        raise HTTPException(404, "Finding not found")
    result = _finding_dict(f)
    result["notes"] = [
        {"id": n.id, "timestamp": n.timestamp.isoformat(), "author": n.author, "note": n.note}
        for n in f.notes
    ]
    result["history"] = [
        {
            "id": h.id, "timestamp": h.timestamp.isoformat(),
            "old_status": h.old_status, "new_status": h.new_status,
            "changed_by": h.changed_by, "reason": h.reason,
        }
        for h in f.history
    ]
    return result


@router.post("/{finding_id}/status")
def update_finding_status(
    finding_id: str,
    body: FindingStatusUpdate,
    db: Session = Depends(get_db),
):
    f = db.get(Finding, finding_id)
    if f is None:
        raise HTTPException(404, "Finding not found")

    if body.status not in _VALID_STATUSES:
        raise HTTPException(400, f"Invalid status '{body.status}'.  Valid: {sorted(_VALID_STATUSES)}")

    old = f.status
    if old == body.status:
        return {"finding_id": finding_id, "status": f.status, "unchanged": True}

    f.status = body.status
    f.last_seen = datetime.now(timezone.utc)

    change = FindingStatusChange(
        finding_id=finding_id,
        old_status=old,
        new_status=body.status,
        changed_by=body.changed_by,
        reason=body.reason,
    )
    db.add(change)
    db.commit()
    return {"finding_id": finding_id, "status": f.status, "old_status": old}


@router.post("/{finding_id}/notes")
def add_note(finding_id: str, body: NoteCreate, db: Session = Depends(get_db)):
    f = db.get(Finding, finding_id)
    if f is None:
        raise HTTPException(404, "Finding not found")

    note = FindingNote(finding_id=finding_id, note=body.note, author=body.author)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": note.id,
        "finding_id": finding_id,
        "timestamp": note.timestamp.isoformat(),
        "author": note.author,
        "note": note.note,
    }


def _finding_dict(f: Finding) -> dict:
    return {
        "id": f.id,
        "scan_id": f.scan_id,
        "host_id": f.host_id,
        "service_id": f.service_id,
        "web_target_id": f.web_target_id,
        "title": f.title,
        "description": f.description,
        "severity": f.severity,
        "confidence": f.confidence,
        "source": f.source,
        "source_severity": f.source_severity,
        "template_id": f.template_id,
        "cve": f.cve,
        "cwe": f.cwe,
        "cvss_score": f.cvss_score,
        "cvss_vector": f.cvss_vector,
        "affected_asset": f.affected_asset,
        "affected_url": f.affected_url,
        "evidence": json.loads(f.evidence) if f.evidence else None,
        "remediation": f.remediation,
        "references": json.loads(f.references) if f.references else None,
        "status": f.status,
        "first_seen": f.first_seen.isoformat() if f.first_seen else None,
        "last_seen": f.last_seen.isoformat() if f.last_seen else None,
    }
