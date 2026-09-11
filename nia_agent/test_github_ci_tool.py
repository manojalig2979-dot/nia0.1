from agent_orchestrator import NiaAgentOrchestrator


class FakeGitHubAutomation:
    def inspect_ci_workflows(self):
        return {"workflow_count": 1, "workflows": [{"name": "Tests"}]}


def test_orchestrator_dispatches_github_ci_inspection():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.github_automation = FakeGitHubAutomation()

    result = agent._execute_tool("inspect_github_ci", {})

    assert result == "{'workflow_count': 1, 'workflows': [{'name': 'Tests'}]}"
