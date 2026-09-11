from pathlib import Path

from code_workspace import CodeWorkspace


def make_plan(old_text, new_text):
    return {
        "reason": "Repair the runtime failure.",
        "expected_behavior": "The function no longer raises the detected exception.",
        "risk_level": "low",
        "changes": [{
            "relative_path": "worker.py",
            "old_text": old_text,
            "new_text": new_text,
        }],
    }


def test_validates_proposed_python_fix_without_writing(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    original = "def run():\n    return 1 / 0\n"
    source_path.write_text(original, encoding="utf-8")

    result = CodeWorkspace(str(tmp_path)).validate_proposed_change(
        make_plan("return 1 / 0", "return 0")
    )

    assert result["valid"] is True
    assert result["checks"] == [{"path": "worker.py", "check": "python_compile", "passed": True}]
    assert source_path.read_text(encoding="utf-8") == original


def test_reports_syntax_error_in_proposed_python_fix(tmp_path):
    source_path = Path(tmp_path) / "worker.py"
    source_path.write_text("def run():\n    return 1\n", encoding="utf-8")

    result = CodeWorkspace(str(tmp_path)).validate_proposed_change(
        make_plan("return 1", "return (")
    )

    assert result["valid"] is False
    assert result["checks"][0]["check"] == "python_compile"
    assert result["checks"][0]["passed"] is False
    assert "SyntaxError" in result["checks"][0]["error"]
