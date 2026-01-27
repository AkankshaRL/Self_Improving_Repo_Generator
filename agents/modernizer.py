from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import re

class ModernizerAgent:
    """Updates generated code to use latest library versions and patterns"""
    
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        self.deprecation_patterns = self._load_deprecation_patterns()
    
    def modernize_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Update all Python files to use modern syntax - OPTIMIZED for batch processing"""
        
        # OPTIMIZATION: Apply quick fixes first (no LLM calls)
        quick_fixed = {}
        python_files = {}
        
        for path, content in files.items():
            if path.endswith('.py'):
                fixed = self._apply_quick_fixes(content)
                quick_fixed[path] = fixed
                python_files[path] = fixed
            else:
                quick_fixed[path] = content
        
        # OPTIMIZATION: Single LLM call for ALL Python files instead of per-file
        if python_files:
            modernized_python = self._llm_modernize_batch(python_files)
            quick_fixed.update(modernized_python)
        
        return quick_fixed
    
    def _apply_quick_fixes(self, code: str) -> str:
        """Apply regex-based fixes for known deprecations - NO LLM NEEDED"""
        
        fixes = [
            # LangChain: Old import paths
            (r'from langchain\.llms import OpenAI', 'from langchain_openai import OpenAI'),
            (r'from langchain\.chat_models import ChatOpenAI', 'from langchain_openai import ChatOpenAI'),
            (r'from langchain\.embeddings import OpenAIEmbeddings', 'from langchain_openai import OpenAIEmbeddings'),
            
            # Pydantic v2 updates
            (r'from pydantic import BaseSettings', 'from pydantic_settings import BaseSettings'),
            (r'class Config:', 'model_config = ConfigDict('),
            
            # Type hints modernization
            (r'from typing import List\n', ''),
            (r'from typing import Dict\n', ''),
            (r'from typing import Tuple\n', ''),
            (r'from typing import Set\n', ''),
            (r': List\[', ': list['),
            (r': Dict\[', ': dict['),
            (r': Tuple\[', ': tuple['),
            (r': Set\[', ': set['),
            (r'-> List\[', '-> list['),
            (r'-> Dict\[', '-> dict['),
            
            # LangChain LCEL updates
            (r'\.run\(', '.invoke('),
            (r'LLMChain\(', '# Updated to LCEL pattern\n'),
        ]
        
        for pattern, replacement in fixes:
            code = re.sub(pattern, replacement, code)
        
        return code
    
    def _llm_modernize_batch(self, python_files: Dict[str, str]) -> Dict[str, str]:
        """OPTIMIZATION: Modernize ALL files in a single LLM call"""
        
        if not python_files:
            return {}
        
        # Build prompt with all files
        files_content = "\n\n".join([
            f"=== FILE: {path} ===\n```python\n{code}\n```"
            for path, code in python_files.items()
        ])
        
        prompt = f"""You are a Python code modernization expert. Update ALL the following files to use latest patterns.

{files_content}

REQUIREMENTS:
1. Update deprecated imports and methods
2. Use Python 3.10+ native type hints (list[], dict[], not List[], Dict[])
3. Use latest LangChain patterns (LCEL with | operator, .invoke() not .run())
4. Use Pydantic v2 syntax (model_config, not class Config)
5. Ensure async/await patterns are correct
6. Keep all functionality identical

RESPONSE FORMAT:
```python:filename1.py
# modernized code
```

```python:filename2.py
# modernized code
```

Return ALL files with the SAME filenames in the format above."""

        try:
            template = ChatPromptTemplate.from_template("{prompt}")
            chain = template | self.llm
            response = chain.invoke({"prompt": prompt})
            
            # Parse response
            modernized = self._parse_batch_response(response.content)
            
            # Return modernized files, fallback to original if parsing fails
            return {path: modernized.get(path, code) for path, code in python_files.items()}
            
        except Exception as e:
            print(f"Warning: Batch modernization failed: {e}")
            return python_files  # Return originals on error
    
    def _parse_batch_response(self, content: str) -> Dict[str, str]:
        """Parse LLM response containing multiple modernized files"""
        files = {}
        
        # Pattern: ```python:filename.py ... ```
        pattern = r'```(?:python)?:([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for filename, code in matches:
            filename = filename.strip()
            code = code.strip()
            files[filename] = code
        
        return files
    
    def _load_deprecation_patterns(self) -> dict:
        """Load common deprecation patterns"""
        return {
            'langchain': {
                'old': ['LLMChain', 'from langchain.llms', 'ChatOpenAI'],
                'new': ['Use LCEL with |', 'from langchain_openai', 'Use invoke()']
            },
            'pydantic': {
                'old': ['BaseSettings', 'class Config'],
                'new': ['pydantic_settings.BaseSettings', 'model_config = ConfigDict']
            }
        }