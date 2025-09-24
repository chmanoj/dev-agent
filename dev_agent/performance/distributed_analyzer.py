"""Distributed analysis capabilities for enterprise-scale projects."""

from __future__ import annotations

import asyncio
import json
import logging
import multiprocessing
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..models.analysis import AnalysisResult
from ..models.project_state import ProjectState
from .performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)


@dataclass
class AnalysisTask:
    """Represents a distributed analysis task."""
    
    task_id: str
    task_type: str
    file_paths: List[str]
    parameters: Dict[str, Any]
    priority: int = 0
    dependencies: List[str] = None
    estimated_duration: float = 0.0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class WorkerNode:
    """Represents a worker node in the distributed system."""
    
    node_id: str
    host: str
    port: int
    capabilities: List[str]
    max_concurrent_tasks: int
    current_load: int = 0
    status: str = "idle"  # idle, busy, offline
    last_heartbeat: float = 0.0


@dataclass
class DistributedAnalysisResult:
    """Result from distributed analysis."""
    
    task_id: str
    node_id: str
    success: bool
    result_data: Any
    processing_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DistributedConfig:
    """Configuration for distributed analysis."""
    
    enable_distributed: bool = True
    coordinator_port: int = 8765
    worker_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    load_balancing_strategy: str = "least_loaded"  # least_loaded, round_robin, capability_based
    enable_fault_tolerance: bool = True
    result_aggregation_timeout: int = 600  # 10 minutes
    enable_task_splitting: bool = True
    min_files_per_task: int = 10
    max_files_per_task: int = 100


