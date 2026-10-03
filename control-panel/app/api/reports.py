"""Reports API — generate Markdown, JSON, and HTML reports."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scan
from app.reports import generate_html_report, generate_json_report, generate_markdown_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{scan_id}")
def get_report(
    scan_id: str,
    format: str = Query("json", pattern="^(json|markdown|html)$"),
    db: Session = Depends(get_db),
):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "Scan not found")

    if format == "json":
        report = generate_json_report(db, scan_id)
        return Response(
            content=json.dumps(report, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={scan_id}.json"},
        )
    elif format == "markdown":
        md = generate_markdown_report(db, scan_id)
        return PlainTextResponse(
            md,
            headers={"Content-Disposition": f"attachment; filename={scan_id}.md"},
        )
    elif format == "html":
        html = generate_html_report(db, scan_id)
        return HTMLResponse(
            html,
            headers={"Content-Disposition": f"attachment; filename={scan_id}.html"},
        )
    raise HTTPException(400, f"Unknown format '{format}'")
