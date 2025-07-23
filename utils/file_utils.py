"""
File and directory utilities
"""

import os
from pathlib import Path
from typing import Union

def ensure_directory_exists(directory_path: Union[str, Path]) -> None:
    """
    Ensure that a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to the directory to ensure exists
    """
    if directory_path:
        Path(directory_path).mkdir(parents=True, exist_ok=True) 