from langchain_google_genai import ChatGoogleGenerativeAI
from execution.sandbox import SandboxRunner
from typing import Dict, Tuple, List
import ast
import json
import re
import os

class VerifierAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.sandbox = SandboxRunner()
    
    def verify_files(self, files: Dict[str, str]) -> Tuple[Dict[str, bool], List[str]]:
        """Verify all generated files for syntax, runtime errors, and logic issues"""
        
        results = {}
        errors = []
        
        print("   🔍 Running syntax checks...")
        # 1. Syntax verification
        for path, content in files.items():
            if path.endswith('.py'):
                is_valid, error = self._verify_syntax(path, content)
                results[path] = is_valid
                if error:
                    errors.append(f"SYNTAX ERROR in {path}: {error}")
        
        if errors:
            return results, errors
        
        print("   🔍 Running runtime tests...")
        # 2. Runtime verification in sandbox
        runtime_ok, runtime_errors = self.sandbox.test_execution(files)
        if not runtime_ok:
            errors.extend([f"RUNTIME ERROR: {e}" for e in runtime_errors])
        
        print("   🔍 Checking for common issues...")
        # 3. Check for common runtime issues
        common_errors = self._check_common_issues(files)
        errors.extend(common_errors)
        
        # Skip integration tests on Windows to avoid file locking issues
        if os.name != 'nt':  # Only run on non-Windows systems
            print("   🔍 Running integration tests...")
            # 4. Try to run actual workflow if main.py exists
            integration_errors = self._test_integration(files)
            errors.extend(integration_errors)
        
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
    
    def _check_common_issues(self, files: Dict[str, str]) -> List[str]:
        """Check for common runtime issues in code"""
        errors = []
        
        for path, content in files.items():
            if not path.endswith('.py'):
                continue
            
            # Check for JSON parsing without error handling
            if 'json.loads(' in content or 'json.load(' in content:
                if 'try:' not in content or 'JSONDecodeError' not in content:
                    errors.append(f"{path}: JSON parsing without proper error handling (JSONDecodeError)")
            
            # Check for dict access without .get()
            if re.search(r'\[\s*["\'].*?["\']\s*\](?!\s*=)', content):
                # Found dictionary access - check if there's validation
                if 'KeyError' not in content and '.get(' not in content:
                    errors.append(f"{path}: Direct dictionary access without error handling or .get()")
            
            # Check for API calls without error handling
            if 'requests.get' in content or 'requests.post' in content:
                if 'try:' not in content or 'requests.exceptions' not in content:
                    errors.append(f"{path}: HTTP requests without proper error handling")
            
            # Check for file operations without error handling
            if 'open(' in content:
                if 'try:' not in content or ('with open' not in content and 'finally:' not in content):
                    errors.append(f"{path}: File operations without proper error handling")
            
            # Check for missing type validation
            if 'def ' in content:
                # Check if function has type hints
                functions = re.findall(r'def\s+\w+\s*\([^)]*\)', content)
                for func in functions:
                    if '->' not in func and 'test_' not in func and '__init__' not in func:
                        # Missing return type hint
                        pass  # Warning level, not error
            
            # Check for await without async
            if 'await ' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'await ' in line:
                        # Look backwards for async def
                        found_async = False
                        for j in range(max(0, i-10), i):
                            if 'async def' in lines[j]:
                                found_async = True
                                break
                        if not found_async:
                            errors.append(f"{path}: 'await' used outside async function near line {i+1}")
        
        return errors
    
    def _test_integration(self, files: Dict[str, str]) -> List[str]:
        """Try to run the generated code with test inputs"""
        errors = []
        
        # Check if there's a main.py or entry point
        entry_point = None
        for path in files.keys():
            if path == 'main.py' or path.endswith('main.py'):
                entry_point = path
                break
        
        if not entry_point:
            return []  # No entry point to test
        
        # Try to do a dry-run execution
        try:
            dry_run_result = self.sandbox.dry_run_with_mocks(files, entry_point)
            if not dry_run_result['success']:
                errors.append(f"Integration test failed: {dry_run_result['error']}")
        except Exception as e:
            errors.append(f"Could not run integration test: {str(e)}")
        
        return errors