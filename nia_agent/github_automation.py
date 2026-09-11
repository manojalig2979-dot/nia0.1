import re
from pathlib import Path


class GitHubAutomation:
    """Read-only local inspection for GitHub Actions workflow metadata."""

    def __init__(self, root_directory: str):
        self.root = Path(root_directory).expanduser().resolve()
        self.workflow_root = self.root / ".github" / "workflows"

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
