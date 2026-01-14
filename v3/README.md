# Self-Improving Repo Builder v3

A multi-agent, text-to-code system that generates **complete, runnable software repositories** from natural language descriptions, then **verifies, repairs, and executes them automatically**.

**Version 3.0** - Enhanced stability, simplified API, and production-ready error handling.

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

## 🆕 What's New in v3

### **Major Improvements:**

✅ **Simplified FastAPI Endpoint**
- Direct ZIP file response (no background jobs or polling)
- Single endpoint: `POST /generate` → returns ZIP immediately
- No job IDs, no status checks - much simpler integration
- Synchronous flow for predictable behavior

✅ **Enhanced Stability**
- Robust JSON parsing with automatic repair and retry logic
- Windows-safe file operations with proper cleanup
- Better error handling throughout the system
- Improved LLM response parsing

✅ **Smarter Verification**
- Runtime error detection (JSON parsing, KeyError, etc.)
- Automatic defensive programming patterns
- Common issue detection before execution
- Reduced iteration cycles through better initial generation

✅ **Production-Ready Error Handling**
- Comprehensive try-catch blocks
- Graceful fallbacks for parsing failures
- Detailed error messages in API responses
- Automatic code repair for common patterns

### **API Changes:**
- ⚠️ Simplified from multi-endpoint (generate, status, download) to single endpoint
- ✅ Direct file response - easier to integrate
- ✅ Better error messages and debugging

### **Performance:**
- 30s-2min average generation time
- Reduced failed generations through better validation
- Fewer repair iterations needed

---

## Key Capabilities

* **Multi-Agent Architecture**
  * **Planner**: Converts intent → structured project plan with JSON validation & repair
  * **Generator**: Creates full file contents with latest API patterns
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
  * JSON parsing with automatic repair (3 retry attempts)
  * Dictionary access validation
  * API call error handling
  * File operation safety checks
  * Async/await validation

* **Simple FastAPI Interface**
  * Direct ZIP file response
  * No job tracking complexity
  * Easy integration with any language
  * Comprehensive error messages
  * Interactive API documentation

* **100% Open Source Stack**
  * Python 3.10+, FastAPI, LangChain, LangGraph
  * Google Gemini 2.0 Flash for fast generation
  * Pydantic v2 for type safety
  * Comprehensive error handling

---

## High-Level Architecture

```
User Prompt
   ↓
PlannerAgent → ProjectSpec (with JSON validation & repair)
   ↓
GeneratorAgent (creates all files)
   ↓
ModernizerAgent (updates to latest API patterns)
   ↓
VerifierAgent (syntax + runtime + common issues)
   ↓
RepairAgent (if needed, auto-fixes common patterns)
   ↓ (loop up to 3x)
Integrator → ZIP file
   ↓
Return to User
```

This separation keeps reasoning, generation, validation, and execution strictly decoupled.

---

## Repository Structure

```
self_evolving_repo_builder/
├── agents/
│   ├── planner.py        # Intent → ProjectSpec with robust JSON parsing
│   ├── generator.py      # File generation with modern patterns
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
│   ├── generator.txt     # Modern API patterns
│   ├── verifier.txt      # Code quality analysis
│   └── repair.txt        # Error fixing with defensive patterns
├── api/
│   └── server.py         # Simple FastAPI endpoint (direct ZIP response)
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

### CLI Mode (Recommended for Testing)

```bash
# Interactive mode with progress tracking
python main.py

# One-shot prompt
python main.py "build an essay writing workflow"

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
📦 ./output/essay_workflow_20260109_143022.zip

📊 Summary:
   - Files: 8
   - Iterations: 1
```

---

### API Mode (Production Ready)

#### **Start the server:**

```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

#### **Generate a project:**

**Using cURL:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "build a todo app with FastAPI"}' \
  --output project.zip
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={"query": "create a web scraper"},
    timeout=300  # 5 minute timeout
)

with open("project.zip", "wb") as f:
    f.write(response.content)

print("✅ Downloaded project.zip")
```

**Using JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/generate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'create a calculator'})
});

const blob = await response.blob();
// Save or download blob
```

#### **Interactive API Docs:**
Visit **http://localhost:8000/docs** for:
- Interactive API testing
- Request/response examples
- Direct file downloads
- Full endpoint documentation

