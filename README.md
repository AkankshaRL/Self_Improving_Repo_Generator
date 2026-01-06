# Self-Improving Repo Builder

A multi-agent, text-to-code system that generates **complete, runnable software repositories** from natural language descriptions, then **verifies, repairs, and executes them automatically**.

This project explores autonomous refinement loops using LLM agents, inspired by research in self-improving systems and agentic workflows.

---

## What This Project Does

Given a prompt like:

> “Build an essay writing workflow using LangGraph”

The system will:

1. Plan the full project structure
2. Generate every required file (code, configs, README, requirements)
3. Statistically verify correctness (syntax, imports, structure)
4. Repair errors automatically
5. Execute the project in an isolated sandbox
6. Return a ready-to-run repository (ZIP or local folder)

No manual scaffolding. No partial code. No broken imports.

---

## Key Capabilities

* **Multi-Agent Architecture**

  * Planner: converts intent → structured project plan
  * Generator: creates full file contents
  * Verifier: performs static code validation
  * Repair: fixes detected issues iteratively
  * Integrator: assembles a final runnable repo

* **Autonomous Refinement Loop**

  * Generation → Verification → Repair → Re-execution
  * Continues until success or hard failure

* **Safe Execution Sandbox**

  * Isolated filesystem
  * Timeout enforcement
  * Structured execution results

* **FastAPI Interface**

  * Production-style API for external usage
  * Suitable for hosting or SaaS-style deployment

* **100% Open Source Stack**

  * Python, FastAPI, LangChain, LangGraph, Gemini API

---

## High-Level Architecture

```
User Prompt
   ↓
PlannerAgent → ProjectSpec
   ↓
GeneratorAgent (per file)
   ↓
VerifierAgent
   ↓
RepairAgent (if needed)
   ↓
Integrator
   ↓
ProjectRunner → SandboxExecutor
   ↓
ExecutionResult
```

This separation keeps reasoning, generation, validation, and execution strictly decoupled.

---

## Repository Structure

```
self_evolving_repo_builder/
├── agents/
│   ├── planner.py        # Intent → ProjectSpec
│   ├── generator.py      # File content generation
│   ├── verifier.py       # Static verification (AST, imports)
│   ├── repair.py         # Targeted fixes
│   └── integrator.py     # Final assembly
├── graph/
│   └── build_graph.py    # Optional dependency graph
├── execution/
│   ├── sandbox.py        # Isolated execution engine
│   └── runner.py         # Project lifecycle runner
├── schemas/
│   └── project_spec.py   # Strongly-typed project contracts
├── prompts/
│   ├── planner.txt
│   ├── generator.txt
│   ├── verifier.txt
│   └── repair.txt
├── api/
│   └── server.py         # FastAPI entrypoint
├── utils/
│   └── fs.py             # Filesystem helpers
├── main.py               # CLI entrypoint
├── requirements.txt
├── .env.example
└── README.md
```

---

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add:

```env
GOOGLE_API_KEY=your_api_key_here
```

---

## Usage

### CLI Mode (Local)

```bash
# Interactive
python main.py

# One-shot prompt
python main.py "build a FastAPI CRUD app with SQLite"
```

---

### API Mode

Start the server:

```bash
uvicorn api.server:app --reload
```

Generate a project:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "build an essay writing workflow using LangGraph"}'
```

Download the generated repository:

```bash
curl http://localhost:8000/download/{job_id} --output project.zip
```

---

## Example Prompts

* “Build an essay writing workflow using LangGraph”
* “Create a FastAPI CRUD API with PostgreSQL”
* “Build a web scraper that stores data in SQLite”
* “Create a chatbot with conversation memory”
* “Generate a LangChain RAG pipeline with PDFs”

---

## Why This Project Matters

This is **not** a template generator.

It demonstrates:

* Agent-based decomposition of complex software tasks
* Automated verification and repair loops
* Programmatic reasoning about code correctness
* Practical application of LangGraph beyond demos
* Foundations for self-improving developer tools

This architecture can be extended into:

* Internal developer platforms
* Auto-scaffolding tools
* AI coding copilots
* Research on autonomous software agents

---

## Troubleshooting

**API key errors**

* Ensure `.env` exists and `GOOGLE_API_KEY` is valid

**Execution failures**

* Review execution logs returned by the API
* Inspect sandbox stderr output

**Generation loops**

* Increase timeout
* Adjust repair iteration limits

---

## References

* LangChain: [https://python.langchain.com](https://python.langchain.com)
* LangGraph: [https://langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)
* Gemini API: [https://ai.google.dev/docs](https://ai.google.dev/docs)

---

## Development Status & Roadmap

This project is under active development.
APIs, internal abstractions, and agent behavior may change.

The current version focuses on correctness, safety, and architectural clarity, rather than polish or scale.

### Planned Improvements

- Streamlit-based hosted UI for interactive usage

- Persistent job storage and history

- Smarter runtime verification (tests + coverage)

- Dependency resolution and lockfile generation

- Multi-language support (beyond Python)

- Incremental regeneration instead of full-file rewrites

- Cloud-hosted execution backends

Expect sharp edges — and rapid evolution.

---