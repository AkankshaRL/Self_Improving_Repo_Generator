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
        
        for error in errors:
            file_path = self._extract_file_from_error(error)
            if file_path and file_path in files:
                fixed_content = self._fix_file(file_path, files[file_path], error)
                repaired_files[file_path] = fixed_content
        
        return repaired_files
    
    def _fix_file(self, file_path: str, content: str, error: str) -> str:
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "file_path": file_path,
            "original_code": content,
            "error_message": error
        })
        
        return self._extract_code(response.content)
    
    def _extract_file_from_error(self, error: str) -> str:
        """Extract file path from error message"""
        if ":" in error:
            return error.split(":")[0].strip()
        return ""
    
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