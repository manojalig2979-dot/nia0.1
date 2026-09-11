from agent_orchestrator import NiaAgentOrchestrator


class FakeGitReview:
    def commit(self, message, paths, confirm=False):
        assert message == "Repair runtime failure"
        assert paths == ["worker.py"]
        assert confirm is True
        return "Commit created successfully. Push was not performed."


def test_orchestrator_dispatches_runtime_fix_commit_with_confirmation():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.git_review = FakeGitReview()

    result = agent._execute_tool(
        "commit_runtime_fix",
        {"message": "Repair runtime failure", "paths": ["worker.py"], "confirm": True},
    )

    assert result == "Commit created successfully. Push was not performed."
