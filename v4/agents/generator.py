from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec
from typing import Dict, Optional, List

class GeneratorAgent:
    """Generates high-quality code with embedded best practices"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/generator.txt", "r") as f:
            self.prompt_template = f.read()
    
    def generate_files(self, project_spec: ProjectSpec, previous_errors: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate all files - optimized for single-pass quality"""
        
        generated_files = {}
        total = len(project_spec.files)
        
        # Build error context if retrying
        error_context = ""
        if previous_errors:
            error_context = "\n\nPREVIOUS ERRORS TO FIX:\n" + "\n".join(f"- {e}" for e in previous_errors[:5])
        
        print(f"   📝 Generating {total} code files...")
        
        for i, file_spec in enumerate(project_spec.files, 1):
            try:
                content = self._generate_file(project_spec, file_spec, error_context)
                generated_files[file_spec.path] = content
                print(f"      ✅ {file_spec.path} ({i}/{total})")
            except Exception as e:
                print(f"      ❌ {file_spec.path}: {str(e)[:50]}")
                generated_files[file_spec.path] = self._placeholder(file_spec.path)
        
        # Generate supporting files
        generated_files["requirements.txt"] = self._gen_requirements(project_spec)
        generated_files["README.md"] = self._gen_readme(project_spec)
        if project_spec.env_variables:
            generated_files[".env.example"] = self._gen_env(project_spec)
        
        return generated_files
    
    def _generate_file(self, spec: ProjectSpec, file_spec: FileSpec, errors: str) -> str:
        """Generate single file with best practices embedded"""
        
        # Non-code files
        if file_spec.path in ["requirements.txt", "README.md", ".env.example"]:
            return ""
        
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        # Build context
        other_files = "\n".join([f"- {f.path}: {f.description}" for f in spec.files if f.path != file_spec.path])
        deps = "\n".join([f"- {d.package} ({d.version or 'latest'})" for d in spec.dependencies])
        
        response = chain.invoke({
            "file_path": file_spec.path,
            "file_description": file_spec.description,
            "project_name": spec.project_name,
            "project_description": spec.description,
            "other_files": other_files,
            "dependencies": deps,
            "error_context": errors
        })
        
        return self._extract_code(response.content)
    
    def _extract_code(self, content: str) -> str:
        """Extract code from markdown blocks"""
        import re
        
        # Remove markdown blocks
        content = re.sub(r'```python\s*\n', '', content)
        content = re.sub(r'```\s*\n', '', content)
        content = re.sub(r'```', '', content)
        
        # Find actual code start
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line for kw in ['import', 'from', 'def', 'class', 'if __name__']):
                return '\n'.join(lines[i:]).strip()
        
        return content.strip()
    
    def _gen_requirements(self, spec: ProjectSpec) -> str:
        lines = []
        for dep in spec.dependencies:
            if dep.version:
                lines.append(f"{dep.package}=={dep.version}")
            else:
                lines.append(dep.package)
        return '\n'.join(lines) + '\n'
    
    def _gen_readme(self, spec: ProjectSpec) -> str:
        readme = f"""# {spec.project_name}

{spec.description}

## Installation

\`\`\`bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
\`\`\`
"""
        if spec.env_variables:
            readme += "\n## Configuration\n\nCreate `.env` file:\n\n```\n"
            for key, desc in spec.env_variables.items():
                readme += f"{key}=your_value  # {desc}\n"
            readme += "```\n"
        
        readme += f"\n## Usage\n\n```bash\npython {spec.entry_point}\n```\n"
        return readme
    
    def _gen_env(self, spec: ProjectSpec) -> str:
        lines = []
        for key, desc in spec.env_variables.items():
            lines.append(f"# {desc}")
            lines.append(f"{key}=")
        return '\n'.join(lines)
    
    def _placeholder(self, path: str) -> str:
        return f"""# Placeholder for {path}

def main():
    print("TODO: Implement {path}")

if __name__ == "__main__":
    main() 
"""