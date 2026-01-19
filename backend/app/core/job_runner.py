"""
Job Runner - Executes mini app workflows in background threads.

The job runner manages:
- Thread pool for concurrent execution
- Job lifecycle management
- Workflow step execution
- Error handling and recovery
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from typing import Callable, Optional
import logging
import traceback

from config.settings import JobSettings
from app.core.job_store import Job, JobStore, JobStatus
from app.core.llm_client import LLMClient
from app.core.tool_registry import ToolRegistry


logger = logging.getLogger(__name__)


class JobRunner:
    """
    Background job execution manager.

    Handles execution of mini app workflows in background threads,
    managing the job lifecycle from pending to completion/failure.
    """

    def __init__(
        self,
        job_store: JobStore,
        tool_registry: ToolRegistry,
        llm_client: LLMClient,
        settings: JobSettings,
    ):
        """
        Initialize the job runner.

        Args:
            job_store: Job storage backend
            tool_registry: Available tool registry
            llm_client: LLM client for generation
            settings: Job runner configuration
        """
        self.job_store = job_store
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        self.settings = settings

        self._executor = ThreadPoolExecutor(max_workers=settings.max_concurrent)
        self._cancellation_events: dict[str, Event] = {}

    def submit(
        self, job: Job, workflow_executor: Callable[[Job, Callable[[str], None]], dict]
    ) -> str:
        """
        Submit a job for execution.

        Args:
            job: The job to execute
            workflow_executor: Callable that executes the workflow

        Returns:
            str: The job ID
        """
        # Create cancellation event for this job
        cancel_event = Event()
        self._cancellation_events[job.job_id] = cancel_event

        # Submit to thread pool
        self._executor.submit(self._execute_job, job, workflow_executor, cancel_event)

        return job.job_id

    def _execute_job(
        self, job: Job, workflow_executor: Callable, cancel_event: Event
    ) -> None:
        """
        Execute a job in a background thread.

        Args:
            job: The job to execute
            workflow_executor: Callable that executes the workflow
            cancel_event: Event to signal cancellation
        """
        try:
            # Update status to running
            job.status = JobStatus.RUNNING
            job.add_log(f"Starting workflow: {job.miniapp_id}")
            self.job_store.update(job)

            # Define log callback
            def on_log(message: str):
                if cancel_event.is_set():
                    raise InterruptedError("Job cancelled")
                job.add_log(message)
                self.job_store.update(job)

            # Execute the workflow
            result = workflow_executor(job, on_log)

            # Check for cancellation
            if cancel_event.is_set():
                job.cancel()
            else:
                job.complete(result)
                job.add_log("Workflow complete")

        except InterruptedError:
            job.cancel()

        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            logger.debug(traceback.format_exc())
            job.fail(str(e))

        finally:
            # Update final state
            self.job_store.update(job)

            # Cleanup cancellation event
            if job.job_id in self._cancellation_events:
                del self._cancellation_events[job.job_id]

    def cancel(self, job_id: str) -> bool:
        """
        Request cancellation of a running job.

        Args:
            job_id: The job identifier

        Returns:
            bool: True if cancellation was requested

        Raises:
            ValueError: If job is not running
        """
        job = self.job_store.get(job_id)

        if not job:
            raise ValueError(f"Job '{job_id}' not found")

        if job.status != JobStatus.RUNNING:
            raise ValueError(
                f"Job '{job_id}' is not running (status: {job.status.value})"
            )

        if job_id in self._cancellation_events:
            self._cancellation_events[job_id].set()
            return True

        return False

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the job runner.

        Args:
            wait: Whether to wait for running jobs to complete
        """
        # Signal all jobs to cancel
        for event in self._cancellation_events.values():
            event.set()

        # Shutdown executor
        self._executor.shutdown(wait=wait)
