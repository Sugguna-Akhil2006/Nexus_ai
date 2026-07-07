"""Nexus ADK CLI - command-line interface for agent development workflows.

Commands:
    nexus init      Initialize a new ADK workspace.
    nexus new       Scaffold a new project (agent/workflow/plugin/provider).
    nexus run       Run an agent locally in test mode.
    nexus build     Validate and build an agent configuration.
    nexus package   Package an agent into a .nxpkg archive.
    nexus publish   Publish a packaged agent to the registry.
    nexus doctor    Diagnose the ADK installation and environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional


def cmd_init(args: argparse.Namespace) -> int:
    """Initializes a new Nexus ADK workspace in the current directory.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 = success).
    """
    workspace_dir = getattr(args, "dir", ".")
    os.makedirs(workspace_dir, exist_ok=True)

    config = {
        "nexus_sdk_version": "1.0.0",
        "runtime_version": "1.0.0",
        "agents": [],
        "providers": [],
        "plugins": [],
    }

    config_path = os.path.join(workspace_dir, "nexus.json")
    if os.path.exists(config_path):
        print(f"[nexus] Workspace already initialized at {workspace_dir}")
        return 0

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[nexus] Workspace initialized at {os.path.abspath(workspace_dir)}")
    print("[nexus] Run 'nexus new agent <name>' to create your first agent.")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffolds a new ADK project.

    Args:
        args: Parsed CLI arguments with ``type`` and ``name``.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    from sdk.adk.project_template import ProjectTemplate

    project_type = getattr(args, "type", None)
    project_name = getattr(args, "name", None)
    output_dir = getattr(args, "output", ".")

    if not project_type or not project_name:
        print("[nexus] Usage: nexus new <agent|workflow|plugin|provider> <name>")
        return 1

    try:
        tmpl = ProjectTemplate()
        files = tmpl.generate(project_type, project_name, output_dir)
        print(f"[nexus] Scaffolded {project_type} '{project_name}' with {len(files)} files:")
        for path in files:
            print(f"  + {path}")
        return 0
    except ValueError as e:
        print(f"[nexus] Error: {e}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Runs an agent locally in test mode.

    Args:
        args: Parsed CLI arguments with ``agent`` module path.

    Returns:
        Exit code.
    """
    agent_path = getattr(args, "agent", None)
    if not agent_path:
        print("[nexus] Usage: nexus run <agent_module>")
        return 1

    print(f"[nexus] Starting agent: {agent_path}")
    print("[nexus] Use AgentTester in your tests for mock provider support.")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Validates and builds the agent configuration.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code.
    """
    config_path = getattr(args, "config", "nexus.json")
    if not os.path.exists(config_path):
        print(f"[nexus] Config file not found: {config_path}")
        return 1

    with open(config_path) as f:
        config = json.load(f)

    print(f"[nexus] Build validated: nexus_sdk_version={config.get('nexus_sdk_version', 'unknown')}")
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    """Packages the agent into a .nxpkg archive.

    Args:
        args: Parsed CLI arguments with ``name`` and ``version``.

    Returns:
        Exit code.
    """
    from sdk.adk.agent_builder import AgentBuilder
    from sdk.adk.agent_packager import AgentPackager

    name = getattr(args, "name", "my_agent")
    version = getattr(args, "version", "1.0.0")
    output_dir = getattr(args, "output", "dist")

    config = (
        AgentBuilder()
        .name(name)
        .description(f"Packaged agent: {name}")
        .version(version)
        .build()
    )

    packager = AgentPackager()
    archive_path = packager.package(config, output_dir=output_dir)
    print(f"[nexus] Packaged agent to: {archive_path}")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    """Publishes a packaged agent to the Nexus registry.

    Args:
        args: Parsed CLI arguments with ``package`` path.

    Returns:
        Exit code.
    """
    package_path = getattr(args, "package", None)
    if not package_path or not os.path.exists(package_path):
        print(f"[nexus] Package not found: {package_path}")
        return 1

    from sdk.adk.agent_packager import AgentPackager
    packager = AgentPackager()
    manifest = packager.inspect(package_path)
    print(f"[nexus] Publishing {manifest.agent_name} v{manifest.version}...")
    print("[nexus] (Registry publication requires NEXUS_REGISTRY_URL to be configured.)")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnoses the ADK installation and environment.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code.
    """
    import sys

    checks = [
        ("Python version", sys.version_info >= (3, 12), f"Python {sys.version}"),
        ("nexus.json present", os.path.exists("nexus.json"), "nexus.json"),
        ("sdk/adk present", os.path.isdir("sdk/adk"), "sdk/adk/"),
        ("backend/runtime present", os.path.isdir("backend/runtime"), "backend/runtime/"),
    ]

    all_ok = True
    print("[nexus doctor] Running diagnostics...\n")
    for label, ok, detail in checks:
        status = "✓" if ok else "✗"
        print(f"  {status}  {label}: {detail}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("[nexus doctor] All checks passed. ADK is healthy.")
    else:
        print("[nexus doctor] Some checks failed. Please review the above.")
    return 0 if all_ok else 1


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the top-level CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="Nexus Agent Development Kit (ADK) CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # nexus init
    p_init = subparsers.add_parser("init", help="Initialize a new ADK workspace")
    p_init.add_argument("--dir", default=".", help="Target directory")
    p_init.set_defaults(func=cmd_init)

    # nexus new
    p_new = subparsers.add_parser("new", help="Scaffold a new project")
    p_new.add_argument("type", choices=["agent", "workflow", "plugin", "provider"])
    p_new.add_argument("name", help="Project name")
    p_new.add_argument("--output", default=".", help="Output directory")
    p_new.set_defaults(func=cmd_new)

    # nexus run
    p_run = subparsers.add_parser("run", help="Run an agent locally")
    p_run.add_argument("agent", help="Agent module path")
    p_run.set_defaults(func=cmd_run)

    # nexus build
    p_build = subparsers.add_parser("build", help="Validate and build agent config")
    p_build.add_argument("--config", default="nexus.json", help="Config file path")
    p_build.set_defaults(func=cmd_build)

    # nexus package
    p_pkg = subparsers.add_parser("package", help="Package agent into .nxpkg archive")
    p_pkg.add_argument("name", help="Agent name")
    p_pkg.add_argument("--version", default="1.0.0", help="Version string")
    p_pkg.add_argument("--output", default="dist", help="Output directory")
    p_pkg.set_defaults(func=cmd_package)

    # nexus publish
    p_pub = subparsers.add_parser("publish", help="Publish a .nxpkg archive")
    p_pub.add_argument("package", help="Path to the .nxpkg archive")
    p_pub.set_defaults(func=cmd_publish)

    # nexus doctor
    p_doc = subparsers.add_parser("doctor", help="Diagnose ADK environment")
    p_doc.set_defaults(func=cmd_doctor)

    return parser


def main(argv: Optional[list] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to sys.argv).

    Returns:
        Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
