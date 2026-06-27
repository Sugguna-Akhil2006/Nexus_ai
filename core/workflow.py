import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
from typing import Any, Dict, List, Optional, Union
import uuid

from core.event import Event, EventBus, EventType
from core.exceptions import WorkflowException
from core.executor import Executor
from core.logger import StructuredLogger
from core.planner import ExecutionPlan
from core.result import Result


class WorkflowValidationError(WorkflowException):
    """Raised when workflow validation or graph validation fails."""
    pass


class WorkflowNotFoundError(WorkflowException):
    """Raised when the requested workflow cannot be found."""
    pass


class WorkflowStatus(Enum):
    """Execution states representing Workflow orchestrator progression."""
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class WorkflowNode:
    """Represents a discrete step/node within the Workflow graph.

    Attributes:
        node_id: Unique string identifying the node.
        execution_plan: The plan details associated with this step.
        dependencies: Dependencies (node IDs) this step depends on.
        metadata: Node metadata details.
    """
    node_id: str
    execution_plan: ExecutionPlan
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowEdge:
    """Represents a directed link modeling execution constraints.

    Attributes:
        source_node: Target source node ID.
        target_node: Target node ID dependant on the source.
        edge_type: Classification categorization.
    """
    source_node: str
    target_node: str
    edge_type: str = "DEFAULT"


