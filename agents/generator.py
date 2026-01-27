from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec
from typing import Dict
import requests
from bs4 import BeautifulSoup
import re

class GeneratorAgent:
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        with open("prompts/generator.txt", "r") as f:
            self.prompt_template = f.read()
    
    def generate_files(self, project_spec: ProjectSpec) -> Dict[str, str]:
        """Generate all code files in a SINGLE LLM call for efficiency"""
        
        # Fetch latest documentation for dependencies
        latest_docs = self._fetch_latest_docs(project_spec.dependencies)
        
        # OPTIMIZATION: Generate ALL files in one call instead of per-file
        generated_files = self._generate_all_files_batch(project_spec, latest_docs)
        
        # Generate additional files (no LLM needed)
        generated_files["requirements.txt"] = self._generate_requirements(project_spec)
        generated_files["README.md"] = self._generate_readme(project_spec)
        generated_files[".env.example"] = self._generate_env_example(project_spec)
        
        return generated_files
    
    def _generate_all_files_batch(self, project_spec: ProjectSpec, latest_docs: Dict[str, str]) -> Dict[str, str]:
        """Generate all files in a single LLM call - MAJOR OPTIMIZATION"""
        
        # Build comprehensive prompt for all files
        prompt = self._build_batch_generation_prompt()
        chain = ChatPromptTemplate.from_template(prompt) | self.llm
        
        # Build documentation context
        doc_context = "\n\n".join([
            f"Latest {pkg} documentation snippet:\n{doc}" 
            for pkg, doc in latest_docs.items()
        ])
        
        # Build file specifications
        files_spec = "\n\n".join([
            f"File: {file_spec.path}\n"
            f"Description: {file_spec.description}\n"
            f"Type: {file_spec.file_type.value}"
            for file_spec in project_spec.files
        ])
        
        response = chain.invoke({
            "project_name": project_spec.project_name,
            "project_description": project_spec.description,
            "files_specification": files_spec,
            "dependencies": [d.package for d in project_spec.dependencies],
            "latest_docs": doc_context,
            "entry_point": project_spec.entry_point
        })
        
        # Parse response to extract all files
        return self._parse_multi_file_response(response.content, project_spec.files)
    
    def _build_batch_generation_prompt(self) -> str:
        """Build prompt that generates all files at once"""
        return """You are an expert software engineer. Generate ALL code files for this project in a single response.

Project Details:
- Name: {project_name}
- Description: {project_description}
- Entry Point: {entry_point}

Files to Generate:
{files_specification}

Dependencies: {dependencies}

{latest_docs}

CRITICAL REQUIREMENTS:
1. Use LATEST patterns and syntax:
   - LangChain: Use LCEL with | operator, NOT LLMChain
   - Imports: from langchain_openai import ChatOpenAI (not from langchain.chat_models)
   - Pydantic: v2 syntax with model_config, NOT class Config
   - Type hints: Use native Python 3.10+ (list[str], dict[str, int]) NOT typing.List
   - Modern async/await patterns where appropriate

2. Include proper error handling:
   - try/except for JSON parsing with JSONDecodeError
   - .get() for dict access or proper KeyError handling
   - try/except for HTTP requests with requests.exceptions
   - with statements for file operations

3. Add type hints to all functions

4. Make code production-ready with validation and error messages

FORMAT YOUR RESPONSE AS:
```python:filename.py
# code here
```

```python:another_file.py
# code here
```

Generate complete, working code for ALL files now:"""
    
    def _parse_multi_file_response(self, content: str, file_specs: list[FileSpec]) -> Dict[str, str]:
        """Parse LLM response containing multiple files"""
        files = {}
        
        # Pattern to match code blocks with filenames
        # Matches: ```python:filename.py or ```filename.py
        pattern = r'```(?:python)?:([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for filename, code in matches:
            filename = filename.strip()
            code = code.strip()
            files[filename] = code
        
        # Fallback: if no filename markers, try to match by file count
        if not files:
            code_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
            for i, code in enumerate(code_blocks):
                if i < len(file_specs):
                    files[file_specs[i].path] = code.strip()
        
        return files
    
    def _fetch_latest_docs(self, dependencies) -> Dict[str, str]:
        """Fetch latest documentation snippets for key dependencies"""
        docs = {}
        
        # Map of common packages to their documentation URLs
        doc_urls = {
            "langchain": "https://python.langchain.com/docs/get_started/introduction",
            "langgraph": "https://langchain-ai.github.io/langgraph/",
            "fastapi": "https://fastapi.tiangolo.com/",
            "pydantic": "https://docs.pydantic.dev/latest/",
            "openai": "https://platform.openai.com/docs/api-reference",
            "anthropic": "https://docs.anthropic.com/claude/reference/getting-started-with-the-api"
        }
        
        for dep in dependencies:
            package_name = dep.package.lower()
            if package_name in doc_urls:
                try:
                    response = requests.get(doc_urls[package_name], timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text = soup.get_text()[:1000]
                        docs[package_name] = text
                except Exception as e:
                    print(f"Warning: Could not fetch docs for {package_name}: {e}")
                    docs[package_name] = "No documentation fetched"
        
        return docs
    
    def _generate_requirements(self, spec: ProjectSpec) -> str:
        """Generate requirements.txt with explicit versions"""
        lines = []
        for dep in spec.dependencies:
            if dep.version:
                lines.append(f"{dep.package}=={dep.version}")
            else:
                try:
                    version = self._get_latest_pypi_version(dep.package)
                    lines.append(f"{dep.package}>={version}")
                except:
                    lines.append(dep.package)
        return "\n".join(lines)
    
    def _get_latest_pypi_version(self, package_name: str) -> str:
        """Fetch latest version from PyPI API"""
        try:
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['info']['version']
        except:
            pass
        return "latest"
    
    def _generate_readme(self, spec: ProjectSpec) -> str:
        return spec.readme_content or f"""# {spec.project_name}

{spec.description}

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
Copy .env.example to .env and configure your environment variables.

## Usage
```bash
python {spec.entry_point}
```
"""
    
    def _generate_env_example(self, spec: ProjectSpec) -> str:
        lines = [f"{k}=your_{k.lower()}_here" for k in spec.env_variables.keys()]
        return "\n".join(lines)