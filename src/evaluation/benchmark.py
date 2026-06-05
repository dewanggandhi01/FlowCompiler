"""
Benchmark Runner.

Loads the 20-prompt benchmark dataset and runs the compilation pipeline
for each prompt, collecting metrics.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from src.agents.pipeline import CompilationPipeline
from src.schemas.runtime_schema import RuntimeStatus

from .metrics import BenchmarkResult, MetricsCollector, MetricsReport

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).parent / "dataset.json"


class BenchmarkRunner:
    """
    Runs the benchmark evaluation suite.

    Loads 20 prompts (10 normal + 10 edge cases),
    runs each through the compilation pipeline,
    and collects metrics.
    """

    def __init__(self) -> None:
        self.dataset = self._load_dataset()

    def _load_dataset(self) -> list[dict]:
        """Load benchmark dataset from JSON file."""
        try:
            with open(DATASET_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Benchmark dataset not found at {DATASET_PATH}")
            return []

    def run_benchmark(self, collector: MetricsCollector | None = None) -> dict:
        """
        Run full benchmark evaluation.

        Args:
            collector: Optional MetricsCollector. Created if not provided.

        Returns:
            Dictionary with report data.
        """
        if collector is None:
            collector = MetricsCollector()

        pipeline = CompilationPipeline()

        logger.info(f"Starting benchmark with {len(self.dataset)} prompts")

        for item in self.dataset:
            result = self._run_single(pipeline, item)
            collector.add_result(result)
            logger.info(
                f"Benchmark {item['id']} ({item['category']}): "
                f"{result.status} in {result.latency_ms:.0f}ms"
            )

        report = collector.generate_report()
        logger.info(
            f"Benchmark complete: {report.success_rate:.1%} success rate, "
            f"avg latency {report.avg_latency_ms:.0f}ms"
        )

        return report.model_dump()

    def _run_single(self, pipeline: CompilationPipeline, item: dict) -> BenchmarkResult:
        """Run a single benchmark prompt."""
        result = BenchmarkResult(
            id=item["id"],
            prompt=item["prompt"],
            category=item["category"],
            difficulty=item.get("difficulty", "unknown"),
            expected_entities_min=item.get("expected_entities_min", 0),
            expected_features_min=item.get("expected_features_min", 0),
        )

        start = time.time()
        try:
            output = pipeline.compile(item["prompt"])

            result.status = output.status
            result.latency_ms = output.total_duration_ms or 0
            result.total_tokens = output.total_tokens
            result.estimated_cost_usd = output.estimated_cost_usd
            result.assumptions_count = len(output.assumptions)

            # Count entities and features from intent
            if output.intent:
                result.entities_generated = len(output.intent.entities)
                result.features_generated = len(output.intent.features)
                result.entities_met = result.entities_generated >= result.expected_entities_min
                result.features_met = result.features_generated >= result.expected_features_min

            # Validation
            if output.validation_result:
                result.validation_status = output.validation_result.status
                result.validation_errors = len(output.validation_result.errors)
                result.validation_warnings = len(output.validation_result.warnings)

            # Repair
            result.repair_iterations = output.repair_iterations
            if output.repair_reports:
                result.repair_success = output.repair_reports[-1].success

            # Simulation
            if output.simulation_result:
                result.simulation_status = output.simulation_result.runtime_status.value
                result.simulation_issues = len(output.simulation_result.issues)

            if output.errors:
                result.error_message = "; ".join(output.errors[:3])

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            result.latency_ms = (time.time() - start) * 1000
            logger.error(f"Benchmark {item['id']} failed: {e}")

        return result

    def run_single_prompt(self, prompt: str, prompt_id: str = "custom") -> BenchmarkResult:
        """Run a single custom prompt through the benchmark."""
        pipeline = CompilationPipeline()
        item = {
            "id": prompt_id,
            "prompt": prompt,
            "category": "custom",
            "difficulty": "unknown",
            "expected_entities_min": 0,
            "expected_features_min": 0,
        }
        return self._run_single(pipeline, item)
