# Nexus AI: Enterprise Agent Orchestration Framework

Nexus AI is an enterprise-grade agent orchestration framework. This project is organized as a monorepo containing a high-performance **FastAPI Backend Engine** and a modern **Next.js Frontend Client**.

---

## 🏗️ Project Architecture & Directory Structure

The repository is structured to maintain clean boundaries between the runtime execution layer, SDK packages, and client interfaces:

```text
nexus_ai/
├── backend/               # FastAPI Backend Engine
│   ├── runtime/           # Core runtime primitives (BaseAgent, Task, Result, State, Memory, EventBus)
│   ├── execution/         # Task Queue, Planner, Dispatcher, Scheduler, Executor
│   ├── workflow/          # Workflow orchestration and DAG execution engines
│   ├── agents/            # System & Capability Agents (OCR, Chat, Embeddings, Search)
│   ├── interfaces/        # Abstract contracts (Storage, Model, Vector, Prompt, Context)
│   ├── providers/         # API integrations (OpenAI, Ollama, Qdrant REST) & Model Router
│   ├── tools/             # Thread-safe Tool Registry and discovery framework
│   ├── sdk/               # Extension contracts and packaging tools
│   ├── api/               # REST API and WebSockets Gateway controllers
│   ├── platform/          # Quotas, provider configuration, failover logic
│   ├── governance/        # Security, Audits, Policy enforcement
│   ├── observability/     # Telemetry collector, metrics, cost tracking
│   └── tests/             # Unit and integration test suites
├── frontend/              # Next.js Frontend Dashboard Web App
│   ├── app/               # React Server Components & Routing (Dashboard, Analytics, Marketplace)
│   ├── components/        # Reusable UI components & shadcn design system
│   ├── lib/               # Utility functions, API clients, React Hooks
│   ├── authentication/    # Auth forms, contexts, and JWT session handling
│   └── workflow_builder/  # Visual designer interface for DAG agent workflows
├── sdk/               # Software Development Kits
│   └── adk/               # Agent Development Kit (ADK) (builders, decorators, CLI, packaging)
├── docker-compose.yml     # Local orchestration for database, cache, and app services
├── Dockerfile             # Multi-stage production container build
├── run_server.py          # Unified local backend startup launcher script
└── requirements.txt       # Python dependencies
```

---

## 🛠️ Tech Stack

### Backend
* **Language**: Python 3.12+
* **Framework**: FastAPI (REST + WebSockets)
* **Server**: Uvicorn
* **Configuration**: Pydantic Settings
* **Databases**: SQLite (local mock), PostgreSQL (production target via docker-compose)
* **Message Broker / Cache**: Redis

### Frontend
* **Framework**: Next.js 15+ (App Router)
* **Styling**: Tailwind CSS & Vanilla CSS Design System
* **Icons**: Lucide React
* **State & Fetching**: React Context, Hooks, and WebSocket client connections

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: version 3.12 or higher installed.
- **Node.js**: version 18.x or higher installed.
- **Docker**: Optional, for containerized databases.

---

### 2. Backend Setup & Run

#### A. Direct Local Startup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server (boots on port `8000`):
   ```bash
   python run_server.py
   ```

#### B. Verification Test Suites
Run the core tests to verify runtime integrity:
```bash
# Backend core tests
python -m unittest discover backend/tests

# Agent Development Kit (ADK) tests
python -m unittest sdk/adk/tests/test_adk.py -v

# Distributed Runtime tests
python -m unittest backend/distributed/tests/test_distributed.py -v
```

---

### 3. Frontend Setup & Run

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser to view the application dashboard.

---

### 4. Running with Docker Compose
To launch the backend along with Redis and PostgreSQL services:
```bash
docker-compose up --build
```
This boots the backend app container linked to Redis and PostgreSQL services, exposing the REST API gateway on port `8000`.

---

## 📦 Agent Development Kit (ADK)

The Agent Development Kit (ADK) located in `sdk/adk/` provides developer-friendly tools:
- **Builders**: Fluent builders for Agents, Workflows, Prompt templates, and Memory.
- **Decorators**: `@tool` decorator mapping functions straight to a thread-safe `ToolRegistry`.
- **Packaging**: CLI commands (`nexus pack`) to bundle agents into portable `.nxpkg` files.
- **CLI**: Executable interface for agent orchestration, testing, and lifecycle management.

---

## 🤝 Integration Boundaries

1. **Relational Database (`backend/api/sqlite_mock.py` / `backend/persistence/`)**:
   - Currently defaults to a local SQLite schema managing users, workspaces, documents, conversations, and messages.
   - For production, inherit or replace `sqlite_mock.py` / `DBStorage` with the PostgreSQL client connection.
2. **Next.js Frontend Client**:
   - Connects using standard HTTP REST endpoints (auth registration, workspaces, documents) and the `/api/chat/ws` WebSocket channel.