#!/usr/bin/env python3
"""
Server entry point for EmailTriageEnv OpenEnv.
Serves the Flask application on Hugging Face Spaces and other deployment platforms.
"""
import os
import sys

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


def main():
    """Main entry point for server execution."""
    port = int(os.getenv("PORT", 7860))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"Starting EmailTriageEnv API server on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
