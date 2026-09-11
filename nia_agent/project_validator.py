"""Bounded project validation for NIA's Phase 2 workspace."""

import subprocess
import sys
from pathlib import Path


class ProjectValidator:
    """Run safe, project-local validation checks without changing Git state."""

    def __init__(self, root_directory: str, timeout_seconds: int = 120):
        self.root = Path(root_directory).expanduser().resolve()
        self.timeout_seconds = timeout_seconds

    def validate(self) -> str:
        python_files = list(self.root.rglob("*.py"))
        python_files = [
            path for path in python_files
            if not any(part in {".git", "__pycache__", ".venv", "venv", "nia_browser_profile"} for part in path.parts)
        ]
        if not python_files:
            return "No Python files found; no validation command was run."

        pytest_files = [
            path for path in python_files
            if path.name.startswith("test_") or "test_" in path.stem or path.name.endswith("_test.py")
        ]

        if pytest_files:
            command = [sys.executable, "-m", "pytest", "-q"]
            action = "pytest"
        else:
            command = [sys.executable, "-m", "compileall", "-q", str(self.root)]
            action = "compileall"

        result = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )
        if result.returncode == 0:
            if action == "pytest":
                return f"Validation passed: pytest succeeded for {len(pytest_files)} test file(s)."
            return f"Validation passed: compileall succeeded for {len(python_files)} files."

        details = (result.stderr or result.stdout).strip()
        if action == "pytest":
            return f"Validation failed: pytest returned exit code {result.returncode}.\n{details}"
        return f"Validation failed: Python compilation returned exit code {result.returncode}.\n{details}"
