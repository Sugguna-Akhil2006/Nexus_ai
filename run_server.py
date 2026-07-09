"""Startup launcher for the Nexus AI Backend API Server."""

import sys
import os

# Ensure project root is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    import uvicorn
    print("Launching Nexus AI Gateway Service...")
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
