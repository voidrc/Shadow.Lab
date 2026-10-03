import asyncio
import json
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import docker
from docker.errors import APIError, DockerException, NotFound
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api import assets, findings, reports, scans
from app.database import init_db
from app.models import Finding, Scan, ScanStatus
from app.profiles import PROFILES

DOCKER_HOST = os.getenv("DOCKER_HOST", "tcp://socket-proxy:2375")
TAILSCALE_SOCKET = os.getenv("TAILSCALE_SOCKET", "/var/run/tailscale/tailscaled.sock")
TAILSCALE_CHECK_INTERVAL = int(os.getenv("TAILSCALE_CHECK_INTERVAL", "15"))
LABEL_FILTER = "shadow.lab.manage=true"
LOG_TAIL_MAX = int(os.getenv("LOG_TAIL_MAX", "2000"))

state = {"tailscale": {"healthy": False, "message": "not checked", "checked_at": None}}
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def docker_client():
    return docker.DockerClient(base_url=DOCKER_HOST, timeout=10)


def check_tailscale() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(
            ["tailscale", "--socket", TAILSCALE_SOCKET, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return {"healthy": False, "message": result.stderr.strip() or "tailscale status failed", "checked_at": checked_at}
        status = json.loads(result.stdout)
        backend_state = status.get("BackendState")
        self_node = status.get("Self") or {}
        tailscale_ips = self_node.get("TailscaleIPs") or []
        healthy = backend_state == "Running" and bool(tailscale_ips)
        message = f"{backend_state}; {', '.join(tailscale_ips) or 'no tailnet IP'}"
        return {"healthy": healthy, "message": message, "checked_at": checked_at}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {"healthy": False, "message": str(exc), "checked_at": checked_at}


async def monitor_tailscale():
    while True:
        state["tailscale"] = await asyncio.to_thread(check_tailscale)
        await asyncio.sleep(TAILSCALE_CHECK_INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    state["tailscale"] = await asyncio.to_thread(check_tailscale)
    task = asyncio.create_task(monitor_tailscale())
    yield
    task.cancel()


app = FastAPI(title="shadow.lab Control Panel", lifespan=lifespan)

# Register scanner-platform API routers
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(assets.router)
app.include_router(reports.router)


def serialize_container(container) -> dict:
    container.reload()
    labels = container.labels
    health = container.attrs.get("State", {}).get("Health", {}).get("Status", "none")
    return {
        "id": container.short_id,
        "name": container.name,
        "display_name": labels.get("shadow.lab.name", container.name),
        "description": labels.get("shadow.lab.description", ""),
        "url": labels.get("shadow.lab.url", ""),
        "status": container.status,
        "health": health,
    }


def managed_container(container_id: str):
    try:
        container = docker_client().containers.get(container_id)
    except NotFound as exc:
        raise HTTPException(404, "Service not found") from exc
    except DockerException as exc:
        raise HTTPException(503, f"Docker API unavailable: {exc}") from exc
    if container.labels.get("shadow.lab.manage") != "true":
        raise HTTPException(403, "Container is not managed by this panel")
    return container


@app.get("/healthz")
def healthz():
    tailscale = state["tailscale"]
    try:
        docker_client().ping()
        docker_ok = True
    except DockerException:
        docker_ok = False
    if not tailscale["healthy"] or not docker_ok:
        raise HTTPException(503, {"tailscale": tailscale, "docker": docker_ok})
    return {"status": "healthy", "tailscale": tailscale, "docker": True}


@app.get("/api/services")
def services():
    try:
        containers = docker_client().containers.list(all=True, filters={"label": LABEL_FILTER})
        return sorted((serialize_container(item) for item in containers), key=lambda item: item["display_name"].lower())
    except DockerException as exc:
        raise HTTPException(503, f"Docker API unavailable: {exc}") from exc


@app.post("/api/services/{container_id}/{action}")
def service_action(container_id: str, action: str):
    if action not in {"start", "stop", "restart"}:
        raise HTTPException(400, "Unsupported action")
    container = managed_container(container_id)
    try:
        if action == "start":
            container.start()
        else:
            getattr(container, action)(timeout=10)
        return serialize_container(container)
    except APIError as exc:
        raise HTTPException(502, f"Docker action failed: {exc}") from exc


@app.get("/api/services/{container_id}/logs", response_class=PlainTextResponse)
def service_logs(container_id: str, tail: int = Query(200, ge=1, le=LOG_TAIL_MAX)):
    container = managed_container(container_id)
    try:
        return container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
    except APIError as exc:
        raise HTTPException(502, f"Could not read logs: {exc}") from exc


# ── Dashboard pages ──────────────────────────────────────────────────────────

def _dashboard_stats():
    """Gather summary stats for the dashboard."""
    from app.database import get_session
    with get_session() as session:
        total_scans = session.query(Scan).count()
        active_scans = session.query(Scan).filter(
            Scan.status.notin_([
                ScanStatus.COMPLETE.value, ScanStatus.FAILED.value, ScanStatus.CANCELLED.value
            ])
        ).count()
        total_hosts = session.query(Scan).filter(Scan.hosts_discovered > 0).count()
        total_findings = session.query(Finding).count()
        findings_by_severity = {}
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            findings_by_severity[sev] = session.query(Finding).filter(Finding.severity == sev).count()
        recent_scans = session.query(Scan).order_by(Scan.created_at.desc()).limit(10).all()
        return {
            "total_scans": total_scans,
            "active_scans": active_scans,
            "total_findings": total_findings,
            "findings_by_severity": findings_by_severity,
            "recent_scans": recent_scans,
            "profiles": list(PROFILES.values()),
        }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    stats = _dashboard_stats()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services(),
        "tailscale": state["tailscale"],
        "stats": stats,
    })


@app.get("/scans/new", response_class=HTMLResponse)
def scan_new(request: Request):
    return templates.TemplateResponse("scan_new.html", {
        "request": request,
        "profiles": list(PROFILES.values()),
        "tailscale": state["tailscale"],
    })


@app.get("/scans", response_class=HTMLResponse)
def scan_list(request: Request):
    from app.database import get_session
    with get_session() as session:
        scan_list = session.query(Scan).order_by(Scan.created_at.desc()).limit(100).all()
    return templates.TemplateResponse("scan_list.html", {
        "request": request,
        "scans": scan_list,
        "tailscale": state["tailscale"],
    })


@app.get("/scans/{scan_id}", response_class=HTMLResponse)
def scan_detail(request: Request, scan_id: str):
    from app.database import get_session
    from app.models import Scope
    with get_session() as session:
        scan = session.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "Scan not found")
        scope = session.get(Scope, scan.scope_id) if scan.scope_id else None
    return templates.TemplateResponse("scan_detail.html", {
        "request": request,
        "scan": scan,
        "scope": scope,
        "tailscale": state["tailscale"],
    })


