#!/usr/bin/env python3
"""
Manual setup script to install the notion_mcp package without using pip -e
This creates the necessary .pth file to make the package importable
"""

import os
import sys
from pathlib import Path

# Get paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
venv_path = project_root / ".venv"
site_packages = venv_path / "lib" / "python3.9" / "site-packages"

print(f"Project root: {project_root}")
print(f"Source path: {src_path}")
print(f"Site packages: {site_packages}")

# Create a .pth file to add our src directory to Python path
pth_file = site_packages / "notion_mcp.pth"

print(f"Creating .pth file: {pth_file}")

# Write the path to our src directory
with open(pth_file, 'w') as f:
    f.write(str(src_path) + '\n')

print("✅ Manual installation complete!")
print(f"Added {src_path} to Python path via {pth_file}")

# Test the import
sys.path.insert(0, str(src_path))
try:
    import notion_mcp
    print("✅ notion_mcp module can be imported!")
except ImportError as e:
    print(f"❌ Import failed: {e}")

print("\nNow restart Claude Desktop to test the MCP server.")