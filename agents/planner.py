from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec, DependencySpec, FileType
from utils.json_validator import JSONValidator
import json
import re

class PlannerAgent:
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        with open("prompts/planner.txt", "r") as f:
            self.prompt_template = f.read()
        self.max_retries = 3
    
    def plan(self, user_query: str) -> ProjectSpec:
        """Generate comprehensive project specification from user query"""
        
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        last_error = None
        
        # Try multiple times with different strategies
        for attempt in range(self.max_retries):
            try:
                if attempt == 0:
                    # First attempt: normal generation
                    response = chain.invoke({"user_query": user_query})
                elif attempt == 1:
                    # Second attempt: explicitly ask for valid JSON
                    response = chain.invoke({
                        "user_query": f"{user_query}\n\nIMPORTANT: Return ONLY valid JSON, ensure all strings are properly quoted and all commas are in place."
                    })
                else:
                    # Third attempt: use structured output with more guidance
                    response = chain.invoke({
                        "user_query": f"{user_query}\n\nRETURN VALID JSON ONLY. Check: all quotes match, all commas present, no trailing commas."
                    })
                
                # Parse LLM response into ProjectSpec
                spec_data = self._parse_llm_response(response.content)
                return ProjectSpec(**spec_data)
                
            except json.JSONDecodeError as e:
                last_error = e
                print(f"   ⚠️  Attempt {attempt + 1} failed: JSON parsing error at char {e.pos}")
                
                # Try to fix common JSON issues and retry
                if attempt < self.max_retries - 1:
                    # Try to repair the JSON
                    try:
                        repaired = self._repair_json(response.content)
                        spec_data = json.loads(repaired)
                        return ProjectSpec(**spec_data)
                    except:
                        continue
            
            except Exception as e:
                last_error = e
                print(f"   ⚠️  Attempt {attempt + 1} failed: {str(e)[:100]}")
        
        # If all retries failed, return a minimal working spec
        print("   ⚠️  All parsing attempts failed, generating minimal spec...")
        return self._create_minimal_spec(user_query)
    
    def _parse_llm_response(self, content: str) -> dict:
        """Extract and parse JSON from LLM response"""
        
        # Extract JSON string
        json_str = self._extract_json(content)
        
        # Use validator to parse and repair
        is_valid, data, error = JSONValidator.validate_and_repair(json_str)
        
        if is_valid:
            if error:
                print(f"   ⚠️  Warning: {error}")
            return data
        else:
            raise ValueError(f"JSON validation failed: {error}")
    
    def _extract_json(self, content: str) -> str:
        """Extract JSON from various formats"""
        
        # Remove markdown code blocks if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Find JSON object boundaries
        start = content.find("{")
        if start == -1:
            raise ValueError("No JSON object found in response")
        
        # Find matching closing brace
        brace_count = 0
        end = start
        
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        
        if brace_count != 0:
            # Try simple approach
            end = content.rfind("}") + 1
        
        return content[start:end]
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common JSON issues"""
        
        # Remove comments (// and /* */)
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Fix trailing commas in arrays and objects
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing commas between elements (simple heuristic)
        json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
        json_str = re.sub(r'}\s*\n\s*{', '},\n{', json_str)
        json_str = re.sub(r']\s*\n\s*"', '],\n"', json_str)
        
        # Escape unescaped quotes in strings (very basic)
        # This is risky but helps with common issues
        
        return json_str
    
    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair malformed JSON"""
        
        # Use a more aggressive repair strategy
        import re
        
        # Fix common issues
        json_str = self._clean_json_string(json_str)
        
        # Try to add missing closing braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        
        # Try to add missing closing brackets
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        
        # Fix unquoted keys (basic pattern)
        json_str = re.sub(r'(\w+)(\s*:)', r'"\1"\2', json_str)
        
        # Fix single quotes to double quotes
        # Be careful with contractions
        json_str = json_str.replace("'", '"')
        
        return json_str
    
    def _create_minimal_spec(self, user_query: str) -> ProjectSpec:
        """Create a minimal working project spec as fallback"""
        
        # Extract key words from query to create project name
        words = user_query.lower().split()
        project_name = '_'.join([w for w in words if w.isalnum()][:3])
        
        return ProjectSpec(
            project_name=project_name or "generated_project",
            description=f"Project based on: {user_query}",
            files=[
                FileSpec(
                    path="main.py",
                    content="",
                    file_type=FileType.PYTHON,
                    description="Main entry point"
                ),
                FileSpec(
                    path="utils.py",
                    content="",
                    file_type=FileType.PYTHON,
                    description="Utility functions"
                )
            ],
            dependencies=[
                DependencySpec(
                    package="python-dotenv",
                    version=None,
                    purpose="Environment variable management"
                )
            ],
            env_variables={
                "API_KEY": "Your API key"
            },
            entry_point="main.py",
            test_cases=["Basic functionality test"],
            readme_content=f"# {project_name}\n\n{user_query}"
        )