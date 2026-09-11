from pathlib import Path

from code_workspace import CodeWorkspace


def make_plan():
    return {
        "reason": "Repair the runtime failure.",
        "expected_behavior": "The function returns zero.",
        "risk_level": "low",
        "changes": [{
            "relative_path": "worker.py",
            "old_text": "return 1 / 0",
            "new_text": "return 0",
        }],
    }


def test_runtime_fix_apply_requires_explicit_confirmation(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    original = "def run():\n    return 1 / 0\n"
    source_path.write_text(original, encoding="utf-8")

    try:
        CodeWorkspace(str(tmp_path)).apply_runtime_fix({"found": True}, make_plan(), confirm=False)
    except ValueError as exc:
        assert "confirm=true" in str(exc)
    else:
        raise AssertionError("runtime fixes must require explicit confirmation")
    assert source_path.read_text(encoding="utf-8") == original


def test_runtime_fix_apply_validates_and_writes_after_confirmation(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    source_path.write_text("def run():\n    return 1 / 0\n", encoding="utf-8")

    result = CodeWorkspace(str(tmp_path)).apply_runtime_fix(
        {"found": True}, make_plan(), confirm=True
    )

    assert "Applied 1 file changes" in result
    assert source_path.read_text(encoding="utf-8") == "def run():\n    return 0\n"
