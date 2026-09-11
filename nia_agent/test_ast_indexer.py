import pytest

from ast_indexer import PythonASTIndexer


def test_ast_indexer_collects_python_symbols(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text(
        "import os\n\n"
        "class Example:\n"
        "    def method(self, value):\n"
        "        return value\n\n"
        "def helper(value):\n"
        "    return value\n",
        encoding="utf-8",
    )

    indexer = PythonASTIndexer(str(tmp_path))
    result = indexer.inspect_file(file_path)

    assert result["syntax_error"] is None
    assert any(item["name"] == "Example" and item["kind"] == "class" and item["line"] == 3 for item in result["classes"])
    assert any(item["name"] == "method" and item["kind"] == "method" and item["line"] == 4 for item in result["functions"])
    assert any(item["name"] == "helper" and item["kind"] == "function" and item["line"] == 7 for item in result["functions"])
    assert any(item["name"] == "os" and item["kind"] == "import" for item in result["imports"])


def test_ast_indexer_reports_syntax_error(tmp_path):
    broken_file = tmp_path / "broken.py"
    broken_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    indexer = PythonASTIndexer(str(tmp_path))
    result = indexer.inspect_file(broken_file)

    assert result["syntax_error"] is not None
    assert "SyntaxError" in result["syntax_error"]
    assert result["classes"] == []
    assert result["functions"] == []
