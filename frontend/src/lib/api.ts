/**
 * FlowCompiler API Client
 *
 * Type-safe API client for communicating with the FastAPI backend.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://flowcompiler.onrender.com";

// ── Types ──────────────────────────────────────────────

export interface GenerateRequest {
  prompt: string;
}

export interface ValidationError {
  id: string;
  layer: string;
  severity: string;
  field: string;
  message: string;
  expected: string;
  actual: string;
  fix_suggestion: string;
  auto_fixable: boolean;
}

export interface ValidationResult {
  status: "PASS" | "FAIL";
  errors: ValidationError[];
  warnings: ValidationError[];
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
}

export interface RuntimeIssue {
  id: string;
  category: string;
  severity: string;
  description: string;
  component: string;
  suggestion: string;
}

export interface SimulationResult {
  runtime_status: "PASS" | "FAIL" | "PARTIAL";
  issues: RuntimeIssue[];
  simulated_checks: number;
  passed_checks: number;
  failed_checks: number;
}

export interface RepairReport {
  iteration: number;
  layer: string;
  errors_fixed: string[];
  errors_remaining: string[];
  changes_made: string[];
  success: boolean;
}

export interface PipelineStage {
  stage: string;
  status: string;
  duration_ms: number | null;
  token_usage: Record<string, number>;
  error: string | null;
}

export interface Assumption {
  category: string;
  description: string;
  reasoning: string;
}

export interface CompilerOutput {
  compile_id: string;
  original_prompt: string;
  status: "completed" | "failed" | "partial";
  intent: Record<string, unknown> | null;
  system_design: Record<string, unknown> | null;
  runtime_config: {
    ui: Record<string, unknown>;
    api: Record<string, unknown>;
    db: Record<string, unknown>;
    auth: Record<string, unknown>;
  } | null;
  validation_result: ValidationResult | null;
  simulation_result: SimulationResult | null;
  repair_reports: RepairReport[];
  repair_iterations: number;
  assumptions: Assumption[];
  stages: PipelineStage[];
  total_duration_ms: number | null;
  total_tokens: number;
  estimated_cost_usd: number;
  errors: string[];
}

// ── API Functions ──────────────────────────────────────

export async function generateApp(prompt: string): Promise<CompilerOutput> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Generation failed");
  }
  return res.json();
}

export async function validateSchemas(schemas: {
  ui: Record<string, unknown>;
  api: Record<string, unknown>;
  db: Record<string, unknown>;
  auth: Record<string, unknown>;
}): Promise<ValidationResult> {
  const res = await fetch(`${API_BASE}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(schemas),
  });
  if (!res.ok) throw new Error("Validation failed");
  return res.json();
}

export async function simulateRuntime(schemas: {
  ui: Record<string, unknown>;
  api: Record<string, unknown>;
  db: Record<string, unknown>;
  auth: Record<string, unknown>;
}): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(schemas),
  });
  if (!res.ok) throw new Error("Simulation failed");
  return res.json();
}

export async function runEvaluation(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/evaluate`, { method: "POST" });
  if (!res.ok) throw new Error("Evaluation failed");
  return res.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
