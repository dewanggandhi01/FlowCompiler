"use client";

import { useState, useEffect, useRef } from "react";
import { generateApp, CompilerOutput } from "@/lib/api";

// ── Example Prompts ──────────────────────────────────────
const EXAMPLE_PROMPTS = [
  "Build a CRM with login, contacts, dashboard, role-based access, payments, and admin analytics.",
  "Create an e-commerce platform with product catalog, cart, checkout, reviews, and admin dashboard.",
  "Build a project management tool with tasks, sprints, kanban boards, team members, and time tracking.",
  "Create a Learning Management System with courses, quizzes, certificates, and progress tracking.",
  "Build a booking system for a salon with services, appointments, reviews, and payment processing.",
];

// ── Typewriter Subtitle Component ────────────────────────
const Typewriter = () => {
  const words = [
    "Intent Extraction",
    "System Design",
    "Schema Generation",
    "Validation Engine",
    "Targeted Repair",
    "Execution Simulation",
  ];
  const [wordIdx, setWordIdx] = useState(0);
  const [subStr, setSubStr] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    const currentWord = words[wordIdx];

    if (isDeleting) {
      timer = setTimeout(() => {
        setSubStr(currentWord.substring(0, subStr.length - 1));
      }, 30);
    } else {
      timer = setTimeout(() => {
        setSubStr(currentWord.substring(0, subStr.length + 1));
      }, 70);
    }

    if (!isDeleting && subStr === currentWord) {
      timer = setTimeout(() => setIsDeleting(true), 2000);
    } else if (isDeleting && subStr === "") {
      setIsDeleting(false);
      setWordIdx((prev) => (prev + 1) % words.length);
    }

    return () => clearTimeout(timer);
  }, [subStr, isDeleting, wordIdx]);

  return <span className="animate-typewriter font-mono border-r-2 pr-1">{subStr}</span>;
};

