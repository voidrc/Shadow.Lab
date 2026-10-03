"""Hosts, services, and web-targets API."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Host, Service, WebTarget

router = APIRouter(prefix="/api", tags=["assets"])


@router.get("/hosts")
def list_hosts(
    scope_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    query = select(Host).order_by(Host.ip).limit(limit)
    if scope_id:
        query = query.where(Host.scope_id == scope_id)
    if scan_id:
        query = query.where(Host.scan_id == scan_id)
    hosts = db.execute(query).scalars().all()
    return [_host_dict(h, db) for h in hosts]


@router.get("/hosts/{host_id}")
def get_host(host_id: str, db: Session = Depends(get_db)):
    h = db.get(Host, host_id)
    if h is None:
        raise HTTPException(404, "Host not found")
    return _host_dict(h, db, include_services=True)


@router.get("/services")
def list_services(
    host_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    query = select(Service).order_by(Service.port).limit(limit)
    if host_id:
        query = query.where(Service.host_id == host_id)
    if state:
        query = query.where(Service.state == state)
    services = db.execute(query).scalars().all()
    return [_service_dict(s) for s in services]


@router.get("/web-targets")
def list_web_targets(
    host: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    query = select(WebTarget).order_by(WebTarget.url).limit(limit)
    if host:
        query = query.where(WebTarget.host == host)
    targets = db.execute(query).scalars().all()
    return [_web_target_dict(t) for t in targets]


def _host_dict(h: Host, db: Session, include_services: bool = False) -> dict:
    result = {
        "id": h.id,
        "scope_id": h.scope_id,
        "scan_id": h.scan_id,
        "ip": h.ip,
        "hostname": h.hostname,
        "os_guess": h.os_guess,
        "mac_address": h.mac_address,
        "first_seen": h.first_seen.isoformat() if h.first_seen else None,
        "last_seen": h.last_seen.isoformat() if h.last_seen else None,
        "service_count": len(h.services),
    }
    if include_services:
        result["services"] = [_service_dict(s) for s in h.services]
    return result


def _service_dict(s: Service) -> dict:
    return {
        "id": s.id,
        "host_id": s.host_id,
        "protocol": s.protocol,
        "port": s.port,
        "state": s.state,
        "service_name": s.service_name,
        "product": s.product,
        "version": s.version,
        "banner": s.banner,
        "first_seen": s.first_seen.isoformat() if s.first_seen else None,
        "last_seen": s.last_seen.isoformat() if s.last_seen else None,
        "has_web_target": s.web_target is not None,
    }


def _web_target_dict(t: WebTarget) -> dict:
    return {
        "id": t.id,
        "service_id": t.service_id,
        "scheme": t.scheme,
        "host": t.host,
        "port": t.port,
        "url": t.url,
        "title": t.title,
        "status_code": t.status_code,
        "content_length": t.content_length,
        "content_type": t.content_type,
        "server_header": t.server_header,
        "technologies": t.technology_list,
        "redirect_url": t.redirect_url,
        "tls_info": json.loads(t.tls_info) if t.tls_info else None,
        "first_seen": t.first_seen.isoformat() if t.first_seen else None,
        "last_seen": t.last_seen.isoformat() if t.last_seen else None,
    }
