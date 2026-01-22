#!/usr/bin/env python3
"""
HACS Integration Preflight Check.

Validates Home Assistant custom integrations for HACS submission readiness.
Mirrors HACS reviewer expectations, flags errors/warnings, and offers autofixes.

References:
- https://hacs.xyz/docs/publish/start/
- https://hacs.xyz/docs/publish/integration/
- https://hacs.xyz/docs/publish/include/
- https://hacs.xyz/docs/publish/action/
- https://github.com/home-assistant/brands
- https://developers.home-assistant.io/docs/creating_integration_manifest/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

# ANSI color codes for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Expected key ordering for manifest.json (per Home Assistant guidelines)
MANIFEST_KEY_ORDER = [
    "domain",
    "name",
    "after_dependencies",
    "bluetooth",
    "codeowners",
    "config_flow",
    "dependencies",
    "dhcp",
    "documentation",
    "homekit",
    "integration_type",
    "iot_class",
    "issue_tracker",
    "loggers",
    "mqtt",
    "quality_scale",
    "requirements",
    "ssdp",
    "usb",
    "version",
    "zeroconf",
]

# Required fields in manifest.json for HACS
MANIFEST_REQUIRED_FIELDS = [
    "domain",
    "name",
    "documentation",
    "codeowners",
    "version",
]

# Recommended fields for manifest.json
MANIFEST_RECOMMENDED_FIELDS = [
    "iot_class",
    "issue_tracker",
    "config_flow",
]

# Valid iot_class values
VALID_IOT_CLASSES = [
    "assumed_state",
    "calculated",
    "cloud_polling",
    "cloud_push",
    "local_polling",
    "local_push",
]

# Valid integration_type values
VALID_INTEGRATION_TYPES = [
    "device",
    "entity",
    "hardware",
    "helper",
    "hub",
    "service",
    "system",
    "virtual",
]


class PreflightResult:
    """Container for preflight check results."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.fixes_available: list[str] = []
        self.fixes_applied: list[str] = []

    @property
    def passed(self) -> bool:
        """Return True if no errors were found."""
        return len(self.errors) == 0


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"  {RED}✗ ERROR:{RESET} {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"  {YELLOW}⚠ WARNING:{RESET} {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"  {BLUE}ℹ INFO:{RESET} {text}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"  {GREEN}✓{RESET} {text}")


def print_fix(text: str) -> None:
    """Print a fix message."""
    print(f"  {GREEN}🔧 FIXED:{RESET} {text}")


def find_integration_root() -> Path | None:
    """Find the root directory of the integration."""
    cwd = Path.cwd()

    # Look for custom_components directory
    custom_components = cwd / "custom_components"
    if custom_components.exists():
        # Find integration directories (those with manifest.json)
        for integration_dir in custom_components.iterdir():
            if integration_dir.is_dir():
                manifest = integration_dir / "manifest.json"
                if manifest.exists():
                    return cwd

    # Check if we're inside custom_components
    if cwd.parent.name == "custom_components":
        return cwd.parent.parent

    return None


def find_integration_domain(root: Path) -> str | None:
    """Find the integration domain from the directory structure."""
    custom_components = root / "custom_components"
    if custom_components.exists():
        for integration_dir in custom_components.iterdir():
            if integration_dir.is_dir():
                manifest = integration_dir / "manifest.json"
                if manifest.exists():
                    return integration_dir.name
    return None


def get_github_remote() -> tuple[str, str] | None:
    """Get the GitHub owner and repo from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()

        # Parse GitHub URL patterns
        # SSH: git@github.com:owner/repo.git
        # HTTPS: https://github.com/owner/repo.git
        patterns = [
            r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
            r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$",
        ]

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1), match.group(2)

    except subprocess.CalledProcessError:
        pass

    return None


def check_repository(root: Path, result: PreflightResult) -> None:
    """Check repository requirements."""
    print_header("Repository Checks")

    # Check git repository
    git_dir = root / ".git"
    if not git_dir.exists():
        result.errors.append("Not a git repository")
        print_error("Not a git repository")
    else:
        print_success("Git repository detected")

    # Check GitHub remote
    github = get_github_remote()
    if github:
        owner, repo = github
        print_success(f"GitHub remote: {owner}/{repo}")
        result.info.append(f"GitHub: {owner}/{repo}")
    else:
        result.errors.append("No GitHub remote found")
        print_error("No GitHub remote found (required for HACS)")

    # Check for single integration
    custom_components = root / "custom_components"
    if custom_components.exists():
        integrations = [
            d.name
            for d in custom_components.iterdir()
            if d.is_dir() and (d / "manifest.json").exists()
        ]
        if len(integrations) == 1:
            print_success(f"Single integration detected: {integrations[0]}")
        elif len(integrations) > 1:
            result.errors.append(f"Multiple integrations found: {integrations}")
            print_error(f"HACS requires single integration, found: {integrations}")
        else:
            result.errors.append("No integration found in custom_components/")
            print_error("No integration found in custom_components/")


def load_json_file(path: Path) -> dict[str, Any] | None:
    """Load and parse a JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e)}


