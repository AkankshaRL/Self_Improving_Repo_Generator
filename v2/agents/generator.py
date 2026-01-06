from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec
from typing import Dict
import requests
from bs4 import BeautifulSoup

class GeneratorAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/generator.txt", "r") as f:
            self.prompt_template = f.read()
    
    def generate_files(self, project_spec: ProjectSpec) -> Dict[str, str]:
        """Generate all code files based on project specification"""
        
        # Fetch latest documentation for dependencies
        latest_docs = self._fetch_latest_docs(project_spec.dependencies)
        
        generated_files = {}
        
        for file_spec in project_spec.files:
            content = self._generate_file_content(file_spec, project_spec, latest_docs)
            generated_files[file_spec.path] = content
        
        # Generate additional files
        generated_files["requirements.txt"] = self._generate_requirements(project_spec)
        generated_files["README.md"] = self._generate_readme(project_spec)
        generated_files[".env.example"] = self._generate_env_example(project_spec)
        
        return generated_files
    
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
                    # Simple fetch (in production, use proper web scraping with rate limits)
                    response = requests.get(doc_urls[package_name], timeout=5)
                    if response.status_code == 200:
                        # Extract key info (simplified - you'd want better parsing)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Get first few paragraphs or code examples
                        text = soup.get_text()[:1000]  # First 1000 chars
                        docs[package_name] = text
                except Exception as e:
                    print(f"Warning: Could not fetch docs for {package_name}: {e}")
                    docs[package_name] = "No documentation fetched"
        
        return docs
    
    def _generate_file_content(self, file_spec: FileSpec, project_spec: ProjectSpec, latest_docs: Dict[str, str]) -> str:
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        # Build documentation context
        doc_context = "\n\n".join([
            f"Latest {pkg} documentation snippet:\n{doc}" 
            for pkg, doc in latest_docs.items()
        ])
        
        response = chain.invoke({
            "file_path": file_spec.path,
            "file_description": file_spec.description,
            "project_context": project_spec.description,
            "dependencies": [d.package for d in project_spec.dependencies],
            "latest_docs": doc_context
        })
        
        return self._extract_code(response.content)
    
    def _generate_requirements(self, spec: ProjectSpec) -> str:
        """Generate requirements.txt with explicit versions fetched from PyPI"""
        lines = []
        for dep in spec.dependencies:
            if dep.version:
                lines.append(f"{dep.package}=={dep.version}")
            else:
                # Fetch latest version from PyPI
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
    
    def _extract_code(self, content: str) -> str:
        """Extract code from markdown code blocks"""
        if "```python" in content:
            start = content.find("```python") + 10
            end = content.find("```", start)
            return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        return content.strip()