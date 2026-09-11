import re
import shutil
import subprocess
from pathlib import Path


class GitHubAutomation:
    """Read-only local inspection for GitHub Actions workflow metadata."""

    def __init__(self, root_directory: str):
        self.root = Path(root_directory).expanduser().resolve()
        self.workflow_root = self.root / ".github" / "workflows"

    def _git_command(self, *arguments: str) -> str:
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
            raise RuntimeError((result.stderr or result.stdout).strip() or "git command failed")
        return result.stdout.strip()

    @staticmethod
    def _unquote(value: str) -> str:
        return value.strip().strip("'\"")

    def _inspect_workflow(self, path: Path) -> dict:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        name = path.stem
        triggers = []
        jobs = []
        section = None

        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            key_match = re.match(r"^([\w.-]+|['\"]?[\w.-]+['\"]?):(?:\s*(.*))?$", stripped)
            if indent == 0 and key_match:
                key = self._unquote(key_match.group(1))
                value = key_match.group(2) or ""
                if key == "name" and value:
                    name = self._unquote(value)
                section = key if key in {"on", "jobs"} else None
                if key == "on" and value.startswith("["):
                    triggers.extend(
                        self._unquote(item) for item in value.strip("[]").split(",") if item.strip()
                    )
                continue

            if indent == 2 and section == "on":
                trigger_match = re.match(r"^([\w.-]+):", stripped)
                if trigger_match:
                    triggers.append(self._unquote(trigger_match.group(1)))
            elif indent == 2 and section == "jobs":
                job_match = re.match(r"^([\w.-]+):", stripped)
                if job_match:
                    jobs.append(self._unquote(job_match.group(1)))

        return {
            "path": path.relative_to(self.root).as_posix(),
            "name": name,
            "triggers": list(dict.fromkeys(triggers)),
            "jobs": list(dict.fromkeys(jobs)),
        }

    def inspect_ci_workflows(self) -> dict:
        """Return workflow metadata without contacting GitHub or editing files."""
        if not self.workflow_root.is_dir():
            return {
                "workflow_count": 0,
                "workflows": [],
                "workflow_directory": ".github/workflows",
            }

        paths = sorted(
            path for path in self.workflow_root.iterdir()
            if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
        )
        workflows = [self._inspect_workflow(path) for path in paths]
        return {
            "workflow_count": len(workflows),
            "workflows": workflows,
            "workflow_directory": ".github/workflows",
        }

    def create_pull_request(
        self,
        title: str,
        body: str = "",
        base: str = "main",
        head: str | None = None,
        confirm: bool = False,
    ) -> str:
        """Create a GitHub pull request through the GitHub CLI after explicit approval."""
        if not confirm:
            raise ValueError("Set confirm=true only after reviewing the branch and pull request details.")
        if not str(title).strip():
            raise ValueError("Pull request title must not be empty.")

        gh_path = shutil.which("gh")
        if not gh_path:
            raise FileNotFoundError("GitHub CLI 'gh' is not installed or not on PATH.")

        branch_name = head or self._git_command("branch", "--show-current")
        command = [
            gh_path,
            "pr",
            "create",
            "--title",
            str(title).strip(),
            "--base",
            str(base).strip() or "main",
            "--head",
            branch_name.strip() or "main",
        ]
        if body.strip():
            command.extend(["--body", body.strip()])

        result = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip() or "GitHub PR creation failed")
        return (result.stdout or result.stderr).strip() or "Pull request created successfully."

    def inspect_pr_status(self, pr_number: str | None = None) -> str:
        """Inspect the CI status and review comments for a GitHub pull request using the GitHub CLI."""
        gh_path = shutil.which("gh")
        if not gh_path:
            raise FileNotFoundError("GitHub CLI 'gh' is not installed or not on PATH.")

        output_parts = []

        view_cmd = [gh_path, "pr", "status"] if not pr_number else [gh_path, "pr", "view", str(pr_number)]
        view_result = subprocess.run(
            view_cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if view_result.returncode == 0 and view_result.stdout.strip():
            output_parts.append(f"--- PR Status/View ---\n{view_result.stdout.strip()}")
        elif view_result.stderr:
            output_parts.append(f"--- PR Status/View Error ---\n{view_result.stderr.strip()}")

        checks_cmd = [gh_path, "pr", "checks"]
        if pr_number:
            checks_cmd.append(str(pr_number).strip())
            
        checks_result = subprocess.run(
            checks_cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if checks_result.returncode == 0 and checks_result.stdout.strip():
            output_parts.append(f"--- PR Checks ---\n{checks_result.stdout.strip()}")
        elif checks_result.stderr:
            output_parts.append(f"--- PR Checks Error ---\n{checks_result.stderr.strip()}")

        if not output_parts:
            return "No PR status or checks could be retrieved."

        return "\n\n".join(output_parts)

