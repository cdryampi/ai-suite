#!/usr/bin/env python3
"""
Entry point for the AI Suite backend server.

Usage:
    python run.py

Environment variables:
    FLASK_ENV: development | production (default: development)
    FLASK_PORT: Port to run on (default: 5000)
    FLASK_HOST: Host to bind to (default: 127.0.0.1)
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    """Run the Flask development server."""
    env = os.getenv("FLASK_ENV", "development")
    port = int(os.getenv("FLASK_PORT", "5000"))
    host = os.getenv("FLASK_HOST", "127.0.0.1")

    app = create_app(env)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                      AI Suite Backend                         ║
╠══════════════════════════════════════════════════════════════╣
║  Environment: {env:<46} ║
║  Server:      http://{host}:{port:<36} ║
║  API Docs:    http://{host}:{port}/api/health{" " * 24} ║
╚══════════════════════════════════════════════════════════════╝
""")

    app.run(host=host, port=port, debug=(env == "development"), threaded=True)


if __name__ == "__main__":
    main()