class DistributedAnalyzer:
    """Distributed analysis system for enterprise-scale codebases."""

    def __init__(
        self,
        base_analyzer: ICodebaseAnalyzer,
        config: Optional[DistributedConfig] = None,
        performance_optimizer: Optional[PerformanceOptimizer] = None,
    ):
        """Initialize the distributed analyzer.
        
        Args:
            base_analyzer: Base analyzer to distribute
            config: Distributed analysis configuration
            performance_optimizer: Performance optimizer instance
        """
        self.base_analyzer = base_analyzer
        self.config = config or DistributedConfig()
        self.performance_optimizer = performance_optimizer
        
        # Distributed system state
        self.coordinator_id = str(uuid.uuid4())
        self.worker_nodes: Dict[str, WorkerNode] = {}
        self.active_tasks: Dict[str, AnalysisTask] = {}
        self.completed_tasks: Dict[str, DistributedAnalysisResult] = {}
        self.task_queue: List[AnalysisTask] = []
        
        # Load balancing
        self.round_robin_index = 0
        
        # Fault tolerance
        self.failed_tasks: Dict[str, int] = {}  # task_id -> retry_count
        
        logger.info(f"DistributedAnalyzer initialized with coordinator ID: {self.coordinator_id}")

    async def analyze_distributed(
        self,
        project_path: str,
        analysis_types: List[str],
        progress_callback: Optional[callable] = None,
    ) -> AnalysisResult:
        """Perform distributed analysis of a large codebase.
        
        Args:
            project_path: Path to the project root
            analysis_types: Types of analysis to perform
            progress_callback: Progress callback function
            
        Returns:
            Aggregated analysis result
        """
        start_time = time.time()
        
        if not self.config.enable_distributed or not self.worker_nodes:
            logger.info("Distributed analysis disabled or no workers available, falling back to local")
            return await self._analyze_local(project_path, analysis_types, progress_callback)
        
        logger.info(f"Starting distributed analysis of {project_path}")
        
        try:
            # Discover and partition files
            all_files = self._discover_analysis_files(project_path)
            tasks = self._create_analysis_tasks(all_files, analysis_types)
            
            logger.info(f"Created {len(tasks)} analysis tasks for {len(all_files)} files")
            
            # Execute tasks in distributed manner
            results = await self._execute_distributed_tasks(tasks, progress_callback)
            
            # Aggregate results
            final_result = self._aggregate_results(results, project_path)
            
            processing_time = time.time() - start_time
            final_result.processing_time = processing_time
            
            logger.info(f"Distributed analysis completed in {processing_time:.2f}s")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Distributed analysis failed: {e}")
            # Fallback to local analysis
            return await self._analyze_local(project_path, analysis_types, progress_callback)

    def register_worker_node(
        self,
        host: str,
        port: int,
        capabilities: List[str],
        max_concurrent_tasks: int = 4,
    ) -> str:
        """Register a new worker node.
        
        Args:
            host: Worker host address
            port: Worker port
            capabilities: List of analysis capabilities
            max_concurrent_tasks: Maximum concurrent tasks for this worker
            
        Returns:
            Worker node ID
        """
        node_id = str(uuid.uuid4())
        
        worker = WorkerNode(
            node_id=node_id,
            host=host,
            port=port,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            last_heartbeat=time.time(),
        )
        
        self.worker_nodes[node_id] = worker
        
        logger.info(f"Registered worker node {node_id} at {host}:{port}")
        
        return node_id

    def unregister_worker_node(self, node_id: str) -> None:
        """Unregister a worker node.
        
        Args:
            node_id: Worker node ID to unregister
        """
        if node_id in self.worker_nodes:
            self.worker_nodes.pop(node_id)
            logger.info(f"Unregistered worker node {node_id}")

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get current cluster status.
        
        Returns:
            Dictionary with cluster information
        """
        total_workers = len(self.worker_nodes)
        active_workers = len([w for w in self.worker_nodes.values() if w.status != "offline"])
        total_capacity = sum(w.max_concurrent_tasks for w in self.worker_nodes.values())
        current_load = sum(w.current_load for w in self.worker_nodes.values())
        
        return {
            "coordinator_id": self.coordinator_id,
            "total_workers": total_workers,
            "active_workers": active_workers,
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization": current_load / total_capacity if total_capacity > 0 else 0.0,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
        }

    async def _execute_distributed_tasks(
        self,
        tasks: List[AnalysisTask],
        progress_callback: Optional[callable] = None,
    ) -> List[DistributedAnalysisResult]:
        """Execute analysis tasks across distributed workers."""
        self.task_queue.extend(tasks)
        results = []
        
        # Start task scheduler
        scheduler_task = asyncio.create_task(self._task_scheduler())
        
        # Wait for all tasks to complete
        total_tasks = len(tasks)
        completed_count = 0
        
        while completed_count < total_tasks:
            await asyncio.sleep(1)  # Check every second
            
            # Count completed tasks
            completed_count = len([
                task for task in tasks
                if task.task_id in self.completed_tasks
            ])
            
            # Update progress
            if progress_callback:
                progress_callback(
                    completed_count,
                    total_tasks,
                    f"Completed {completed_count}/{total_tasks} distributed tasks"
                )
            
            # Check for timeout
            if time.time() - tasks[0].estimated_duration > self.config.result_aggregation_timeout:
                logger.warning("Distributed analysis timeout reached")
                break
        
        # Stop scheduler
        scheduler_task.cancel()
        
        # Collect results
        for task in tasks:
            if task.task_id in self.completed_tasks:
                results.append(self.completed_tasks[task.task_id])
        
        return results

    async def _task_scheduler(self) -> None:
        """Task scheduler that assigns tasks to available workers."""
        while True:
            try:
                # Check for available workers and queued tasks
                if not self.task_queue:
                    await asyncio.sleep(0.1)
                    continue
                
                available_workers = self._get_available_workers()
                if not available_workers:
                    await asyncio.sleep(0.1)
                    continue
                
                # Assign tasks to workers
                for worker in available_workers:
                    if not self.task_queue:
                        break
                    
                    if worker.current_load >= worker.max_concurrent_tasks:
                        continue
                    
                    # Find suitable task for this worker
                    task = self._find_suitable_task(worker)
                    if task:
                        await self._assign_task_to_worker(task, worker)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
                await asyncio.sleep(1)

    def _get_available_workers(self) -> List[WorkerNode]:
        """Get list of available worker nodes."""
        current_time = time.time()
        available = []
        
        for worker in self.worker_nodes.values():
            # Check if worker is responsive
            if current_time - worker.last_heartbeat > self.config.worker_timeout:
                worker.status = "offline"
                continue
            
            # Check if worker has capacity
            if worker.current_load < worker.max_concurrent_tasks:
                available.append(worker)
        
        return available

    def _find_suitable_task(self, worker: WorkerNode) -> Optional[AnalysisTask]:
        """Find a suitable task for the given worker."""
        for task in self.task_queue:
            # Check if worker has required capabilities
            if task.task_type in worker.capabilities or "all" in worker.capabilities:
                # Check dependencies
                if all(dep_id in self.completed_tasks for dep_id in task.dependencies):
                    return task
        
        return None

    async def _assign_task_to_worker(self, task: AnalysisTask, worker: WorkerNode) -> None:
        """Assign a task to a worker node."""
        # Remove task from queue
        self.task_queue.remove(task)
        
        # Add to active tasks
        self.active_tasks[task.task_id] = task
        
        # Update worker load
        worker.current_load += 1
        worker.status = "busy"
        
        logger.debug(f"Assigned task {task.task_id} to worker {worker.node_id}")
        
        # Execute task on worker (simulated - in real implementation, this would be a network call)
        try:
            result = await self._execute_task_on_worker(task, worker)
            
            # Task completed successfully
            self.completed_tasks[task.task_id] = result
            self.active_tasks.pop(task.task_id, None)
            
            # Update worker load
            worker.current_load -= 1
            if worker.current_load == 0:
                worker.status = "idle"
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed on worker {worker.node_id}: {e}")
            
            # Handle task failure
            await self._handle_task_failure(task, worker, str(e))

    async def _execute_task_on_worker(
        self,
        task: AnalysisTask,
        worker: WorkerNode,
    ) -> DistributedAnalysisResult:
        """Execute a task on a worker node (simulated)."""
        start_time = time.time()
        
        # In a real implementation, this would send the task to the worker via network
        # For simulation, we'll execute locally with some delay
        
        try:
            # Simulate network delay
            await asyncio.sleep(0.1)
            
            # Execute analysis on the files
            if task.task_type == "syntax_analysis":
                result_data = await self._perform_syntax_analysis(task.file_paths)
            elif task.task_type == "semantic_analysis":
                result_data = await self._perform_semantic_analysis(task.file_paths)
            elif task.task_type == "quality_analysis":
                result_data = await self._perform_quality_analysis(task.file_paths)
            else:
                result_data = {"message": f"Unknown task type: {task.task_type}"}
            
            processing_time = time.time() - start_time
            
            return DistributedAnalysisResult(
                task_id=task.task_id,
                node_id=worker.node_id,
                success=True,
                result_data=result_data,
                processing_time=processing_time,
                metadata={"worker_host": worker.host, "worker_port": worker.port},
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return DistributedAnalysisResult(
                task_id=task.task_id,
                node_id=worker.node_id,
                success=False,
                result_data=None,
                processing_time=processing_time,
                error_message=str(e),
            )

    async def _handle_task_failure(
        self,
        task: AnalysisTask,
        worker: WorkerNode,
        error_message: str,
    ) -> None:
        """Handle task failure with retry logic."""
        # Update worker load
        worker.current_load -= 1
        if worker.current_load == 0:
            worker.status = "idle"
        
        # Remove from active tasks
        self.active_tasks.pop(task.task_id, None)
        
        # Check retry count
        retry_count = self.failed_tasks.get(task.task_id, 0)
        
        if retry_count < self.config.max_retries:
            # Retry the task
            self.failed_tasks[task.task_id] = retry_count + 1
            self.task_queue.append(task)
            
            logger.info(f"Retrying task {task.task_id} (attempt {retry_count + 1})")
        else:
            # Task failed permanently
            self.completed_tasks[task.task_id] = DistributedAnalysisResult(
                task_id=task.task_id,
                node_id=worker.node_id,
                success=False,
                result_data=None,
                processing_time=0.0,
                error_message=f"Task failed after {self.config.max_retries} retries: {error_message}",
            )
            
            logger.error(f"Task {task.task_id} failed permanently after {self.config.max_retries} retries")

    def _discover_analysis_files(self, project_path: str) -> List[str]:
        """Discover files that need analysis."""
        files = []
        project_root = Path(project_path)
        
        # Supported file extensions
        supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp'}
        
        for file_path in project_root.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix in supported_extensions and
                not any(part.startswith('.') for part in file_path.parts)):
                files.append(str(file_path))
        
        return files

    def _create_analysis_tasks(
        self,
        files: List[str],
        analysis_types: List[str],
    ) -> List[AnalysisTask]:
        """Create analysis tasks from file list."""
        tasks = []
        
        if self.config.enable_task_splitting:
            # Split files into optimal chunks
            file_chunks = self._split_files_into_chunks(files)
        else:
            # Single task per analysis type
            file_chunks = [files]
        
        for analysis_type in analysis_types:
            for i, file_chunk in enumerate(file_chunks):
                task = AnalysisTask(
                    task_id=str(uuid.uuid4()),
                    task_type=analysis_type,
                    file_paths=file_chunk,
                    parameters={},
                    priority=0,
                    estimated_duration=len(file_chunk) * 0.1,  # Rough estimate
                )
                tasks.append(task)
        
        return tasks

    def _split_files_into_chunks(self, files: List[str]) -> List[List[str]]:
        """Split files into optimal chunks for processing."""
        chunks = []
        current_chunk = []
        
        for file_path in files:
            current_chunk.append(file_path)
            
            if len(current_chunk) >= self.config.max_files_per_task:
                chunks.append(current_chunk)
                current_chunk = []
        
        # Add remaining files
        if current_chunk:
            chunks.append(current_chunk)
        
        # Ensure minimum chunk size
        if len(chunks) > 1:
            final_chunks = []
            for chunk in chunks:
                if len(chunk) >= self.config.min_files_per_task:
                    final_chunks.append(chunk)
                else:
                    # Merge small chunks with the last chunk
                    if final_chunks:
                        final_chunks[-1].extend(chunk)
                    else:
                        final_chunks.append(chunk)
            chunks = final_chunks
        
        return chunks

    async def _perform_syntax_analysis(self, file_paths: List[str]) -> Dict[str, Any]:
        """Perform syntax analysis on files."""
        # Simulated syntax analysis
        results = {
            "files_analyzed": len(file_paths),
            "syntax_errors": [],
            "warnings": [],
        }
        
        # In real implementation, this would use the base analyzer
        for file_path in file_paths:
            try:
                # Simulate analysis
                await asyncio.sleep(0.01)  # Simulate processing time
                
                # Add some mock results
                if "test" in file_path.lower():
                    results["warnings"].append(f"Test file detected: {file_path}")
                
            except Exception as e:
                results["syntax_errors"].append(f"Error in {file_path}: {e}")
        
        return results

    async def _perform_semantic_analysis(self, file_paths: List[str]) -> Dict[str, Any]:
        """Perform semantic analysis on files."""
        # Simulated semantic analysis
        results = {
            "files_analyzed": len(file_paths),
            "symbols_found": 0,
            "dependencies": [],
        }
        
        for file_path in file_paths:
            try:
                await asyncio.sleep(0.02)  # Simulate processing time
                
                # Mock symbol counting
                results["symbols_found"] += 10  # Mock value
                
            except Exception as e:
                logger.error(f"Semantic analysis error in {file_path}: {e}")
        
        return results

    async def _perform_quality_analysis(self, file_paths: List[str]) -> Dict[str, Any]:
        """Perform quality analysis on files."""
        # Simulated quality analysis
        results = {
            "files_analyzed": len(file_paths),
            "quality_score": 0.8,
            "issues": [],
        }
        
        for file_path in file_paths:
            try:
                await asyncio.sleep(0.015)  # Simulate processing time
                
                # Mock quality issues
                if len(Path(file_path).read_text(errors='ignore')) > 1000:
                    results["issues"].append(f"Large file detected: {file_path}")
                
            except Exception as e:
                logger.error(f"Quality analysis error in {file_path}: {e}")
        
        return results

    def _aggregate_results(
        self,
        results: List[DistributedAnalysisResult],
        project_path: str,
    ) -> AnalysisResult:
        """Aggregate distributed analysis results."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # Aggregate data from successful results
        total_files = 0
        total_symbols = 0
        all_issues = []
        total_processing_time = sum(r.processing_time for r in successful_results)
        
        for result in successful_results:
            if result.result_data:
                total_files += result.result_data.get("files_analyzed", 0)
                total_symbols += result.result_data.get("symbols_found", 0)
                
                # Collect issues
                if "issues" in result.result_data:
                    all_issues.extend(result.result_data["issues"])
                if "syntax_errors" in result.result_data:
                    all_issues.extend(result.result_data["syntax_errors"])
                if "warnings" in result.result_data:
                    all_issues.extend(result.result_data["warnings"])
        
        # Calculate overall quality score
        quality_scores = [
            r.result_data.get("quality_score", 0.5)
            for r in successful_results
            if r.result_data and "quality_score" in r.result_data
        ]
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        
        # Create aggregated result
        return AnalysisResult(
            success=len(failed_results) == 0,
            message=f"Distributed analysis completed: {len(successful_results)} successful, {len(failed_results)} failed",
            files_analyzed=total_files,
            symbols_found=total_symbols,
            issues_found=len(all_issues),
            quality_score=overall_quality,
            processing_time=total_processing_time,
            metadata={
                "distributed": True,
                "worker_nodes": len(self.worker_nodes),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(failed_results),
                "total_tasks": len(results),
            },
        )

    async def _analyze_local(
        self,
        project_path: str,
        analysis_types: List[str],
        progress_callback: Optional[callable] = None,
    ) -> AnalysisResult:
        """Fallback to local analysis."""
        logger.info("Performing local analysis as fallback")
        
        # Use base analyzer for local analysis
        return self.base_analyzer.analyze_codebase(project_path)