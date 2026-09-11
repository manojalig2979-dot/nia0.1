from pathlib import Path

from ast_indexer import PythonASTIndexer
from system_diagnostics import SystemDiagnostics


def test_links_traceback_location_to_nearest_python_symbol(tmp_path):
    source = (
        "class Worker:\n"
        "    def run(self):\n"
        "        value = 1 / 0\n"
        "        return value\n"
    )
    source_path = Path(tmp_path) / "worker.py"
    source_path.write_text(source, encoding="utf-8")
    diagnostics = SystemDiagnostics(log_dir=str(tmp_path))
    report = diagnostics._parse_traceback(
        'Traceback (most recent call last):\n'
        f'  File "{source_path}", line 3, in run\n'
        "ZeroDivisionError: division by zero\n",
        str(source_path),
    )

    linked = PythonASTIndexer(str(tmp_path)).resolve_location(
        report["file"], report["line"]
    )

    assert linked["symbol"] == "run"
    assert linked["kind"] == "method"
    assert linked["parent"] == "Worker"
    assert linked["line"] == 3
    assert linked["symbol_line"] == 2


def test_returns_file_only_when_location_has_no_symbol(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    source_path.write_text("import math\n\nVALUE = 1\n", encoding="utf-8")

    linked = PythonASTIndexer(str(tmp_path)).resolve_location(str(source_path), 3)

    assert linked == {"file": "worker.py", "line": 3, "symbol": None}
