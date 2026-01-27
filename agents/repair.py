from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List
import re

class RepairAgent:
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        with open("prompts/repair.txt", "r") as f:
            self.prompt_template = f.read()
    
    def repair_files(self, files: Dict[str, str], errors: List[str]) -> Dict[str, str]:
        """Fix errors in generated code - OPTIMIZED with batch processing"""
        
        if not errors:
            return files
        
        # OPTIMIZATION: Apply all quick fixes first (no LLM)
        repaired_files = files.copy()
        errors_by_file = self._group_errors_by_file(errors)
        
        for file_path, file_errors in errors_by_file.items():
            if file_path in files:
                repaired_files[file_path] = self._apply_quick_fixes(files[file_path], file_errors)
        
        # Check if any errors remain that need LLM
        complex_errors = self._get_complex_errors(errors_by_file)
        
        if complex_errors:
            # OPTIMIZATION: Single LLM call for ALL complex repairs
            print(f"   🔧 Running LLM repair for {len(complex_errors)} files...")
            repaired_files = self._llm_batch_repair(repaired_files, complex_errors)
        
        return repaired_files
    
    def _group_errors_by_file(self, errors: List[str]) -> Dict[str, List[str]]:
        """Group errors by the file they belong to"""
        grouped = {}
        
        for error in errors:
            # Try to extract filename
            if ':' in error:
                parts = error.split(':', 1)
                file_path = parts[0].strip()
                error_msg = parts[1].strip()
                
                if file_path not in grouped:
                    grouped[file_path] = []
                grouped[file_path].append(error_msg)
            else:
                # Generic error
                if 'general' not in grouped:
                    grouped['general'] = []
                grouped['general'].append(error)
        
        return grouped
    
    def _apply_quick_fixes(self, content: str, errors: List[str]) -> str:
        """Apply automatic fixes for common issues - NO LLM"""
        
        for error in errors:
            error_lower = error.lower()
            
            # Fix: JSON parsing without error handling
            if 'json parsing' in error_lower or 'jsondecode' in error_lower:
                if 'json.loads(' in content and 'try:' not in content:
                    content = self._wrap_json_parsing(content)
            
            # Fix: Dictionary access without .get()
            if 'dictionary access' in error_lower or 'keyerror' in error_lower:
                content = self._fix_dict_access(content)
            
            # Fix: Missing error handling for requests
            if 'http request' in error_lower or 'requests.' in error_lower:
                content = self._add_request_error_handling(content)
            
            # Fix: await without async
            if 'await' in error_lower and 'async' in error_lower:
                content = self._fix_async_await(content)
        
        return content
    
    def _get_complex_errors(self, errors_by_file: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Filter for errors that need LLM intervention"""
        complex = {}
        
        for file_path, file_errors in errors_by_file.items():
            complex_file_errors = [e for e in file_errors if self._is_complex_error(e)]
            if complex_file_errors:
                complex[file_path] = complex_file_errors
        
        return complex
    
    def _llm_batch_repair(self, files: Dict[str, str], errors_by_file: Dict[str, List[str]]) -> Dict[str, str]:
        """OPTIMIZATION: Repair ALL files with errors in a single LLM call"""
        
        # Build prompt with all files and their errors
        files_and_errors = []
        for file_path, file_errors in errors_by_file.items():
            if file_path in files:
                errors_text = '\n'.join([f"  - {e}" for e in file_errors])
                files_and_errors.append(
                    f"=== FILE: {file_path} ===\n"
                    f"ERRORS:\n{errors_text}\n\n"
                    f"CODE:\n```python\n{files[file_path]}\n```"
                )
        
        combined_context = "\n\n".join(files_and_errors)
        
        prompt = f"""You are a Python debugging expert. Fix ALL the errors in these files.

{combined_context}

INSTRUCTIONS:
1. Fix each error mentioned
2. Maintain all functionality
3. Add proper error handling where needed
4. Keep code structure intact

RESPONSE FORMAT:
```python:filename1.py
# fixed code
```

```python:filename2.py
# fixed code
```

Return ALL files that needed fixes in the format above."""

        try:
            template = ChatPromptTemplate.from_template("{prompt}")
            chain = template | self.llm
            response = chain.invoke({"prompt": prompt})
            
            # Parse response
            fixed_files = self._parse_batch_response(response.content)
            
            # Merge fixed files back
            result = files.copy()
            result.update(fixed_files)
            return result
            
        except Exception as e:
            print(f"Warning: Batch repair failed: {e}")
            return files
    
    def _parse_batch_response(self, content: str) -> Dict[str, str]:
        """Parse LLM response containing multiple fixed files"""
        files = {}
        
        pattern = r'```(?:python)?:([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for filename, code in matches:
            files[filename.strip()] = code.strip()
        
        return files
    
    def _wrap_json_parsing(self, content: str) -> str:
        """Wrap JSON parsing with proper error handling"""
        pattern = r'(\s*)(\w+\s*=\s*)?json\.(loads?)\((.*?)\)'
        
        def replace_json(match):
            indent = match.group(1)
            var_assignment = match.group(2) or ''
            method = match.group(3)
            args = match.group(4)
            var_name = var_assignment.split('=')[0].strip() if '=' in var_assignment else 'result'
            
            return f"""{indent}try:
{indent}    {var_assignment}json.{method}({args})
{indent}except json.JSONDecodeError as e:
{indent}    print(f"JSON parsing error: {{e}}")
{indent}    {var_name} = {{}}"""
        
        return re.sub(pattern, replace_json, content)
    
    def _fix_dict_access(self, content: str) -> str:
        """Replace dict['key'] with dict.get('key')"""
        pattern = r'(\w+)\[(["\'])(\w+)\2\]'
        
        def replace_dict(match):
            var = match.group(1)
            key = match.group(3)
            return f"{var}.get('{key}')"
        
        return re.sub(pattern, replace_dict, content)
    
    def _add_request_error_handling(self, content: str) -> str:
        """Add error handling around requests calls"""
        if 'import requests' not in content:
            return content
        
        if 'from requests.exceptions import' not in content:
            content = content.replace(
                'import requests',
                'import requests\nfrom requests.exceptions import RequestException, Timeout'
            )
        
        return content
    
    def _fix_async_await(self, content: str) -> str:
        """Fix async/await issues"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def ' in line and 'async def' not in line:
                # Check if any line below has await
                for j in range(i+1, min(i+20, len(lines))):
                    if 'await ' in lines[j]:
                        lines[i] = line.replace('def ', 'async def ')
                        break
        
        return '\n'.join(lines)
    
    def _is_complex_error(self, error: str) -> bool:
        """Check if error requires LLM intervention"""
        simple_keywords = ['json parsing', 'dictionary access', 'keyerror', 'await', 'http request']
        return not any(keyword in error.lower() for keyword in simple_keywords)