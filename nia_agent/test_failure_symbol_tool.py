from agent_orchestrator import NiaAgentOrchestrator


class FakeIndexer:
    def resolve_location(self, path, line):
        return {
            "file": path,
            "line": line,
            "symbol": "run",
            "kind": "method",
            "parent": "Worker",
            "symbol_line": 2,
        }


def test_orchestrator_dispatches_failure_symbol_linking():
    agent = object.__new__(NiaAgentOrchestrator)
    agent.ast_indexer = FakeIndexer()

    result = agent._execute_tool(
        "link_runtime_failure",
        {"path": "worker.py", "line": 3},
    )

    assert result == "{'file': 'worker.py', 'line': 3, 'symbol': 'run', 'kind': 'method', 'parent': 'Worker', 'symbol_line': 2}"
