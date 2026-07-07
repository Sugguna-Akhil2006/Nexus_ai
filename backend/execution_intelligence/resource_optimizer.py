"""Resource optimizer recommending CPU, memory, and worker distributions."""

from backend.execution_intelligence.models import ResourceOptimizationModel, ExecutionMetricsModel


class ResourceOptimizer:
    """Optimizes system compute parameters and thread/worker concurrency."""

    @staticmethod
    def recommend_resources(metrics: ExecutionMetricsModel) -> ResourceOptimizationModel:
        """Determines hardware sizing and queue layouts based on workflow performance characteristics."""
        # Baseline resources
        cpu = 1.0
        memory = 512.0
        gpu = 0.0

        # Adjust based on memory consumption
        if metrics.average_memory_usage_mb > 350:
            memory = 1024.0
            cpu = 2.0
        elif metrics.average_memory_usage_mb > 700:
            memory = 2048.0
            cpu = 4.0

        # Suggest GPU utilization if there are multiple slow modules suggesting model embedding / parsing runs
        if len(metrics.module_execution_times) > 4:
            gpu = 20.0  # target 20% GPU offloading for local OCR/embedding runtimes

        # Queue and worker distribution
        workers = {
            "default_queue": 2,
            "heavy_task_queue": 1
        }

        # If failures are high or retry rate is high, allocate more default workers to reduce backlogs
        exec_count = metrics.execution_count or 1
        if (metrics.failures_count / exec_count) > 0.15 or (metrics.retry_counts / exec_count) > 0.5:
            workers["default_queue"] = 4
            workers["heavy_task_queue"] = 2
            strategy = "Dynamic Priority Queue Balancing"
        else:
            strategy = "Standard Round-Robin"

        return ResourceOptimizationModel(
            recommended_cpu_cores=cpu,
            recommended_memory_mb=memory,
            gpu_utilization_target_pct=gpu,
            queue_balancing_strategy=strategy,
            worker_distribution=workers
        )
