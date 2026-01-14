from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List

class RepairAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/repair.txt", "r") as f:
            self.prompt_template = f.read()
    
    def repair_files(self, files: Dict[str, str], errors: List[str]) -> Dict[str, str]:
        """Fix errors in generated code"""
        
        repaired_files = files.copy()
        
        # Group errors by file
        errors_by_file = self._group_errors_by_file(errors)
        
        for file_path, file_errors in errors_by_file.items():
            if file_path in files:
                print(f"   🔧 Repairing {file_path}...")
                fixed_content = self._fix_file(file_path, files[file_path], file_errors)
                repaired_files[file_path] = fixed_content
        
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
                # Generic error, apply to all Python files
                if 'general' not in grouped:
                    grouped['general'] = []
                grouped['general'].append(error)
        
        return grouped
    
    def _fix_file(self, file_path: str, content: str, errors: List[str]) -> str:
        """Fix specific errors in a file"""
        
        # Apply quick fixes first
        fixed_content = self._apply_quick_fixes(content, errors)
        
        # If quick fixes didn't work or errors remain, use LLM
        if any(self._is_complex_error(e) for e in errors):
            fixed_content = self._llm_fix(file_path, fixed_content, errors)
        
        return fixed_content
    
    def _apply_quick_fixes(self, content: str, errors: List[str]) -> str:
        """Apply automatic fixes for common issues"""
        
        for error in errors:
            error_lower = error.lower()
            
            # Fix: JSON parsing without error handling
            if 'json parsing' in error_lower or 'jsondecode' in error_lower:
                if 'json.loads(' in content and 'try:' not in content:
                    # Add try-except around json.loads
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
    
    def _wrap_json_parsing(self, content: str) -> str:
        """Wrap JSON parsing with proper error handling"""
        
        import re
        
        # Find json.loads or json.load calls
        pattern = r'(\s*)(\w+\s*=\s*)?json\.(loads?)\((.*?)\)'
        
        def replace_json(match):
            indent = match.group(1)
            var_assignment = match.group(2) or ''
            method = match.group(3)
            args = match.group(4)
            
            return f"""{indent}try:
{indent}    {var_assignment}json.{method}({args})
{indent}except json.JSONDecodeError as e:
{indent}    print(f"JSON parsing error: {{e}}")
{indent}    {var_assignment.split('=')[0].strip() if '=' in var_assignment else 'result'} = {{}}"""
        
        return re.sub(pattern, replace_json, content)
    
    def _fix_dict_access(self, content: str) -> str:
        """Replace dict['key'] with dict.get('key', default)"""
        
        import re
        
        # This is a simplified version - in production you'd want more sophisticated parsing
        # Replace response['key'] with response.get('key')
        pattern = r'(\w+)\[(["\'])(\w+)\2\]'
        
        def replace_dict(match):
            var = match.group(1)
            key = match.group(3)
            return f"{var}.get('{key}')"
        
        return re.sub(pattern, replace_dict, content)
    
    def _add_request_error_handling(self, content: str) -> str:
        """Add error handling around requests calls"""
        
        import re
        
        if 'import requests' not in content:
            return content
        
        # Add requests exception import if not present
        if 'from requests.exceptions import' not in content:
            content = content.replace(
                'import requests',
                'import requests\nfrom requests.exceptions import RequestException, Timeout'
            )
        
        return content
    
    def _fix_async_await(self, content: str) -> str:
        """Fix async/await issues"""
        
        import re
        
        # Find functions with await but not marked as async
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def ' in line and 'async def' not in line:
                # Check if any line below has await
                for j in range(i+1, min(i+20, len(lines))):
                    if 'await ' in lines[j]:
                        # This function needs to be async
                        lines[i] = line.replace('def ', 'async def ')
                        break
        
        return '\n'.join(lines)
    
    def _is_complex_error(self, error: str) -> bool:
        """Check if error requires LLM intervention"""
        
        simple_keywords = ['json parsing', 'dictionary access', 'keyerror', 'await']
        return not any(keyword in error.lower() for keyword in simple_keywords)
    
    def _llm_fix(self, file_path: str, content: str, errors: List[str]) -> str:
        """Use LLM to fix complex errors"""
        
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        errors_text = '\n'.join([f"- {e}" for e in errors])
        
        response = chain.invoke({
            "file_path": file_path,
            "original_code": content,
            "error_message": errors_text
        })
        
        return self._extract_code(response.content)
    
    def _extract_code(self, content: str) -> str:
        if "```python" in content:
            start = content.find("```python") + 10
            end = content.find("```", start)
            return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        return content.strip()