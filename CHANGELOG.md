# Changelog - Nexus AI

All notable changes to this project will be documented in this file.

## [1.0.0-RC1] - 2026-07-08

### Added
- **Ops and Hardening**: Integrated Redis caching, distributed locks, circuit breakers, Prom telemetry, and structured JSON loggers.
- **Role Inheritance**: Added permission hierarchy resolution.
- **Virus Upload Scanning**: Configured malware check hook blocking files carrying EICAR patterns.
- **Operations endpoints**: `/health`, `/readiness`, `/liveness`, and `/version` endpoints.

### Fixed
- Fixed missing governance model classes in `models.py`.
- Fixed directory permissions startup checks.
