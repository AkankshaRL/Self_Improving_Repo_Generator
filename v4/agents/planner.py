from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schemas.project_spec import ProjectSpec, FileSpec, DependencySpec, FileType
from utils.json_validator import JSONValidator
import json
import re

class PlannerAgent:
    """Hybrid planner: Templates for common cases, LLM for custom projects"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        with open("prompts/planner.txt", "r") as f:
            self.prompt_template = f.read()
        self.templates = self._load_templates()
    
    def plan(self, user_query: str) -> ProjectSpec:
        """Smart planning: Templates first (90% cases), LLM fallback (10% cases)"""
        
        # Try template matching first (no LLM call needed)
        template_match = self._match_template(user_query)
        
        if template_match:
            print(f"   💡 Using {template_match} template (0 LLM calls)")
            return self._apply_template(template_match, user_query)
        
        # Only use LLM for truly custom projects
        print("   🤖 Custom project detected, using LLM planner (1 LLM call)")
        return self._llm_plan(user_query)
    
    def _match_template(self, query: str) -> str:
        """Match query to template using keywords - EXPANDED"""
        q = query.lower()
        
        # Web API keywords
        if any(kw in q for kw in ['fastapi', 'api', 'rest', 'endpoint', 'crud', 'todo app', 'blog api']):
            return 'fastapi'
        
        # Web scraper keywords  
        if any(kw in q for kw in ['scraper', 'scrape', 'beautifulsoup', 'extract', 'web scraping']):
            return 'scraper'
        
        # Data analysis keywords
        if any(kw in q for kw in ['pandas', 'analyze', 'data analysis', 'csv', 'visualization', 'matplotlib']):
            return 'data_analysis'
        
        # LangChain/AI keywords
        if any(kw in q for kw in ['langchain', 'chatbot', 'llm', 'ai assistant', 'rag', 'openai', 'anthropic']):
            return 'langchain'
        
        # CLI keywords
        if any(kw in q for kw in ['cli', 'command line', 'terminal', 'script', 'game']):
            return 'cli'
        
        # Auth system keywords
        if any(kw in q for kw in ['auth', 'authentication', 'jwt', 'login', 'user management']):
            return 'auth'
        
        return None
    
    def _apply_template(self, template_name: str, user_query: str) -> ProjectSpec:
        """Apply pre-defined template with query customization"""
        template = self.templates[template_name]
        
        # Extract project name from query
        words = [w for w in user_query.lower().split() if w.isalnum()]
        project_name = '_'.join(words[:3]) if words else template['project_name']
        
        return ProjectSpec(
            project_name=project_name,
            description=user_query,
            files=template['files'],
            dependencies=template['dependencies'],
            env_variables=template['env_variables'],
            entry_point=template['entry_point'],
            test_cases=template['test_cases'],
            readme_content=template['readme_content']
        )
    
    def _llm_plan(self, user_query: str) -> ProjectSpec:
        """LLM-based planning with single retry"""
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        chain = prompt | self.llm
        
        for attempt in range(2):  # Reduced from 3 to 2
            try:
                response = chain.invoke({"user_query": user_query})
                spec_data = self._parse_llm_response(response.content)
                return ProjectSpec(**spec_data)
            except Exception as e:
                if attempt == 1:
                    print(f"   ⚠️  LLM planning failed: {str(e)[:100]}")
                    # Fallback to CLI template
                    return self._apply_template('cli', user_query)
    
    def _parse_llm_response(self, content: str) -> dict:
        json_str = self._extract_json(content)
        is_valid, data, error = JSONValidator.validate_and_repair(json_str)
        if is_valid:
            return data
        raise ValueError(f"JSON validation failed: {error}")
    
    def _extract_json(self, content: str) -> str:
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        start = content.find("{")
        if start == -1:
            raise ValueError("No JSON found")
        brace_count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[start:i+1]
        return content[start:]
    
    def _load_templates(self) -> dict:
        """Enhanced templates with modern patterns"""
        return {
            'fastapi': {
                'project_name': 'fastapi_app',
                'files': [
                    FileSpec(path="main.py", content="", file_type=FileType.PYTHON,
                            description="FastAPI app with async CRUD endpoints, proper error handling, and Pydantic v2 models"),
                    FileSpec(path="models.py", content="", file_type=FileType.PYTHON,
                            description="Pydantic v2 models with Field validators"),
                    FileSpec(path="database.py", content="", file_type=FileType.PYTHON,
                            description="SQLAlchemy async engine and session management"),
                    FileSpec(path="config.py", content="", file_type=FileType.PYTHON,
                            description="Pydantic Settings for environment configuration"),
                ],
                'dependencies': [
                    DependencySpec(package="fastapi", version="0.115.0", purpose="Modern async web framework"),
                    DependencySpec(package="uvicorn", version="0.32.0", purpose="ASGI server with uvloop"),
                    DependencySpec(package="sqlalchemy", version="2.0.36", purpose="Async ORM"),
                    DependencySpec(package="pydantic", version="2.10.3", purpose="Data validation v2"),
                    DependencySpec(package="pydantic-settings", version="2.6.1", purpose="Settings management"),
                ],
                'env_variables': {"DATABASE_URL": "sqlite+aiosqlite:///./app.db"},
                'entry_point': 'main.py',
                'test_cases': ["Test async CRUD operations", "Test validation", "Test error handling"],
                'readme_content': "# FastAPI Application\n\nModern async REST API with SQLAlchemy 2.0 and Pydantic v2"
            },
            
            'langchain': {
                'project_name': 'langchain_app',
                'files': [
                    FileSpec(path="chatbot.py", content="", file_type=FileType.PYTHON,
                            description="LangChain chatbot using LCEL (| operator), conversation memory, and streaming"),
                    FileSpec(path="config.py", content="", file_type=FileType.PYTHON,
                            description="Configuration with pydantic-settings"),
                ],
                'dependencies': [
                    DependencySpec(package="langchain", version="0.3.14", purpose="LLM orchestration"),
                    DependencySpec(package="langchain-openai", version="0.2.14", purpose="OpenAI integration"),
                    DependencySpec(package="langchain-google-genai", version="2.0.8", purpose="Gemini integration"),
                    DependencySpec(package="pydantic-settings", version="2.6.1", purpose="Settings"),
                ],
                'env_variables': {"GOOGLE_API_KEY": "Gemini API key", "OPENAI_API_KEY": "Optional OpenAI key"},
                'entry_point': 'chatbot.py',
                'test_cases': ["Test conversation flow", "Test memory persistence"],
                'readme_content': "# LangChain Chatbot\n\nModern chatbot using LCEL and conversation memory"
            },
            
            'scraper': {
                'project_name': 'web_scraper',
                'files': [
                    FileSpec(path="scraper.py", content="", file_type=FileType.PYTHON,
                            description="Async web scraper with BeautifulSoup4, rate limiting, and error handling"),
                    FileSpec(path="storage.py", content="", file_type=FileType.PYTHON,
                            description="Save data to CSV/JSON with pandas"),
                ],
                'dependencies': [
                    DependencySpec(package="beautifulsoup4", version="4.12.3", purpose="HTML parsing"),
                    DependencySpec(package="aiohttp", version="3.11.11", purpose="Async HTTP client"),
                    DependencySpec(package="pandas", version="2.2.3", purpose="Data handling"),
                ],
                'env_variables': {},
                'entry_point': 'scraper.py',
                'test_cases': ["Test async scraping", "Test data extraction"],
                'readme_content': "# Async Web Scraper\n\nFast web scraping with aiohttp and BeautifulSoup"
            },
            
            'data_analysis': {
                'project_name': 'data_analyzer',
                'files': [
                    FileSpec(path="analyze.py", content="", file_type=FileType.PYTHON,
                            description="Data analysis with pandas, statistical functions, and data cleaning"),
                    FileSpec(path="visualize.py", content="", file_type=FileType.PYTHON,
                            description="Create plots with matplotlib and seaborn"),
                ],
                'dependencies': [
                    DependencySpec(package="pandas", version="2.2.3", purpose="Data analysis"),
                    DependencySpec(package="matplotlib", version="3.10.0", purpose="Plotting"),
                    DependencySpec(package="seaborn", version="0.13.2", purpose="Statistical viz"),
                    DependencySpec(package="numpy", version="2.2.1", purpose="Numerical computing"),
                ],
                'env_variables': {},
                'entry_point': 'analyze.py',
                'test_cases': ["Test data loading", "Test statistical analysis"],
                'readme_content': "# Data Analysis Tool\n\nAnalyze and visualize datasets with pandas"
            },
            
            'cli': {
                'project_name': 'cli_tool',
                'files': [
                    FileSpec(path="main.py", content="", file_type=FileType.PYTHON,
                            description="CLI app with rich formatting, click commands, and proper error handling"),
                    FileSpec(path="commands.py", content="", file_type=FileType.PYTHON,
                            description="Command implementations with type hints"),
                ],
                'dependencies': [
                    DependencySpec(package="click", version="8.1.8", purpose="CLI framework"),
                    DependencySpec(package="rich", version="13.9.4", purpose="Terminal formatting"),
                ],
                'env_variables': {},
                'entry_point': 'main.py',
                'test_cases': ["Test command execution"],
                'readme_content': "# CLI Tool\n\nCommand-line application with rich formatting"
            },
            
            'auth': {
                'project_name': 'auth_system',
                'files': [
                    FileSpec(path="main.py", content="", file_type=FileType.PYTHON,
                            description="FastAPI auth system with JWT, password hashing, and OAuth2"),
                    FileSpec(path="models.py", content="", file_type=FileType.PYTHON,
                            description="User models with SQLAlchemy 2.0"),
                    FileSpec(path="security.py", content="", file_type=FileType.PYTHON,
                            description="JWT token handling and password hashing with bcrypt"),
                ],
                'dependencies': [
                    DependencySpec(package="fastapi", version="0.115.0", purpose="Web framework"),
                    DependencySpec(package="python-jose", version="3.3.0", purpose="JWT tokens"),
                    DependencySpec(package="passlib", version="1.7.4", purpose="Password hashing"),
                    DependencySpec(package="python-multipart", version="0.0.20", purpose="Form data"),
                ],
                'env_variables': {"SECRET_KEY": "JWT secret key", "ALGORITHM": "HS256"},
                'entry_point': 'main.py',
                'test_cases': ["Test registration", "Test login", "Test token validation"],
                'readme_content': "# Auth System\n\nJWT authentication with FastAPI"
            }
        }