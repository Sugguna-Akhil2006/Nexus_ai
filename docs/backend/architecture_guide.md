# Backend Architecture Guide - Nexus AI

This guide documents the design principles, architectural patterns, and package layouts of the Nexus AI platform backend.

## Architecture Paradigm

Nexus AI follows the **Clean Architecture** paradigm, ensuring separation of concerns across distinct layers:

```
+-------------------------------------------------------------+
|                      REST / WS API Gateway                  |
|                         (FastAPI Layer)                     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Platform Infrastructure                 |
|             (Auth, Database, Storage, Background)           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      Core Interfaces                        |
+-------------------------------------------------------------+
```

### 1. API Gateways & Routing (`backend/api/`)
Interfaces with external clients using FastAPI REST endpoints and WebSocket protocols. Handles input serialization, schema compliance, HTTP status codes, and Gzip response compressions.

### 2. Platform Core Services (`backend/platform/`)
Contains domain-specific implementations for:
- **Authentication**: JWT token management, session state tracking, account lockout policies, and credentials storage.
- **Persistence**: Relational database connection pools and repository abstractions.
- **Storage**: Sanitized file uploads, virus scanning hooks, and secure download authorizations.
- **Background processing**: Multithreaded workers executing FIFO queues, DLQ configurations, and scheduled interval timers.
- **Hardening & Security**: Token-bucket rate limiters, CORS policies, CSRF validations, and structured JSON logs.

### 3. Core Framework Interfaces (`backend/interfaces/`)
Abstract interfaces defining execution, model, search, and vector store providers.
