from pathlib import Path

from project_validator import ProjectValidator


def test_validate_prefers_pytest_when_tests_exist(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "test_example.py").write_text(
        "def test_ok():\n"
        "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    validator = ProjectValidator(str(project))
    result = validator.validate()

    assert "pytest" in result.lower()
    assert "passed" in result.lower() or "failed" in result.lower()


def test_validate_handles_missing_tests_gracefully(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "example.py").write_text("print('hello')\n", encoding="utf-8")

    validator = ProjectValidator(str(project))
    result = validator.validate()

    assert "compile" in result.lower() or "no python files" in result.lower()
