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
        healthy = backend_state == "Running" and bool(self_node.get("TailscaleIPs"))
        message = f"{backend_state}; {', '.join(self_node.get('TailscaleIPs', [])) or 'no tailnet IP'}"
        return {"healthy": healthy, "message": message, "checked_at": checked_at}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {"healthy": False, "message": str(exc), "checked_at": checked_at}


async def monitor_tailscale():
    while True:
        state["tailscale"] = await asyncio.to_thread(check_tailscale)
        await asyncio.sleep(TAILSCALE_CHECK_INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    state["tailscale"] = await asyncio.to_thread(check_tailscale)
    task = asyncio.create_task(monitor_tailscale())
    yield
    task.cancel()


app = FastAPI(title="shadow.lab Control Panel", lifespan=lifespan)


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


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "services": services(), "tailscale": state["tailscale"]})


@app.post("/services/{container_id}/action")
def browser_action(container_id: str, action: str = Form(...)):
    service_action(container_id, action)
    return RedirectResponse("/", status_code=303)


@app.get("/services/{container_id}/logs", response_class=HTMLResponse)
def browser_logs(request: Request, container_id: str, tail: int = Query(200, ge=1, le=LOG_TAIL_MAX)):
    container = managed_container(container_id)
    logs = service_logs(container_id, tail)
    return templates.TemplateResponse("logs.html", {"request": request, "name": container.labels.get("shadow.lab.name", container.name), "logs": logs})
