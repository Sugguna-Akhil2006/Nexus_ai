# Environment Setup Guide - Nexus AI

This guide documents environment variables and configurations required for the local development server.

## Quickstart

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create a `.env` file based on `.env.example`:
   ```ini
   PORT=8000
   REDIS_HOST=localhost
   REDIS_PORT=6379
   DB_TYPE=sqlite
   DB_DSN=nexus_ai.db
   ```

3. **Start Development Server**:
   ```bash
   python run_server.py
   ```
   The REST gateway will start running on port `8000`.
