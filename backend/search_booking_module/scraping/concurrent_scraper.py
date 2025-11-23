"""Concurrent scraping manager with queue and worker pool."""

from typing import List, Dict, Any, Optional, Callable, Awaitable
import asyncio
import logging
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ScrapingTask:
    """Represents a single scraping task."""
    
    def __init__(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 0,
        retries: int = 0,
        max_retries: int = 3
    ):
        """Initialize scraping task.
        
        Args:
            task_id: Unique identifier for the task
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority (higher = more important)
            retries: Current retry count
            max_retries: Maximum retry attempts
        """
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.retries = retries
        self.max_retries = max_retries
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.status = 'pending'  # pending, running, completed, failed
    
    def __lt__(self, other):
        """Compare tasks by priority (for priority queue)."""
        return self.priority > other.priority  # Higher priority first


class ConcurrentScraper:
    """Manages concurrent scraping with queue and worker pool."""
    
    def __init__(
        self,
        max_workers: int = 5,
        queue_size: int = 100,
        timeout: float = 300.0
    ):
        """Initialize concurrent scraper.
        
        Args:
            max_workers: Maximum number of concurrent workers
            queue_size: Maximum queue size
            timeout: Task timeout in seconds
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.timeout = timeout
        
        self.task_queue = asyncio.PriorityQueue(maxsize=queue_size)
        self.workers: List[asyncio.Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, ScrapingTask] = {}
        self.failed_tasks: Dict[str, ScrapingTask] = {}
        
        self.is_running = False
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'retried_tasks': 0,
            'total_time': 0.0,
        }
    
    async def start(self):
        """Start the worker pool."""
        if self.is_running:
            logger.warning("Concurrent scraper is already running")
            return
        
        self.is_running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        logger.info(f"Started {self.max_workers} workers")
    
    async def stop(self):
        """Stop the worker pool and wait for tasks to complete."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for queue to be empty
        await self.task_queue.join()
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Wait for running tasks to complete
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} running tasks to complete...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("Concurrent scraper stopped")
    
    async def submit(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 0
    ) -> str:
        """Submit a task to the queue.
        
        Args:
            task_id: Unique identifier for the task
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority (higher = more important)
            
        Returns:
            Task ID
            
        Raises:
            asyncio.QueueFull: If queue is full
        """
        task = ScrapingTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        try:
            await asyncio.wait_for(
                self.task_queue.put((priority, task)),
                timeout=5.0
            )
            self.stats['total_tasks'] += 1
            logger.debug(f"Submitted task {task_id} with priority {priority}")
            return task_id
        except asyncio.TimeoutError:
            raise asyncio.QueueFull(f"Queue is full, cannot submit task {task_id}")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a task to complete and return its result.
        
        Args:
            task_id: Task identifier
            timeout: Maximum time to wait
            
        Returns:
            Task result
            
        Raises:
            asyncio.TimeoutError: If timeout is exceeded
            Exception: If task failed
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if task is completed
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task.error:
                    raise task.error
                return task.result
            
            # Check if task failed
            if task_id in self.failed_tasks:
                task = self.failed_tasks[task_id]
                raise task.error or Exception(f"Task {task_id} failed")
            
            # Check timeout
            if timeout:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    raise asyncio.TimeoutError(f"Task {task_id} timed out after {timeout}s")
            
            await asyncio.sleep(0.1)
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes tasks from the queue."""
        logger.debug(f"{worker_name} started")
        
        while self.is_running:
            try:
                # Get task from queue (with timeout to allow checking is_running)
                try:
                    priority, task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process task
                await self._process_task(task, worker_name)
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                logger.debug(f"{worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"{worker_name} error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before continuing
        
        logger.debug(f"{worker_name} stopped")
    
    async def _process_task(self, task: ScrapingTask, worker_name: str):
        """Process a single task."""
        task.status = 'running'
        task.started_at = datetime.utcnow()
        
        logger.debug(f"{worker_name} processing task {task.task_id}")
        
        try:
            # Execute task with timeout
            result = await asyncio.wait_for(
                task.func(*task.args, **task.kwargs),
                timeout=self.timeout
            )
            
            task.completed_at = datetime.utcnow()
            task.result = result
            task.status = 'completed'
            
            # Calculate duration
            duration = (task.completed_at - task.started_at).total_seconds()
            self.stats['total_time'] += duration
            self.stats['completed_tasks'] += 1
            
            self.completed_tasks[task.task_id] = task
            logger.debug(f"{worker_name} completed task {task.task_id} in {duration:.2f}s")
            
        except asyncio.TimeoutError:
            task.status = 'failed'
            task.error = asyncio.TimeoutError(f"Task {task.task_id} timed out after {self.timeout}s")
            self._handle_task_failure(task, worker_name)
            
        except Exception as e:
            task.status = 'failed'
            task.error = e
            self._handle_task_failure(task, worker_name)
    
    def _handle_task_failure(self, task: ScrapingTask, worker_name: str):
        """Handle task failure, potentially retrying."""
        task.completed_at = datetime.utcnow()
        duration = (task.completed_at - task.started_at).total_seconds()
        
        if task.retries < task.max_retries:
            # Retry task
            task.retries += 1
            task.status = 'pending'
            task.started_at = None
            task.completed_at = None
            task.error = None
            
            # Re-submit with lower priority
            asyncio.create_task(
                self.task_queue.put((task.priority - 1, task))
            )
            
            self.stats['retried_tasks'] += 1
            logger.warning(
                f"{worker_name} retrying task {task.task_id} "
                f"(attempt {task.retries}/{task.max_retries})"
            )
        else:
            # Max retries exceeded
            self.stats['failed_tasks'] += 1
            self.failed_tasks[task.task_id] = task
            logger.error(
                f"{worker_name} failed task {task.task_id} after {task.retries} retries: {task.error}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        avg_time = (
            self.stats['total_time'] / self.stats['completed_tasks']
            if self.stats['completed_tasks'] > 0
            else 0.0
        )
        
        success_rate = (
            self.stats['completed_tasks'] / self.stats['total_tasks']
            if self.stats['total_tasks'] > 0
            else 0.0
        )
        
        return {
            **self.stats,
            'avg_task_time': avg_time,
            'success_rate': success_rate,
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks_count': len(self.completed_tasks),
            'failed_tasks_count': len(self.failed_tasks),
        }
    
    async def wait_for_all(self, timeout: Optional[float] = None):
        """Wait for all tasks in the queue to complete."""
        await self.task_queue.join()
        
        # Wait for running tasks
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

