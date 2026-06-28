"""Software Development Kit (SDK) and Stable Extension Layer Module.

Provides versioning schemas, manifests, ABC extension contracts, compatibility validators,
registries, scaffolders, and utility helpers for plugin extensions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class SDKError(NexusException):
    """Base exception for all SDK related errors."""
    pass


class SDKValidationError(SDKError):
    """Raised when extension manifest or properties validation fails."""
    pass


class SDKCompatibilityError(SDKError):
    """Raised when extension version compatibility validation fails."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class ExtensionType(Enum):
    """Supported SDK extension types classifications."""
    AGENT = "AGENT"
    TOOL = "TOOL"
    PLUGIN = "PLUGIN"
    MODEL_PROVIDER = "MODEL_PROVIDER"
    STORAGE_PROVIDER = "STORAGE_PROVIDER"
    VECTOR_PROVIDER = "VECTOR_PROVIDER"
    AUTH_PROVIDER = "AUTH_PROVIDER"
    WORKFLOW = "WORKFLOW"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class SDKVersion:
    """Immutable model representing semantic version bounds.

    Attributes:
        major: Major semver integer.
        minor: Minor semver integer.
        patch: Patch semver integer.
        compatibility: Target compatibility constraints string.
        release_date: Release timestamp.
        metadata: Extra version metadata.
    """
    major: int
    minor: int
    patch: int
    compatibility: str
    release_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKManifest:
    """Immutable catalog manifest defining extension metadata parameters.

    Attributes:
        extension_name: Unique identifier string.
        extension_type: ExtensionType type categorization.
        sdk_version: Required SDK version (semver format).
        runtime_version: Required Runtime version (semver format).
        author: Author identifier string.
        license: License details.
        capabilities: List of capabilities key tags.
        dependencies: Dependencies mapping names to versions.
        metadata: Extra metadata configurations.
    """
    extension_name: str
    extension_type: ExtensionType
    sdk_version: str
    runtime_version: str
    author: str
    license: str
    capabilities: List[str]
    dependencies: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# SDK Base ABC
# =====================================================================

class SDKBase(ABC):
    """Abstract Base Class specifying interfaces extending the SDK platform."""

    @property
    @abstractmethod
    def manifest(self) -> SDKManifest:
        """Retrieves manifest metadata describing the extension."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initializes extension configs."""
        pass

    @abstractmethod
    def validate(self) -> None:
        """Runs diagnostics self-validation checks."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Activates extension tasks services."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Deactivates active extension services."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Disposes resources and shuts down extension."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connections health."""
        pass


# =====================================================================
# Compatibility Validator
# =====================================================================

class CompatibilityValidator:
    """Verifies semver compatibility matrices across SDK and Runtime boundaries."""

    CURRENT_SDK_VERSION = "1.0.0"
    CURRENT_RUNTIME_VERSION = "1.0.0"

    @staticmethod
    def validate_compatibility(manifest: SDKManifest) -> None:
        """Checks compatibility of the extension manifest.

        Args:
            manifest: Conforming SDKManifest details.

        Raises:
            SDKCompatibilityError: If major versions mismatch.
            SDKValidationError: If version formats are invalid.
        """
        # Validate SDK Version Compatibility
        try:
            sdk_parts = [int(p) for p in manifest.sdk_version.split(".")]
            curr_parts = [int(p) for p in CompatibilityValidator.CURRENT_SDK_VERSION.split(".")]
            if len(sdk_parts) < 3:
                raise SDKValidationError(f"Invalid SDK semver format: {manifest.sdk_version}")
            if sdk_parts[0] != curr_parts[0]:
                raise SDKCompatibilityError(
                    f"Incompatible SDK major version. Required: '{manifest.sdk_version}', "
                    f"Current: '{CompatibilityValidator.CURRENT_SDK_VERSION}'."
                )
        except ValueError as e:
            raise SDKValidationError(f"Invalid SDK version characters: {manifest.sdk_version}") from e

        # Validate Runtime Version Compatibility
        try:
            rt_parts = [int(p) for p in manifest.runtime_version.split(".")]
            curr_rt_parts = [int(p) for p in CompatibilityValidator.CURRENT_RUNTIME_VERSION.split(".")]
            if len(rt_parts) < 3:
                raise SDKValidationError(f"Invalid Runtime semver format: {manifest.runtime_version}")
            if rt_parts[0] != curr_rt_parts[0]:
                raise SDKCompatibilityError(
                    f"Incompatible Runtime major version. Required: '{manifest.runtime_version}', "
                    f"Current: '{CompatibilityValidator.CURRENT_RUNTIME_VERSION}'."
                )
        except ValueError as e:
            raise SDKValidationError(f"Invalid Runtime version characters: {manifest.runtime_version}") from e


# =====================================================================
# SDK Registry
# =====================================================================

