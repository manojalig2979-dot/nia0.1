from pathlib import Path

from github_automation import GitHubAutomation


def test_inspects_local_github_workflows_read_only(tmp_path):
    workflow_dir = Path(tmp_path) / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "tests.yml"
    workflow.write_text(
        "name: Tests\n"
        "on:\n"
        "  push:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    report = GitHubAutomation(str(tmp_path)).inspect_ci_workflows()

    assert report["workflow_count"] == 1
    assert report["workflows"][0]["name"] == "Tests"
    assert report["workflows"][0]["triggers"] == ["push", "pull_request"]
    assert report["workflows"][0]["jobs"] == ["test", "lint"]
    assert workflow.read_text(encoding="utf-8").startswith("name: Tests")


def test_reports_missing_workflow_directory(tmp_path):
    report = GitHubAutomation(str(tmp_path)).inspect_ci_workflows()

    assert report == {"workflow_count": 0, "workflows": [], "workflow_directory": ".github/workflows"}
