# Self-Improving Repo Builder

A multi-agent, text-to-code system that generates **complete, runnable software repositories** from natural language descriptions, then **verifies, repairs, and executes them automatically**.

This project explores autonomous refinement loops using LLM agents, inspired by research in self-improving systems and agentic workflows.

---

## What This Project Does

Given a prompt like:

> "Build an essay writing workflow using LangGraph"

The system will:

1. **Plan** the full project structure
2. **Generate** every required file (code, configs, README, requirements)
3. **Modernize** code to use latest library APIs
4. **Verify** correctness (syntax, imports, runtime errors, common issues)
5. **Repair** errors automatically with retry loops
6. **Execute** the project in an isolated sandbox
7. **Return** a ready-to-run repository (ZIP or local folder)

No manual scaffolding. No partial code. No broken imports. No deprecated APIs.

---

## Key Capabilities

* **Multi-Agent Architecture**
  * **Planner**: Converts intent → structured project plan with JSON validation
  * **Generator**: Creates full file contents with real-time documentation fetching
  * **Modernizer**: Updates deprecated code patterns to latest APIs
  * **Verifier**: Performs static + runtime validation (syntax, imports, error handling)
  * **Repair**: Fixes detected issues iteratively (auto-wraps JSON parsing, fixes dict access, etc.)
  * **Integrator**: Assembles a final runnable repo

* **Autonomous Refinement Loop**
  * Generation → Modernization → Verification → Repair → Re-verification
  * Continues until success or max iterations (default: 3)
  * Each iteration intelligently targets specific error types

* **Safe Execution Sandbox**
  * Isolated filesystem with Windows-safe cleanup
  * Dependency installation in temp environment
  * Timeout enforcement (configurable)
  * Structured execution results
  * Runtime error detection (JSON parsing, KeyError, etc.)

* **Robust Error Handling**
  * JSON parsing with automatic repair
  * Dictionary access validation
  * API call error handling
  * File operation safety checks
  * Async/await validation

* **FastAPI Interface**
  * Production-style API for external usage
  * Background job processing
  * Status checking and download endpoints
  * Suitable for hosting or SaaS-style deployment

* **100% Open Source Stack**
  * Python 3.10+, FastAPI, LangChain, LangGraph, Google Gemini API
  * Pydantic v2 for type safety
  * BeautifulSoup for doc scraping
  * Requests for PyPI version fetching

---

## High-Level Architecture

```
User Prompt
   ↓
PlannerAgent → ProjectSpec (with JSON validation & repair)
   ↓
GeneratorAgent (fetches latest docs from PyPI + official sources)
   ↓
ModernizerAgent (updates to latest API patterns)
   ↓
VerifierAgent (syntax + runtime + common issues)
   ↓
RepairAgent (if needed, auto-fixes common patterns)
   ↓ (loop up to 3x)
Integrator → ZIP file
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
│   ├── planner.py        # Intent → ProjectSpec with robust JSON parsing
│   ├── generator.py      # File generation + latest doc fetching
│   ├── verifier.py       # Static + runtime validation
│   ├── repair.py         # Targeted fixes with auto-patterns
│   ├── modernizer.py     # Updates deprecated code to latest APIs
│   └── integrator.py     # Final assembly into ZIP
├── graph/
│   └── build_graph.py    # LangGraph workflow orchestration
├── execution/
│   ├── sandbox.py        # Isolated execution (Windows-safe)
│   └── runner.py         # Project lifecycle runner
├── schemas/
│   └── project_spec.py   # Strongly-typed contracts (Pydantic v2)
├── prompts/
│   ├── planner.txt       # Enhanced with JSON validation rules
│   ├── generator.txt     # Includes latest docs context
│   ├── verifier.txt      # Code quality analysis
│   └── repair.txt        # Error fixing with defensive patterns
├── api/
│   └── server.py         # FastAPI entrypoint with async jobs
├── utils/
│   ├── fs.py             # Filesystem helpers
│   └── json_validator.py # Robust JSON parsing & repair
├── config/
│   ├── test_config.py    # Test scenarios and validation rules
│   └── windows_config.py # Windows-specific file handling
├── main.py               # CLI entrypoint with progress tracking
├── requirements.txt      # All dependencies
├── .env.example          # Environment template
└── README.md             # This file
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

Required packages:
- `langchain==0.1.0` - LLM orchestration
- `langchain-google-genai==0.0.6` - Gemini integration
- `langgraph==0.0.20` - Workflow graphs
- `python-dotenv==1.0.0` - Environment management
- `pydantic==2.5.0` - Type validation
- `fastapi==0.108.0` - API framework
- `uvicorn==0.25.0` - ASGI server
- `requests>=2.31.0` - HTTP client
- `beautifulsoup4>=4.12.0` - HTML parsing

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add:

```env
GOOGLE_API_KEY=your_api_key_here