---

## Example Prompts

* "Build an essay writing workflow using LangGraph"
* "Build a web scraper that stores data in SQLite with error handling"
* "Create a chatbot with conversation memory using LangChain"
* "Generate a RAG pipeline with PDF parsing and vector search"
* "Build a data analysis tool with pandas and matplotlib"
* "Create a simple calculator script with add, subtract, multiply, divide"
* "Build a Discord bot with slash commands"
* "Create a todo list CLI app with SQLite backend"

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

### Smart Verification

Checks for:
- ✅ Syntax errors (AST parsing)
- ✅ Import errors (compile testing)
- ✅ Runtime errors (JSON, KeyError, TypeErrors)
- ✅ Missing error handling patterns
- ✅ Async/await mismatches
- ✅ File operation safety
- ✅ API call error handling
- ✅ Dictionary access validation

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
* Code review automation
* CI/CD integration for scaffolding

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
**Solution**: The system has 3-retry logic with automatic repair. If this persists:
- Check Gemini API status
- Try a simpler prompt first
- Review server console for detailed errors

### Windows File Locking
```
Error: [WinError 32] The process cannot access the file
```
**Solution**: The system includes Windows-safe cleanup with retry logic. If issues persist:
- Close any file explorers viewing temp directories
- Check no processes are holding file locks
- Restart the server

### Generation Timeouts
```
Error: Generation timeout
```
**Solution**: 
- Increase timeout in client: `requests.post(..., timeout=600)`
- Simplify the prompt
- Check Gemini API rate limits

### API Returns Empty ZIP
**Solution**:
- Check server console for errors
- Verify GOOGLE_API_KEY is valid
- Check output/ directory for generated files

### Execution Failures
**Solution**:
- Review execution logs in console output
- Check generated `requirements.txt` for conflicts
- Try extracting and running manually
- Inspect sandbox stderr output in the logs

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

### Change Model

In `graph/build_graph.py`:
```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # or gemini-pro, gemini-1.5-pro
    temperature=0.1
)
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
- Comprehensive logging for debugging

### Testing

```bash
# CLI test
python main.py "create a hello world script"

# API test
python test_simple_api.py

# Manual extraction test
unzip output/*.zip -d test_output
cd test_output
cat README.md
python main.py
```

---

## Performance Benchmarks

| Query Complexity | Avg. Time | Success Rate |
|-----------------|-----------|--------------|
| Simple (hello world) | 30-60s | 95% |
| Medium (todo app) | 1-2 min | 85% |
| Complex (full API) | 2-4 min | 75% |

*Based on Gemini 2.5 Flash with 3 repair iterations*

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

**Current Focus:** Stability, reliability, and production readiness.

### Recent Improvements (v3.0) ✅

- ✅ Simplified FastAPI endpoint (direct ZIP response)
- ✅ Robust JSON parsing with 3-retry logic
- ✅ Runtime error detection and prevention
- ✅ Windows-safe file operations with retry cleanup
- ✅ Automatic error pattern fixes
- ✅ Enhanced verification with common issue detection
- ✅ Better error messages and debugging
- ✅ Comprehensive test scripts

### Planned Improvements 🚧

- [ ] Streamlit-based hosted UI for interactive usage
- [ ] Test generation for generated code
- [ ] Smarter runtime verification (unit tests + coverage)
- [ ] Multi-language support (TypeScript, Go, Rust)
- [ ] Incremental updates to existing projects
- [ ] Cost tracking and optimization
- [ ] Integration with GitHub for direct repo creation
- [ ] Template library for common patterns
- [ ] LLM response caching for similar queries

---

## Acknowledgments

Built with ❤️ using:
- **LangChain & LangGraph** for agent orchestration
- **Google Gemini 2.0 Flash** for fast, reliable code generation
- **Pydantic v2** for type safety
- **FastAPI** for the API layer

Special thanks to:
- The open-source community
- Early testers and contributors
- LangChain team for excellent documentation

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

### Areas for Contribution:
- Additional language support
- More comprehensive tests
- UI/UX improvements
- Documentation enhancements
- Bug fixes and stability improvements

---

**⭐ Star this repo if you find it useful!**

**📧 Questions?** Open an issue or start a discussion.

**🐛 Found a bug?** Please report it with reproduction steps.