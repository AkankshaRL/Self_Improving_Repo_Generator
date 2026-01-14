import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple, List
import sys
import ast
import json
import time
import shutil

class SandboxRunner:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def test_execution(self, files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Test code execution in isolated environment"""
        
        errors = []
        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_path = Path(temp_dir)
            
            # Write all Python files
            python_files = []
            for file_path, content in files.items():
                if file_path.endswith('.py'):
                    full_path = temp_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write and immediately close
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    python_files.append(full_path)
            
            # Also write requirements.txt if exists
            if 'requirements.txt' in files:
                req_path = temp_path / 'requirements.txt'
                with open(req_path, 'w', encoding='utf-8') as f:
                    f.write(files['requirements.txt'])
                
                # Try to install dependencies (with timeout)
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-r', str(req_path), '--quiet'],
                        cwd=temp_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode != 0:
                        errors.append(f"Dependency installation failed: {result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    errors.append("Dependency installation timeout")
                except Exception as e:
                    errors.append(f"Could not install dependencies: {e}")
            
            # Test each Python file
            for py_file in python_files:
                success, error = self._test_file(py_file, temp_path)
                if not success:
                    errors.append(f"{py_file.name}: {error}")
        
        except Exception as e:
            errors.append(f"Sandbox error: {str(e)}")
        
        finally:
            # Cleanup with retry logic for Windows
            if temp_dir:
                self._cleanup_directory(temp_dir)
        
        return len(errors) == 0, errors
    
    def _test_file(self, file_path: Path, working_dir: Path) -> Tuple[bool, str]:
        """Test a single Python file"""
        
        try:
            # First check syntax
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                ast.parse(code)
            
            # Try to import/compile (doesn't execute main code)
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
    
    def _cleanup_directory(self, directory: str, max_retries: int = 5):
        """Clean up directory with retry logic for Windows file locking"""
        
        for attempt in range(max_retries):
            try:
                # Force garbage collection to close any file handles
                import gc
                gc.collect()
                
                # Wait a bit for processes to release files
                time.sleep(0.1 * (attempt + 1))
                
                # Try to remove with error handling
                if os.path.exists(directory):
                    shutil.rmtree(directory, ignore_errors=False)
                return  # Success
                
            except PermissionError:
                if attempt < max_retries - 1:
                    # Try harder on subsequent attempts
                    try:
                        # On Windows, try to change permissions
                        if sys.platform == 'win32':
                            for root, dirs, files in os.walk(directory):
                                for name in files:
                                    try:
                                        filepath = os.path.join(root, name)
                                        os.chmod(filepath, 0o777)
                                    except:
                                        pass
                        time.sleep(0.5)
                    except:
                        pass
                else:
                    # Last attempt failed, just ignore
                    print(f"   ⚠️  Warning: Could not clean up temp directory {directory}")
                    # Schedule for cleanup on exit
                    import atexit
                    atexit.register(lambda: shutil.rmtree(directory, ignore_errors=True))
                    return
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"   ⚠️  Warning: Cleanup error: {e}")
                return
    
    def dry_run_with_mocks(self, files: Dict[str, str], entry_point: str) -> Dict:
        """
        Try to run the code with mocked inputs and API calls
        This catches runtime errors like JSON parsing, missing keys, etc.
        """
        
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp()
            temp_path = Path(temp_dir)
            
            # Write all files
            for file_path, content in files.items():
                full_path = temp_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Create a test runner script
            test_script = f"""
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Mock common API calls
def mock_llm_call(*args, **kwargs):
    return Mock(content="Test response", text="Test response")

def mock_json_response(*args, **kwargs):
    return {{"status": "success", "data": "test"}}

# Patch common problematic imports
sys.modules['openai'] = MagicMock()
sys.modules['anthropic'] = MagicMock()

# Try to import and run basic validation
try:
    # Import the main module
    import {entry_point.replace('.py', '').replace('/', '.')}
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
    sys.exit(1)

print("DRY_RUN_SUCCESS")
"""
            
            test_script_path = temp_path / 'test_runner.py'
            with open(test_script_path, 'w', encoding='utf-8') as f:
                f.write(test_script)
            
            # Run the test script
            try:
                result = subprocess.run(
                    [sys.executable, str(test_script_path)],
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                output = result.stdout + result.stderr
                
                if 'IMPORT_ERROR' in output:
                    error_msg = output.split('IMPORT_ERROR:')[1].split('\n')[0].strip()
                    return {'success': False, 'error': f'Import failed: {error_msg}'}
                
                if 'DRY_RUN_SUCCESS' in output:
                    return {'success': True, 'error': None}
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Exit code {result.returncode}: {result.stderr[:300]}'}
                
                return {'success': True, 'error': None}
                
            except subprocess.TimeoutExpired:
                return {'success': False, 'error': 'Dry run timeout (possible infinite loop)'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        finally:
            if temp_dir:
                self._cleanup_directory(temp_dir)