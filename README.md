# FlowCompiler — AI Application Compiler

> **Production-grade AI system that converts natural language software requirements into complete, executable application configurations.**
> <img width="950" height="599" alt="image" src="https://github.com/user-attachments/assets/97bcd366-3d74-4a32-9d46-56907b35d27e" />


FlowCompiler behaves like a **compiler** for software applications: you provide a natural language description of what you want to build, and it generates production-ready UI, API, Database, and Auth schemas — validated, repaired, and simulation-tested.

```
"Build a CRM with login, contacts, dashboard,
 role-based access, payments, and analytics."
          ↓
┌─────────────────────────────────────────┐
│  1. Intent Extraction                    │
│  2. System Design                        │
│  3. Schema Generation (UI/API/DB/Auth)   │
│  4. Cross-Layer Validation               │
│  5. Targeted Repair Engine               │
│  6. Runtime Simulation                   │
└─────────────────────────────────────────┘
          ↓
   Executable Configuration (JSON)
```

---

## Architecture

```
src/
├── api/                    # FastAPI routes
│   └── routes.py
├── agents/                 # AI pipeline agents
│   ├── base_agent.py       # Abstract base with retry/structured outputs
│   ├── intent_extractor.py # Stage 1: NL → structured intent
│   ├── system_designer.py  # Stage 2: Intent → architecture
│   ├── schema_generator.py # Stage 3: Architecture → 4 schemas
│   ├── validator.py        # Stage 4: Cross-layer validation
│   ├── repair_agent.py     # Stage 5: Targeted repair engine
│   ├── execution_simulator.py # Stage 6: Runtime simulation
│   └── pipeline.py         # LangGraph orchestrator
├── schemas/                # Pydantic v2 models
│   ├── intent_schema.py
│   ├── system_design_schema.py
│   ├── ui_schema.py
│   ├── api_schema.py
│   ├── db_schema.py
│   ├── auth_schema.py
│   ├── validation_schema.py
│   └── runtime_schema.py
├── runtime/                # Config → executable code generators
│   ├── ui_runtime.py
│   ├── api_runtime.py
│   └── db_runtime.py
├── evaluation/             # Benchmark framework
│   ├── benchmark.py
│   ├── metrics.py
│   └── dataset.json        # 20 benchmark prompts
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── test_schemas.py
│   ├── test_validator.py
│   └── test_api.py
├── app.py                  # FastAPI application
└── config.py               # Settings management
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- OpenAI API key
- PostgreSQL (optional, for full deployment)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/dewanggandhi01/FlowCompiler.git
cd FlowCompiler

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start Backend

```bash
uvicorn src.app:app --reload --port 8000
```

### 3. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:3000** for the dashboard.

### 4. Docker (Full Stack)

```bash
docker-compose up --build
```

---

## API Reference

### POST `/generate`
Full pipeline execution from prompt to runtime config.

**Request:**
```json
{
  "prompt": "Build a CRM with login, contacts, dashboard, role-based access, payments, and analytics."
}
```

**Response:** `CompilerOutput` with all stage results, schemas, validation, simulation, and metrics.

### POST `/validate`
Validate existing schemas across all four layers.

```json
{
  "ui": { ... },
  "api": { ... },
  "db": { ... },
  "auth": { ... }
}
```

### POST `/repair`
Repair failing schemas with targeted fixes.

### POST `/simulate`
Run execution simulation on generated schemas.

### POST `/evaluate`
Run the 20-prompt benchmark suite with metrics.

### GET `/health`
Health check endpoint.

---

## Testing

```bash
# Run all tests
pytest src/tests/ -v

# With coverage
pytest src/tests/ --cov=src --cov-report=html -v

# Specific test file
pytest src/tests/test_validator.py -v
```

---

## Evaluation Benchmark

20 prompts (10 normal + 10 edge cases) testing:
- CRM, ERP, LMS, E-commerce, Booking, etc.
- Ambiguous, contradictory, minimal, overly complex inputs
- Non-English prompts

Metrics tracked: success rate, validation failures, repair count, runtime pass rate, latency, cost.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS, ShadCN UI |
| Backend | FastAPI, Python 3.12 |
| AI | LangGraph, LangChain, OpenAI (GPT-4o, Structured Outputs) |
| Database | PostgreSQL |
| Validation | Pydantic v2, JSON Schema |
| Deployment | Docker, Vercel, Render |

---

## License

MIT
