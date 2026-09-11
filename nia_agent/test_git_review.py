import subprocess

from git_review import GitReview


def test_git_review_reports_branch_and_staged_vs_unstaged(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)

    (repo / "tracked.txt").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    (repo / "tracked.txt").write_text("after\n", encoding="utf-8")
    (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=repo, check=True)

    review = GitReview(str(repo))
    output = review.review()

    assert "Branch:" in output or "branch:" in output
    assert "Staged" in output or "staged" in output
    assert "Unstaged" in output or "unstaged" in output
    assert "staged.txt" in output
    assert "tracked.txt" in output
