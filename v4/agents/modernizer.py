from typing import Dict
import re

class ModernizerAgent:
    """Fast rule-based modernization - NO LLM needed"""
    
    def modernize_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Apply regex-based modernization rules"""
        
        modernized = {}
        for path, content in files.items():
            if path.endswith('.py'):
                modernized[path] = self._apply_rules(content)
            else:
                modernized[path] = content
        return modernized
    
    def _apply_rules(self, code: str) -> str:
        """Apply all modernization rules in one pass"""
        
        rules = [
            # LangChain updates
            (r'from langchain\.llms import OpenAI', 'from langchain_openai import OpenAI'),
            (r'from langchain\.chat_models import ChatOpenAI', 'from langchain_openai import ChatOpenAI'),
            (r'from langchain\.embeddings import OpenAIEmbeddings', 'from langchain_openai import OpenAIEmbeddings'),
            
            # Pydantic v2
            (r'from pydantic import BaseSettings', 'from pydantic_settings import BaseSettings'),
            
            # Modern type hints
            (r': List\[', ': list['),
            (r': Dict\[', ': dict['),
            (r': Tuple\[', ': tuple['),
            (r': Set\[', ': set['),
            (r'-> List\[', '-> list['),
            (r'-> Dict\[', '-> dict['),
            (r'-> Optional\[', '-> '),
        ]
        
        for pattern, replacement in rules:
            code = re.sub(pattern, replacement, code)
        
        return code