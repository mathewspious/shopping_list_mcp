"""
Main entry point for Shopping List MCP Server
This file handles proper module initialization for FastMCP Cloud deployment
"""

import sys
import os

# Add the current directory to Python path
# This allows src imports to work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import and run the server
from src.server import main

if __name__ == "__main__":
    main()