"""Read-only project indexing for NIA's Phase 2 code workspace."""

import json
import os
import re
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

    def _resolve_file(self, relative_path: str) -> Path:
        requested = Path(relative_path)
        if requested.is_absolute():
            raise ValueError("Use a project-relative file path.")

        candidate = (self.root / requested).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("File path is outside the configured project.") from exc
        if not candidate.is_file():
            raise FileNotFoundError(f"Project file not found: {relative_path}")
        return candidate

    def _detect_language(self, relative_path: str) -> str:
        suffix = Path(relative_path).suffix.lower()
        language_map = {
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".json": "json",
            ".py": "python",
        }
        return language_map.get(suffix, "unknown")

    def inspect_file_structure(self, relative_path: str) -> dict:
        path = self._resolve_file(relative_path)
        source = path.read_text(encoding="utf-8")
        language = self._detect_language(relative_path)

        if language in {"javascript", "typescript"}:
            symbols = []
            pattern = re.compile(r"(?:class\s+(\w+)|function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=)")
            for index, line in enumerate(source.splitlines(), start=1):
                match = pattern.search(line)
                if not match:
                    continue
                if match.group(1):
                    kind = "class"
                    name = match.group(1)
                elif match.group(2):
                    kind = "function"
                    name = match.group(2)
                else:
                    kind = "variable"
                    name = match.group(3)
                symbols.append({"name": name, "kind": kind, "line": index})
            return {"path": relative_path, "language": language, "symbols": symbols}

        if language == "json":
            data = json.loads(source)
            keys = []

            def walk(value, prefix=""):
                if isinstance(value, dict):
                    for key in value:
                        keys.append(key if not prefix else f"{prefix}.{key}")
                        walk(value[key], f"{prefix}.{key}" if prefix else key)
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        walk(item, f"{prefix}[{index}]")

            walk(data)
            return {"path": relative_path, "language": language, "keys": keys}

        if language == "html":
            tags = []
            for match in re.finditer(r"<\s*/?\s*([A-Za-z0-9-]+)", source):
                tag = match.group(1).lower()
                if tag not in tags:
                    tags.append(tag)
            return {"path": relative_path, "language": language, "tags": tags, "ids": sorted(set(re.findall(r'id=[\"\']([^\"\']+)[\"\']', source))), "classes": sorted(set(re.findall(r'class=[\"\']([^\"\']+)[\"\']', source)))}

        if language == "css":
            selectors = []
            for match in re.finditer(r"([.#]?[A-Za-z0-9_-]+(?:\s+[.#]?[A-Za-z0-9_-]+)*)\s*\{", source):
                selector = match.group(1).strip()
                if selector and selector not in selectors:
                    selectors.append(selector)
            return {"path": relative_path, "language": language, "selectors": selectors}

        return {"path": relative_path, "language": language, "symbols": [], "keys": [], "tags": [], "selectors": []}

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
