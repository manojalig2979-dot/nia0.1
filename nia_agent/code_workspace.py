"""Safe read and preview operations for NIA's Phase 2 code workspace."""

import difflib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


class CodeWorkspace:
    """Read project files and preview exact changes without writing to disk."""

    def __init__(self, root_directory: str, max_file_bytes: int = 1_000_000):
        self.root = Path(root_directory).expanduser().resolve()
        self.max_file_bytes = max_file_bytes

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
        if candidate.stat().st_size > self.max_file_bytes:
            raise ValueError("File is too large for a safe workspace read.")
        return candidate

    def read_file(self, relative_path: str) -> str:
        path = self._resolve_file(relative_path)
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Only UTF-8 text files are supported.") from exc

    def preview_change(self, relative_path: str, old_text: str, new_text: str) -> str:
        if not old_text:
            raise ValueError("old_text must not be empty.")
        current_text = self.read_file(relative_path)
        occurrences = current_text.count(old_text)
        if occurrences == 0:
            raise ValueError("old_text was not found in the selected file.")
        if occurrences > 1:
            raise ValueError("old_text occurs more than once; provide a more specific block.")

        proposed_text = current_text.replace(old_text, new_text, 1)
        diff = difflib.unified_diff(
            current_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile=relative_path,
            tofile=relative_path,
        )
        return "".join(diff) or "No changes proposed."

    def preview_multi_change(self, changes: list[dict]) -> str:
        if not changes:
            raise ValueError("Provide at least one file change.")

        previews = []
        for change in changes:
            relative_path = change.get("relative_path", "")
            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")
            previews.append(self.preview_change(relative_path, old_text, new_text))
        return "\n".join(previews)

    def validate_change_plan(self, plan: dict) -> dict:
        if not isinstance(plan, dict):
            raise ValueError("Change plan must be a dictionary.")

        reason = str(plan.get("reason", "")).strip()
        expected_behavior = str(plan.get("expected_behavior", "")).strip()
        risk_level = str(plan.get("risk_level", "")).strip()
        changes = plan.get("changes", [])

        if not reason or not expected_behavior or not risk_level:
            raise ValueError("Change plan requires reason, expected_behavior, and risk_level.")
        if not isinstance(changes, list) or not changes:
            raise ValueError("Change plan requires at least one change entry.")

        sensitive_names = {
            ".env",
            ".env.local",
            "config.json",
            "config.example.json",
            "secrets.json",
            "credentials.json",
            "token.json",
            "api_keys.json",
            "*.pem",
            "id_rsa",
            ".gitignore",
        }

        diffs = []
        affected_files = []

        for change in changes:
            relative_path = str(change.get("relative_path", "")).strip()
            old_text = str(change.get("old_text", ""))
            new_text = str(change.get("new_text", ""))
            if not relative_path:
                raise ValueError("Each change requires a relative_path.")

            basename = Path(relative_path).name.lower()
            if basename in sensitive_names or ".env" in basename or "secret" in basename or "key" in basename or "config" in basename:
                raise ValueError(f"Sensitive path rejected: {relative_path}")
            if any(part in {".nia_backups", "nia_browser_profile", ".git"} for part in Path(relative_path).parts):
                raise ValueError(f"Sensitive path rejected: {relative_path}")

            path = self._resolve_file(relative_path)
            current_text = self.read_file(relative_path)
            occurrences = current_text.count(old_text)
            if not old_text:
                raise ValueError(f"old_text must not be empty for {relative_path}.")
            if occurrences == 0:
                raise ValueError(f"old_text was not found in {relative_path}; the plan may be stale.")
            if occurrences > 1:
                raise ValueError(f"old_text occurs more than once in {relative_path}; provide a more specific block.")

            proposed_text = current_text.replace(old_text, new_text, 1)
            diff = "".join(difflib.unified_diff(
                current_text.splitlines(keepends=True),
                proposed_text.splitlines(keepends=True),
                fromfile=relative_path,
                tofile=relative_path,
            ))
            diffs.append(diff)
            affected_files.append(relative_path)

        combined_diff = "\n".join(diffs)
        return {
            "valid": True,
            "reason": reason,
            "expected_behavior": expected_behavior,
            "risk_level": risk_level,
            "affected_files": affected_files,
            "diff": combined_diff,
        }

    def preview_runtime_fix(self, failure: dict, plan: dict) -> dict:
        """Build an approval-required fix preview for a detected runtime failure."""
        if not isinstance(failure, dict) or not failure.get("found"):
            raise ValueError("A detected runtime failure is required before proposing a fix.")

        validated_plan = self.validate_change_plan(plan)
        context_keys = ("category", "file", "line", "symbol", "kind", "parent")
        failure_context = {
            key: failure[key]
            for key in context_keys
            if key in failure and failure[key] is not None
        }
        return {
            "approval_required": True,
            "failure": failure_context,
            "plan": validated_plan,
        }

    def validate_proposed_change(self, plan: dict) -> dict:
        """Validate an exact change plan without writing its proposed content."""
        self.validate_change_plan(plan)
        checks = []
        for change in plan["changes"]:
            relative_path = str(change.get("relative_path", ""))
            current_text = self.read_file(relative_path)
            proposed_text = current_text.replace(change["old_text"], change["new_text"], 1)
            if Path(relative_path).suffix.lower() != ".py":
                continue

            check = {
                "path": relative_path,
                "check": "python_compile",
                "passed": True,
            }
            try:
                compile(proposed_text, relative_path, "exec")
            except SyntaxError as exc:
                check["passed"] = False
                check["error"] = f"SyntaxError: {exc.msg} (line {exc.lineno}, column {exc.offset})"
            checks.append(check)

        return {"valid": all(check["passed"] for check in checks), "checks": checks}

    def apply_runtime_fix(self, failure: dict, plan: dict, confirm: bool = False) -> str:
        """Apply a validated runtime fix only after explicit confirmation."""
        if not isinstance(failure, dict) or not failure.get("found"):
            raise ValueError("A detected runtime failure is required before applying a fix.")
        if not confirm:
            raise ValueError("Set confirm=true only after reviewing preview_runtime_fix.")

        self.validate_change_plan(plan)
        validation = self.validate_proposed_change(plan)
        if not validation["valid"]:
            raise ValueError(f"Proposed runtime fix failed validation: {validation['checks']}")
        return self.apply_multi_change(plan["changes"], confirm=True)

    def apply_change(
        self,
        relative_path: str,
        old_text: str,
        new_text: str,
        confirm: bool = False,
    ) -> str:
        """Apply one exact replacement after explicit confirmation, with a backup."""
        if not confirm:
            raise ValueError("Set confirm=true only after reviewing preview_file_change.")
        path = self._resolve_file(relative_path)
        current_text = self.read_file(relative_path)
        occurrences = current_text.count(old_text)
        if not old_text:
            raise ValueError("old_text must not be empty.")
        if occurrences == 0:
            raise ValueError("old_text was not found; the file may have changed since preview.")
        if occurrences > 1:
            raise ValueError("old_text occurs more than once; provide a more specific block.")

        proposed_text = current_text.replace(old_text, new_text, 1)
        backup_directory = self.root / ".nia_backups"
        backup_directory.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = backup_directory / f"{path.name}.{timestamp}.bak"
        shutil.copy2(path, backup_path)

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_file.write(proposed_text)
            temporary_path = Path(temporary_file.name)
        try:
            temporary_path.replace(path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        diff = difflib.unified_diff(
            current_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile=relative_path,
            tofile=relative_path,
        )
        return f"Applied change to {relative_path}. Backup: {backup_path.relative_to(self.root)}\n" + "".join(diff)

    def apply_multi_change(self, changes: list[dict], confirm: bool = False) -> str:
        """Apply a validated multi-file plan with backups and rollback on failure."""
        if not confirm:
            raise ValueError("Set confirm=true only after reviewing preview_multi_file_change.")
        if not changes:
            raise ValueError("Provide at least one file change.")

        prepared = []
        seen_paths = set()
        for change in changes:
            relative_path = change.get("relative_path", "")
            if relative_path in seen_paths:
                raise ValueError(f"File appears more than once: {relative_path}")
            seen_paths.add(relative_path)
            path = self._resolve_file(relative_path)
            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")
            current_text = self.read_file(relative_path)
            occurrences = current_text.count(old_text)
            if not old_text or occurrences == 0:
                raise ValueError(f"old_text was not found in {relative_path}; the plan may be stale.")
            if occurrences > 1:
                raise ValueError(f"old_text occurs more than once in {relative_path}.")
            prepared.append((relative_path, path, current_text, current_text.replace(old_text, new_text, 1)))

        backup_directory = self.root / ".nia_backups"
        backup_directory.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backups = []
        written = []
        try:
            for index, (relative_path, path, current_text, proposed_text) in enumerate(prepared):
                backup_path = backup_directory / f"{path.name}.{timestamp}_{index}.bak"
                shutil.copy2(path, backup_path)
                backups.append((path, backup_path))
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary_file:
                    temporary_file.write(proposed_text)
                    temporary_path = Path(temporary_file.name)
                temporary_path.replace(path)
                written.append(path)
        except Exception:
            for path, backup_path in backups:
                if path in written:
                    shutil.copy2(backup_path, path)
            raise

        diffs = []
        for relative_path, path, current_text, proposed_text in prepared:
            diffs.append("".join(difflib.unified_diff(
                current_text.splitlines(keepends=True),
                proposed_text.splitlines(keepends=True),
                fromfile=relative_path,
                tofile=relative_path,
            )))
        return f"Applied {len(prepared)} file changes. Backups stored in .nia_backups.\n" + "\n".join(diffs)
