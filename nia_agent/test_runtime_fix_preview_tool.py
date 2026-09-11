from agent_orchestrator import NiaAgentOrchestrator


class FakeWorkspace:
    def preview_runtime_fix(self, failure, plan):
        return {"approval_required": True, "failure": failure, "plan": plan}


def test_orchestrator_dispatches_runtime_fix_preview():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.code_workspace = FakeWorkspace()

    result = agent._execute_tool(
        "preview_runtime_fix",
        {"failure": {"found": True}, "plan": {"reason": "test"}},
    )

    assert result == "{'approval_required': True, 'failure': {'found': True}, 'plan': {'reason': 'test'}}"
