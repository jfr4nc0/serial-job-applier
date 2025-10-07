#!/usr/bin/env python3
"""Start LinkedIn MCP server as HTTP server."""

import os
import subprocess
import sys
from pathlib import Path


def start_http_server():
    """Start the LinkedIn MCP server as HTTP server."""
    print("Starting LinkedIn MCP HTTP Server...")

    # Change to the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Start the server
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "linkedin_mcp.linkedin.linkedin_server",
        "--http",
        "--host",
        "localhost",
        "--port",
        "8000",
    ]

    print(f"Running: {' '.join(cmd)}")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_http_server()
