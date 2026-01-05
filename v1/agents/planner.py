from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec, DependencySpec, FileType
import json

class PlannerAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/planner.txt", "r") as f:
            self.prompt_template = f.read()
    
    def plan(self, user_query: str) -> ProjectSpec:
        """Generate comprehensive project specification from user query"""
        
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        response = chain.invoke({"user_query": user_query})
        
        # Parse LLM response into ProjectSpec
        spec_data = self._parse_llm_response(response.content)
        return ProjectSpec(**spec_data)
    
    def _parse_llm_response(self, content: str) -> dict:
        """Extract JSON from LLM response"""
        try:
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Failed to parse planner response: {e}")