from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class FileType(str, Enum):
    PYTHON = "python"
    CONFIG = "config"
    MARKDOWN = "markdown"
    ENV = "env"
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"

class FileSpec(BaseModel):
    path: str
    content: str = ""
    file_type: FileType
    description: str

class DependencySpec(BaseModel):
    package: str
    version: Optional[str] = None
    purpose: str

class ProjectSpec(BaseModel):
    project_name: str
    description: str
    files: List[FileSpec] = Field(default_factory=list)
    dependencies: List[DependencySpec] = Field(default_factory=list)
    env_variables: Dict[str, str] = Field(default_factory=dict)
    entry_point: str = "main.py"
    test_cases: List[str] = Field(default_factory=list)
    readme_content: str = ""
    
class AgentState(BaseModel):
    user_query: str
    project_spec: Optional[ProjectSpec] = None
    generated_files: Dict[str, str] = Field(default_factory=dict)
    verification_results: Dict[str, bool] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 3
    final_zip_path: Optional[str] = None