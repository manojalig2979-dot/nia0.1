from agent_orchestrator import NiaAgentOrchestrator


class FakeGitHubAutomation:
    def create_pull_request(self, title, body="", base="main", head=None, confirm=False):
        return {
            "title": title,
            "body": body,
            "base": base,
            "head": head,
            "confirm": confirm,
        }


def test_orchestrator_dispatches_github_pr_creation():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.github_automation = FakeGitHubAutomation()

    result = agent._execute_tool(
        "create_github_pr",
        {"title": "Add feature", "body": "Describe the change.", "base": "main", "head": "feature/test-branch", "confirm": True},
    )

    assert result == "{'title': 'Add feature', 'body': 'Describe the change.', 'base': 'main', 'head': 'feature/test-branch', 'confirm': True}"
