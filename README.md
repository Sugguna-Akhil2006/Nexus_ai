# Nexus AI Backend Engine

This repository contains the backend engine and runtime of **Nexus AI**, an enterprise-grade agent orchestration framework. 

In accordance with team boundaries, this project is structured as a pure, frontend-independent, container-free backend package, ready for database provider and frontend client integration.

---

## 🏗️ Reorganized Backend Directory Structure

The repository is organized according to the clean architecture design patterns:

```text
backend/
├── runtime/           # Core Runtime (BaseAgent, Task, Result, State, Memory, EventBus, Logger, Exceptions)
├── execution/         # Execution Engine (Task Queue, Planner, Dispatcher, Scheduler, Executor)
├── workflow/          # Workflow Engine
├── agents/            # System Agents (Authentication, Workspace, Orchestrator) & Capability Agents (Document, OCR, Embedding, Search, Chat)
├── interfaces/        # Public Interfaces and Abstract Base Classes (Storage, Model, Vector, Prompt, Context)
├── providers/         # Official Provider Clients (Ollama, OpenAI, Qdrant REST Vector client) & Model Router
├── tools/             # Tool Framework (Execution and Discovery registries)
├── sdk/               # Nexus SDK & Extension contracts (Base Providers)
├── api/               # REST and WebSockets API gateway controllers (incorporates local SQLite mock storage)
├── services/          # System Services
├── config/            # Environment configurations
├── distributed/       # Distributed Runtime & Cluster Execution (Scheduler, Queue, Failover, Worker Manager)
├── mcp/               # Model Context Protocol (MCP) Client & Server transport layers
├── connectors/        # Universal Connector Framework for enterprise integrations
├── platform/          # Platform Operations (Quotas, Provider/Model Management, Failover)
├── governance/        # Security, Audit Logs, Risk Assessors, Policy Enforcement
├── observability/     # Telemetry Collector, Metrics, Cost Trackers, LRU Caches
├── knowledge_fabric/  # Unified Knowledge Fabric semantic layer
└── tests/             # Unit and Integration test suites
sdk/
└── adk/               # Agent Development Kit (ADK) (builders, decorators, templates, CLI, packaging)
```

---

## 🛠️ Tech Stack & Dependencies

* **Language**: Python 3.12+
* **REST & WebSockets Gateway**: FastAPI
* **HTTP Server**: Uvicorn
* **Environment Configuration**: Pydantic Settings
* **HTTP Client Calls**: urllib (dependency-free)

---

## 📦 Agent Development Kit (ADK)

The repository now exposes a developer-focused **Agent Development Kit (ADK)** at `sdk/adk/` containing:
- Fluent builders for Agents, Workflows, Prompt templates, and Memory.
- `@tool` decorator mapping functions straight to a thread-safe `ToolRegistry`.
- An integrated test runner (`AgentTester`) with mock providers and execution replay.
- Packaging utilities to pack agents into portable `.nxpkg` archives.
- A `nexus` Command Line Interface (CLI).

---

## 🌐 Distributed Runtime & Cluster Execution

The distributed runtime layer at `backend/distributed/` scales execution across cluster worker nodes:
- Dynamic cluster topologies with worker heartbeats and self-healing rejoin capability.
- Capability-based, Round-Robin, Least-Loaded, and Priority scheduling policies.
- Automated failover detecting offline workers and rescheduling orphaned workflow tasks.
- Shared cluster-wide priority queue with task priority, cancellation, and execution metrics.

---

## 🚀 Running & Verification

### 1. Verification Test Suites
To execute all backend runtime test suites:

```bash
python -m unittest discover backend/tests
```

To run the **Agent Development Kit (ADK)** verification suite:
```bash
python -m unittest sdk/adk/tests/test_adk.py -v
```

To run the **Distributed Runtime** verification suite:
```bash
python -m unittest backend/distributed/tests/test_distributed.py -v
```

### 2. Start the Backend API Server
To boot the FastAPI gateway locally on port 8000 (running with in-memory fallback registries and mock databases):

```bash
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

---

## 📋 Architectural Audits & Refactoring Reports

The project has undergone a complete architecture review and refactoring audit prior to the v1.0 release. The reports can be found in the artifacts directory:
- [Architecture Review Report](file:///C:/Users/akhil/.gemini/antigravity-ide/brain/bcdb31cc-9416-476b-84b1-562b2eac0cd8/ArchitectureReviewReport.md): Detailed audit on layering separation, context boundaries, and module coupling.
- [Technical Debt Report](file:///C:/Users/akhil/.gemini/antigravity-ide/brain/bcdb31cc-9416-476b-84b1-562b2eac0cd8/TechnicalDebtReport.md): Catalog of code smells, pass-only stubs, and deprecations.
- [Maintainability Scorecard](file:///C:/Users/akhil/.gemini/antigravity-ide/brain/bcdb31cc-9416-476b-84b1-562b2eac0cd8/MaintainabilityScorecard.md): Score summary for Architecture, Code Quality, Docs, Testing, and Performance.
- [Refactoring Roadmap](file:///C:/Users/akhil/.gemini/antigravity-ide/brain/bcdb31cc-9416-476b-84b1-562b2eac0cd8/RefactoringRoadmap.md): Prioritized step-by-step roadmap for refactoring high, medium, and low-priority technical debt.

---

## 🤝 Integration Boundaries (Teammate Responsibilities)

The backend engine defines clear abstraction contracts to integrate external services:

1. **Relational Database (`backend/api/sqlite_mock.py` / `backend/persistence/`)**:
   * Currently implements a local mock SQLite schema managing users, workspaces, documents, conversations, and messages.
   * *Teammate Integration*: The database developer should inherit or replace `sqlite_mock.py` / `DBStorage` with the production PostgreSQL repository schema client.
2. **Next.js Frontend Client**:
   * *Teammate Integration*: Connects via standard HTTP REST endpoints (auth registration, workspaces CRUD, document uploads) and the `/api/chat/ws` WebSocket channel.