def check_manifest_json(
    root: Path, domain: str, result: PreflightResult, autofix: bool = False
) -> None:
    """Check manifest.json for HACS requirements."""
    print_header("manifest.json Validation")

    manifest_path = root / "custom_components" / domain / "manifest.json"
    manifest = load_json_file(manifest_path)

    if manifest is None:
        result.errors.append("manifest.json not found")
        print_error("manifest.json not found")
        return

    if "_parse_error" in manifest:
        result.errors.append(f"manifest.json parse error: {manifest['_parse_error']}")
        print_error(f"JSON parse error: {manifest['_parse_error']}")
        return

    # Check required fields
    for field in MANIFEST_REQUIRED_FIELDS:
        if field not in manifest:
            result.errors.append(f"manifest.json missing required field: {field}")
            print_error(f"Missing required field: {field}")
        else:
            print_success(f"Required field present: {field}")

    # Check recommended fields
    for field in MANIFEST_RECOMMENDED_FIELDS:
        if field not in manifest:
            result.warnings.append(f"manifest.json missing recommended field: {field}")
            print_warning(f"Missing recommended field: {field}")

    # Validate domain matches directory
    if manifest.get("domain") != domain:
        result.errors.append(
            f"manifest.json domain '{manifest.get('domain')}' "
            f"doesn't match directory '{domain}'"
        )
        print_error(f"Domain mismatch: manifest says '{manifest.get('domain')}', directory is '{domain}'")
    else:
        print_success(f"Domain matches directory: {domain}")

    # Validate version format (semantic versioning)
    version = manifest.get("version", "")
    if version:
        # Allow calver (YYYY.M.V) or semver (X.Y.Z)
        if not re.match(r"^\d+\.\d+\.\d+(-\w+)?$", version):
            result.warnings.append(f"Version '{version}' may not follow standard versioning")
            print_warning(f"Version format: {version} (consider semver or calver)")
        else:
            print_success(f"Version: {version}")
    else:
        result.errors.append("Version is required")
        print_error("Version is required")

    # Validate iot_class
    iot_class = manifest.get("iot_class")
    if iot_class:
        if iot_class not in VALID_IOT_CLASSES:
            result.errors.append(f"Invalid iot_class: {iot_class}")
            print_error(f"Invalid iot_class: {iot_class}")
            print_info(f"Valid values: {', '.join(VALID_IOT_CLASSES)}")
        else:
            print_success(f"iot_class: {iot_class}")

    # Validate integration_type
    integration_type = manifest.get("integration_type")
    if integration_type:
        if integration_type not in VALID_INTEGRATION_TYPES:
            result.errors.append(f"Invalid integration_type: {integration_type}")
            print_error(f"Invalid integration_type: {integration_type}")
            print_info(f"Valid values: {', '.join(VALID_INTEGRATION_TYPES)}")
        else:
            print_success(f"integration_type: {integration_type}")

    # Validate codeowners format
    codeowners = manifest.get("codeowners", [])
    if codeowners:
        for owner in codeowners:
            if not owner.startswith("@"):
                result.errors.append(f"Codeowner must start with @: {owner}")
                print_error(f"Codeowner must start with @: {owner}")
            else:
                print_success(f"Codeowner: {owner}")

    # Check documentation URL
    doc_url = manifest.get("documentation", "")
    if doc_url:
        if not doc_url.startswith(("http://", "https://")):
            result.errors.append("Documentation must be a valid URL")
            print_error("Documentation must be a valid URL")
        else:
            print_success(f"Documentation URL: {doc_url}")

    # Check key ordering
    current_keys = list(manifest.keys())
    expected_order = [k for k in MANIFEST_KEY_ORDER if k in current_keys]
    # Add any keys not in our expected order list at the end
    extra_keys = [k for k in current_keys if k not in MANIFEST_KEY_ORDER]

    if current_keys != expected_order + extra_keys:
        result.warnings.append("manifest.json keys are not in recommended order")
        result.fixes_available.append("manifest.json key ordering")
        print_warning("Keys are not in recommended order")

        if autofix:
            # Reorder keys
            ordered_manifest = {}
            for key in MANIFEST_KEY_ORDER:
                if key in manifest:
                    ordered_manifest[key] = manifest[key]
            # Add extra keys at the end
            for key in extra_keys:
                ordered_manifest[key] = manifest[key]

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(ordered_manifest, f, indent=2)
                f.write("\n")

            result.fixes_applied.append("manifest.json key ordering")
            print_fix("Reordered manifest.json keys")
    else:
        print_success("Key ordering is correct")


