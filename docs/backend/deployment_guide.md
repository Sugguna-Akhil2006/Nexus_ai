# Deployment Guide - Nexus AI

This guide documents the procedures for compiling, configuring, and launching the Nexus AI backend services inside production Docker containers.

## Docker Build & Launch

Deploy the full application stack containing the REST API server, Redis cache, and PostgreSQL database:

```bash
# Build and run containers in background
docker compose up -d --build
```

### Health Monitoring

Verify liveness status of the running backend container using:

```bash
docker inspect --format='{{json .State.Health}}' nexus_ai-app-1
```

Or hit the HTTP liveness probe endpoint `/api/platform/liveness`.
