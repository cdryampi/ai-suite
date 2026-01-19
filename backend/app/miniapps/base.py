"""
Base classes for mini apps (AI-powered workflow applications).

Mini apps define deterministic workflows that combine tools, LLM prompts,
and business logic to accomplish specific tasks. Each mini app:

1. Defines input/output schemas
2. Implements a workflow using the Planner and tools
3. Generates artifacts (text, images, JSON, etc.)
4. Logs its execution for auditability

Example:
    class MyMiniApp(BaseMiniApp):
        def run(self, input_data, variant, options):
            # Use planner, call tools, return results
            pass
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class MiniAppMetadata:
    """Metadata describing a mini app."""

    id: str
    """Unique identifier (e.g., 'realestate_ads')"""

    name: str
    """Human-readable name (e.g., 'Real Estate Ad Generator')"""

    description: str
    """Brief description of what the mini app does"""

    version: str = "1.0.0"
    """Semantic version"""

    author: str = "AI Suite"
    """Author or organization"""

    tags: List[str] = field(default_factory=list)
    """Tags for categorization (e.g., ['marketing', 'real-estate'])"""

    variants: Dict[int, str] = field(default_factory=dict)
    """Available variants (e.g., {1: 'Basic', 2: 'Detailed', 3: 'SEO-optimized'})"""


@dataclass
class MiniAppResult:
    """Result of a mini app execution."""

    status: str
    """Status: 'ok' or 'error'"""

    logs: List[str] = field(default_factory=list)
    """Execution logs (chronological)"""

    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    """Generated artifacts (text, image, json, etc.)"""

    result: Dict[str, Any] = field(default_factory=dict)
    """Structured result data"""

    error: Optional[str] = None
    """Error message if status is 'error'"""

    execution_time: Optional[float] = None
    """Execution time in seconds"""

    started_at: Optional[datetime] = None
    """Timestamp when execution started"""

    completed_at: Optional[datetime] = None
    """Timestamp when execution completed"""


class BaseMiniApp(ABC):
    """
    Abstract base class for all mini apps.

    A mini app is a self-contained workflow that uses the AI Suite's
    orchestration capabilities to accomplish a specific task.

    Subclasses must:
    1. Define metadata via get_metadata()
    2. Implement the run() method
    3. Use the provided components (job_store, llm_client, tool_registry)

    The BaseMiniApp handles:
    - Job creation and tracking
    - Logging
    - Artifact management
    - Error handling
    """

    def __init__(self, job_store, llm_client, tool_registry, artifact_manager):
        """
        Initialize the mini app with core components.

        Args:
            job_store: JobStore instance for job tracking
            llm_client: LLMClient instance for LLM interactions
            tool_registry: ToolRegistry instance for tool access
            artifact_manager: ArtifactManager instance for artifact storage
        """
        self.job_store = job_store
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.artifact_manager = artifact_manager
        self._metadata = self.get_metadata()

    @abstractmethod
    def get_metadata(self) -> MiniAppMetadata:
        """
        Return metadata describing this mini app.

        Returns:
            MiniAppMetadata instance with id, name, description, etc.
        """
        pass

    @abstractmethod
    def run(
        self,
        input_data: str,
        variant: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> MiniAppResult:
        """
        Execute the mini app workflow.

        This is the main entry point for the mini app. Implementations should:
        1. Validate inputs
        2. Create a job in the job_store
        3. Execute the workflow (call tools, use LLM, etc.)
        4. Generate artifacts
        5. Return a MiniAppResult

        Args:
            input_data: Input data (format defined by the mini app)
            variant: Workflow variant (e.g., 1=basic, 2=detailed)
            options: Additional options (mini-app specific)

        Returns:
            MiniAppResult with status, logs, artifacts, and result data
        """
        pass

    @property
    def metadata(self) -> MiniAppMetadata:
        """Get the mini app's metadata."""
        return self._metadata

    def _log(self, job_id: str, message: str) -> None:
        """
        Add a log entry to the job.

        Args:
            job_id: The job ID to log to
            message: Log message
        """
        job = self.job_store.get(job_id)
        if job:
            job.logs.append(f"[{datetime.now().isoformat()}] {message}")
            self.job_store.update(job_id, job)

    def _validate_variant(self, variant: int) -> None:
        """
        Validate that the requested variant is supported.

        Args:
            variant: Variant number

        Raises:
            ValueError: If variant is not supported
        """
        if variant not in self._metadata.variants:
            raise ValueError(
                f"Variant {variant} not supported. "
                f"Available variants: {list(self._metadata.variants.keys())}"
            )

    def _create_result(
        self,
        status: str,
        logs: List[str],
        artifacts: List[Dict[str, Any]],
        result: Dict[str, Any],
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> MiniAppResult:
        """
        Helper to create a MiniAppResult.

        Args:
            status: 'ok' or 'error'
            logs: List of log messages
            artifacts: List of artifact dicts
            result: Result data dict
            error: Error message (if any)
            execution_time: Execution time in seconds
            started_at: Start timestamp
            completed_at: Completion timestamp

        Returns:
            MiniAppResult instance
        """
        return MiniAppResult(
            status=status,
            logs=logs,
            artifacts=artifacts,
            result=result,
            error=error,
            execution_time=execution_time,
            started_at=started_at,
            completed_at=completed_at,
        )
