import github_automation

from github_automation import GitHubAutomation


def test_create_pull_request_requires_explicit_confirmation(tmp_path):
    automation = GitHubAutomation(str(tmp_path))

    try:
        automation.create_pull_request("Add feature", confirm=False)
    except ValueError as exc:
        assert "confirm=true" in str(exc).lower()
    else:
        raise AssertionError("Pull request creation must require explicit confirmation.")


def test_create_pull_request_calls_gh_cli_after_approval(tmp_path, monkeypatch):
    automation = GitHubAutomation(str(tmp_path))
    command_calls = []

    monkeypatch.setattr(github_automation.shutil, "which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(
        automation,
        "_git_command",
        lambda *args: "feature/test-branch" if args == ("branch", "--show-current") else "main",
    )

    def fake_run(command, cwd=None, capture_output=False, text=None, encoding=None, errors=None, check=False):
        command_calls.append(command)

        class Result:
            returncode = 0
            stdout = "https://github.com/example/repo/pull/123"
            stderr = ""

        return Result()

    monkeypatch.setattr(github_automation.subprocess, "run", fake_run)

    result = automation.create_pull_request(
        "Add feature",
        body="Describe the change.",
        base="main",
        head="feature/test-branch",
        confirm=True,
    )

    assert result == "https://github.com/example/repo/pull/123"
    assert command_calls and command_calls[0][:3] == ["/usr/bin/gh", "pr", "create"]
