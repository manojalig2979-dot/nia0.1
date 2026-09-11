from agent_orchestrator import NiaAgentOrchestrator


class FakeDiagnostics:
    def analyze_runtime_output(self, output, source="terminal"):
        return {"found": True, "category": "timeout", "source": source}


def test_orchestrator_dispatches_runtime_output_analysis():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.diagnostics = FakeDiagnostics()

    result = agent._execute_tool(
        "analyze_runtime_output",
        {"output": "Command timed out", "source": "terminal"},
    )

    assert result == "{'found': True, 'category': 'timeout', 'source': 'terminal'}"
