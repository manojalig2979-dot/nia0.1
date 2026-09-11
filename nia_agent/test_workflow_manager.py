from workflow_manager import WorkflowManager


def test_create_project_task_workflow_builds_step_sequence():
    manager = WorkflowManager()
    workflow = manager.create_project_task_workflow("Fix login bug in the auth module")

    assert workflow["task_description"] == "Fix login bug in the auth module"
    assert workflow["steps"][0]["step"] == "inspect_project"
    assert any(step["step"] == "review_git_changes" for step in workflow["steps"])
    assert workflow["required_approvals"] == ["user_approval_before_apply", "user_approval_before_commit", "user_approval_before_push"]


def test_create_project_task_workflow_rejects_empty_task():
    manager = WorkflowManager()

    try:
        manager.create_project_task_workflow("   ")
        assert False, "Expected empty task descriptions to be rejected."
    except ValueError as exc:
        assert "task description" in str(exc).lower()