class SDKRegistry:
    """Thread-safe singleton registry routing extension registrations."""

    _instance: Optional["SDKRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "SDKRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._extensions: Dict[str, SDKBase] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register(self, extension: SDKBase) -> None:
        """Registers a new SDK extension with validation checks."""
        if not extension:
            raise SDKValidationError("Extension instance cannot be None.")

        manifest = extension.manifest
        if not manifest or not manifest.extension_name or not str(manifest.extension_name).strip():
            raise SDKValidationError("Extension manifest must specify a valid extension_name.")

        # Check Version Compatibility
        CompatibilityValidator.validate_compatibility(manifest)

        with self._lock:
            if manifest.extension_name in self._extensions:
                raise SDKValidationError(f"Extension '{manifest.extension_name}' already registered.")

            # Duplicate capability/permissions check (placeholder check)
            self._extensions[manifest.extension_name] = extension

        SDKUtilities.publish_event("sdk.extension.registered", {"name": manifest.extension_name})
        SDKUtilities.publish_event("sdk.extension.loaded", {"name": manifest.extension_name})
        self._logger.info(f"Successfully registered SDK extension: {manifest.extension_name}")

    def unregister(self, extension_name: str) -> None:
        """Removes a registered extension."""
        with self._lock:
            if extension_name not in self._extensions:
                raise SDKValidationError(f"Extension '{extension_name}' not found.")
            ext = self._extensions[extension_name]
            # Deactivate if running
            try:
                ext.stop()
            except Exception:
                pass
            del self._extensions[extension_name]

        SDKUtilities.publish_event("sdk.extension.removed", {"name": extension_name})
        self._logger.info(f"Unregistered SDK extension: {extension_name}")

    def discover(self) -> List[SDKBase]:
        """Discovers active extensions registered."""
        with self._lock:
            return list(self._extensions.values())

    def list_extensions(self) -> List[SDKManifest]:
        """Lists manifests of active extensions."""
        with self._lock:
            return [e.manifest for e in self._extensions.values()]

    def validate(self, extension_name: str) -> bool:
        """Triggers self-validation checks inside target extension."""
        with self._lock:
            if extension_name not in self._extensions:
                raise SDKValidationError(f"Extension '{extension_name}' not registered.")
            ext = self._extensions[extension_name]

        try:
            ext.validate()
            SDKUtilities.publish_event("sdk.extension.validated", {"name": extension_name, "valid": True})
            return True
        except Exception as e:
            SDKUtilities.publish_event("sdk.extension.failed", {"name": extension_name, "error": str(e)})
            raise SDKValidationError(f"Extension '{extension_name}' validation failed: {e}") from e

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered extensions."""
        with self._lock:
            results = {}
            for name, ext in self._extensions.items():
                try:
                    results[name] = ext.health_check()
                except Exception:
                    results[name] = False
            return results


# =====================================================================
# SDK Utilities Helper
# =====================================================================

class SDKUtilities:
    """Insulated wrapper helpers exposing runtime services without leakage."""

    @staticmethod
    def get_logger(name: str) -> StructuredLogger:
        """Retrieves structured logging provider."""
        return StructuredLogger()

    @staticmethod
    def publish_event(event_name: str, payload: Dict[str, Any]) -> None:
        """Publishes event to EventBus."""
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="SDK",
            payload={"event_name": event_name, **payload}
        )
        EventBus().publish(event)


# =====================================================================
# SDK Scaffolder Abstraction
# =====================================================================

class SDKScaffolder(ABC):
    """Abstract code files scaffolding template generator."""

    @abstractmethod
    def scaffold(self, target_dir: str, extension_name: str, ext_type: ExtensionType) -> Dict[str, str]:
        """Generates manifest and starting classes templates contents maps."""
        pass


class DefaultSDKScaffolder(SDKScaffolder):
    """Reference scaffolding code generator."""

    def scaffold(self, target_dir: str, extension_name: str, ext_type: ExtensionType) -> Dict[str, str]:
        if not extension_name or not str(extension_name).strip():
            raise SDKValidationError("extension_name cannot be empty.")

        manifest_content = f"""{{
  "extension_name": "{extension_name}",
  "extension_type": "{ext_type.value}",
  "sdk_version": "1.0.0",
  "runtime_version": "1.0.0",
  "author": "Scaffolder",
  "license": "MIT",
  "capabilities": ["custom_task"],
  "dependencies": {{}}
}}"""

        class_content = f"""\"\"\"Scaffolded {ext_type.value} extension module for {extension_name}.\"\"\"

from backend.sdk.sdk import SDKBase, SDKManifest, ExtensionType

class {extension_name}Extension(SDKBase):
    @property
    def manifest(self) -> SDKManifest:
        return SDKManifest(
            extension_name="{extension_name}",
            extension_type=ExtensionType.{ext_type.name},
            sdk_version="1.0.0",
            runtime_version="1.0.0",
            author="Scaffolder",
            license="MIT",
            capabilities=["custom_task"]
        )

    def initialize(self) -> None:
        pass

    def validate(self) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health_check(self) -> bool:
        return True
"""
        return {
            "manifest.json": manifest_content.strip(),
            "extension.py": class_content.strip()
        }


# =====================================================================
# Mock SDK Extension
# =====================================================================

class MockAgentExtension(SDKBase):
    """Mock agent extension representing third party SDK plugins."""

    def __init__(self) -> None:
        self.initialized = False
        self.validated = False
        self.running = False

    @property
    def manifest(self) -> SDKManifest:
        return SDKManifest(
            extension_name="mock_agent_ext",
            extension_type=ExtensionType.AGENT,
            sdk_version="1.0.0",
            runtime_version="1.0.0",
            author="Developer",
            license="MIT",
            capabilities=["chat_modifications"]
        )

    def initialize(self) -> None:
        self.initialized = True

    def validate(self) -> None:
        self.validated = True

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def shutdown(self) -> None:
        self.initialized = False

    def health_check(self) -> bool:
        return True
