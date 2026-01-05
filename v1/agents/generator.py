from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec
from typing import Dict

class GeneratorAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/generator.txt", "r") as f:
            self.prompt_template = f.read()
    
    def generate_files(self, project_spec: ProjectSpec) -> Dict[str, str]:
        """Generate all code files based on project specification"""
        
        generated_files = {}
        
        for file_spec in project_spec.files:
            content = self._generate_file_content(file_spec, project_spec)
            generated_files[file_spec.path] = content
        
        # Generate additional files
        generated_files["requirements.txt"] = self._generate_requirements(project_spec)
        generated_files["README.md"] = self._generate_readme(project_spec)
        generated_files[".env.example"] = self._generate_env_example(project_spec)
        
        return generated_files
    
    def _generate_file_content(self, file_spec: FileSpec, project_spec: ProjectSpec) -> str:
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "file_path": file_spec.path,
            "file_description": file_spec.description,
            "project_context": project_spec.description,
            "dependencies": [d.package for d in project_spec.dependencies]
        })
        
        return self._extract_code(response.content)
    
    def _generate_requirements(self, spec: ProjectSpec) -> str:
        lines = []
        for dep in spec.dependencies:
            if dep.version:
                lines.append(f"{dep.package}=={dep.version}")
            else:
                lines.append(dep.package)
        return "\n".join(lines)
    
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