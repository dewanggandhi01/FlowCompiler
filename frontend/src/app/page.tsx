"use client";

import { useState } from "react";
import { generateApp, CompilerOutput } from "@/lib/api";

// ── Example Prompts ──────────────────────────────────────

const EXAMPLE_PROMPTS = [
  "Build a CRM with login, contacts, dashboard, role-based access, payments, and admin analytics.",
  "Create an e-commerce platform with product catalog, cart, checkout, reviews, and admin dashboard.",
  "Build a project management tool with tasks, sprints, kanban boards, team members, and time tracking.",
  "Create a Learning Management System with courses, quizzes, certificates, and progress tracking.",
  "Build a booking system for a salon with services, appointments, reviews, and payment processing.",
];

// ── Pipeline Stages ──────────────────────────────────────

const STAGES = [
  { key: "intent_extraction", label: "Intent Extraction", icon: "🔍", desc: "Extract entities, features, roles" },
  { key: "system_design", label: "System Design", icon: "📐", desc: "Architecture & relationships" },
  { key: "schema_generation", label: "Schema Generation", icon: "⚙️", desc: "UI, API, DB, Auth schemas" },
  { key: "validation", label: "Validation", icon: "✅", desc: "Cross-layer integrity" },
  { key: "repair", label: "Repair Engine", icon: "🔧", desc: "Targeted fixes" },
  { key: "execution_simulation", label: "Simulation", icon: "🚀", desc: "Runtime verification" },
];

// ── Stage Status Component ───────────────────────────────

function StageStatus({ status }: { status: string }) {
  const classes: Record<string, string> = {
    completed: "badge-pass",
    failed: "badge-fail",
    running: "badge-running",
    pending: "badge-pending",
  };
  return <span className={`badge ${classes[status] || "badge-pending"}`}>{status}</span>;
}

