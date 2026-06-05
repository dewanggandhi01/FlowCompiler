"""
Runtime Schema — Final output of the compilation pipeline.

Defines the executable runtime configuration that is sufficient
to automatically create an application.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .api_schema import APISchema
from .auth_schema import AuthSchema
from .db_schema import DBSchema
from .intent_schema import Assumption, ExtractedIntent
from .system_design_schema import SystemDesign
from .ui_schema import UISchema
from .validation_schema import RepairReport, ValidationResult


class RuntimeStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class RuntimeIssue(BaseModel):
    """An issue found during runtime simulation."""
    id: str
    category: str = Field(
        ...,
        description="Category: form_submission, endpoint_resolution, db_integrity, "
        "permission_resolution, route_reachability, data_flow",
    )
    severity: str = Field(default="error")
    description: str
    component: str = Field(default="", description="Which component is affected")
    suggestion: str = Field(default="")


class RuntimeSimulationResult(BaseModel):
    """
    Stage 6 Output: Execution simulation result.

    Verifies that the generated configuration would work at runtime.
    """
    runtime_status: RuntimeStatus
    issues: list[RuntimeIssue] = Field(default_factory=list)
    simulated_checks: int = Field(default=0)
    passed_checks: int = Field(default=0)
    failed_checks: int = Field(default=0)
    simulation_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed simulation results per category",
    )


class RuntimeConfig(BaseModel):
    """
    Final Executable Runtime Configuration.

    This output is sufficient to automatically create an application.
    Contains all UI, API, DB, and Auth configurations.
    """
    ui: UISchema = Field(default_factory=UISchema)
    api: APISchema = Field(default_factory=APISchema)
    db: DBSchema = Field(default_factory=DBSchema)
    auth: AuthSchema = Field(default_factory=AuthSchema)


class PipelineStageResult(BaseModel):
    """Result of a single pipeline stage."""
    stage: str
    status: str = Field(default="pending", description="pending, running, completed, failed")
    duration_ms: Optional[float] = None
    token_usage: dict[str, int] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    error: Optional[str] = None


class CompilerOutput(BaseModel):
    """
    Complete compiler output — wraps all pipeline stages.

    This is the top-level response from the /generate endpoint.
    """
    # Metadata
    compile_id: str = Field(..., description="Unique compilation run identifier")
    original_prompt: str = Field(..., description="The user's original natural language prompt")
    status: str = Field(default="completed", description="completed, failed, partial")

    # Stage outputs
    intent: Optional[ExtractedIntent] = None
    system_design: Optional[SystemDesign] = None
    runtime_config: Optional[RuntimeConfig] = None

    # Validation & simulation
    validation_result: Optional[ValidationResult] = None
    simulation_result: Optional[RuntimeSimulationResult] = None

    # Repair tracking
    repair_reports: list[RepairReport] = Field(default_factory=list)
    repair_iterations: int = Field(default=0)

    # Assumptions
    assumptions: list[Assumption] = Field(default_factory=list)

    # Pipeline metrics
    stages: list[PipelineStageResult] = Field(default_factory=list)
    total_duration_ms: Optional[float] = None
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)

    # Errors
    errors: list[str] = Field(default_factory=list)