@dataclass
class Workflow:
    """Encapsulates nodes, edges, states and identities.

    Attributes:
        workflow_id: Unique UUID identifier.
        name: Common workflow name descriptor.
        description: Informational textual description.
        created_at: Instant timestamp when workflow was constructed.
        nodes: Map of node IDs to Node definitions.
        edges: List of Edges configuring node links.
        status: Current workflow status.
        metadata: Workflow metadata details.
    """
    workflow_id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    nodes: Dict[str, WorkflowNode]
    edges: List[WorkflowEdge]
    status: WorkflowStatus = WorkflowStatus.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowResult:
    """Consolidated execution context output metrics.

    Attributes:
        workflow_id: Associated Workflow UUID.
        node_results: Map of node IDs to execution outcomes.
        overall_status: Ending workflow status.
        started_at: Workflow execution start timestamp.
        completed_at: Workflow execution end timestamp.
        execution_metrics: Workflow-wide consolidated execution statistics.
    """
    workflow_id: uuid.UUID
    node_results: Dict[str, Result]
    overall_status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    execution_metrics: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """Thread-safe Singleton engine coordinating Workflow DAG executions."""
    _instance: Optional["WorkflowEngine"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "WorkflowEngine":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self.logger = StructuredLogger()
            self.event_bus = EventBus()
            self._workflows: Dict[uuid.UUID, Workflow] = {}
            self._workflow_statuses: Dict[uuid.UUID, WorkflowStatus] = {}
            self._definitions: Dict[str, Dict[str, Any]] = {}
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def create_workflow(
        self,
        name: str,
        description: str,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """Constructs and registers a new Workflow instance.

        Args:
            name: Workflow name.
            description: Workflow description.
            nodes: Nodes list.
            edges: Graph edges.
            metadata: Metadata mapping.

        Returns:
            Workflow: Created workflow object.
        """
        # Node duplication validation
        seen_ids = set()
        for node in nodes:
            if node.node_id in seen_ids:
                raise WorkflowValidationError(f"Duplicate node ID detected: '{node.node_id}'")
            seen_ids.add(node.node_id)

        node_map = {n.node_id: n for n in nodes}
        workflow_id = uuid.uuid4()
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            nodes=node_map,
            edges=edges,
            status=WorkflowStatus.CREATED,
            metadata=metadata.copy() if metadata else {}
        )

        self.validate(workflow)

        with self._lock:
            self._workflows[workflow_id] = workflow
            self._workflow_statuses[workflow_id] = WorkflowStatus.CREATED

        self._publish_event("workflow.created", workflow_id)
        self.logger.info(f"Workflow created. ID: {workflow_id}. Name: {name}")
        return workflow

    def register_definition(
        self,
        name: str,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registers a workflow schema for reuse.

        Args:
            name: Definition identifier.
            nodes: Definitions nodes.
            edges: Definition edges.
            description: Description.
            metadata: Optional metadata.
        """
        with self._lock:
            self._definitions[name] = {
                "nodes": nodes,
                "edges": edges,
                "description": description,
                "metadata": metadata or {}
            }

    def list_workflows(self) -> List[Workflow]:
        """Lists all workflow instances managed by the engine.

        Returns:
            List[Workflow]: List of Workflows.
        """
        with self._lock:
            return list(self._workflows.values())

    def status(self, workflow_id: Union[uuid.UUID, str]) -> WorkflowStatus:
        """Retrieves active workflow status.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            WorkflowStatus: The workflow status.
        """
        w_id = uuid.UUID(str(workflow_id)) if not isinstance(workflow_id, uuid.UUID) else workflow_id
        with self._lock:
            if w_id not in self._workflow_statuses:
                raise WorkflowNotFoundError(f"Workflow ID '{w_id}' not found.")
            return self._workflow_statuses[w_id]

    def pause(self, workflow_id: Union[uuid.UUID, str]) -> bool:
        """Pauses a running workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            bool: True if status updated, False otherwise.
        """
        w_id = uuid.UUID(str(workflow_id)) if not isinstance(workflow_id, uuid.UUID) else workflow_id
        with self._lock:
            if w_id not in self._workflow_statuses:
                return False
            if self._workflow_statuses[w_id] != WorkflowStatus.RUNNING:
                return False
            self._workflow_statuses[w_id] = WorkflowStatus.PAUSED
            self._workflows[w_id].status = WorkflowStatus.PAUSED
            self._publish_event("workflow.paused", w_id)
            self.logger.info(f"Workflow paused. ID: {w_id}")
            return True

    def resume(self, workflow_id: Union[uuid.UUID, str]) -> bool:
        """Resumes a paused workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            bool: True if status updated, False otherwise.
        """
        w_id = uuid.UUID(str(workflow_id)) if not isinstance(workflow_id, uuid.UUID) else workflow_id
        with self._lock:
            if w_id not in self._workflow_statuses:
                return False
            if self._workflow_statuses[w_id] != WorkflowStatus.PAUSED:
                return False
            self._workflow_statuses[w_id] = WorkflowStatus.RUNNING
            self._workflows[w_id].status = WorkflowStatus.RUNNING
            self._publish_event("workflow.resumed", w_id)
            self.logger.info(f"Workflow resumed. ID: {w_id}")
            return True

    def cancel(self, workflow_id: Union[uuid.UUID, str]) -> bool:
        """Cancels a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            bool: True if cancellation succeeded.
        """
        w_id = uuid.UUID(str(workflow_id)) if not isinstance(workflow_id, uuid.UUID) else workflow_id
        with self._lock:
            if w_id not in self._workflow_statuses:
                return False
            current = self._workflow_statuses[w_id]
            if current in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
                return False
            self._workflow_statuses[w_id] = WorkflowStatus.CANCELLED
            self._workflows[w_id].status = WorkflowStatus.CANCELLED
            self._publish_event("workflow.cancelled", w_id)
            self.logger.warning(f"Workflow cancelled. ID: {w_id}")
            return True

    def validate(self, workflow: Workflow) -> None:
        """Validates workflow graph for cycles, orphan nodes, and missing dependencies.

        Args:
            workflow: The Workflow to validate.

        Raises:
            WorkflowValidationError: If validations fail.
        """
        if not workflow.nodes:
            raise WorkflowValidationError("Workflow must contain at least one node.")

        # Check missing dependencies
        for nid, node in workflow.nodes.items():
            for dep in node.dependencies:
                if dep not in workflow.nodes:
                    raise WorkflowValidationError(
                        f"Missing dependency: Node '{nid}' depends on non-existent node '{dep}'"
                    )

        for edge in workflow.edges:
            if edge.source_node not in workflow.nodes:
                raise WorkflowValidationError(f"Edge source '{edge.source_node}' does not exist.")
            if edge.target_node not in workflow.nodes:
                raise WorkflowValidationError(f"Edge target '{edge.target_node}' does not exist.")

        # Build adjacency list
        adj = {nid: [] for nid in workflow.nodes}
        for edge in workflow.edges:
            adj[edge.source_node].append(edge.target_node)
        for nid, node in workflow.nodes.items():
            for dep in node.dependencies:
                adj[dep].append(nid)

        # Circular dependency DFS check
        visited = {}

        def has_cycle(curr: str) -> bool:
            visited[curr] = 1  # visiting
            for neighbor in adj[curr]:
                if visited.get(neighbor) == 1:
                    return True
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
            visited[curr] = 2  # visited
            return False

        for nid in workflow.nodes:
            if nid not in visited:
                if has_cycle(nid):
                    raise WorkflowValidationError("Circular dependency detected in graph.")

        # Orphan nodes verification
        connected = set()
        for edge in workflow.edges:
            connected.add(edge.source_node)
            connected.add(edge.target_node)
        for nid, node in workflow.nodes.items():
            for dep in node.dependencies:
                connected.add(dep)
                connected.add(nid)

        if len(workflow.nodes) > 1:
            for nid in workflow.nodes:
                if nid not in connected:
                    raise WorkflowValidationError(f"Orphan node detected: '{nid}' has no connections.")

    def execute(self, workflow: Workflow) -> WorkflowResult:
        """Executes a workflow graph concurrently delegating to the Executor.

        Args:
            workflow: The Workflow.

        Returns:
            WorkflowResult: Result metrics.
        """
        self.validate(workflow)
        started_at = datetime.utcnow()
        w_id = workflow.workflow_id

        with self._lock:
            self._workflow_statuses[w_id] = WorkflowStatus.RUNNING
            workflow.status = WorkflowStatus.RUNNING

        self._publish_event("workflow.started", w_id)
        self.logger.info(f"Workflow execution started. ID: {w_id}")

        node_statuses = {nid: "PENDING" for nid in workflow.nodes}
        node_results: Dict[str, Result] = {}
        active_futures = {}

        executor = Executor()

        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                # Intercept pause or cancel
                with self._lock:
                    current_status = self._workflow_statuses[w_id]
                    if current_status == WorkflowStatus.CANCELLED:
                        self._cancel_remaining_nodes(node_statuses, node_results)
                        break

                    if current_status == WorkflowStatus.PAUSED:
                        # Release lock, sleep, re-acquire lock
                        self._lock.release()
                        time.sleep(0.1)
                        self._lock.acquire()
                        continue

                # Identify eligible nodes
                eligible_nodes = []
                for nid, node in workflow.nodes.items():
                    if node_statuses[nid] == "PENDING":
                        # Check dependencies success
                        dependencies_met = True
                        for dep in node.dependencies:
                            if node_statuses[dep] != "SUCCESS":
                                dependencies_met = False
                                break
                        if dependencies_met:
                            # Also check edges where target_node matches nid
                            for edge in workflow.edges:
                                if edge.target_node == nid and node_statuses[edge.source_node] != "SUCCESS":
                                    dependencies_met = False
                                    break
                        if dependencies_met:
                            eligible_nodes.append(node)

                # Submit eligible nodes to the pool
                for node in eligible_nodes:
                    node_statuses[node.node_id] = "RUNNING"
                    future = pool.submit(executor.execute, node.execution_plan)
                    active_futures[future] = node.node_id

                # If nothing running and no nodes eligible, check if done
                if not active_futures:
                    has_pending = any(s == "PENDING" for s in node_statuses.values())
                    if has_pending:
                        # Deadlock or failed dependencies prevent execution completion
                        for nid in node_statuses:
                            if node_statuses[nid] in ("PENDING", "RUNNING"):
                                node_statuses[nid] = "FAILED"
                        break
                    else:
                        break

                # Wait for any to complete
                done, _ = concurrent.futures.wait(
                    active_futures.keys(),
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    nid = active_futures.pop(future)
                    try:
                        result = future.result()
                        node_results[nid] = result
                        if result.is_success():
                            node_statuses[nid] = "SUCCESS"
                        else:
                            node_statuses[nid] = "FAILED"
                    except Exception as e:
                        node_statuses[nid] = "FAILED"
                        node_results[nid] = Result.failure(errors=[str(e)])

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        # Resolve overall status
        with self._lock:
            current_status = self._workflow_statuses[w_id]
            if current_status != WorkflowStatus.CANCELLED:
                all_success = all(s == "SUCCESS" for s in node_statuses.values())
                final_status = WorkflowStatus.COMPLETED if all_success else WorkflowStatus.FAILED
                self._workflow_statuses[w_id] = final_status
                workflow.status = final_status
            else:
                final_status = WorkflowStatus.CANCELLED

        # Fire lifecycle events
        if final_status == WorkflowStatus.COMPLETED:
            self._publish_event("workflow.completed", w_id)
            self.logger.info(f"Workflow completed successfully. ID: {w_id}")
        elif final_status == WorkflowStatus.FAILED:
            self._publish_event("workflow.failed", w_id)
            self.logger.error(f"Workflow execution failed. ID: {w_id}")
        else:
            self._publish_event("workflow.cancelled", w_id)

        metrics = {
            "duration": duration,
            "total_nodes": len(workflow.nodes),
            "completed_nodes": sum(1 for s in node_statuses.values() if s == "SUCCESS")
        }

        return WorkflowResult(
            workflow_id=w_id,
            node_results=node_results,
            overall_status=final_status,
            started_at=started_at,
            completed_at=completed_at,
            execution_metrics=metrics
        )

    def _cancel_remaining_nodes(self, node_statuses: Dict[str, str], node_results: Dict[str, Result]) -> None:
        for nid in node_statuses:
            if node_statuses[nid] in ("PENDING", "RUNNING"):
                node_statuses[nid] = "CANCELLED"
                node_results[nid] = Result.cancel()

    def _publish_event(self, event_name: str, workflow_id: uuid.UUID) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkflowEngine",
            payload={"event_name": event_name, "workflow_id": str(workflow_id)}
        )
        self.event_bus.publish(event)
