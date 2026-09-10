"""Read-only Git status and diff review for NIA's Phase 2 workspace."""

import subprocess
from pathlib import Path


class GitReview:
    """Inspect Git state without staging, committing, or changing files."""

    def __init__(self, root_directory: str, max_diff_chars: int = 30000):
        self.root = Path(root_directory).expanduser().resolve()
        self.max_diff_chars = max_diff_chars

    def _run(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            raise RuntimeError(message or f"git {' '.join(arguments)} failed")
        return result.stdout

    def review(self) -> str:
        try:
            repository_root = self._run("rev-parse", "--show-toplevel").strip()
        except (OSError, RuntimeError) as exc:
            return f"Git review unavailable: {exc}"

        status = self._run("status", "--short").strip()
        diff_stat = self._run("diff", "--stat").strip()
        diff = self._run("diff")
        if len(diff) > self.max_diff_chars:
            diff = diff[:self.max_diff_chars] + "\n... diff truncated ..."

        if not status:
            status = "Working tree clean."
        if not diff_stat:
            diff_stat = "No unstaged tracked-file diff."
        if not diff:
            diff = "No unstaged diff available."

        return (
            f"Git repository: {repository_root}\n"
            f"Status:\n{status}\n\n"
            f"Diff summary:\n{diff_stat}\n\n"
            f"Unstaged diff:\n{diff}"
        )
