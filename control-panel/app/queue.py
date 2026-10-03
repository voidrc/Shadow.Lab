"""Redis-backed job queue and progress channel.

The control panel enqueues scan jobs; workers dequeue and execute them.
Progress updates are published to a pub/sub channel for live dashboard updates.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)


def _redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_scan(scan_id: str, payload: dict) -> None:
    """Add a scan job to the queue."""
    r = _redis()
    r.rpush(settings.queue_name, json.dumps({"scan_id": scan_id, **payload}))
    logger.info("Enqueued scan %s", scan_id)


def dequeue_scan(timeout: int = 5) -> dict | None:
    """Block up to *timeout* seconds waiting for a scan job.  Returns None on timeout."""
    r = _redis()
    result = r.blpop(settings.queue_name, timeout=timeout)
    if result is None:
        return None
    _queue, raw = result
    return json.loads(raw)


def cancel_scan(scan_id: str) -> None:
    """Publish a cancellation signal for *scan_id*."""
    publish("scan.cancel", scan_id, scan_id=scan_id)


def publish(event_type: str, scan_id: str | None = None, **data: Any) -> None:
    """Publish a progress / event message to the pub/sub channel."""
    r = _redis()
    msg = json.dumps({"event": event_type, "scan_id": scan_id, "data": data})
    r.publish(settings.progress_channel, msg)


def read_events(channel: str | None = None):
    """Generator that yields events from the pub/sub channel."""
    r = _redis()
    pubsub = r.pubsub()
    pubsub.subscribe(channel or settings.progress_channel)
    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        pubsub.close()


def is_cancelled(scan_id: str) -> bool:
    """Check whether a cancellation signal has been published for *scan_id*.

    Uses a simple key with TTL so cancellation is persistent across worker polls.
    """
    r = _redis()
    return r.exists(f"scan:cancel:{scan_id}") > 0


def set_cancelled(scan_id: str) -> None:
    r = _redis()
    r.setex(f"scan:cancel:{scan_id}", 3600, "1")
    cancel_scan(scan_id)


def clear_cancelled(scan_id: str) -> None:
    r = _redis()
    r.delete(f"scan:cancel:{scan_id}")
