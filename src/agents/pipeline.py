"""
Compilation Pipeline — LangGraph Orchestrator.

Orchestrates all 6 stages of the AI Application Compiler using LangGraph.
Manages state transitions, conditional repair loops, and full tracing.

Pipeline:
  Intent Extraction → System Design → Schema Generation →
  Validation → (Repair Loop) → Execution Simulation → Final Config
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.config import get_settings
from src.schemas.api_schema import APISchema
from src.schemas.auth_schema import AuthSchema
from src.schemas.db_schema import DBSchema
from src.schemas.intent_schema import ExtractedIntent
from src.schemas.runtime_schema import (
    CompilerOutput,
    PipelineStageResult,
    RuntimeConfig,
    RuntimeSimulationResult,
    RuntimeStatus,
)
from src.schemas.system_design_schema import SystemDesign
from src.schemas.ui_schema import UISchema
from src.schemas.validation_schema import RepairReport, ValidationResult

from .execution_simulator import ExecutionSimulator
from .intent_extractor import IntentExtractorAgent
from .repair_agent import RepairEngine
from .schema_generator import GeneratedSchemas, SchemaGeneratorAgent
from .system_designer import SystemDesignerAgent
from .validator import ValidationEngine

logger = logging.getLogger(__name__)


# ── Pipeline State ───────────────────────────────────────


class PipelineState(TypedDict, total=False):
    """State flowing through the LangGraph pipeline."""
    # Input
    prompt: str
    compile_id: str

    # Stage 1 output
    intent: ExtractedIntent | None

    # Stage 2 output
    system_design: SystemDesign | None

    # Stage 3 output
    ui_schema: UISchema | None
    api_schema: APISchema | None
    db_schema: DBSchema | None
    auth_schema: AuthSchema | None

    # Stage 4 output
    validation_result: ValidationResult | None

    # Stage 5 output
    repair_reports: list[RepairReport]
    repair_iteration: int

    # Stage 6 output
    simulation_result: RuntimeSimulationResult | None

    # Metrics
    stages: list[PipelineStageResult]
    total_tokens: int
    errors: list[str]
    start_time: float


# ── Pipeline Builder ─────────────────────────────────────


class CompilationPipeline:
    """
    LangGraph-based compilation pipeline.

    Orchestrates the 6 stages with conditional repair loops.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.intent_extractor = IntentExtractorAgent()
        self.system_designer = SystemDesignerAgent()
        self.schema_generator = SchemaGeneratorAgent()
        self.validator = ValidationEngine()
        self.repair_engine = RepairEngine()
        self.execution_simulator = ExecutionSimulator()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        graph = StateGraph(PipelineState)

        # Add nodes
        graph.add_node("extract_intent", self._extract_intent)
        graph.add_node("design_system", self._design_system)
        graph.add_node("generate_schemas", self._generate_schemas)
        graph.add_node("validate", self._validate)
        graph.add_node("repair", self._repair)
        graph.add_node("simulate", self._simulate)

        # Set entry point
        graph.set_entry_point("extract_intent")

        # Add edges
        graph.add_edge("extract_intent", "design_system")
        graph.add_edge("design_system", "generate_schemas")
        graph.add_edge("generate_schemas", "validate")

        # Conditional edge: validation → repair or simulate
        graph.add_conditional_edges(
            "validate",
            self._should_repair,
            {
                "repair": "repair",
                "simulate": "simulate",
            },
        )

        # After repair → validate again
        graph.add_edge("repair", "validate")

        # After simulation → end
        graph.add_edge("simulate", END)

        return graph.compile()

    # ── Stage Nodes ──────────────────────────────────────

    def _extract_intent(self, state: PipelineState) -> dict:
        """Stage 1: Extract intent from prompt."""
        stage_start = time.time()
        try:
            result = self.intent_extractor.run(state["prompt"])
            duration = (time.time() - stage_start) * 1000
            return {
                "intent": result.data,
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="intent_extraction",
                        status="completed",
                        duration_ms=duration,
                        token_usage={
                            "prompt_tokens": result.token_usage.prompt_tokens,
                            "completion_tokens": result.token_usage.completion_tokens,
                            "total_tokens": result.token_usage.total_tokens,
                        },
                    )
                ],
                "total_tokens": state.get("total_tokens", 0) + result.token_usage.total_tokens,
            }
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return {
                "errors": state.get("errors", []) + [f"Intent extraction failed: {str(e)}"],
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="intent_extraction",
                        status="failed",
                        duration_ms=(time.time() - stage_start) * 1000,
                        error=str(e),
                    )
                ],
            }

    def _design_system(self, state: PipelineState) -> dict:
        """Stage 2: Design system architecture."""
        if not state.get("intent"):
            return {"errors": state.get("errors", []) + ["Cannot design system: no intent"]}

        stage_start = time.time()
        try:
            result = self.system_designer.run(state["intent"])
            duration = (time.time() - stage_start) * 1000
            return {
                "system_design": result.data,
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="system_design",
                        status="completed",
                        duration_ms=duration,
                        token_usage={
                            "prompt_tokens": result.token_usage.prompt_tokens,
                            "completion_tokens": result.token_usage.completion_tokens,
                            "total_tokens": result.token_usage.total_tokens,
                        },
                    )
                ],
                "total_tokens": state.get("total_tokens", 0) + result.token_usage.total_tokens,
            }
        except Exception as e:
            logger.error(f"System design failed: {e}")
            return {
                "errors": state.get("errors", []) + [f"System design failed: {str(e)}"],
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="system_design",
                        status="failed",
                        duration_ms=(time.time() - stage_start) * 1000,
                        error=str(e),
                    )
                ],
            }

    def _generate_schemas(self, state: PipelineState) -> dict:
        """Stage 3: Generate UI, API, DB, Auth schemas."""
        if not state.get("system_design"):
            return {"errors": state.get("errors", []) + ["Cannot generate schemas: no system design"]}

        stage_start = time.time()
        try:
            result = self.schema_generator.run(state["system_design"])
            schemas: GeneratedSchemas = result.data
            duration = (time.time() - stage_start) * 1000
            return {
                "ui_schema": schemas.ui,
                "api_schema": schemas.api,
                "db_schema": schemas.db,
                "auth_schema": schemas.auth,
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="schema_generation",
                        status="completed",
                        duration_ms=duration,
                        token_usage={
                            "prompt_tokens": result.token_usage.prompt_tokens,
                            "completion_tokens": result.token_usage.completion_tokens,
                            "total_tokens": result.token_usage.total_tokens,
                        },
                    )
                ],
                "total_tokens": state.get("total_tokens", 0) + result.token_usage.total_tokens,
            }
        except Exception as e:
            logger.error(f"Schema generation failed: {e}")
            return {
                "errors": state.get("errors", []) + [f"Schema generation failed: {str(e)}"],
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage="schema_generation",
                        status="failed",
                        duration_ms=(time.time() - stage_start) * 1000,
                        error=str(e),
                    )
                ],
            }

    def _validate(self, state: PipelineState) -> dict:
        """Stage 4: Validate all schemas."""
        ui = state.get("ui_schema")
        api = state.get("api_schema")
        db = state.get("db_schema")
        auth = state.get("auth_schema")

        if not all([ui, api, db, auth]):
            return {
                "validation_result": ValidationResult(
                    status="FAIL",
                    errors=[],
                    total_checks=0,
                    passed_checks=0,
                    failed_checks=0,
                ),
                "errors": state.get("errors", []) + ["Cannot validate: missing schemas"],
            }

        stage_start = time.time()
        result = self.validator.validate(ui, api, db, auth)
        duration = (time.time() - stage_start) * 1000

        return {
            "validation_result": result,
            "stages": state.get("stages", []) + [
                PipelineStageResult(
                    stage="validation",
                    status="completed",
                    duration_ms=duration,
                )
            ],
        }

    def _repair(self, state: PipelineState) -> dict:
        """Stage 5: Repair failing schemas."""
        iteration = state.get("repair_iteration", 0) + 1
        stage_start = time.time()

        try:
            repaired_ui, repaired_api, repaired_db, repaired_auth, report = self.repair_engine.repair(
                ui=state["ui_schema"],
                api=state["api_schema"],
                db=state["db_schema"],
                auth=state["auth_schema"],
                validation_result=state["validation_result"],
                iteration=iteration,
            )

            duration = (time.time() - stage_start) * 1000
            return {
                "ui_schema": repaired_ui,
                "api_schema": repaired_api,
                "db_schema": repaired_db,
                "auth_schema": repaired_auth,
                "repair_reports": state.get("repair_reports", []) + [report],
                "repair_iteration": iteration,
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage=f"repair_iteration_{iteration}",
                        status="completed",
                        duration_ms=duration,
                    )
                ],
            }
        except Exception as e:
            logger.error(f"Repair failed: {e}")
            return {
                "repair_iteration": iteration,
                "errors": state.get("errors", []) + [f"Repair iteration {iteration} failed: {str(e)}"],
                "stages": state.get("stages", []) + [
                    PipelineStageResult(
                        stage=f"repair_iteration_{iteration}",
                        status="failed",
                        duration_ms=(time.time() - stage_start) * 1000,
                        error=str(e),
                    )
                ],
            }

    def _simulate(self, state: PipelineState) -> dict:
        """Stage 6: Simulate runtime execution."""
        ui = state.get("ui_schema")
        api = state.get("api_schema")
        db = state.get("db_schema")
        auth = state.get("auth_schema")

        if not all([ui, api, db, auth]):
            return {
                "simulation_result": RuntimeSimulationResult(
                    runtime_status=RuntimeStatus.FAIL,
                    issues=[],
                ),
                "errors": state.get("errors", []) + ["Cannot simulate: missing schemas"],
            }

        stage_start = time.time()
        result = self.execution_simulator.simulate(ui, api, db, auth)
        duration = (time.time() - stage_start) * 1000

        return {
            "simulation_result": result,
            "stages": state.get("stages", []) + [
                PipelineStageResult(
                    stage="execution_simulation",
                    status="completed",
                    duration_ms=duration,
                )
            ],
        }

    # ── Conditional Edge ─────────────────────────────────

    def _has_schemas(self, state: PipelineState) -> bool:
        return all([
            state.get("ui_schema"),
            state.get("api_schema"),
            state.get("db_schema"),
            state.get("auth_schema"),
        ])

    def _should_repair(self, state: PipelineState) -> str:
        """Decide whether to repair or proceed to simulation."""
        if not self._has_schemas(state):
            return "simulate"

        validation = state.get("validation_result")
        iteration = state.get("repair_iteration", 0)

        if validation and validation.status == "FAIL":
            if iteration < self.settings.max_repair_iterations:
                logger.info(
                    f"Validation FAILED (iteration {iteration}), entering repair loop"
                )
                return "repair"
            else:
                logger.warning(
                    f"Max repair iterations ({self.settings.max_repair_iterations}) reached, "
                    f"proceeding to simulation with remaining errors"
                )
                return "simulate"
        else:
            logger.info("Validation PASSED, proceeding to simulation")
            return "simulate"

    # ── Public API ───────────────────────────────────────

    def compile(self, prompt: str) -> CompilerOutput:
        """
        Run the full compilation pipeline.

        Args:
            prompt: Natural language software requirement.

        Returns:
            CompilerOutput with all stage results.
        """
        compile_id = f"compile_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        logger.info(f"Starting compilation {compile_id}")

        # Initialize state
        initial_state: PipelineState = {
            "prompt": prompt,
            "compile_id": compile_id,
            "intent": None,
            "system_design": None,
            "ui_schema": None,
            "api_schema": None,
            "db_schema": None,
            "auth_schema": None,
            "validation_result": None,
            "repair_reports": [],
            "repair_iteration": 0,
            "simulation_result": None,
            "stages": [],
            "total_tokens": 0,
            "errors": [],
            "start_time": start_time,
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        total_duration = (time.time() - start_time) * 1000
        total_tokens = final_state.get("total_tokens", 0)

        # Calculate cost (GPT-4o pricing: $2.50/1M input, $10/1M output)
        estimated_cost = (total_tokens / 1_000_000) * 6.25  # Rough average

        # Determine status
        errors = final_state.get("errors", [])
        simulation = final_state.get("simulation_result")
        if errors:
            status = "failed" if not final_state.get("ui_schema") else "partial"
        elif simulation and simulation.runtime_status == RuntimeStatus.PASS:
            status = "completed"
        else:
            status = "partial"

        # Build runtime config
        runtime_config = None
        if all([
            final_state.get("ui_schema"),
            final_state.get("api_schema"),
            final_state.get("db_schema"),
            final_state.get("auth_schema"),
        ]):
            runtime_config = RuntimeConfig(
                ui=final_state["ui_schema"],
                api=final_state["api_schema"],
                db=final_state["db_schema"],
                auth=final_state["auth_schema"],
            )

        # Build compiler output
        output = CompilerOutput(
            compile_id=compile_id,
            original_prompt=prompt,
            status=status,
            intent=final_state.get("intent"),
            system_design=final_state.get("system_design"),
            runtime_config=runtime_config,
            validation_result=final_state.get("validation_result"),
            simulation_result=final_state.get("simulation_result"),
            repair_reports=final_state.get("repair_reports", []),
            repair_iterations=final_state.get("repair_iteration", 0),
            assumptions=(
                final_state["intent"].assumptions
                if final_state.get("intent") else []
            ),
            stages=final_state.get("stages", []),
            total_duration_ms=total_duration,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            errors=errors,
        )

        logger.info(
            f"Compilation {compile_id} {status}: "
            f"{total_duration:.0f}ms, {total_tokens} tokens, "
            f"${estimated_cost:.4f}"
        )

        return output
