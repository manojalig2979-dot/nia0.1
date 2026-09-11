from pathlib import Path

from system_diagnostics import SystemDiagnostics


def test_analyzes_python_traceback_without_exposing_unrelated_log_data(tmp_path):
    log_path = Path(tmp_path) / "runtime.log"
    log_path.write_text(
        "INFO startup complete\n"
        "Traceback (most recent call last):\n"
        "  File \"C:/projects/nia/worker.py\", line 42, in run\n"
        "    result = 1 / 0\n"
        "ZeroDivisionError: division by zero\n"
        "DEBUG internal token=should-not-be-returned\n",
        encoding="utf-8",
    )
    diagnostics = SystemDiagnostics(log_dir=str(tmp_path))

    report = diagnostics.analyze_log_file(str(log_path))

    assert report["found"] is True
    assert report["exception_type"] == "ZeroDivisionError"
    assert report["message"] == "division by zero"
    assert report["file"] == "C:/projects/nia/worker.py"
    assert report["line"] == 42
    assert "should-not-be-returned" not in str(report)


def test_returns_no_error_for_clean_runtime_log(tmp_path):
    log_path = Path(tmp_path) / "clean.log"
    log_path.write_text("INFO startup complete\nINFO ready\n", encoding="utf-8")

    report = SystemDiagnostics(log_dir=str(tmp_path)).analyze_log_file(str(log_path))

    assert report == {"found": False, "source": str(log_path)}


def test_runtime_log_analysis_rejects_paths_outside_log_directory(tmp_path):
    outside_path = Path(tmp_path).parent / "outside.log"
    outside_path.write_text("Traceback (most recent call last):\n", encoding="utf-8")

    diagnostics = SystemDiagnostics(log_dir=str(tmp_path))

    try:
        diagnostics.analyze_runtime_log("../outside.log")
    except ValueError as exc:
        assert "inside the diagnostics log directory" in str(exc)
    else:
        raise AssertionError("path traversal should be rejected")