def check_hacs_json(
    root: Path, result: PreflightResult, autofix: bool = False
) -> None:
    """Check hacs.json for HACS requirements."""
    print_header("hacs.json Validation")

    hacs_path = root / "hacs.json"
    hacs = load_json_file(hacs_path)

    if hacs is None:
        result.warnings.append("hacs.json not found (optional but recommended)")
        print_warning("hacs.json not found (optional but recommended)")
        result.fixes_available.append("Create hacs.json")

        if autofix:
            # Create default hacs.json
            default_hacs = {
                "name": "Integration Name",
                "render_readme": True,
                "homeassistant": "2024.1.0",
            }
            with open(hacs_path, "w", encoding="utf-8") as f:
                json.dump(default_hacs, f, indent=2)
                f.write("\n")
            result.fixes_applied.append("Created hacs.json")
            print_fix("Created default hacs.json (please update name)")
        return

    if "_parse_error" in hacs:
        result.errors.append(f"hacs.json parse error: {hacs['_parse_error']}")
        print_error(f"JSON parse error: {hacs['_parse_error']}")
        return

    # Check name field
    if "name" in hacs:
        print_success(f"Name: {hacs['name']}")
    else:
        result.warnings.append("hacs.json missing 'name' field")
        print_warning("Missing 'name' field")

    # Check render_readme
    if hacs.get("render_readme"):
        print_success("render_readme: true")
    else:
        result.warnings.append("render_readme is not enabled")
        print_warning("Consider enabling render_readme: true")

    # Check homeassistant minimum version
    if "homeassistant" in hacs:
        print_success(f"Minimum HA version: {hacs['homeassistant']}")
    else:
        result.warnings.append("No minimum Home Assistant version specified")
        print_warning("Consider specifying minimum Home Assistant version")

    # Check for deprecated/invalid fields
    deprecated_fields = ["hide_default_branch", "content_in_root", "zip_release"]
    for field in deprecated_fields:
        if field in hacs:
            result.warnings.append(f"hacs.json contains deprecated field: {field}")
            print_warning(f"Deprecated field: {field}")


def check_required_files(root: Path, domain: str, result: PreflightResult) -> None:
    """Check for required files."""
    print_header("Required Files")

    integration_dir = root / "custom_components" / domain

    # Required files
    required_files = [
        ("__init__.py", "Integration initialization"),
        ("manifest.json", "Integration manifest"),
    ]

    for filename, description in required_files:
        filepath = integration_dir / filename
        if filepath.exists():
            print_success(f"{filename} ({description})")
        else:
            result.errors.append(f"Missing required file: {filename}")
            print_error(f"Missing: {filename} ({description})")

    # Recommended files
    recommended_files = [
        (root / "README.md", "README.md (repository root)"),
        (root / "LICENSE", "LICENSE file"),
        (root / "hacs.json", "hacs.json"),
        (integration_dir / "strings.json", "strings.json (for translations)"),
        (integration_dir / "translations" / "en.json", "English translations"),
    ]

    for filepath, description in recommended_files:
        if filepath.exists():
            print_success(description)
        else:
            result.warnings.append(f"Missing recommended file: {description}")
            print_warning(f"Missing: {description}")

    # Check for config_flow if config_flow: true in manifest
    manifest_path = integration_dir / "manifest.json"
    manifest = load_json_file(manifest_path)
    if manifest and manifest.get("config_flow"):
        config_flow = integration_dir / "config_flow.py"
        if config_flow.exists():
            print_success("config_flow.py (required when config_flow: true)")
        else:
            result.errors.append("config_flow.py missing but config_flow: true in manifest")
            print_error("config_flow.py required when config_flow: true in manifest")


