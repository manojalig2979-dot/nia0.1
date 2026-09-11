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
            branch = self._run("branch", "--show-current").strip() or "(detached HEAD)"
            status = self._run("status", "--short").strip()
            staged_status = self._run("diff", "--cached", "--stat").strip()
            unstaged_status = self._run("diff", "--stat").strip()
            staged_diff = self._run("diff", "--cached")
            unstaged_diff = self._run("diff")
        except (OSError, RuntimeError) as exc:
            return f"Git review unavailable: {exc}"

        if len(staged_diff) > self.max_diff_chars:
            staged_diff = staged_diff[:self.max_diff_chars] + "\n... diff truncated ..."
        if len(unstaged_diff) > self.max_diff_chars:
            unstaged_diff = unstaged_diff[:self.max_diff_chars] + "\n... diff truncated ..."

        if not status:
            status = "Working tree clean."
        if not staged_status:
            staged_status = "No staged changes."
        if not unstaged_status:
            unstaged_status = "No unstaged changes."
        if not staged_diff:
            staged_diff = "No staged diff available."
        if not unstaged_diff:
            unstaged_diff = "No unstaged diff available."

        return (
            f"Git repository: {repository_root}\n"
            f"Branch: {branch}\n\n"
            f"Status:\n{status}\n\n"
            f"Staged changes:\n{staged_status}\n\n"
            f"Staged diff:\n{staged_diff}\n\n"
            f"Unstaged changes:\n{unstaged_status}\n\n"
            f"Unstaged diff:\n{unstaged_diff}"
        )

    def commit(self, message: str, paths: list[str], confirm: bool = False) -> str:
        """Stage selected safe paths and commit them after explicit confirmation."""
        if not confirm:
            raise ValueError("Set confirm=true only after reviewing Git changes.")
        if not message.strip():
            raise ValueError("Commit message must not be empty.")
        if not paths:
            raise ValueError("Provide at least one project-relative path to stage.")

        blocked_fragments = ("config.json", ".env", "nia_browser_profile", ".nia_backups")
        safe_paths = []
        for path_text in paths:
            path = Path(path_text)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Path must be project-relative: {path_text}")
            if any(fragment in path.as_posix() for fragment in blocked_fragments):
                raise ValueError(f"Sensitive path cannot be committed: {path_text}")
            safe_paths.append(path.as_posix())

        self._run("add", "--", *safe_paths)
        try:
            commit_result = self._run("commit", "-m", message.strip()).strip()
        except RuntimeError:
            self._run("reset", "HEAD", "--", *safe_paths)
            raise
        return f"Commit created successfully. Push was not performed.\n{commit_result}"
