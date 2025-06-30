#!/usr/bin/env python3
"""Build script to create executable zip archive."""

import zipfile
from pathlib import Path

def create_executable_zip():
    """Create a self-executing zip archive."""
    project_root = Path(__file__).parent
    zip_path = project_root / "grader"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main.py as __main__.py so Python can execute the zip
        zipf.write(project_root / "main.py", "__main__.py")
        zipf.write(project_root / "pytest_grader.py", "pytest_grader.py")

    print('Successfully built grader')