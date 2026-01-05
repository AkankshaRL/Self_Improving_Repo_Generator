from langchain_google_genai import ChatGoogleGenerativeAI
from execution.sandbox import SandboxRunner
from typing import Dict, Tuple
import ast

class VerifierAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.sandbox = SandboxRunner()
    
    def verify_files(self, files: Dict[str, str]) -> Tuple[Dict[str, bool], list]:
        """Verify all generated files for syntax and runtime errors"""
        
        results = {}
        errors = []
        
        # Syntax verification
        for path, content in files.items():
            if path.endswith('.py'):
                is_valid, error = self._verify_syntax(path, content)
                results[path] = is_valid
                if error:
                    errors.append(f"{path}: {error}")
        
        # Runtime verification in sandbox
        runtime_ok, runtime_errors = self.sandbox.test_execution(files)
        if not runtime_ok:
            errors.extend(runtime_errors)
        
        return results, errors
    
    def _verify_syntax(self, path: str, content: str) -> Tuple[bool, str]:
        """Check Python syntax"""
        try:
            ast.parse(content)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)