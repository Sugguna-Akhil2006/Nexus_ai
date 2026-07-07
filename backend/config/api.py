"""FastAPI APIRouter routing configuration queries, feature flags, and validation checks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from backend.config.config_exporter import ConfigExporter
from backend.config.config_manager import ConfigManager
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/config", tags=["Environment Configuration"])

# Singleton manager
_manager = ConfigManager()


@router.get("/current", summary="Get active configuration parameters")
def get_current_config(
    format: str = Query("json", regex="^(json|yaml|toml)$"),
) -> Any:
    """Returns all operational application settings in JSON, YAML, or TOML format."""
    config = _manager.get_config()

    if format == "yaml":
        yaml_str = ConfigExporter.export_yaml(config)
        return Response(content=yaml_str, media_type="application/x-yaml")

    if format == "toml":
        toml_str = ConfigExporter.export_toml(config)
        return Response(content=toml_str, media_type="application/x-toml")

    # Default JSON
    return ProductResponse.ok(data=config)


@router.get("/environment", summary="Get active deployment environment profile status")
def get_environment() -> ProductResponse[Dict[str, Any]]:
    """Returns the current deployment environment, host, port, and debug states."""
    config = _manager.get_config()
    return ProductResponse.ok(
        data={
            "environment": config.environment,
            "host": config.server.host,
            "port": config.server.port,
            "reload": config.server.reload,
            "log_level": config.server.log_level,
        }
    )


@router.get("/feature-flags", summary="Get active feature flag toggles")
def get_feature_flags() -> ProductResponse[Dict[str, bool]]:
    """Returns boolean flag overrides for modules and experimental features."""
    flags = _manager.feature_flags.list_flags()
    return ProductResponse.ok(data=flags)


@router.post("/validate", summary="Audit configuration settings for warnings/errors")
def post_validate_config() -> ProductResponse[Dict[str, Any]]:
    """Audits configurations and reports missing keys or range violations."""
    errors = _manager.validate_config()
    return ProductResponse.ok(
        data={
            "valid": len(errors) == 0,
            "errors": errors,
        }
    )
