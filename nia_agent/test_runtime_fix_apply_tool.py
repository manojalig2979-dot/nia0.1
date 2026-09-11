from agent_orchestrator import NiaAgentOrchestrator


class FakeWorkspace:
    def apply_runtime_fix(self, failure, plan, confirm=False):
        assert confirm is True
        return "Applied runtime fix"


class FakeValidator:
    def validate(self):
        return "Validation passed"


def test_orchestrator_applies_runtime_fix_then_validates():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.code_workspace = FakeWorkspace()
    agent.project_validator = FakeValidator()

    result = agent._execute_tool(
        "apply_runtime_fix",
        {"failure": {"found": True}, "plan": {}, "confirm": True},
    )

    assert result == "{'apply': 'Applied runtime fix', 'validation': 'Validation passed'}"
