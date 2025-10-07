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

# Import the MCP server instance
# FastMCP Cloud will use this automatically
from src.server import mcp

# Only run main() if executed directly (local development)
if __name__ == "__main__":
    from src.server import main
    main()