def check_github_workflows(root: Path, result: PreflightResult, autofix: bool = False) -> None:
    """Check for required GitHub workflows."""
    print_header("GitHub Workflows")

    workflows_dir = root / ".github" / "workflows"

    if not workflows_dir.exists():
        result.errors.append(".github/workflows directory not found")
        print_error(".github/workflows directory not found")
        result.fixes_available.append("Create HACS workflow")

        if autofix:
            workflows_dir.mkdir(parents=True, exist_ok=True)
            print_fix("Created .github/workflows directory")

    # Check for HACS workflow
    hacs_workflow_names = ["hacs.yml", "hacs.yaml", "validate.yml", "validate.yaml"]
    hacs_workflow_found = False

    for name in hacs_workflow_names:
        workflow_path = workflows_dir / name
        if workflow_path.exists():
            hacs_workflow_found = True
            print_success(f"HACS workflow found: {name}")

            # Validate workflow content
            try:
                with open(workflow_path, encoding="utf-8") as f:
                    content = f.read()
                if "hacs/action" in content:
                    print_success("Uses official hacs/action")
                else:
                    result.warnings.append("HACS workflow doesn't use official hacs/action")
                    print_warning("Consider using official hacs/action")

                if 'category: "integration"' in content or "category: integration" in content:
                    print_success("Correct category: integration")
                else:
                    result.warnings.append("HACS workflow should specify category: integration")
                    print_warning("Should specify category: integration")
            except Exception:
                pass
            break

    if not hacs_workflow_found:
        result.errors.append("HACS validation workflow not found")
        print_error("HACS validation workflow not found")
        result.fixes_available.append("Create HACS workflow")

        if autofix and workflows_dir.exists():
            hacs_workflow = workflows_dir / "hacs.yml"
            hacs_content = """---
name: HACS Action

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  hacs:
    name: HACS Action
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: HACS Action
        uses: hacs/action@main
        with:
          category: integration
"""
            with open(hacs_workflow, "w", encoding="utf-8") as f:
                f.write(hacs_content)
            result.fixes_applied.append("Created HACS workflow")
            print_fix("Created .github/workflows/hacs.yml")

    # Check for hassfest workflow (recommended)
    hassfest_workflow_names = ["hassfest.yml", "hassfest.yaml"]
    hassfest_found = False

    for name in hassfest_workflow_names:
        if (workflows_dir / name).exists():
            hassfest_found = True
            print_success(f"Hassfest workflow found: {name}")
            break

    if not hassfest_found:
        result.warnings.append("Hassfest workflow not found (recommended)")
        print_warning("Consider adding hassfest validation workflow")


def check_branding(root: Path, domain: str, result: PreflightResult) -> None:
    """Check branding status in Home Assistant brands repository."""
    print_header("Home Assistant Brands")

    brands_url = f"https://raw.githubusercontent.com/home-assistant/brands/master/custom_integrations/{domain}/icon.png"

    try:
        request = urllib.request.Request(brands_url, method="HEAD")
        request.add_header("User-Agent", "HACS-Preflight-Check")
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status == 200:
                print_success(f"Brand icon found in home-assistant/brands")
                result.info.append("Brand assets registered")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            result.info.append("Brand assets not yet registered (optional)")
            print_info("Brand icon not found in home-assistant/brands")
            print_info("Consider submitting brand assets: https://github.com/home-assistant/brands")
        else:
            print_warning(f"Could not check brands: HTTP {e.code}")
    except Exception as e:
        print_warning(f"Could not check brands: {e}")


