"""Sync Engine directing manual and incremental sync schedules."""

from __future__ import annotations

from datetime import datetime
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.connectors.models import ConnectorConfig, SyncJob
from backend.connectors.connection_pool import ConnectionPool


class SyncEngine:
    """Manages data synchronizations and checkpoint state boundaries."""

    def __init__(self, pool: Optional[ConnectionPool] = None) -> None:
        self.pool = pool or ConnectionPool()
        self._event_bus = EventBus()
        self._jobs: Dict[str, SyncJob] = {}
        self._lock = threading.Lock()

    def trigger_sync(self, config: ConnectorConfig, checkpoint: Optional[Dict[str, Any]] = None) -> SyncJob:
        """Launches sync process execution."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = SyncJob(
            job_id=job_id,
            connector_id=config.connector_id,
            status="running",
            start_time=datetime.utcnow(),
            checkpoint_state=checkpoint or {}
        )

        with self._lock:
            self._jobs[job_id] = job

        # Emit sync started event
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="SyncEngine",
            payload={"event": "sync.started", "connector_id": config.connector_id, "job_id": job_id}
        ))

        try:
            conn = self.pool.get_connection(config)
            items = conn.sync_data(job.checkpoint_state)
            
            job.records_processed = len(items)
            job.status = "completed"
            job.end_time = datetime.utcnow()
            
            # Save checkpoint state increment
            job.checkpoint_state["last_timestamp"] = job.end_time.isoformat()

            # Emit sync completed event
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="SyncEngine",
                payload={
                    "event": "sync.completed",
                    "connector_id": config.connector_id,
                    "job_id": job_id,
                    "records_processed": job.records_processed
                }
            ))

        except Exception as e:
            job.status = "failed"
            job.end_time = datetime.utcnow()
            job.error_message = str(e)

            # Emit sync failed event
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="SyncEngine",
                payload={
                    "event": "sync.failed",
                    "connector_id": config.connector_id,
                    "job_id": job_id,
                    "error": str(e)
                }
            ))

        return job

    def get_job(self, job_id: str) -> Optional[SyncJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[SyncJob]:
        with self._lock:
            return list(self._jobs.values())
