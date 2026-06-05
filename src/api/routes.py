"""
FastAPI Routes — All API endpoints for the AI Application Compiler.

Endpoints:
  POST /generate  — Full pipeline execution
  POST /validate  — Validate existing schemas
  POST /repair    — Repair failing schemas
  POST /simulate  — Run execution simulation
  POST /evaluate  — Run evaluation benchmark
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agents.execution_simulator import ExecutionSimulator
from src.agents.pipeline import CompilationPipeline
from src.agents.repair_agent import RepairEngine
from src.agents.validator import ValidationEngine
from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.runtime_schema import CompilerOutput, RuntimeSimulationResult
from src.schemas.ui_schema import UISchema
from src.schemas.validation_schema import ValidationResult

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request Models ───────────────────────────────────────


class GenerateRequest(BaseModel):
    """Request body for /generate endpoint."""
    prompt: str = Field(..., min_length=5, description="Natural language software requirement")


class ValidateRequest(BaseModel):
    """Request body for /validate endpoint."""
    ui: dict = Field(default_factory=dict)
    api: dict = Field(default_factory=dict)
    db: dict = Field(default_factory=dict)
    auth: dict = Field(default_factory=dict)


class RepairRequest(BaseModel):
    """Request body for /repair endpoint."""
    ui: dict = Field(default_factory=dict)
    api: dict = Field(default_factory=dict)
    db: dict = Field(default_factory=dict)
    auth: dict = Field(default_factory=dict)
    validation_result: dict = Field(default_factory=dict)


class SimulateRequest(BaseModel):
    """Request body for /simulate endpoint."""
    ui: dict = Field(default_factory=dict)
    api: dict = Field(default_factory=dict)
    db: dict = Field(default_factory=dict)
    auth: dict = Field(default_factory=dict)


# ── Endpoints ────────────────────────────────────────────


@router.post("/generate", response_model=CompilerOutput)
async def generate(request: GenerateRequest) -> CompilerOutput:
    """
    Full compilation pipeline.

    Takes a natural language prompt and generates a complete
    executable application configuration through 6 stages.
    """
    logger.info(f"Generate request: {request.prompt[:100]}...")
    try:
        pipeline = CompilationPipeline()
        result = pipeline.compile(request.prompt)
        return result
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
async def validate(request: ValidateRequest) -> ValidationResult:
    """
    Validate existing schemas.

    Takes UI, API, DB, and Auth schemas and runs cross-layer validation.
    """
    try:
        ui = UISchema.model_validate(request.ui)
        api = APISchema.model_validate(request.api)
        db = DBSchema.model_validate(request.db)
        auth = AuthSchema.model_validate(request.auth)

        engine = ValidationEngine()
        result = engine.validate(ui, api, db, auth)
        return result
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/repair")
async def repair(request: RepairRequest) -> dict:
    """
    Repair failing schemas.

    Takes schemas with validation errors and performs targeted repairs.
    """
    try:
        ui = UISchema.model_validate(request.ui)
        api = APISchema.model_validate(request.api)
        db = DBSchema.model_validate(request.db)
        auth = AuthSchema.model_validate(request.auth)
        validation = ValidationResult.model_validate(request.validation_result)

        engine = RepairEngine()
        repaired_ui, repaired_api, repaired_db, repaired_auth, report = engine.repair(
            ui, api, db, auth, validation
        )

        return {
            "ui": repaired_ui.model_dump(),
            "api": repaired_api.model_dump(),
            "db": repaired_db.model_dump(),
            "auth": repaired_auth.model_dump(),
            "repair_report": report.model_dump(),
        }
    except Exception as e:
        logger.error(f"Repair failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Repair failed: {str(e)}")


@router.post("/simulate", response_model=RuntimeSimulationResult)
async def simulate(request: SimulateRequest) -> RuntimeSimulationResult:
    """
    Run execution simulation.

    Simulates runtime to verify generated configuration would work.
    """
    try:
        ui = UISchema.model_validate(request.ui)
        api = APISchema.model_validate(request.api)
        db = DBSchema.model_validate(request.db)
        auth = AuthSchema.model_validate(request.auth)

        simulator = ExecutionSimulator()
        result = simulator.simulate(ui, api, db, auth)
        return result
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/evaluate")
async def evaluate() -> dict:
    """
    Run evaluation benchmark.

    Executes the full benchmark dataset and returns metrics.
    """
    try:
        from src.evaluation.benchmark import BenchmarkRunner
        from src.evaluation.metrics import MetricsCollector

        runner = BenchmarkRunner()
        collector = MetricsCollector()
        results = runner.run_benchmark(collector)
        return results
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "flowcompiler"}
