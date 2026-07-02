"""Identifies architectural layout styles within workspace code organizations."""

from typing import List, Optional
from backend.intelligence.github.models import ArchitectureStyle
from backend.intelligence.github.repository import GitRepositoryReader


class ArchitectureDetector:
    """Detects layout styles (MVC, Microservices, Hexagonal, Clean Architecture, Monolith)."""

    def detect_architecture(self, reader: GitRepositoryReader) -> Optional[ArchitectureStyle]:
        """Runs file path analysis to identify code architecture patterns.

        Args:
            reader: Workspace reader context.

        Returns:
            Optional[ArchitectureStyle]: The detected architecture layout.
        """
        files = reader.scan_files()
        
        has_controllers = False
        has_models = False
        has_views = False
        has_routes = False
        
        has_domain = False
        has_infrastructure = False
        has_application = False
        
        has_docker = False
        has_kubernetes = False
        
        has_services = False
        has_api = False
        
        for f in files:
            path_lower = f.lower()
            if "controller" in path_lower:
                has_controllers = True
            if "model" in path_lower:
                has_models = True
            if "view" in path_lower or "templates" in path_lower:
                has_views = True
            if "route" in path_lower:
                has_routes = True
            if "domain" in path_lower:
                has_domain = True
            if "infrastructure" in path_lower:
                has_infrastructure = True
            if "application" in path_lower or "usecase" in path_lower:
                has_application = True
            if "dockerfile" in path_lower or "docker-compose" in path_lower:
                has_docker = True
            if "k8s" in path_lower or "kubernetes" in path_lower or "helm" in path_lower:
                has_kubernetes = True
            if "service" in path_lower:
                has_services = True
            if "api" in path_lower:
                has_api = True

        evidence = []
        name = "Modular Monolith"
        confidence = 0.6

        if has_domain and has_infrastructure and has_application:
            name = "Clean / Hexagonal Architecture"
            confidence = 0.85
            evidence = ["Detected separation of domain, application, and infrastructure layers."]
        elif has_controllers and has_models and (has_views or has_routes):
            name = "Model-View-Controller (MVC)"
            confidence = 0.8
            evidence = ["Detected controller routes mapping to models and views structures."]
        elif has_docker and has_kubernetes:
            name = "Microservices / Containerized Deployment"
            confidence = 0.8
            evidence = ["Detected multiple container configs and container orchestrations (Kubernetes/Helm)."]
        elif has_api and has_services:
            name = "Service-Oriented Architecture (SOA)"
            confidence = 0.7
            evidence = ["Detected API routing tables mapping to decoupled logic services."]
        else:
            evidence = ["Traditional monolithic repository structure with shared files."]

        return ArchitectureStyle(
            name=name,
            confidence=confidence,
            evidence=evidence
        )
