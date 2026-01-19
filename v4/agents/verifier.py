from typing import Dict, Tuple, List
import ast
import re

class VerifierAgent:
    """Static analysis only - NO LLM needed"""
    
    def verify_files(self, files: Dict[str, str]) -> Tuple[Dict[str, bool], List[str]]:
        """Fast static verification"""
        
        results = {}
        errors = []
        
        for path, content in files.items():
            if path.endswith('.py'):
                is_valid, error = self._check_syntax(path, content)
                results[path] = is_valid
                if error:
                    errors.append(f"{path}: {error}")
        
        # Check for common runtime issues
        errors.extend(self._check_patterns(files))
        
        return results, errors
    
    def _check_syntax(self, path: str, content: str) -> Tuple[bool, str]:
        try:
            ast.parse(content)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)
    
    def _check_patterns(self, files: Dict[str, str]) -> List[str]:
        """Check for common issues"""
        errors = []
        
        for path, content in files.items():
            if not path.endswith('.py'):
                continue
            
            # JSON without error handling
            if 'json.loads(' in content and 'JSONDecodeError' not in content:
                errors.append(f"{path}: Missing JSONDecodeError handling")
            
            # Requests without error handling  
            if ('requests.get' in content or 'requests.post' in content) and 'RequestException' not in content:
                errors.append(f"{path}: Missing request error handling")
            
            # await without async
            if 'await ' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'await ' in line:
                        # Check for async def above
                        found_async = any('async def' in lines[j] for j in range(max(0, i-10), i))
                        if not found_async:
                            errors.append(f"{path} line {i+1}: await without async function")
                            break
        
        return errors