def check_code_quality(root: Path, domain: str, result: PreflightResult) -> None:
    """Check code quality indicators."""
    print_header("Code Quality")

    integration_dir = root / "custom_components" / domain

    # Check for type hints (py.typed marker)
    py_typed = integration_dir / "py.typed"
    if py_typed.exists():
        print_success("Type hints enabled (py.typed present)")
    else:
        result.warnings.append("Consider adding py.typed for type checking")
        print_warning("Consider adding py.typed for type checking")

    # Check for tests directory
    tests_dir = root / "tests"
    if tests_dir.exists() and any(tests_dir.glob("test_*.py")):
        test_count = len(list(tests_dir.glob("**/test_*.py")))
        print_success(f"Tests found: {test_count} test file(s)")
    else:
        result.warnings.append("No tests found (highly recommended)")
        print_warning("No tests found (highly recommended for quality)")

    # Check for pre-commit config
    precommit = root / ".pre-commit-config.yaml"
    if precommit.exists():
        print_success("Pre-commit configuration found")
    else:
        result.warnings.append("No pre-commit configuration found")
        print_warning("Consider adding pre-commit for code quality")

    # Check for pyproject.toml or setup.py
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if pyproject.exists():
        print_success("pyproject.toml found")
    elif setup_py.exists():
        print_success("setup.py found")
    else:
        result.info.append("No pyproject.toml or setup.py found")
        print_info("Consider adding pyproject.toml for project metadata")


def print_summary(result: PreflightResult) -> None:
    """Print the final summary."""
    print_header("Summary")

    if result.errors:
        print(f"\n  {RED}{BOLD}Errors ({len(result.errors)}):{RESET}")
        for error in result.errors:
            print(f"    {RED}✗{RESET} {error}")

    if result.warnings:
        print(f"\n  {YELLOW}{BOLD}Warnings ({len(result.warnings)}):{RESET}")
        for warning in result.warnings:
            print(f"    {YELLOW}⚠{RESET} {warning}")

    if result.fixes_applied:
        print(f"\n  {GREEN}{BOLD}Fixes Applied ({len(result.fixes_applied)}):{RESET}")
        for fix in result.fixes_applied:
            print(f"    {GREEN}🔧{RESET} {fix}")

    if result.fixes_available and not result.fixes_applied:
        print(f"\n  {BLUE}{BOLD}Autofixes Available:{RESET}")
        for fix in result.fixes_available:
            print(f"    {BLUE}💡{RESET} {fix}")
        print(f"\n  Run with {CYAN}--fix{RESET} to apply autofixes")

    print()
    if result.passed:
        print(f"  {GREEN}{BOLD}✓ PREFLIGHT PASSED{RESET}")
        print(f"  {GREEN}Your integration appears ready for HACS submission!{RESET}")
    else:
        print(f"  {RED}{BOLD}✗ PREFLIGHT FAILED{RESET}")
        print(f"  {RED}Please fix the errors above before submitting to HACS.{RESET}")

    print()


def main() -> int:
    """Run the HACS preflight check."""
    parser = argparse.ArgumentParser(
        description="HACS Integration Preflight Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Run preflight check
  %(prog)s --fix              Run with autofixes enabled
  %(prog)s --skip-brands      Skip brands repository check
        """,
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply available autofixes",
    )
    parser.add_argument(
        "--skip-brands",
        action="store_true",
        help="Skip Home Assistant brands check",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors and summary",
    )

    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║        HACS Integration Preflight Check                  ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")

    result = PreflightResult()

    # Find integration root
    root = find_integration_root()
    if root is None:
        print_error("Could not find integration root directory")
        print_info("Run this from the repository root containing custom_components/")
        return 1

    # Find domain
    domain = find_integration_domain(root)
    if domain is None:
        print_error("Could not find integration domain")
        return 1

    print(f"\n  {BLUE}Integration:{RESET} {domain}")
    print(f"  {BLUE}Root:{RESET} {root}")

    # Run all checks
    check_repository(root, result)
    check_manifest_json(root, domain, result, autofix=args.fix)
    check_hacs_json(root, result, autofix=args.fix)
    check_required_files(root, domain, result)
    check_github_workflows(root, result, autofix=args.fix)

    if not args.skip_brands:
        check_branding(root, domain, result)

    check_code_quality(root, domain, result)

    # Print summary
    print_summary(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
