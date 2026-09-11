from agent_orchestrator import NiaAgentOrchestrator


class FakeDiagnostics:
    def analyze_runtime_log(self, path):
        return {"found": True, "source": path}


def test_orchestrator_dispatches_runtime_log_analysis():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.diagnostics = FakeDiagnostics()

    result = agent._execute_tool("analyze_runtime_log", {"path": "runtime.log"})

    assert result == "{'found': True, 'source': 'runtime.log'}"
