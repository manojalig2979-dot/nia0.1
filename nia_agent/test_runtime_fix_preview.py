from pathlib import Path

from code_workspace import CodeWorkspace


def test_runtime_fix_preview_contains_failure_context_and_diff(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    source_path.write_text("def run():\n    return 1 / 0\n", encoding="utf-8")
    workspace = CodeWorkspace(str(tmp_path))
    failure = {
        "found": True,
        "category": "runtime_exception",
        "file": "worker.py",
        "line": 2,
        "symbol": "run",
    }
    plan = {
        "reason": "Replace the invalid division with a safe return value.",
        "expected_behavior": "run returns zero instead of raising ZeroDivisionError.",
        "risk_level": "low",
        "changes": [{
            "relative_path": "worker.py",
            "old_text": "return 1 / 0",
            "new_text": "return 0",
        }],
    }

    preview = workspace.preview_runtime_fix(failure, plan)

    assert preview["approval_required"] is True
    assert preview["failure"]["symbol"] == "run"
    assert preview["plan"]["valid"] is True
    assert "-    return 1 / 0" in preview["plan"]["diff"]
    assert "+    return 0" in preview["plan"]["diff"]
    assert source_path.read_text(encoding="utf-8") == "def run():\n    return 1 / 0\n"


def test_runtime_fix_preview_rejects_undetected_failure(tmp_path):
    (Path(tmp_path) / "worker.py").write_text("value = 1\n", encoding="utf-8")
    plan = {
        "reason": "Change value.",
        "expected_behavior": "Value changes.",
        "risk_level": "low",
        "changes": [{"relative_path": "worker.py", "old_text": "value = 1", "new_text": "value = 2"}],
    }

    try:
        CodeWorkspace(str(tmp_path)).preview_runtime_fix({"found": False}, plan)
    except ValueError as exc:
        assert "detected runtime failure" in str(exc)
    else:
        raise AssertionError("an undetected failure must not produce a fix preview")
