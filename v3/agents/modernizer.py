from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import ast
import re

class ModernizerAgent:
    """Updates generated code to use latest library versions and patterns"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.deprecation_patterns = self._load_deprecation_patterns()
    
    def modernize_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Update all Python files to use modern syntax"""
        
        modernized = {}
        
        for path, content in files.items():
            if path.endswith('.py'):
                modernized[path] = self._modernize_code(content)
            else:
                modernized[path] = content
        
        return modernized
    
    def _modernize_code(self, code: str) -> str:
        """Apply automatic modernizations"""
        
        # Apply regex-based fixes for common deprecations
        code = self._apply_quick_fixes(code)
        
        # Use LLM for complex modernizations
        code = self._llm_modernize(code)
        
        return code
    
    def _apply_quick_fixes(self, code: str) -> str:
        """Apply regex-based fixes for known deprecations"""
        
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
    
    def _llm_modernize(self, code: str) -> str:
        """Use LLM to update complex deprecated patterns"""
        
        prompt = """You are a Python code modernization expert. Update this code to use the latest library versions and patterns.

Original Code:
```python
{code}
```

Your task:
1. Update all deprecated imports and methods
2. Use modern Python 3.10+ syntax (native type hints)
3. Update to latest LangChain patterns (LCEL with | operator)
4. Update to Pydantic v2 syntax
5. Ensure all async/await patterns are correct
6. Keep all functionality the same

Return ONLY the modernized code in ```python blocks. No explanations."""

        try:
            template = ChatPromptTemplate.from_template(prompt)
            chain = template | self.llm
            response = chain.invoke({"code": code})
            
            # Extract code
            content = response.content
            if "```python" in content:
                start = content.find("```python") + 10
                end = content.find("```", start)
                return content[start:end].strip()
            
            return code  # Return original if extraction fails
            
        except Exception as e:
            print(f"Warning: Could not modernize code: {e}")
            return code
    
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