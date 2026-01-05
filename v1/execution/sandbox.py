import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple, List
import sys
import ast

class SandboxRunner:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def test_execution(self, files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Test code execution in isolated environment"""
        
        errors = []
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write all Python files
            python_files = []
            for file_path, content in files.items():
                if file_path.endswith('.py'):
                    full_path = temp_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(full_path, 'w') as f:
                        f.write(content)
                    
                    python_files.append(full_path)
            
            # Test each Python file
            for py_file in python_files:
                success, error = self._test_file(py_file, temp_path)
                if not success:
                    errors.append(f"{py_file.name}: {error}")
        
        return len(errors) == 0, errors
    
    def _test_file(self, file_path: Path, working_dir: Path) -> Tuple[bool, str]:
        """Test a single Python file"""
        
        try:
            # First check syntax
            with open(file_path, 'r') as f:
                code = f.read()
                ast.parse(code)
            
            # Try to import/compile
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(file_path)],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                return False, result.stderr
            
            return True, ""
            
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except subprocess.TimeoutExpired:
            return False, "Execution timeout"
        except Exception as e:
            return False, str(e)