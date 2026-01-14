import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

class CodeRunner:
    """Execute generated code safely"""
    
    @staticmethod
    def run_script(script_path: Path, timeout: int = 60) -> Tuple[bool, str, str]:
        """Run a Python script and capture output"""
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script_path.parent
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Execution timeout exceeded"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_command(command: str, cwd: Optional[Path] = None, timeout: int = 60) -> Tuple[bool, str]:
        """Run arbitrary command"""
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except Exception as e:
            return False, str(e)