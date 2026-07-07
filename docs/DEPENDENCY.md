# Subsystem Dependencies Manifest

- **backend/runtime/**: Zero internal dependencies. Base layer.
- **backend/intelligence/core/**: Depends on runtime.
- **backend/governance/**: Depends on runtime, workspace registry, database.
- **backend/sdk/**: Depends on public API, authentication, exceptions.
