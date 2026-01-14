from pathlib import Path
from typing import List
import shutil

class FileSystemUtils:
    """Utility functions for file system operations"""
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Create directory if it doesn't exist"""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def write_file(path: Path, content: str) -> None:
        """Write content to file, creating directories as needed"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def read_file(path: Path) -> str:
        """Read file content"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def list_python_files(directory: Path) -> List[Path]:
        """List all Python files in directory recursively"""
        return list(directory.rglob("*.py"))
    
    @staticmethod
    def clean_directory(directory: Path) -> None:
        """Remove directory and all contents"""
        if directory.exists():
            shutil.rmtree(directory)
    
    @staticmethod
    def copy_directory(src: Path, dst: Path) -> None:
        """Copy directory recursively"""
        shutil.copytree(src, dst, dirs_exist_ok=True)