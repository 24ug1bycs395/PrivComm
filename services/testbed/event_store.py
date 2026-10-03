"""
Transient in-memory event store for live testbed execution events.

Events are NOT persisted to disk or Supabase — they exist only while
the process is running and are consumed by the frontend via polling.
Each job maintains a capped ring-buffer (max 200 events) so long-running
traffic profiles never cause unbounded memory growth.
"""

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

_lock = threading.Lock()
# Map of job_id -> deque of event dicts (max 200 per job)
_job_events: Dict[str, Deque[Dict[str, Any]]] = {}
_event_counters: Dict[str, int] = {}

MAX_EVENTS_PER_JOB = 200


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def init_job(job_id: str) -> None:
    """Initialize the event buffer for a new job."""
    with _lock:
        _job_events[job_id] = deque(maxlen=MAX_EVENTS_PER_JOB)
        _event_counters[job_id] = 0


def emit(job_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append a structured event to the job's in-memory buffer.
    Automatically assigns id and timestamp if not present.
    Returns the event dict (with id/timestamp filled in).
    """
    with _lock:
        if job_id not in _job_events:
            _job_events[job_id] = deque(maxlen=MAX_EVENTS_PER_JOB)
            _event_counters[job_id] = 0

        _event_counters[job_id] += 1
        event.setdefault("id", _event_counters[job_id])
        event.setdefault("timestamp", _ts())
        _job_events[job_id].append(event)
    return event


def get_events(job_id: str, since_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Return events for a job, optionally filtered to only events after since_id.
    Returns a plain list (copy) so callers can safely serialise it.
    """
    with _lock:
        events = list(_job_events.get(job_id, []))

    if since_id is not None:
        events = [e for e in events if e.get("id", 0) > since_id]
    return events


def clear_job(job_id: str) -> None:
    """Remove a job's event buffer (optional cleanup after completion)."""
    with _lock:
        _job_events.pop(job_id, None)
        _event_counters.pop(job_id, None)
