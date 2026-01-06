"""
Windows-specific configuration to avoid file locking issues
"""

import os
import sys

# Detect if running on Windows
IS_WINDOWS = sys.platform == 'win32' or os.name == 'nt'

# Configuration settings
CONFIG = {
    # Skip intensive integration tests on Windows to avoid file locks
    'skip_integration_tests': IS_WINDOWS,
    
    # Use more lenient file cleanup
    'ignore_cleanup_errors': IS_WINDOWS,
    
    # Longer wait times for file operations on Windows
    'file_operation_delay': 0.5 if IS_WINDOWS else 0.1,
    
    # Max retries for file operations
    'max_cleanup_retries': 5 if IS_WINDOWS else 2,
    
    # Use separate output directory to avoid conflicts
    'output_dir': './output',
    
    # Temp directory handling
    'use_custom_temp': False,  # Use system temp by default
    'custom_temp_dir': './temp' if IS_WINDOWS else None,
}

def get_config(key: str):
    """Get configuration value"""
    return CONFIG.get(key)

def is_windows() -> bool:
    """Check if running on Windows"""
    return IS_WINDOWS

# Windows-specific file handling utilities
if IS_WINDOWS:
    def safe_remove_file(filepath: str, max_retries: int = 3):
        """Safely remove a file on Windows with retries"""
        import time
        
        for attempt in range(max_retries):
            try:
                if os.path.exists(filepath):
                    os.chmod(filepath, 0o777)
                    os.remove(filepath)
                return True
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.2 * (attempt + 1))
                else:
                    print(f"Warning: Could not remove {filepath}")
                    return False
        return False
    
    def safe_remove_directory(dirpath: str, max_retries: int = 3):
        """Safely remove a directory on Windows with retries"""
        import shutil
        import time
        import gc
        
        for attempt in range(max_retries):
            try:
                gc.collect()  # Force garbage collection
                time.sleep(0.2 * (attempt + 1))
                
                if os.path.exists(dirpath):
                    # Change permissions recursively
                    for root, dirs, files in os.walk(dirpath):
                        for name in files:
                            try:
                                filepath = os.path.join(root, name)
                                os.chmod(filepath, 0o777)
                            except:
                                pass
                    
                    shutil.rmtree(dirpath, ignore_errors=(attempt == max_retries - 1))
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Warning: Could not remove directory {dirpath}: {e}")
                    return False
        return False
else:
    # Unix systems - simpler implementation
    def safe_remove_file(filepath: str, max_retries: int = 1):
        import os
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    
    def safe_remove_directory(dirpath: str, max_retries: int = 1):
        import shutil
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
        return True