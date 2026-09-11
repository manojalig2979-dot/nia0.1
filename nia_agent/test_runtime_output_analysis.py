from system_diagnostics import SystemDiagnostics


def test_classifies_missing_dependency_from_terminal_output(tmp_path):
    output = "Starting worker\nModuleNotFoundError: No module named 'requests'\n"

    report = SystemDiagnostics(log_dir=str(tmp_path)).analyze_runtime_output(output)

    assert report["found"] is True
    assert report["category"] == "missing_dependency"
    assert report["exception_type"] == "ModuleNotFoundError"
    assert report["message"] == "No module named 'requests'"
    assert report["source"] == "terminal"


def test_classifies_timeout_without_executing_the_command(tmp_path):
    report = SystemDiagnostics(log_dir=str(tmp_path)).analyze_runtime_output(
        "Command timed out after 12 seconds\n"
    )

    assert report == {
        "found": True,
        "category": "timeout",
        "message": "Command timed out after 12 seconds",
        "source": "terminal",
    }


def test_ignores_clean_terminal_output(tmp_path):
    report = SystemDiagnostics(log_dir=str(tmp_path)).analyze_runtime_output(
        "Build completed successfully\n"
    )

    assert report == {"found": False, "source": "terminal"}
