# Nexus AI Backend Engine

This repository contains the backend engine and runtime of **Nexus AI**, an enterprise-grade agent orchestration framework. 

In accordance with team boundaries, this project is structured as a pure, frontend-independent, container-free backend package, ready for database provider and frontend client integration.

---

## 🏗️ Reorganized Backend Directory Structure

The repository is organized according to the clean architecture design patterns:

```text
backend/
├── runtime/       # Core Runtime (BaseAgent, Task, Result, State, Memory, EventBus, Logger, Exceptions)
├── execution/     # Execution Engine (Task Queue, Planner, Dispatcher, Scheduler, Executor)
├── workflow/      # Workflow Engine
├── agents/        # System Agents (Authentication, Workspace, Orchestrator) & Capability Agents (Document, OCR, Embedding, Search, Chat)
├── interfaces/    # Public Interfaces and Abstract Base Classes (Storage, Model, Vector, Prompt, Context)
├── providers/     # Official Provider Clients (Ollama, OpenAI, Qdrant REST Vector client)
├── tools/         # Tool Framework (Execution and Discovery registries)
├── sdk/           # Nexus SDK & Extension contracts (Base Providers)
├── api/           # REST and WebSockets API gateway controllers (incorporates local SQLite mock storage)
├── services/      # System Services
├── config/        # Environment configurations
└── tests/         # Unit and Integration test suite
```

---

## 🛠️ Tech Stack & Dependencies

* **Language**: Python 3.10+
* **REST & WebSockets Gateway**: FastAPI
* **HTTP Server**: Uvicorn
* **Environment Configuration**: Pydantic Settings
* **HTTP Client Calls**: urllib (dependency-free)

---

## 🚀 Running & Verification

### 1. Verification Test Suite
To execute all 291 unit and integration test cases covering agents lifecycle, scheduler loops, and streaming API gateways:

```bash
python -m unittest discover backend/tests
```

### 2. Start the Backend API Server
To boot the FastAPI gateway locally on port 8000 (running with in-memory fallback registries and mock databases):

```bash
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

---

## 🤝 Integration Boundaries (Teammate Responsibilities)

The backend engine defines clear abstraction contracts to integrate external services:

1. **Relational Database (`backend/api/sqlite_mock.py`)**:
   * Currently implements a local mock SQLite schema managing users, workspaces, documents, conversations, and messages.
   * *Teammate Integration*: The database developer should inherit or replace `sqlite_mock.py` / `DBStorage` with the production PostgreSQL repository schema client.
2. **Next.js Frontend Client**:
   * *Teammate Integration*: Connects via standard HTTP REST endpoints (auth registration, workspaces CRUD, document uploads) and the `/api/chat/ws` WebSocket channel.