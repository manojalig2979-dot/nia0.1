from code_workspace import CodeWorkspace


def test_change_plan_builds_combined_diff_and_validates_match(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sample = project / "sample.py"
    sample.write_text("hello = 'world'\nprint(hello)\n", encoding="utf-8")

    workspace = CodeWorkspace(str(project))
    plan = {
        "reason": "Update the greeting variable to a new message.",
        "expected_behavior": "The program prints the new greeting value.",
        "risk_level": "low",
        "changes": [
            {
                "relative_path": "sample.py",
                "old_text": "hello = 'world'",
                "new_text": "hello = 'planet'",
            }
        ],
    }

    validated = workspace.validate_change_plan(plan)
    assert validated["valid"] is True
    assert "sample.py" in validated["affected_files"]
    assert "diff" in validated
    assert "hello = 'planet'" in validated["diff"]


def test_change_plan_rejects_sensitive_paths_and_unmatched_text(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sample = project / "sample.py"
    sample.write_text("hello = 'world'\n", encoding="utf-8")

    workspace = CodeWorkspace(str(project))
    plan = {
        "reason": "Rotate API key for access.",
        "expected_behavior": "Use the key safely.",
        "risk_level": "medium",
        "changes": [
            {
                "relative_path": "config.json",
                "old_text": '"token": "old"',
                "new_text": '"token": "new"',
            }
        ],
    }

    try:
        workspace.validate_change_plan(plan)
        assert False, "Expected validation to reject the unsafe plan."
    except ValueError as exc:
        text = str(exc).lower()
        assert "secret" in text or "sensitive" in text or "config.json" in text
