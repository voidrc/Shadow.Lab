"""Event system for scan lifecycle notifications.

Initially logs all events.  Designed so email/Discord/Slack/webhook sinks can
be added later by registering additional handlers.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[["Event"], None]


@dataclass
class Event:
    type: str
    scan_id: str | None = None
    payload: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_json(self) -> str:
        return json.dumps(asdict(self))


_handlers: list[EventHandler] = []


def register_handler(handler: EventHandler) -> None:
    _handlers.append(handler)


def emit(event_type: str, scan_id: str | None = None, **payload) -> Event:
    event = Event(type=event_type, scan_id=scan_id, payload=payload)
    for handler in _handlers:
        try:
            handler(event)
        except Exception:
            logger.exception("Event handler failed for %s", event_type)
    return event


def _log_handler(event: Event) -> None:
    logger.info("EVENT %s scan=%s %s", event.type, event.scan_id, event.payload)


register_handler(_log_handler)
