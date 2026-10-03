"""Worker process — dequeues scan jobs and runs the scan pipeline.

The worker connects to Redis for job dequeueing and cancellation signals.
It creates its own SQLite session for database access (in single-host mode)
or connects to the control panel API (in multi-host mode).

Usage:
    python -m app.worker
"""
from __future__ import annotations

import logging
import signal
import sys
import time

from app.config import settings
from app.database import SessionLocal, init_db
from app.executor import LocalExecutor, SSHExecutor
from app.models import Scan, ScanStatus, Scope as ScopeModel
from app.profiles import get_profile
from app.queue import dequeue_scan, is_cancelled, clear_cancelled
from app.scope import Scope, ScopeManager
from app.scanner.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shadow.worker")

_running = True


def _handle_signal(signum, _frame) -> None:
    global _running
    logger.info("Received signal %d — shutting down", signum)
    _running = False


def run_worker() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    init_db()
    logger.info("Worker %s started, polling queue %s", settings.worker_id, settings.queue_name)

    while _running:
        try:
            job = dequeue_scan(timeout=5)
            if job is None:
                continue
            scan_id = job["scan_id"]
            logger.info("Received scan job: %s", scan_id)
            _process_scan(scan_id)
        except Exception:
            logger.exception("Worker error")
            time.sleep(1)

    logger.info("Worker %s stopped", settings.worker_id)


def _process_scan(scan_id: str) -> None:
    session = SessionLocal()
    try:
        scan = session.get(Scan, scan_id)
        if scan is None:
            logger.error("Scan %s not found in database", scan_id)
            return

        if scan.status == ScanStatus.CANCELLED.value:
            logger.info("Scan %s was cancelled before processing", scan_id)
            return

        scope_model = session.get(ScopeModel, scan.scope_id)
        if scope_model is None:
            logger.error("Scope %s not found for scan %s", scan.scope_id, scan_id)
            scan.status = ScanStatus.FAILED.value
            scan.error = "Scope not found"
            session.commit()
            return

        scope = Scope.from_json(scope_model.cidrs)
        profile = get_profile(scan.profile)

        # Select executor: "local" or a remote host name (e.g. "medusa")
        worker_target = scan.worker or settings.worker_id
        if worker_target == "local" or worker_target == settings.worker_id:
            executor = LocalExecutor()
            logger.info("Scan %s using local executor", scan_id)
        else:
            executor = SSHExecutor(
                host=worker_target,
                user=settings.worker_remote_user,
            )
            logger.info("Scan %s using SSH executor → %s", scan_id, worker_target)

        def cancel_check() -> bool:
            if is_cancelled(scan_id):
                logger.info("Scan %s cancellation detected", scan_id)
                return True
            return False

        pipeline = Pipeline(
            session=session,
            scan=scan,
            scope=scope,
            profile=profile,
            worker_id=settings.worker_id,
            cancel_check=cancel_check,
            executor=executor,
        )
        pipeline.run()
        session.commit()
        clear_cancelled(scan_id)
        logger.info("Scan %s finished with status %s", scan_id, scan.status)

    except Exception:
        logger.exception("Failed to process scan %s", scan_id)
        session.rollback()
        try:
            scan = session.get(Scan, scan_id)
            if scan:
                scan.status = ScanStatus.FAILED.value
                session.commit()
        except Exception:
            pass
    finally:
        session.close()


if __name__ == "__main__":
    run_worker()
