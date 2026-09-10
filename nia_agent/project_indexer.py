"""Read-only project indexing for NIA's Phase 2 code workspace."""

import os
from collections import Counter
from pathlib import Path


DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "nia_browser_profile",
    ".pytest_cache",
    ".mypy_cache",
    ".nia_backups",
}


class ProjectIndexer:
    """Build a bounded, text-focused inventory of a project directory."""

    def __init__(self, root_directory: str, max_files: int = 2000):
        self.root = Path(root_directory).expanduser().resolve()
        self.max_files = max_files

    def index(self) -> dict:
        if not self.root.exists():
            return {"root": str(self.root), "exists": False, "error": "Project directory does not exist."}
        if not self.root.is_dir():
            return {"root": str(self.root), "exists": False, "error": "Project path is not a directory."}

        files = []
        extension_counts = Counter()
        ignored_files = 0

        for current_root, directory_names, file_names in os.walk(self.root):
            directory_names[:] = [
                name for name in directory_names
                if name not in DEFAULT_IGNORED_DIRECTORIES and not name.startswith(".")
            ]
            for file_name in sorted(file_names):
                path = Path(current_root) / file_name
                if path.is_symlink():
                    continue
                try:
                    relative_path = path.relative_to(self.root)
                    size = path.stat().st_size
                except OSError:
                    ignored_files += 1
                    continue

                if len(files) >= self.max_files:
                    ignored_files += 1
                    continue
                if size > 2_000_000:
                    ignored_files += 1
                    continue

                extension = path.suffix.lower() or "[no extension]"
                extension_counts[extension] += 1
                files.append({
                    "path": relative_path.as_posix(),
                    "extension": extension,
                    "size_bytes": size,
                })

        files.sort(key=lambda item: item["path"].lower())
        return {
            "root": str(self.root),
            "exists": True,
            "file_count": len(files),
            "ignored_file_count": ignored_files,
            "extensions": dict(sorted(extension_counts.items())),
            "files": files,
        }

    def format_summary(self) -> str:
        result = self.index()
        if not result.get("exists"):
            return f"Project index error: {result.get('error', 'Unknown error')}"

        extension_summary = ", ".join(
            f"{extension}: {count}"
            for extension, count in result["extensions"].items()
        ) or "none"
        file_lines = "\n".join(
            f"- {item['path']} ({item['size_bytes']} bytes)"
            for item in result["files"]
        )
        return (
            f"Project: {result['root']}\n"
            f"Files indexed: {result['file_count']}\n"
            f"Ignored files: {result['ignored_file_count']}\n"
            f"Extensions: {extension_summary}\n"
            f"Indexed files:\n{file_lines or '- none'}"
        )
