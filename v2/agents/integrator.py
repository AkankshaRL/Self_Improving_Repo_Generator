import os
import zipfile
from pathlib import Path
from typing import Dict
from schemas.project_spec import ProjectSpec
from datetime import datetime

class IntegratorAgent:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def package_project(self, project_spec: ProjectSpec, files: Dict[str, str]) -> str:
        """Package all generated files into a zip file"""
        
        # Create unique project directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.output_dir / f"{project_spec.project_name}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Write all files
        for file_path, content in files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Create zip file
        zip_path = self.output_dir / f"{project_spec.project_name}_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir)
                    zipf.write(file_path, arcname)
        
        return str(zip_path)