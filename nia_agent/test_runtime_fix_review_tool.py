from agent_orchestrator import NiaAgentOrchestrator


class FakeGitReview:
    def review(self):
        return "Branch: main\nUnstaged changes: worker.py"


def test_orchestrator_dispatches_runtime_fix_git_review():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.git_review = FakeGitReview()

    result = agent._execute_tool("review_runtime_fix", {})

    assert result == "Branch: main\nUnstaged changes: worker.py"