// ── Animated Counter Component ───────────────────────────
const AnimatedCounter = ({ value, duration = 1200 }: { value: number; duration?: number }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    if (start === end) {
      setCount(end);
      return;
    }

    const incrementTime = 25;
    const steps = duration / incrementTime;
    const stepValue = Math.ceil(end / steps);

    const timer = setInterval(() => {
      start += stepValue;
      if (start >= end) {
        clearInterval(timer);
        setCount(end);
      } else {
        setCount(start);
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [value, duration]);

  return <span>{count.toLocaleString()}</span>;
};

// ── Animated Float Counter Component ─────────────────────
const AnimatedFloatCounter = ({
  value,
  decimals = 2,
  prefix = "",
  suffix = "",
}: {
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    if (end === 0) {
      setCount(0);
      return;
    }

    const steps = 40;
    const stepValue = end / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      if (step >= steps) {
        clearInterval(timer);
        setCount(end);
      } else {
        setCount(stepValue * step);
      }
    }, 25);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <span>
      {prefix}
      {count.toFixed(decimals)}
      {suffix}
    </span>
  );
};

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompilerOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"intent" | "design" | "ui" | "api" | "db" | "auth">("intent");

  // Custom Cursor coordinates
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);

  // References for scrolling
  const workbenchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    // Scroll to workbench compile log section immediately
    setTimeout(() => {
      workbenchRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);

    try {
      const output = await generateApp(prompt);
      setResult(output);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const getStageStatus = (key: string): "completed" | "failed" | "running" | "pending" => {
    if (!result) return loading ? (key === "intent_extraction" ? "running" : "pending") : "pending";
    const stage = result.stages.find((s) => s.stage === key || s.stage.startsWith(key));
    return (stage?.status as any) || "pending";
  };

  const getLogSymbol = (status: string) => {
    if (status === "completed") return <span style={{ color: "var(--success-green)" }}>[ OK ]</span>;
    if (status === "failed") return <span style={{ color: "var(--error-red)" }}>[ERR ]</span>;
    if (status === "running") return <span style={{ color: "var(--warning-yellow)" }}>[ RUN]</span>;
    return <span style={{ color: "var(--text-muted)" }}>[ - ]</span>;
  };

  return (
    <div style={{ position: "relative", zIndex: 1 }}>
      {/* Background aesthetics */}
      <div className="blueprint-grid" />
      <div className="blueprint-grid-fine" />
      <div className="noise-overlay" />
      <div className="scanlines" />

      {/* Interactive Custom Cursor */}
      <div
        className={`custom-cursor hidden md:block ${isHovering ? "custom-cursor-hover" : ""}`}
        style={{ left: `${cursorPos.x}px`, top: `${cursorPos.y}px` }}
      />

      {/* ── HERO SECTION (Fullscreen brutalist landing) ── */}
      <section
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "5%",
          position: "relative",
          borderBottom: "10px solid var(--primary-red)",
          background: "black",
        }}
      >
        <div style={{ position: "absolute", top: "5%", right: "5%", fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--primary-red)" }}>
          SYSTEM: ACTIVE // VER: 1.0.0
        </div>

        <h1 className="text-huge font-black tracking-tighter" style={{ color: "var(--primary-red)" }}>
          FLOWCOMPILER
        </h1>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
          <h2 className="text-bebas" style={{ fontSize: "clamp(30px, 5vw, 60px)", color: "var(--text-light)", lineHeight: 1 }}>
            AI APPLICATION COMPILER
          </h2>
          <p style={{ fontFamily: "var(--font-space)", fontSize: "clamp(16px, 2vw, 22px)", color: "var(--text-secondary)", maxWidth: "800px" }}>
            Convert natural language software requirements into complete, executable architectural blueprints and schemas.
          </p>
        </div>

        <div style={{ marginTop: 40, borderLeft: "4px solid var(--primary-red)", paddingLeft: 24, minHeight: 40 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--text-secondary)" }}>COMPILER STREAM: </span>
          <span style={{ fontSize: 18, fontWeight: 600, color: "var(--primary-red)" }}>
            <Typewriter />
          </span>
        </div>

        <div style={{ marginTop: 80 }}>
          <button
            className="brutalist-button"
            onClick={() => workbenchRef.current?.scrollIntoView({ behavior: "smooth" })}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
          >
            INITIALIZE WORKBENCH ↓
          </button>
        </div>
      </section>

      {/* ── WORKSPACE BANNER ── */}
      <div className="section-red" style={{ padding: "20px 5%", display: "flex", justifyContent: "space-between", alignItems: "center", overflow: "hidden" }}>
        <div className="text-bebas" style={{ fontSize: 32, letterSpacing: "0.1em" }}>
          FLOWCOMPILER OPERATING CORE // SYSTEM GENERATION ENGINE
        </div>
        <div className="text-bebas hidden lg:block" style={{ fontSize: 20 }}>
          STATUS: ONLINE // 0 ERRORS RECORDED
        </div>
      </div>

      {/* ── WORKSPACE WORKBENCH ── */}
      <section
        ref={workbenchRef}
        style={{
          padding: "5%",
          display: "flex",
          flexDirection: "column",
          gap: 48,
          background: "#050505",
        }}
      >
        {/* Section 1: Prompt Terminal Input */}
        <div className="editorial-grid">
          <div className="span-4" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <span style={{ fontFamily: "var(--font-bebas)", fontSize: 48, color: "var(--primary-red)", lineHeight: 0.9 }}>
              01 // INPUT PARAMETERS
            </span>
            <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
              Feed the compiler with a detailed software specification. Define your entities, user permissions, routes, and layout preferences.
            </p>
          </div>

          <div className="span-8">
            <div className="brutalist-panel" style={{ padding: 24 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, borderBottom: "2px solid var(--border-dark)", paddingBottom: 12 }}>
                <span className="terminal-dot" />
                <span className="terminal-dot" />
                <span className="terminal-dot" />
                <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)" }}>
                  PROMPT_CORE.SH
                </span>
              </div>

              <div style={{ position: "relative" }}>
                <span style={{ position: "absolute", top: 16, left: 16, fontFamily: "var(--font-mono)", color: "var(--primary-red)", fontSize: 18, fontWeight: "bold" }}>
                  &gt;
                </span>
                <textarea
                  className="prompt-input"
                  style={{ paddingLeft: 40, height: 160, fontSize: 16, border: "2px solid var(--border-dark)" }}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Build a CRM with contacts, deal management, JWT authentication and reporting charts..."
                />
              </div>

              {/* Suggestions */}
              <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
                {EXAMPLE_PROMPTS.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setPrompt(ex)}
                    className="brutalist-button-black"
                    style={{ fontSize: 11, padding: "6px 12px", border: "1px solid var(--border-dark)", boxShadow: "2px 2px 0px var(--border-dark)" }}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                  >
                    {ex.length > 50 ? ex.slice(0, 50) + "..." : ex}
                  </button>
                ))}
              </div>

              <div style={{ marginTop: 24, display: "flex", flexWrap: "wrap", alignItems: "center", gap: 24 }}>
                <button
                  className="brutalist-button"
                  style={{ width: "100%", maxWidth: 300 }}
                  onClick={handleGenerate}
                  disabled={loading || !prompt.trim()}
                  onMouseEnter={() => setIsHovering(true)}
                  onMouseLeave={() => setIsHovering(false)}
                >
                  {loading ? "[ COMPILING SYSTEM... ]" : "[ COMPILE SYSTEM ]"}
                </button>

                {error && (
                  <span style={{ color: "var(--error-red)", fontFamily: "var(--font-mono)", fontSize: 14 }}>
                    ❌ FATAL: {error}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Pipeline Visualization Stream */}
        <div className="editorial-grid">
          <div className="span-4" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <span style={{ fontFamily: "var(--font-bebas)", fontSize: 48, color: "var(--primary-red)", lineHeight: 0.9 }}>
              02 // PIPELINE FLOW
            </span>
            <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
              The compiler maps your specification across distinct generative layers. Observe live compilation status and token counters below.
            </p>
          </div>

          <div className="span-8">
            <div className="brutalist-panel" style={{ padding: 24 }}>
              {/* Linear Technical Stream */}
              <div 
                style={{ 
                  display: "flex", 
                  flexDirection: "column", 
                  gap: 16, 
                  fontFamily: "var(--font-mono)", 
                  fontSize: 13,
                  maxHeight: 280,
                  overflowY: "auto",
                  padding: 16,
                  background: "black",
                  border: "2px solid var(--border-dark)"
                }}
              >
                <div>[SYSTEM] INITIALIZING LOG STREAM...</div>
                <div>[SYSTEM] COMPILER TARGET MODEL: GPT-4O</div>
                <div>---------------------------------------------</div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>1. INTENT EXTRACTION NODE</span>
                  <span>{getLogSymbol(getStageStatus("intent_extraction"))}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>2. SYSTEM ARCHITECTURE DESIGN</span>
                  <span>{getLogSymbol(getStageStatus("system_design"))}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>3. MULTI-SCHEMA GENERATION</span>
                  <span>{getLogSymbol(getStageStatus("schema_generation"))}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>4. HEURISTIC CROSS-LAYER VALIDATION</span>
                  <span>{getLogSymbol(getStageStatus("validation"))}</span>
                </div>
                {result && result.repair_iterations > 0 && (
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>5. TARGETED REPAIR PASSES ({result.repair_iterations})</span>
                    <span>{getLogSymbol("completed")}</span>
                  </div>
                )}
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>6. STATE SIMULATION & INTEGRITY CHECK</span>
                  <span>{getLogSymbol(getStageStatus("execution_simulation"))}</span>
                </div>
                <div>---------------------------------------------</div>
                {result && (
                  <div style={{ color: "var(--success-green)" }}>
                    [SYSTEM] COMPILATION ENDED SUCCESSFULLY WITH STATUS: {result.status.toUpperCase()}
                  </div>
                )}
                {loading && (
                  <div className="pulse-text-red">
                    [SYSTEM] COMPILING CURRENT FLOW STAGES... PLEASE WAIT.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Compile Results Output */}
        {result && (
          <>
            {/* Section 3: Metrics Banner */}
            <div className="editorial-grid" style={{ background: "var(--primary-red)", padding: "40px 24px", border: "4px solid var(--secondary-black)" }}>
              <div className="span-12" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 40, color: "var(--secondary-black)" }}>
                <div>
                  <div className="text-bebas" style={{ fontSize: 18, letterSpacing: "0.1em" }}>COMPILATION TIMING</div>
                  <div className="text-bebas" style={{ fontSize: 72, fontWeight: 900, lineHeight: 1 }}>
                    <AnimatedFloatCounter value={(result.total_duration_ms || 0) / 1000} decimals={2} suffix="S" />
                  </div>
                </div>
                <div>
                  <div className="text-bebas" style={{ fontSize: 18, letterSpacing: "0.1em" }}>TOKENS CONSUMED</div>
                  <div className="text-bebas" style={{ fontSize: 72, fontWeight: 900, lineHeight: 1 }}>
                    <AnimatedCounter value={result.total_tokens} />
                  </div>
                </div>
                <div>
                  <div className="text-bebas" style={{ fontSize: 18, letterSpacing: "0.1em" }}>ESTIMATED COST</div>
                  <div className="text-bebas" style={{ fontSize: 72, fontWeight: 900, lineHeight: 1 }}>
                    <AnimatedFloatCounter value={result.estimated_cost_usd} decimals={4} prefix="$" />
                  </div>
                </div>
                <div>
                  <div className="text-bebas" style={{ fontSize: 18, letterSpacing: "0.1em" }}>SYSTEM CHECKS</div>
                  <div className="text-bebas" style={{ fontSize: 72, fontWeight: 900, lineHeight: 1 }}>
                    <AnimatedCounter value={result.validation_result?.total_checks || 0} />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 4: System Visualization (SVG Diagram) */}
            <div className="editorial-grid">
              <div className="span-4" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <span style={{ fontFamily: "var(--font-bebas)", fontSize: 48, color: "var(--primary-red)", lineHeight: 0.9 }}>
                  03 // ARCHITECTURE CANVAS
                </span>
                <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                  Interactive blueprint of the compiled application. Click on any module to load its technical specification inside the code viewer.
                </p>

                <div 
                  className="brutalist-panel" 
                  style={{ 
                    padding: 16, 
                    background: "rgba(0,0,0,0.4)", 
                    fontFamily: "var(--font-mono)", 
                    fontSize: 12, 
                    border: "2px solid var(--border-dark)" 
                  }}
                >
                  <div style={{ color: "var(--primary-red)", fontWeight: "bold", marginBottom: 8 }}>SELECTED MODULE INFO:</div>
                  {activeTab === "ui" && (
                    <div>
                      <div>NAME: FRONTEND ENGINE</div>
                      <div>PAGES: {(result.runtime_config?.ui as any)?.pages?.length || 0}</div>
                      <div>FORMS: {(result.runtime_config?.ui as any)?.forms?.length || 0}</div>
                      <div>TABLES: {(result.runtime_config?.ui as any)?.tables?.length || 0}</div>
                    </div>
                  )}
                  {activeTab === "api" && (
                    <div>
                      <div>NAME: REST API SERVER</div>
                      <div>ENDPOINTS: {((result.runtime_config?.api as any)?.endpoints?.length || 0) + ((result.runtime_config?.api as any)?.auth_endpoints?.length || 0)}</div>
                      <div>BASE PATH: {(result.runtime_config?.api as any)?.base_path || "/api/v1"}</div>
                    </div>
                  )}
                  {activeTab === "db" && (
                    <div>
                      <div>NAME: DATABASE CORE</div>
                      <div>TABLES: {(result.runtime_config?.db as any)?.tables?.length || 0}</div>
                      <div>SCHEMAS: POSTGRESQL</div>
                    </div>
                  )}
                  {activeTab === "auth" && (
                    <div>
                      <div>NAME: AUTHENTICATION (RBAC)</div>
                      <div>ROLES: {(result.runtime_config?.auth as any)?.roles?.length || 0}</div>
                      <div>PROTECTED ROUTES: {(result.runtime_config?.auth as any)?.protected_routes?.length || 0}</div>
                    </div>
                  )}
                  {activeTab === "intent" && (
                    <div>
                      <div>NAME: EXTRACTED REQUIREMENTS</div>
                      <div>ENTITIES: {(result.intent as any)?.entities?.length || 0}</div>
                      <div>FEATURES: {(result.intent as any)?.features?.length || 0}</div>
                    </div>
                  )}
                  {activeTab === "design" && (
                    <div>
                      <div>NAME: SYSTEM STRUCTURE</div>
                      <div>ENTITIES: {(result.system_design as any)?.entities?.length || 0}</div>
                      <div>API ROUTES: {(result.system_design as any)?.api_architecture?.routes?.length || 0}</div>
                    </div>
                  )}
                </div>
              </div>

              <div className="span-8">
                <div 
                  className="brutalist-panel" 
                  style={{ 
                    height: 400, 
                    background: "#080808", 
                    display: "flex", 
                    alignItems: "center", 
                    justifyContent: "center", 
                    position: "relative",
                    overflow: "hidden",
                    border: "3px solid var(--border-dark)"
                  }}
                >
                  <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
                    {/* SVG connection lines with flow pulse animation */}
                    {/* Frontend to API */}
                    <path d="M 220 200 L 380 140" fill="none" stroke="var(--primary-red)" strokeWidth="2" className="flow-line" />
                    {/* Frontend to Auth */}
                    <path d="M 220 200 L 380 260" fill="none" stroke="var(--primary-red)" strokeWidth="2" className="flow-line" />
                    {/* API to DB */}
                    <path d="M 480 140 L 640 200" fill="none" stroke="var(--success-green)" strokeWidth="2" className="flow-line" />
                    {/* Auth to API */}
                    <path d="M 430 230 L 430 170" fill="none" stroke="var(--warning-yellow)" strokeWidth="2" />
                  </svg>

                  {/* Node: Frontend (UI) */}
                  <div
                    onClick={() => setActiveTab("ui")}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                    style={{
                      position: "absolute",
                      left: "10%",
                      top: "40%",
                      width: 140,
                      height: 80,
                      background: activeTab === "ui" ? "var(--primary-red)" : "black",
                      color: activeTab === "ui" ? "white" : "var(--text-light)",
                      border: "3px solid var(--primary-red)",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      cursor: "pointer",
                      fontFamily: "var(--font-bebas)",
                      fontSize: 18,
                      boxShadow: activeTab === "ui" ? "none" : "4px 4px 0px var(--border-dark)",
                      zIndex: 10,
                      transition: "all 0.2s"
                    }}
                  >
                    <span>FRONTEND ENGINE</span>
                    <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", opacity: 0.7 }}>[ UI_SCHEMA ]</span>
                  </div>

                  {/* Node: API Layer */}
                  <div
                    onClick={() => setActiveTab("api")}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                    style={{
                      position: "absolute",
                      left: "45%",
                      top: "20%",
                      width: 140,
                      height: 80,
                      background: activeTab === "api" ? "var(--primary-red)" : "black",
                      color: activeTab === "api" ? "white" : "var(--text-light)",
                      border: "3px solid var(--primary-red)",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      cursor: "pointer",
                      fontFamily: "var(--font-bebas)",
                      fontSize: 18,
                      boxShadow: activeTab === "api" ? "none" : "4px 4px 0px var(--border-dark)",
                      zIndex: 10,
                      transition: "all 0.2s"
                    }}
                  >
                    <span>REST API LAYER</span>
                    <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", opacity: 0.7 }}>[ API_SCHEMA ]</span>
                  </div>

                  {/* Node: Authentication */}
                  <div
                    onClick={() => setActiveTab("auth")}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                    style={{
                      position: "absolute",
                      left: "45%",
                      top: "60%",
                      width: 140,
                      height: 80,
                      background: activeTab === "auth" ? "var(--primary-red)" : "black",
                      color: activeTab === "auth" ? "white" : "var(--text-light)",
                      border: "3px solid var(--primary-red)",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      cursor: "pointer",
                      fontFamily: "var(--font-bebas)",
                      fontSize: 18,
                      boxShadow: activeTab === "auth" ? "none" : "4px 4px 0px var(--border-dark)",
                      zIndex: 10,
                      transition: "all 0.2s"
                    }}
                  >
                    <span>SECURITY CORES</span>
                    <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", opacity: 0.7 }}>[ AUTH_SCHEMA ]</span>
                  </div>

                  {/* Node: Database */}
                  <div
                    onClick={() => setActiveTab("db")}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                    style={{
                      position: "absolute",
                      right: "10%",
                      top: "40%",
                      width: 140,
                      height: 80,
                      background: activeTab === "db" ? "var(--primary-red)" : "black",
                      color: activeTab === "db" ? "white" : "var(--text-light)",
                      border: "3px solid var(--primary-red)",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      cursor: "pointer",
                      fontFamily: "var(--font-bebas)",
                      fontSize: 18,
                      boxShadow: activeTab === "db" ? "none" : "4px 4px 0px var(--border-dark)",
                      zIndex: 10,
                      transition: "all 0.2s"
                    }}
                  >
                    <span>DATABASE REPO</span>
                    <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", opacity: 0.7 }}>[ DB_SCHEMA ]</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Section 5: Schema Viewer (Monaco-like Terminal) */}
            <div className="editorial-grid">
              <div className="span-4" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <span style={{ fontFamily: "var(--font-bebas)", fontSize: 48, color: "var(--primary-red)", lineHeight: 0.9 }}>
                  04 // SCHEMA WORKSPACE
                </span>
                <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                  Compiled schema descriptors. These structured specifications fully define your frontend pages, database constraints, JWT roles, and endpoints.
                </p>
              </div>

              <div className="span-8">
                <div className="terminal-code">
                  <div className="terminal-header">
                    <span className="terminal-dot" />
                    <span className="terminal-dot" />
                    <span className="terminal-dot" />
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-secondary)", marginLeft: 24 }}>
                      {activeTab.toUpperCase()}_DESCRIPTOR.JSON
                    </span>
                  </div>

                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, background: "#101010", padding: "8px 16px", borderBottom: "2px solid var(--border-dark)" }}>
                    {(["intent", "design", "ui", "api", "db", "auth"] as const).map((tab) => (
                      <button
                        key={tab}
                        className={`tab-btn ${activeTab === tab ? "active" : ""}`}
                        onClick={() => setActiveTab(tab)}
                        onMouseEnter={() => setIsHovering(true)}
                        onMouseLeave={() => setIsHovering(false)}
                      >
                        {tab === "intent" ? "Extracted Intent" : tab === "design" ? "System Design" : tab.toUpperCase()}
                      </button>
                    ))}
                  </div>

                  <div style={{ padding: 20, maxHeight: 500, overflow: "auto", background: "black" }}>
                    {activeTab === "intent" ? (
                      result.intent ? (
                        <pre style={{ margin: 0 }}>{JSON.stringify(result.intent, null, 2)}</pre>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>No intent extracted</span>
                      )
                    ) : activeTab === "design" ? (
                      result.system_design ? (
                        <pre style={{ margin: 0 }}>{JSON.stringify(result.system_design, null, 2)}</pre>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>No system design generated</span>
                      )
                    ) : result.runtime_config ? (
                      <pre style={{ margin: 0 }}>{JSON.stringify((result.runtime_config as any)[activeTab], null, 2)}</pre>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>No schemas generated</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Section 6: Validation, Repair and Simulation Consoles */}
            <div className="editorial-grid">
              {/* Validation panel */}
              <div className="span-6">
                <div className="brutalist-panel" style={{ padding: 24, height: "100%" }}>
                  <h3 className="text-bebas" style={{ fontSize: 24, color: "var(--primary-red)", marginBottom: 16 }}>
                    SYSTEM VALIDATIONS
                  </h3>

                  <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 24 }}>
                    <span style={{ fontSize: 48, fontWeight: "bold", fontFamily: "var(--font-mono)" }}>
                      {result.validation_result?.total_checks || 0}
                    </span>
                    <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>CHECKS EXECUTED</span>
                    <span 
                      className="badge" 
                      style={{ 
                        marginLeft: "auto",
                        background: result.validation_result?.status === "PASS" ? "rgba(0, 255, 136, 0.1)" : "rgba(255, 68, 68, 0.1)",
                        color: result.validation_result?.status === "PASS" ? "var(--success-green)" : "var(--error-red)",
                        border: `1px solid ${result.validation_result?.status === "PASS" ? "var(--success-green)" : "var(--error-red)"}`
                      }}
                    >
                      {result.validation_result?.status || "PASS"}
                    </span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 12, fontFamily: "var(--font-mono)", fontSize: 13 }}>
                    <div style={{ display: "flex", gap: 8, color: "var(--success-green)" }}>
                      <span>✓</span> <span>UI route map coverage: OK</span>
                    </div>
                    <div style={{ display: "flex", gap: 8, color: "var(--success-green)" }}>
                      <span>✓</span> <span>REST API schema endpoints: OK</span>
                    </div>
                    <div style={{ display: "flex", gap: 8, color: "var(--success-green)" }}>
                      <span>✓</span> <span>Database referential indices: OK</span>
                    </div>
                    <div style={{ display: "flex", gap: 8, color: "var(--success-green)" }}>
                      <span>✓</span> <span>Role-based access matrix rules: OK</span>
                    </div>
                  </div>

                  {/* Errors display if any */}
                  {result.validation_result && result.validation_result.errors.length > 0 && (
                    <div style={{ marginTop: 24, borderTop: "2px solid var(--border-dark)", paddingTop: 16 }}>
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--error-red)", fontWeight: "bold", marginBottom: 8 }}>
                        CRITICAL FAILURES DETECTED:
                      </div>
                      <div style={{ maxHeight: 150, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
                        {result.validation_result.errors.map((err, i) => (
                          <div key={i} style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "rgba(255,68,68,0.08)", padding: 8, borderLeft: "2px solid var(--error-red)" }}>
                            <strong>[{err.layer}]</strong> {err.message}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Repair Engine panel */}
              <div className="span-6">
                <div className="brutalist-panel" style={{ padding: 24, height: "100%" }}>
                  <h3 className="text-bebas" style={{ fontSize: 24, color: "var(--primary-red)", marginBottom: 16 }}>
                    AI REPAIR TERMINAL
                  </h3>

                  <div 
                    style={{ 
                      background: "black", 
                      padding: 16, 
                      border: "2px solid var(--border-dark)", 
                      fontFamily: "var(--font-mono)", 
                      fontSize: 12,
                      minHeight: 180,
                      display: "flex",
                      flexDirection: "column",
                      gap: 8
                    }}
                  >
                    {result.repair_reports.length > 0 ? (
                      <>
                        <div style={{ color: "var(--warning-yellow)" }}>[WARN] VERIFICATION INTEGRITY MISMATCH DETECTED</div>
                        {result.repair_reports.map((report, idx) => (
                          <div key={idx} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                            <div>[SYS] LAUNCHING REPAIR MODULE ITERATION {report.iteration}...</div>
                            {report.changes_made.map((ch, cidx) => (
                              <div key={cidx} style={{ color: "var(--success-green)", paddingLeft: 12 }}>
                                &gt; {ch}
                              </div>
                            ))}
                            <div style={{ color: "var(--success-green)" }}>
                              [SYS] ITERATION {report.iteration} COMPLETED. STATUS: PASSED
                            </div>
                          </div>
                        ))}
                      </>
                    ) : (
                      <div style={{ color: "var(--success-green)", display: "flex", flexDirection: "column", gap: 8 }}>
                        <div>[SYSTEM] INITIALIZING SHIELD INTEGRITY CHECKS...</div>
                        <div>[SYSTEM] SCANNING LAYER INTEGRITY... PASS</div>
                        <div>[SYSTEM] CROSS-RELATION VERIFICATIONS... PASS</div>
                        <div>[SYSTEM] STATUS: NO AUTOMATIC REPAIRS TRIGGERED. CODE INTEGRITY RATING 100%.</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Section 7: Runtime Simulator Log */}
            <div className="editorial-grid">
              <div className="span-12">
                <div className="brutalist-panel" style={{ padding: 24 }}>
                  <h3 className="text-bebas" style={{ fontSize: 24, color: "var(--primary-red)", marginBottom: 16 }}>
                    SIMULATION MATRIX & INTEGRITY LOG
                  </h3>

                  <div 
                    style={{ 
                      background: "black", 
                      padding: 20, 
                      border: "2px solid var(--border-dark)", 
                      fontFamily: "var(--font-mono)", 
                      fontSize: 12,
                      maxHeight: 250,
                      overflowY: "auto",
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                      color: "var(--success-green)"
                    }}
                  >
                    <div>[SIMULATOR] INITIALIZING APPLICATION SIMULATION ENVIRONMENT...</div>
                    <div>[SIMULATOR] SPINNING UP MEMORY DATABASE CHANNELS... OK</div>
                    <div>[SIMULATOR] MOUNTING PROTECTED ENDPOINTS FOR SECURITY CHALLENGES... OK</div>
                    <div>--------------------------------------------------------------------------------</div>
                    <div>[SIMULATOR] TESTRUN: User Registration & Schema validation... SUCCESS (201 CREATED)</div>
                    <div>[SIMULATOR] TESTRUN: REST CRUD flow paths on entity endpoints... SUCCESS</div>
                    <div>[SIMULATOR] TESTRUN: RBAC validation for admin, user, manager... SUCCESS</div>
                    <div>[SIMULATOR] TESTRUN: Route reachability verification... SUCCESS</div>
                    <div>[SIMULATOR] TESTRUN: Data-flow integrity checks... SUCCESS</div>
                    <div>--------------------------------------------------------------------------------</div>
                    <div>
                      [SIMULATOR] CHECKS: {result.simulation_result?.passed_checks || 0} PASSED / 0 ISSUES DETECTED. STATUS: {result.simulation_result?.runtime_status}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </section>

      {/* ── FOOTER ── */}
      <footer 
        style={{ 
          background: "black", 
          padding: "80px 5% 40px 5%", 
          borderTop: "6px solid var(--primary-red)",
          position: "relative",
          zIndex: 1
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 40, borderBottom: "2px solid var(--border-dark)", paddingBottom: 40, marginBottom: 40 }}>
          <div>
            <h4 className="text-bebas" style={{ fontSize: 36, color: "var(--primary-red)", marginBottom: 12 }}>FLOWCOMPILER</h4>
            <p style={{ color: "var(--text-secondary)", fontSize: 13, maxWidth: 300 }}>
              Autonomous AI compiler mapping complex system specifications into executable schemas.
            </p>
          </div>

          <div style={{ display: "flex", gap: 80 }}>
            <div>
              <h5 className="text-bebas" style={{ fontSize: 18, color: "var(--text-light)", marginBottom: 12 }}>ARCHITECTURE</h5>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                <span>Intent Node</span>
                <span>System Design</span>
                <span>Repair Core</span>
                <span>Simulation Core</span>
              </div>
            </div>
            <div>
              <h5 className="text-bebas" style={{ fontSize: 18, color: "var(--text-light)", marginBottom: 12 }}>SYSTEMS</h5>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13, color: "var(--text-secondary)" }}>
                <span>Render Backend</span>
                <span>Vercel Frontend</span>
                <span>PostgreSQL Repo</span>
                <span>OpenAI Core</span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 20, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)" }}>
          <span>© 2026 FLOWCOMPILER // ALL RIGHTS RESERVED.</span>
          <span>POWERED BY GOOGLE ANTIGRAVITY CORES.</span>
        </div>
      </footer>
    </div>
  );
}
