from agent_orchestrator import NiaAgentOrchestrator


class FakeWorkspace:
    def validate_proposed_change(self, plan):
        return {"valid": True, "checks": [{"check": "python_compile", "passed": True}]}


def test_orchestrator_dispatches_runtime_fix_validation():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.code_workspace = FakeWorkspace()

    result = agent._execute_tool("validate_runtime_fix", {"plan": {"changes": []}})

    assert result == "{'valid': True, 'checks': [{'check': 'python_compile', 'passed': True}]}"