# Optional: LangSmith tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_key_here
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

---

## Usage

### CLI Mode (Local)

```bash
# Interactive mode with progress tracking
python main.py

# One-shot prompt
python main.py "build a FastAPI CRUD app with SQLite"

# Custom output directory
python main.py "create a web scraper" --output ./my_projects
```

**Example Output:**
```
🤖 Text-to-Code Generator
==================================================

📝 Processing: build an essay writing workflow
==================================================

⚙️  Initializing workflow...
📋 Planning project structure...
🔨 Generating code files...
🔄 Modernizing code to latest patterns...
   🔍 Running syntax checks...
   🔍 Running runtime tests...
   🔍 Checking for common issues...
✅ Verifying code quality...
📦 Packaging project...

✅ Success! Project generated:
📦 ./output/essay_workflow_20260106_143022.zip

📊 Summary:
   - Files: 8
   - Iterations: 1
```

---

### API Mode

Start the server:

```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

Generate a project:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "build an essay writing workflow using LangGraph"}'
```

Response:
```json
{
  "job_id": "abc123-def456",
  "message": "Code generation started. Use /download/{job_id} to get the result."
}
```

Check status:

```bash
curl http://localhost:8000/status/abc123-def456
```

Download the generated repository:

```bash
curl http://localhost:8000/download/abc123-def456 --output project.zip
```

---

## Example Prompts

* "Build an essay writing workflow using LangGraph"
* "Create a FastAPI CRUD API with PostgreSQL and authentication"
* "Build a web scraper that stores data in SQLite with error handling"
* "Create a chatbot with conversation memory using LangChain"
* "Generate a RAG pipeline with PDF parsing and vector search"
* "Build a data analysis tool with pandas and matplotlib"
* "Create a Discord bot with slash commands"

---

## Advanced Features

### Automatic Code Modernization

The system automatically updates deprecated patterns:

```python
# Old (deprecated)
from langchain.llms import OpenAI
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input)

# New (automatically modernized)
from langchain_openai import OpenAI
chain = prompt | llm
result = chain.invoke(input)
```

### Runtime Error Prevention

Automatically adds defensive programming patterns:

```python
# Before
data = json.loads(response)
value = data['key']

# After (auto-generated)
try:
    data = json.loads(response)
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    data = {}

value = data.get('key', 'default')
```

### Latest API Documentation

Fetches current documentation from:
- Official library docs
- PyPI for latest versions
- GitHub repositories

### Smart Verification

Checks for:
- ✅ Syntax errors (AST parsing)
- ✅ Import errors (compile testing)
- ✅ Runtime errors (JSON, KeyError, TypeErrors)
- ✅ Missing error handling
- ✅ Async/await mismatches
- ✅ File operation safety
- ✅ API call error handling

---

## Why This Project Matters

This is **not** a template generator.

It demonstrates:

* **Agent-based decomposition** of complex software tasks
* **Automated verification and repair loops** with targeted fixes
* **Programmatic reasoning** about code correctness
* **Runtime error prevention** through static analysis
* **Practical application** of LangGraph beyond demos
* **Self-improving systems** that learn from failures
* **Foundations** for autonomous developer tools

This architecture can be extended into:

* Internal developer platforms
* Auto-scaffolding tools for microservices
* AI coding copilots with verification
* Research on autonomous software agents
* Educational tools for learning software patterns

---

## Troubleshooting

### API Key Errors
```
Error: GOOGLE_API_KEY not found
```
**Solution**: Ensure `.env` exists and contains a valid `GOOGLE_API_KEY`

### JSON Parsing Errors
```
Error: Failed to parse planner response
```
**Solution**: The system now auto-repairs JSON. If this persists, the planner prompt may need adjustment.

### Windows File Locking
```
Error: [WinError 32] The process cannot access the file
```
**Solution**: The system includes Windows-safe cleanup. If issues persist, close any file explorers viewing the temp directory.

### Generation Timeouts
```
Error: Generation timeout
```
**Solution**: 
- Increase timeout in `execution/sandbox.py`
- Check internet connection for doc fetching
- Simplify the prompt

### Execution Failures
**Solution**:
- Review execution logs in console output
- Check generated `requirements.txt` for conflicts
- Inspect sandbox stderr output in the logs

### Repair Loop Exhausted
```
Warning: Max iterations reached
```
**Solution**: The system tried 3 times to fix errors. Check the error messages for patterns and adjust the repair agent.

---

## Configuration

### Adjust Max Iterations

In `schemas/project_spec.py`:
```python
class AgentState(BaseModel):
    # ...
    max_iterations: int = 3  # Change to 5 for more repair attempts
```

### Adjust Timeout

In `execution/sandbox.py`:
```python
class SandboxRunner:
    def __init__(self, timeout: int = 30):  # Change to 60 for longer tests
```

### Skip Certain Validations

In `config/test_config.py`:
```python
VALIDATION_RULES = {
    "must_have_error_handling": True,
    "require_logging": False,  # Set to True to enforce
}
```

---

## Development & Contributing

### Project Philosophy

This project prioritizes:
1. **Correctness** over speed
2. **Explainability** over magic
3. **Composability** over monoliths
4. **Safety** over convenience

### Code Style

- Type hints everywhere (Python 3.10+ native types)
- Docstrings for all public functions
- Error handling at boundaries
- Logging for debugging

### Testing

```bash
# Run a simple test
python main.py "create a hello world script"

# Check the output
unzip output/*.zip -d test_output
cd test_output
python main.py
```

---

## References

* LangChain: [https://python.langchain.com](https://python.langchain.com)
* LangGraph: [https://langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)
* Gemini API: [https://ai.google.dev/docs](https://ai.google.dev/docs)
* Pydantic: [https://docs.pydantic.dev](https://docs.pydantic.dev)
* FastAPI: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

## Development Status & Roadmap

This project is under active development.
APIs, internal abstractions, and agent behavior may change.

The current version focuses on correctness, safety, and architectural clarity, rather than polish or scale.

### Recent Improvements ✅

- ✅ Robust JSON parsing with auto-repair
- ✅ Runtime error detection and prevention
- ✅ Code modernization agent
- ✅ Windows-safe file operations
- ✅ Latest API documentation fetching
- ✅ Automatic error pattern fixes
- ✅ Enhanced verification with common issue detection

### Planned Improvements 🚧

- [ ] Streamlit-based hosted UI for interactive usage
- [ ] Persistent job storage and history (SQLite/PostgreSQL)
- [ ] Smarter runtime verification (unit tests + coverage)
- [ ] Dependency resolution and lockfile generation (poetry/pipenv)
- [ ] Multi-language support (TypeScript, Go, Rust)
- [ ] Incremental regeneration instead of full-file rewrites
- [ ] Cloud-hosted execution backends (AWS Lambda, Modal)
- [ ] Cost tracking and optimization
- [ ] Collaborative multi-agent code review
- [ ] Integration with GitHub for direct repo creation

Expect sharp edges — and rapid evolution.

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

Built with ❤️ using:
- LangChain & LangGraph for agent orchestration
- Google Gemini for code generation
- Pydantic for type safety
- FastAPI for the API layer

Special thanks to the open-source community for making this possible.

---

**Star ⭐ this repo if you find it useful!**