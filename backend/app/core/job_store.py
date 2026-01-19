"""
Job Store - In-memory job storage and management.

Provides thread-safe storage for job state, logs, and artifacts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Optional
from uuid import uuid4


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Artifact:
    """
    Output artifact from a job.

    Attributes:
        type: Artifact type (text, image, video, json)
        label: Human-readable label
        path: File path relative to outputs directory
        preview: Optional preview text for text artifacts
    """

    type: str
    label: str
    path: str
    preview: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        d = {"type": self.type, "label": self.label, "path": self.path}
        if self.preview:
            d["preview"] = self.preview
        return d


@dataclass
class Job:
    """
    Job execution record.

    Attributes:
        job_id: Unique job identifier
        miniapp_id: Mini app that created this job
        status: Current execution status
        progress: Execution progress (0.0 to 1.0)
        current_step: Current step being executed
        logs: Execution log messages
        artifacts: Output artifacts
        result: Final result data
        error: Error message if failed
        created_at: Job creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp
    """

    job_id: str
    miniapp_id: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    current_step: Optional[str] = None
    logs: list[str] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    result: Optional[dict] = None
    error: Optional[str] = None
    input_data: Optional[dict] = None
    variant: int = 1
    options: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        self.updated_at = datetime.utcnow()

    def add_artifact(self, artifact: Artifact) -> None:
        """Add an output artifact."""
        self.artifacts.append(artifact)
        self.updated_at = datetime.utcnow()

    def set_progress(self, progress: float, step: Optional[str] = None) -> None:
        """Update job progress."""
        self.progress = min(1.0, max(0.0, progress))
        if step:
            self.current_step = step
        self.updated_at = datetime.utcnow()

    def complete(self, result: dict) -> None:
        """Mark job as complete."""
        self.status = JobStatus.COMPLETE
        self.result = result
        self.progress = 1.0
        self.current_step = None
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error = error
        self.current_step = None
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.add_log(f"ERROR: {error}")

    def cancel(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.current_step = None
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.add_log("Job cancelled by user")

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        d = {
            "job_id": self.job_id,
            "miniapp_id": self.miniapp_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "logs": self.logs,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.completed_at:
            d["completed_at"] = self.completed_at.isoformat()

        return d


class JobStore:
    """
    Thread-safe in-memory job storage.

    Provides CRUD operations for job records with thread safety.
    """

    def __init__(self):
        """Initialize the job store."""
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def create(
        self,
        miniapp_id: str,
        input_data: dict,
        variant: int = 1,
        options: Optional[dict] = None,
    ) -> Job:
        """
        Create a new job.

        Args:
            miniapp_id: ID of the mini app
            input_data: Input data for the job
            variant: Workflow variant
            options: Additional options

        Returns:
            Job: The created job
        """
        job_id = f"job_{uuid4().hex[:12]}"

        job = Job(
            job_id=job_id,
            miniapp_id=miniapp_id,
            input_data=input_data,
            variant=variant,
            options=options,
        )

        with self._lock:
            self._jobs[job_id] = job

        return job

    def get(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.

        Args:
            job_id: The job identifier

        Returns:
            Job or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> None:
        """
        Update a job in the store.

        Args:
            job: The job to update
        """
        with self._lock:
            if job.job_id in self._jobs:
                self._jobs[job.job_id] = job

    def list_all(self, miniapp_id: Optional[str] = None) -> list[Job]:
        """
        List all jobs, optionally filtered by mini app.

        Args:
            miniapp_id: Optional filter by mini app ID

        Returns:
            list[Job]: List of jobs
        """
        with self._lock:
            jobs = list(self._jobs.values())

        if miniapp_id:
            jobs = [j for j in jobs if j.miniapp_id == miniapp_id]

        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def delete(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: The job identifier

        Returns:
            bool: True if deleted, False if not found
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    def cleanup_old(self, max_age_hours: int = 24) -> int:
        """
        Remove jobs older than max_age_hours.

        Args:
            max_age_hours: Maximum job age in hours

        Returns:
            int: Number of jobs removed
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        with self._lock:
            to_remove = [
                job_id
                for job_id, job in self._jobs.items()
                if job.created_at < cutoff and job.status != JobStatus.RUNNING
            ]

            for job_id in to_remove:
                del self._jobs[job_id]
                removed += 1

        return removed
