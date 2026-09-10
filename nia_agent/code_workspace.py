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
