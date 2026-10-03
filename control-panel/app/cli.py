"""shadow — command-line interface for the shadow.lab scanner platform.

Uses the same backend API as the dashboard so there is one implementation
of scan logic.

Usage:
    shadow scan --scope 10.10.20.0/24 --profile safe
    shadow scan list
    shadow scan show scan-2026-000042
    shadow scan cancel scan-2026-000042
    shadow findings list
    shadow findings show <id>
    shadow findings status <id> --status CONFIRMED
    shadow report generate <scan-id> --format markdown
    shadow hosts list
"""
from __future__ import annotations

import argparse
import json
import sys

import httpx

from app.config import settings


def _api(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{settings.control_panel_url}{path}"
    headers = kwargs.pop("headers", {})
    if settings.control_panel_token:
        headers["Authorization"] = f"Bearer {settings.control_panel_token}"
    with httpx.Client(timeout=30) as client:
        return client.request(method, url, headers=headers, **kwargs)


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, default=str))


# ── scan subcommands ──────────────────────────────────────────────────────────

def cmd_scan_create(args):
    resp = _api("POST", "/api/scans/validate-scope", json={
        "scope": args.scope,
        "profile": args.profile,
        "name": args.name,
    })
    data = resp.json()
    if not data.get("valid"):
        print(f"Scope rejected: {data.get('error', 'unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"Authorized scope: {', '.join(data['cidrs'])}")
    print(f"  {data['address_count']} addresses")

    if not args.yes:
        answer = input("\nStart scan with this scope? [y/N] ")
        if answer.lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    body = {
        "scope_id": data["scope_id"],
        "profile": args.profile,
        "name": args.name,
    }
    if args.worker:
        body["worker"] = args.worker
    if args.concurrency:
        body["max_concurrency"] = args.concurrency
    if args.rps:
        body["requests_per_second"] = args.rps

    resp = _api("POST", "/api/scans", json=body)
    if resp.status_code != 201:
        print(f"Failed to create scan: {resp.text}", file=sys.stderr)
        sys.exit(1)
    scan = resp.json()
    print(f"\nScan created: {scan['id']}")
    print(f"  Profile: {scan['profile']}")
    print(f"  Status:  {scan['status']}")
    print(f"  View:    {settings.control_panel_url}/scans/{scan['id']}")


def cmd_scan_list(args):
    resp = _api("GET", "/api/scans", params={"limit": args.limit})
    scans = resp.json()
    if not scans:
        print("No scans found.")
        return
    print(f"{'Scan ID':<22} {'Profile':<10} {'Status':<14} {'Hosts':>6} {'C':>3} {'H':>3} {'M':>3} {'L':>3} {'I':>3}  Created")
    print("-" * 100)
    for s in scans:
        print(f"{s['id']:<22} {s['profile']:<10} {s['status']:<14} {s['hosts_discovered']:>6} "
              f"{s['findings_critical']:>3} {s['findings_high']:>3} {s['findings_medium']:>3} "
              f"{s['findings_low']:>3} {s['findings_info']:>3}  {s['created_at'][:19]}")


def cmd_scan_show(args):
    resp = _api("GET", f"/api/scans/{args.scan_id}")
    if resp.status_code == 404:
        print(f"Scan {args.scan_id} not found.", file=sys.stderr)
        sys.exit(1)
    scan = resp.json()
    print(f"Scan:       {scan['id']}")
    print(f"Profile:    {scan['profile']}")
    print(f"Status:     {scan['status']}")
    print(f"Worker:     {scan.get('worker', 'N/A')}")
    if scan.get("scope"):
        print(f"Scope:      {scan['scope']['name']} ({', '.join(scan['scope']['cidrs'])})")
    print(f"Hosts:      {scan['hosts_discovered']}")
    print(f"Ports:      {scan['ports_discovered']}")
    print(f"Web targets: {scan['web_targets_discovered']}")
    print(f"Findings:   {scan['findings_critical']}C {scan['findings_high']}H "
          f"{scan['findings_medium']}M {scan['findings_low']}L {scan['findings_info']}I")
    if scan.get("stages"):
        print("\nStages:")
        for s in scan["stages"]:
            print(f"  {s['seq']}. {s['name']:<24} {s['status']}")
    if scan.get("logs"):
        print("\nLogs:")
        for l in scan["logs"][-20:]:
            ts = l["timestamp"].split("T")[1].split(".")[0] if l["timestamp"] else ""
            print(f"  [{ts}] {l['level']}: {l['message']}")


def cmd_scan_cancel(args):
    resp = _api("POST", f"/api/scans/{args.scan_id}/cancel")
    if resp.status_code == 404:
        print(f"Scan {args.scan_id} not found.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 409:
        print("Scan is already in a terminal state.", file=sys.stderr)
        sys.exit(1)
    result = resp.json()
    print(f"Scan {result['scan_id']} cancelled. Status: {result['status']}")


def cmd_scan_preflight(args):
    resp = _api("GET", f"/api/scans/preflight/{args.worker}", params={"profile": args.profile})
    if resp.status_code != 200:
        print(f"Preflight failed: {resp.text}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    if data["ok"]:
        print(f"Worker {data['worker']}: all tools available")
        for t in data["available"]:
            print(f"  [OK] {t}")
    else:
        print(f"Worker {data['worker']}: missing tools!")
        for t in data["available"]:
            print(f"  [OK] {t}")
        for t in data["missing"]:
            print(f"  [MISSING] {t}")
        print("\nInstall missing tools:")
        for inst in data["instructions"]:
            print(inst)
        sys.exit(1)


# ── findings subcommands ──────────────────────────────────────────────────────

def cmd_findings_list(args):
    params = {"limit": args.limit}
    if args.severity:
        params["severity"] = args.severity
    if args.source:
        params["source"] = args.source
    if args.status:
        params["status"] = args.status
    resp = _api("GET", "/api/findings", params=params)
    findings = resp.json()
    if not findings:
        print("No findings found.")
        return
    print(f"{'Severity':<10} {'Title':<50} {'Asset':<24} {'Source':<16} {'Status':<16}")
    print("-" * 120)
    for f in findings:
        print(f"{f['severity']:<10} {f['title'][:48]:<50} {(f['affected_asset'] or '')[:22]:<24} "
              f"{f['source']:<16} {f['status']:<16}")


def cmd_findings_show(args):
    resp = _api("GET", f"/api/findings/{args.finding_id}")
    if resp.status_code == 404:
        print(f"Finding {args.finding_id} not found.", file=sys.stderr)
        sys.exit(1)
    _print_json(resp.json())


def cmd_findings_status(args):
    body = {"status": args.status}
    if args.reason:
        body["reason"] = args.reason
    resp = _api("POST", f"/api/findings/{args.finding_id}/status", json=body)
    if resp.status_code == 404:
        print(f"Finding {args.finding_id} not found.", file=sys.stderr)
        sys.exit(1)
    result = resp.json()
    print(f"Finding {result['finding_id']}: {result.get('old_status', '?')} -> {result['status']}")


# ── report subcommands ────────────────────────────────────────────────────────

def cmd_report_generate(args):
    resp = _api("GET", f"/api/reports/{args.scan_id}", params={"format": args.format})
    if resp.status_code == 404:
        print(f"Scan {args.scan_id} not found.", file=sys.stderr)
        sys.exit(1)
    if args.output:
        with open(args.output, "w") as f:
            f.write(resp.text)
        print(f"Report written to {args.output}")
    else:
        print(resp.text)


# ── hosts subcommands ─────────────────────────────────────────────────────────

def cmd_hosts_list(args):
    resp = _api("GET", "/api/hosts", params={"limit": args.limit})
    hosts = resp.json()
    if not hosts:
        print("No hosts discovered.")
        return
    print(f"{'IP':<18} {'Hostname':<24} {'OS':<20} {'Services':>8}")
    print("-" * 72)
    for h in hosts:
        print(f"{h['ip']:<18} {(h['hostname'] or '')[:22]:<24} {(h['os_guess'] or '')[:18]:<20} {h['service_count']:>8}")


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shadow", description="shadow.lab scanner CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    scan_parser = sub.add_parser("scan", help="Scan operations")
    scan_sub = scan_parser.add_subparsers(dest="scan_command", required=True)

    p = scan_sub.add_parser("create", help="Start a new scan")
    p.add_argument("--scope", required=True, help="Authorized scope (CIDR or IP)")
    p.add_argument("--profile", default="safe", choices=["safe", "thorough", "recon"])
    p.add_argument("--name", default=None, help="Optional scan name")
    p.add_argument("--worker", default=None, help="Worker host (e.g. medusa or local)")
    p.add_argument("--concurrency", type=int, default=None, help="Max concurrency override")
    p.add_argument("--rps", type=int, default=None, help="Rate limit override")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    p.set_defaults(func=cmd_scan_create)

    p = scan_sub.add_parser("list", help="List scans")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_scan_list)

    p = scan_sub.add_parser("show", help="Show scan details")
    p.add_argument("scan_id")
    p.set_defaults(func=cmd_scan_show)

    p = scan_sub.add_parser("cancel", help="Cancel a running scan")
    p.add_argument("scan_id")
    p.set_defaults(func=cmd_scan_cancel)

    p = scan_sub.add_parser("preflight", help="Check tools on a worker")
    p.add_argument("worker", help="Worker name (local or hostname like medusa)")
    p.add_argument("--profile", default="safe", choices=["safe", "thorough", "recon"])
    p.set_defaults(func=cmd_scan_preflight)

    # findings
    findings_parser = sub.add_parser("findings", help="Finding operations")
    findings_sub = findings_parser.add_subparsers(dest="findings_command", required=True)

    p = findings_sub.add_parser("list", help="List findings")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--severity", default=None)
    p.add_argument("--source", default=None)
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_findings_list)

    p = findings_sub.add_parser("show", help="Show finding details")
    p.add_argument("finding_id")
    p.set_defaults(func=cmd_findings_show)

    p = findings_sub.add_parser("status", help="Update finding status")
    p.add_argument("finding_id")
    p.add_argument("--status", required=True, choices=["OPEN", "CONFIRMED", "FALSE_POSITIVE", "FIXED", "ACCEPTED"])
    p.add_argument("--reason", default=None)
    p.set_defaults(func=cmd_findings_status)

    # report
    report_parser = sub.add_parser("report", help="Report operations")
    report_sub = report_parser.add_subparsers(dest="report_command", required=True)

    p = report_sub.add_parser("generate", help="Generate a report")
    p.add_argument("scan_id")
    p.add_argument("--format", default="markdown", choices=["json", "markdown", "html"])
    p.add_argument("--output", "-o", default=None, help="Write to file instead of stdout")
    p.set_defaults(func=cmd_report_generate)

    # hosts
    hosts_parser = sub.add_parser("hosts", help="Host operations")
    hosts_sub = hosts_parser.add_subparsers(dest="hosts_command", required=True)

    p = hosts_sub.add_parser("list", help="List discovered hosts")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=cmd_hosts_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