@app.get("/findings", response_class=HTMLResponse)
def findings_page(request: Request):
    from app.database import get_session
    with get_session() as session:
        all_findings = session.query(Finding).order_by(Finding.severity, Finding.last_seen.desc()).limit(200).all()
    return templates.TemplateResponse("findings.html", {
        "request": request,
        "findings": all_findings,
        "tailscale": state["tailscale"],
    })


@app.get("/findings/{finding_id}", response_class=HTMLResponse)
def finding_detail(request: Request, finding_id: str):
    from app.database import get_session
    with get_session() as session:
        finding = session.get(Finding, finding_id)
        if finding is None:
            raise HTTPException(404, "Finding not found")
    return templates.TemplateResponse("finding_detail.html", {
        "request": request,
        "finding": finding,
        "tailscale": state["tailscale"],
    })


# ── Existing browser-action routes (preserved) ──────────────────────────────

@app.post("/services/{container_id}/action")
def browser_action(container_id: str, action: str = Form(...)):
    service_action(container_id, action)
    return RedirectResponse("/", status_code=303)


@app.get("/services/{container_id}/logs", response_class=HTMLResponse)
def browser_logs(request: Request, container_id: str, tail: int = Query(200, ge=1, le=LOG_TAIL_MAX)):
    container = managed_container(container_id)
    logs = service_logs(container_id, tail)
    return templates.TemplateResponse("logs.html", {"request": request, "name": container.labels.get("shadow.lab.name", container.name), "logs": logs})
