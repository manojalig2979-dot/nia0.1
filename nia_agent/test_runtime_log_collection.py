from pathlib import Path

from system_diagnostics import SystemDiagnostics


def test_collects_tracebacks_from_supported_runtime_logs(tmp_path):
    (tmp_path / "application.log").write_text(
        "Traceback (most recent call last):\n"
        "  File \"worker.py\", line 7, in run\n"
        "    raise RuntimeError('failed')\n"
        "RuntimeError: failed\n",
        encoding="utf-8",
    )
    (tmp_path / "clean.txt").write_text("INFO ready\n", encoding="utf-8")
    (tmp_path / "ignored.json").write_text('{"error": "not a log"}', encoding="utf-8")

    reports = SystemDiagnostics(log_dir=str(tmp_path)).collect_runtime_logs()

    assert len(reports) == 1
    assert reports[0]["exception_type"] == "RuntimeError"
    assert reports[0]["file"] == "worker.py"
    assert reports[0]["line"] == 7


def test_runtime_log_collection_is_bounded(tmp_path):
    for index in range(4):
        (tmp_path / f"runtime-{index}.log").write_text(
            "Traceback (most recent call last):\n"
            "  File \"worker.py\", line 1, in run\n"
            "RuntimeError: failed\n",
            encoding="utf-8",
        )

    reports = SystemDiagnostics(log_dir=str(tmp_path)).collect_runtime_logs(max_files=2)

    assert len(reports) == 2
