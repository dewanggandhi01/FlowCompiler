"""
Evaluation Metrics.

Tracks success rate, validation failures, repair count,
runtime pass rate, latency, and cost for benchmark evaluations.
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, Field


class BenchmarkResult(BaseModel):
    """Result for a single benchmark prompt."""
    id: str
    prompt: str
    category: str
    difficulty: str
    status: str = Field(default="pending", description="completed, failed, partial, skipped")
    # Quality metrics
    entities_generated: int = 0
    features_generated: int = 0
    expected_entities_min: int = 0
    expected_features_min: int = 0
    entities_met: bool = False
    features_met: bool = False
    # Validation
    validation_status: str = ""
    validation_errors: int = 0
    validation_warnings: int = 0
    # Repair
    repair_iterations: int = 0
    repair_success: bool = False
    # Simulation
    simulation_status: str = ""
    simulation_issues: int = 0
    # Performance
    latency_ms: float = 0.0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    # Errors
    error_message: str = ""
    assumptions_count: int = 0


class MetricsReport(BaseModel):
    """Aggregated metrics report for the evaluation dashboard."""
    total_prompts: int = 0
    completed: int = 0
    failed: int = 0
    partial: int = 0
    # Rates
    success_rate: float = 0.0
    validation_pass_rate: float = 0.0
    simulation_pass_rate: float = 0.0
    # Repairs
    total_repairs: int = 0
    avg_repair_iterations: float = 0.0
    repair_success_rate: float = 0.0
    # Performance
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    # By category
    normal_success_rate: float = 0.0
    edge_case_success_rate: float = 0.0
    # Individual results
    results: list[BenchmarkResult] = Field(default_factory=list)


class MetricsCollector:
    """Collects and aggregates metrics during benchmark evaluation."""

    def __init__(self) -> None:
        self.results: list[BenchmarkResult] = []

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def generate_report(self) -> MetricsReport:
        """Generate aggregated metrics report."""
        if not self.results:
            return MetricsReport()

        total = len(self.results)
        completed = [r for r in self.results if r.status == "completed"]
        failed = [r for r in self.results if r.status == "failed"]
        partial = [r for r in self.results if r.status == "partial"]

        normal = [r for r in self.results if r.category == "normal"]
        edge = [r for r in self.results if r.category == "edge_case"]
        normal_completed = [r for r in normal if r.status == "completed"]
        edge_completed = [r for r in edge if r.status in ("completed", "partial")]

        latencies = [r.latency_ms for r in self.results if r.latency_ms > 0]

        validation_passed = [r for r in self.results if r.validation_status == "PASS"]
        simulation_passed = [r for r in self.results if r.simulation_status == "PASS"]

        repairs_needed = [r for r in self.results if r.repair_iterations > 0]
        repair_successes = [r for r in repairs_needed if r.repair_success]

        return MetricsReport(
            total_prompts=total,
            completed=len(completed),
            failed=len(failed),
            partial=len(partial),
            success_rate=len(completed) / total if total > 0 else 0,
            validation_pass_rate=len(validation_passed) / total if total > 0 else 0,
            simulation_pass_rate=len(simulation_passed) / total if total > 0 else 0,
            total_repairs=sum(r.repair_iterations for r in self.results),
            avg_repair_iterations=(
                sum(r.repair_iterations for r in repairs_needed) / len(repairs_needed)
                if repairs_needed else 0
            ),
            repair_success_rate=(
                len(repair_successes) / len(repairs_needed) if repairs_needed else 1.0
            ),
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            total_tokens=sum(r.total_tokens for r in self.results),
            total_cost_usd=sum(r.estimated_cost_usd for r in self.results),
            normal_success_rate=(
                len(normal_completed) / len(normal) if normal else 0
            ),
            edge_case_success_rate=(
                len(edge_completed) / len(edge) if edge else 0
            ),
            results=self.results,
        )
