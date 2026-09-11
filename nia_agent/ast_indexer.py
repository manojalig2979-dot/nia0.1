"""Read-only Python AST symbol inspection for NIA."""

import ast
from pathlib import Path


class _SymbolCollector(ast.NodeVisitor):
    """Collect classes, functions, imports, and decorators while tracking class scope."""

    def __init__(self, result: dict):
        self.result = result
        self.class_stack = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.result["classes"].append({
            "name": node.name,
            "kind": "class",
            "line": node.lineno,
            "decorators": [
                d.id if isinstance(d, ast.Name) else getattr(d, "attr", None)
                for d in node.decorator_list
            ],
        })
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_function(node)
        self.generic_visit(node)

    def _record_function(self, node):
        kind = "method" if self.class_stack else "function"
        self.result["functions"].append({
            "name": node.name,
            "kind": kind,
            "line": node.lineno,
            "decorators": [
                d.id if isinstance(d, ast.Name) else getattr(d, "attr", None)
                for d in node.decorator_list
            ],
            "parent": self.class_stack[-1] if self.class_stack else None,
        })
        for decorator in node.decorator_list:
            self.result["decorators"].append({
                "name": decorator.id if isinstance(decorator, ast.Name) else getattr(decorator, "attr", None),
                "target": node.name,
                "line": decorator.lineno,
                "kind": kind,
            })

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.result["imports"].append({
                "name": alias.name,
                "asname": alias.asname,
                "kind": "import",
                "line": node.lineno,
            })

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.result["imports"].append({
                "name": alias.name,
                "module": node.module,
                "asname": alias.asname,
                "kind": "from_import",
                "line": node.lineno,
            })


class PythonASTIndexer:
    """Inspect Python files and extract class, function, import, and decorator symbols."""

    def __init__(self, root_directory: str, max_files: int = 500):
        self.root = Path(root_directory).expanduser().resolve()
        self.max_files = max_files

    def _safe_relative_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.name

    def _iter_python_files(self) -> list[Path]:
        if not self.root.exists() or not self.root.is_dir():
            return []

        files = []
        for path in self.root.rglob("*.py"):
            if not path.is_file():
                continue
            if any(part in {".git", "__pycache__", ".venv", "venv", "nia_browser_profile"} for part in path.parts):
                continue
            files.append(path)
            if len(files) >= self.max_files:
                break
        return sorted(files, key=lambda item: item.relative_to(self.root).as_posix())

    def inspect_file(self, file_path: str | Path) -> dict:
        path = Path(file_path)
        if not path.is_absolute():
            path = (self.root / path).resolve()

        result = {
            "path": self._safe_relative_path(path),
            "classes": [],
            "functions": [],
            "imports": [],
            "decorators": [],
            "syntax_error": None,
        }

        try:
            source = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {**result, "syntax_error": "File not found."}
        except UnicodeDecodeError:
            return {**result, "syntax_error": "File is not valid UTF-8 text."}

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            result["syntax_error"] = (
                f"SyntaxError: {exc.msg} (line {exc.lineno}, column {exc.offset})"
            )
            return result

        collector = _SymbolCollector(result)
        collector.visit(tree)

        result["classes"].sort(key=lambda item: item["line"])
        result["functions"].sort(key=lambda item: item["line"])
        result["imports"].sort(key=lambda item: item["line"])
        result["decorators"].sort(key=lambda item: item["line"])
        return result

    def inspect_project(self, relative_path: str | None = None) -> dict:
        if relative_path:
            return self.inspect_file(relative_path)

        files = []
        for file_path in self._iter_python_files():
            result = self.inspect_file(file_path)
            if result["syntax_error"]:
                files.append({"path": result["path"], "syntax_error": result["syntax_error"], "classes": [], "functions": [], "imports": [], "decorators": []})
            else:
                files.append({
                    "path": result["path"],
                    "syntax_error": None,
                    "classes": result["classes"],
                    "functions": result["functions"],
                    "imports": result["imports"],
                    "decorators": result["decorators"],
                })
        return {"root": str(self.root), "files": files}

    def format_summary(self, relative_path: str | None = None) -> str:
        if relative_path:
            result = self.inspect_file(relative_path)
            if result["syntax_error"]:
                return f"{result['path']}\nSyntax error: {result['syntax_error']}"

            parts = [f"Python symbols for {result['path']}"]
            parts.append("Classes:")
            parts.extend(f"- {item['name']} (line {item['line']})" for item in result["classes"])
            parts.append("Functions:")
            parts.extend(f"- {item['name']} ({item['kind']}, line {item['line']})" for item in result["functions"])
            parts.append("Imports:")
            parts.extend(f"- {item['name']} (line {item['line']})" for item in result["imports"])
            return "\n".join(parts) if parts else f"No symbols found in {result['path']}"

        project = self.inspect_project()
        summaries = []
        for file_info in project["files"]:
            if file_info.get("syntax_error"):
                summaries.append(f"{file_info['path']}\n  Syntax error: {file_info['syntax_error']}")
                continue
            classes = ", ".join(item['name'] for item in file_info["classes"]) or "none"
            functions = ", ".join(item['name'] for item in file_info["functions"]) or "none"
            imports = ", ".join(item['name'] for item in file_info["imports"]) or "none"
            summaries.append(
                f"{file_info['path']}\n  classes: {classes}\n  functions: {functions}\n  imports: {imports}"
            )
        return "\n".join(summaries) if summaries else "No Python files were indexed."