// ── Main Page ────────────────────────────────────────────

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompilerOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"intent" | "design" | "ui" | "api" | "db" | "auth">("intent");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const output = await generateApp(prompt);
      setResult(output);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const getStageStatus = (key: string): string => {
    if (!result) return loading ? (key === "intent_extraction" ? "running" : "pending") : "pending";
    const stage = result.stages.find((s) => s.stage === key || s.stage.startsWith(key));
    return stage?.status || "pending";
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <header style={{ textAlign: "center", marginBottom: 48 }}>
        <h1 style={{ fontSize: 40, fontWeight: 800, marginBottom: 8 }}>
          <span className="gradient-text">FlowCompiler</span>
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 600, margin: "0 auto" }}>
          AI Application Compiler — Convert natural language into production-ready application configurations
        </p>
      </header>

      {/* Section 1: Prompt Input */}
      <section className="glass-card full-width animate-slide-in" style={{ padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <span>💬</span> Describe Your Application
        </h2>
        <textarea
          className="prompt-input"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Build a CRM with login, contacts management, dashboard, role-based access, payments, and admin analytics..."
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
          {EXAMPLE_PROMPTS.map((ex, i) => (
            <button
              key={i}
              onClick={() => setPrompt(ex)}
              style={{
                padding: "6px 12px",
                fontSize: 12,
                background: "rgba(99, 102, 241, 0.1)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: 8,
                color: "var(--text-secondary)",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.color = "var(--accent-light)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.2)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
            >
              {ex.length > 60 ? ex.slice(0, 60) + "..." : ex}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 16 }}>
          <button className="btn-primary" onClick={handleGenerate} disabled={loading || !prompt.trim()}>
            {loading ? (
              <>
                <span className="animate-spin-slow" style={{ display: "inline-block" }}>⚙️</span>
                Compiling...
              </>
            ) : (
              <>🚀 Compile Application</>
            )}
          </button>
          {error && <span style={{ color: "var(--error)", fontSize: 14 }}>❌ {error}</span>}
        </div>
      </section>

      {/* Section 2: Pipeline View */}
      <section className="glass-card full-width animate-slide-in" style={{ padding: 24, marginBottom: 24, animationDelay: "0.1s" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>📊 Compilation Pipeline</h2>
        <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 8 }}>
          {STAGES.map((stage, i) => {
            const status = getStageStatus(stage.key);
            return (
              <div key={stage.key} style={{ display: "flex", alignItems: "center" }}>
                <div
                  className={`glass-card ${status === "running" ? "animate-pulse-glow" : ""}`}
                  style={{
                    padding: "16px 20px",
                    minWidth: 160,
                    textAlign: "center",
                    borderColor: status === "completed" ? "rgba(16, 185, 129, 0.3)" : status === "failed" ? "rgba(239, 68, 68, 0.3)" : undefined,
                  }}
                >
                  <div style={{ fontSize: 24, marginBottom: 4 }}>{stage.icon}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{stage.label}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>{stage.desc}</div>
                  <StageStatus status={status} />
                </div>
                {i < STAGES.length - 1 && (
                  <div style={{ padding: "0 4px", color: "var(--text-muted)", fontSize: 18 }}>→</div>
                )}
              </div>
            );
          })}
        </div>
        {result && (
          <div style={{ display: "flex", gap: 24, marginTop: 16, flexWrap: "wrap" }}>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              ⏱️ <strong>{((result.total_duration_ms || 0) / 1000).toFixed(1)}s</strong> total
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              🔤 <strong>{result.total_tokens.toLocaleString()}</strong> tokens
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              💰 <strong>${result.estimated_cost_usd.toFixed(4)}</strong> cost
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              🔧 <strong>{result.repair_iterations}</strong> repair iterations
            </div>
          </div>
        )}
      </section>

      {result && (
        <div className="dashboard-grid">
          {/* Section 3: Generated Schemas */}
          <section className="glass-card full-width animate-slide-in" style={{ padding: 24, animationDelay: "0.2s" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>📋 Generated Schemas</h2>
            <div style={{ display: "flex", gap: 4, marginBottom: 16, overflowX: "auto", paddingBottom: 4 }}>
              {(["intent", "design", "ui", "api", "db", "auth"] as const).map((tab) => (
                <button key={tab} className={`tab-btn ${activeTab === tab ? "active" : ""}`} onClick={() => setActiveTab(tab)}>
                  {tab === "intent" ? "Extracted Intent" : tab === "design" ? "System Design" : tab.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="code-block" style={{ maxHeight: 500, overflow: "auto" }}>
              {activeTab === "intent" ? (
                result.intent ? (
                  <pre>{JSON.stringify(result.intent, null, 2)}</pre>
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>No intent extracted</span>
                )
              ) : activeTab === "design" ? (
                result.system_design ? (
                  <pre>{JSON.stringify(result.system_design, null, 2)}</pre>
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>No system design generated</span>
                )
              ) : result.runtime_config ? (
                <pre>{JSON.stringify(result.runtime_config[activeTab as "ui" | "api" | "db" | "auth"], null, 2)}</pre>
              ) : (
                <span style={{ color: "var(--text-muted)" }}>No schemas generated</span>
              )}
            </div>
          </section>

          {/* Section 4: Validation Results */}
          <section className="glass-card animate-slide-in" style={{ padding: 24, animationDelay: "0.3s" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
              ✅ Validation Results
              {result.validation_result && (
                <span className={`badge ${result.validation_result.status === "PASS" ? "badge-pass" : "badge-fail"}`} style={{ marginLeft: 12 }}>
                  {result.validation_result.status}
                </span>
              )}
            </h2>
            {result.validation_result ? (
              <div>
                <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    Checks: <strong>{result.validation_result.passed_checks}/{result.validation_result.total_checks}</strong>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--error)" }}>
                    Errors: <strong>{result.validation_result.errors.length}</strong>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--warning)" }}>
                    Warnings: <strong>{result.validation_result.warnings.length}</strong>
                  </div>
                </div>
                {result.validation_result.errors.length > 0 && (
                  <div style={{ maxHeight: 300, overflow: "auto" }}>
                    {result.validation_result.errors.map((err, i) => (
                      <div key={i} style={{
                        padding: "10px 12px",
                        marginBottom: 6,
                        borderRadius: 8,
                        background: "rgba(239, 68, 68, 0.08)",
                        borderLeft: "3px solid var(--error)",
                        fontSize: 13,
                      }}>
                        <div style={{ fontWeight: 600, marginBottom: 2 }}>[{err.layer}] {err.field}</div>
                        <div style={{ color: "var(--text-secondary)" }}>{err.message}</div>
                        {err.fix_suggestion && (
                          <div style={{ color: "var(--info)", marginTop: 4, fontSize: 12 }}>💡 {err.fix_suggestion}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>No validation results yet</p>
            )}
          </section>

          {/* Section 5: Repair Logs */}
          <section className="glass-card animate-slide-in" style={{ padding: 24, animationDelay: "0.4s" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>🔧 Repair Logs</h2>
            {result.repair_reports.length > 0 ? (
              <div>
                <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
                  Total iterations: <strong>{result.repair_iterations}</strong>
                </div>
                {result.repair_reports.map((report, i) => (
                  <div key={i} style={{
                    padding: "12px 14px",
                    marginBottom: 8,
                    borderRadius: 8,
                    background: report.success ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
                    borderLeft: `3px solid ${report.success ? "var(--success)" : "var(--warning)"}`,
                  }}>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                      Iteration {report.iteration} — {report.success ? "✅ All fixed" : "⚠️ Partial fix"}
                    </div>
                    {report.changes_made.map((change, j) => (
                      <div key={j} style={{ fontSize: 12, color: "var(--text-secondary)", marginLeft: 8 }}>
                        • {change}
                      </div>
                    ))}
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                      Fixed: {report.errors_fixed.length} | Remaining: {report.errors_remaining.length}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
                {result.validation_result?.status === "PASS"
                  ? "✅ No repairs needed — validation passed on first try!"
                  : "No repair data available"
                }
              </p>
            )}
          </section>

          {/* Section 6: Runtime Simulation */}
          <section className="glass-card animate-slide-in" style={{ padding: 24, animationDelay: "0.5s" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
              🚀 Runtime Simulation
              {result.simulation_result && (
                <span className={`badge ${result.simulation_result.runtime_status === "PASS" ? "badge-pass" : "badge-fail"}`} style={{ marginLeft: 12 }}>
                  {result.simulation_result.runtime_status}
                </span>
              )}
            </h2>
            {result.simulation_result ? (
              <div>
                <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    Checks: <strong>{result.simulation_result.passed_checks}/{result.simulation_result.simulated_checks}</strong>
                  </div>
                  <div style={{ fontSize: 13, color: "var(--error)" }}>
                    Issues: <strong>{result.simulation_result.issues.length}</strong>
                  </div>
                </div>
                {result.simulation_result.issues.length > 0 && (
                  <div style={{ maxHeight: 250, overflow: "auto" }}>
                    {result.simulation_result.issues.map((issue, i) => (
                      <div key={i} style={{
                        padding: "8px 12px",
                        marginBottom: 4,
                        borderRadius: 6,
                        background: issue.severity === "error" ? "rgba(239, 68, 68, 0.06)" : "rgba(245, 158, 11, 0.06)",
                        fontSize: 12,
                      }}>
                        <span className={`badge ${issue.severity === "error" ? "badge-fail" : "badge-pending"}`} style={{ marginRight: 8 }}>
                          {issue.category}
                        </span>
                        {issue.description}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>No simulation results</p>
            )}
          </section>

          {/* Section 7: Metrics & Assumptions */}
          <section className="glass-card full-width animate-slide-in" style={{ padding: 24, animationDelay: "0.6s" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>📊 Compilation Metrics</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
              {[
                { label: "Status", value: result.status, color: result.status === "completed" ? "var(--success)" : "var(--error)" },
                { label: "Duration", value: `${((result.total_duration_ms || 0) / 1000).toFixed(1)}s`, color: "var(--accent-light)" },
                { label: "Total Tokens", value: result.total_tokens.toLocaleString(), color: "var(--info)" },
                { label: "Est. Cost", value: `$${result.estimated_cost_usd.toFixed(4)}`, color: "var(--warning)" },
                { label: "Repair Iterations", value: String(result.repair_iterations), color: "var(--accent-light)" },
                { label: "Assumptions", value: String(result.assumptions.length), color: "var(--text-secondary)" },
              ].map((metric, i) => (
                <div key={i} className="glass-card" style={{ padding: "16px 20px", textAlign: "center" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {metric.label}
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: metric.color }}>{metric.value}</div>
                </div>
              ))}
            </div>

            {result.assumptions.length > 0 && (
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "var(--text-secondary)" }}>
                  Assumptions Made ({result.assumptions.length})
                </h3>
                <div style={{ maxHeight: 200, overflow: "auto" }}>
                  {result.assumptions.map((a, i) => (
                    <div key={i} style={{ padding: "8px 12px", marginBottom: 4, fontSize: 13, borderLeft: "2px solid var(--accent)", paddingLeft: 12 }}>
                      <strong style={{ color: "var(--accent-light)" }}>{a.category}:</strong>{" "}
                      <span style={{ color: "var(--text-secondary)" }}>{a.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
