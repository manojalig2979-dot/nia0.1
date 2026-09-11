from agent_orchestrator import NiaAgentOrchestrator


class FakeDiagnostics:
    def collect_runtime_logs(self, max_files=10):
        return [{"exception_type": "RuntimeError", "file": "worker.py", "line": 7}]


def test_orchestrator_dispatches_runtime_log_collection():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.diagnostics = FakeDiagnostics()

    result = agent._execute_tool("collect_runtime_logs", {"max_files": 3})

    assert result == "[{'exception_type': 'RuntimeError', 'file': 'worker.py', 'line': 7}]"
