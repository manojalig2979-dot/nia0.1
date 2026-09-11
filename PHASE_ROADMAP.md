# NIA Development Roadmap

Last updated: 2026-09-11
Repository: `nia0.1`
Branch: `main`

## Current State

Phase 1 is complete and pushed to GitHub.

Completed commits:

- `23dd451` Initialize NIA Phase 1 and Phase 2 workspace
- `c06baf6` Improve AI routing and Phase 2 workspace tools
- `0594ee5` Add approved Git commit automation
- `b9c96e4` Add project validation checks
- `c9b53b4` Add safe multi-file change planning

Current repository state at the time of this roadmap: clean and synchronized with `origin/main`.

## Security Before Continuing

- Rotate any API key that was pasted into chat or stored in the old local configuration.
- Keep `nia_agent/config.json` ignored by Git.
- Store the active key in the user environment:

```powershell
[Environment]::SetEnvironmentVariable("NIA_GEMINI_API_KEY", "YOUR_NEW_KEY", "User")
```

- Never paste the real key into chat, source files, Git commits, or GitHub.
- Restart VS Code/NIA after changing environment variables.

## Phase 1: Completed

- PyQt desktop GUI and system tray behavior
- Voice input and Microsoft Swara Neural TTS
- WhatsApp Web integration and persistent browser session
- Desktop app launching and screenshots
- Windows Media Player song routing by default
- YouTube routing only when explicitly requested
- Four local GLB avatars
- Default Michi Bot avatar
- Home-screen avatar selector
- Microphone on/off indicator
- Beep mute control
- Gemini AI command routing
- Desktop shortcut launch scripts
- GitHub repository and main branch
- Secure config example and ignored local secrets

## Phase 2: Completed

- Project inventory with `inspect_project`
- Safe UTF-8 source reading with `read_project_file`
- Single-file unified diff preview
- Explicit-confirmation single-file edits
- Multi-file unified diff preview
- Explicit-confirmation multi-file edits
- Backups in `.nia_backups`
- Rollback protection for multi-file writes
- Python compilation validation with `validate_project`
- Read-only Git status and diff review
- Explicit-confirmation local Git commits
- GitHub push performed manually after review

## Phase 2: Completed Additions

- Better diagnostics with redacted startup logging, AI/provider status, API-key warnings, and microphone availability

All currently planned Phase 2 implementation items are complete and covered by focused regression tests. The next step is release hygiene: run the full suite, review the complete diff, and commit only after explicit approval.

## Phase 2 Historical Breakdown

### 1. Improve Project Indexing

- Detect project type: Python, Node, web, FastAPI, PyQt, and mixed projects.
- Detect entry points such as `main.py`, `pyproject.toml`, `package.json`, and `requirements.txt`.
- Record classes, functions, imports, and module relationships.
- Add file-content search by symbol or keyword.
- Keep browser profiles, caches, secrets, and generated files excluded.

### 2. Add Python AST Understanding

- Parse Python files with the standard-library `ast` module.
- Return classes, functions, decorators, imports, and line numbers.
- Detect syntax errors before proposing changes.
- Build a lightweight symbol index for the configured project.
- Add an orchestrator tool such as `inspect_code_symbols`.

### 3. Add Multi-Language Source Understanding

- Add JavaScript/TypeScript structure detection.
- Add HTML and CSS structure detection.
- Detect JSON configuration keys safely.
- Keep parsing read-only until a change plan is approved.

### 4. Improve Change Planning

- Create a structured change plan before generating replacements.
- Include reason, affected files, expected behavior, and risk level.
- Check that every old-text block still matches before applying.
- Reject plans containing secrets, generated files, or unrelated paths.
- Show a human-readable combined diff before approval.

### 5. Improve Validation

- Keep Python compilation validation.
- Detect and run project-specific tests when available.
- Support `pytest` when installed.
- Support safe Node checks such as `npm test` only when explicitly approved.
- Capture command output and timeout failures.
- Never run destructive or deployment commands automatically.

### 6. Improve Git Workflow

- Show staged and unstaged changes separately.
- Add branch-name inspection.
- Add commit-message preview before committing.
- Add explicit commit approval in the GUI/chat workflow.
- Add optional push approval as a separate action.
- Add branch creation only after explicit approval.
- Never commit `config.json`, `.env`, browser sessions, or backups.

### 7. Add Project Task Workflow

Support a workflow like:

1. User describes a coding task.
2. NIA inspects the project.
3. NIA reads relevant files.
4. NIA proposes a structured plan.
5. NIA previews the diff.
6. User approves.
7. NIA applies the change.
8. NIA validates the project.
9. NIA reviews Git changes.
10. User approves the commit.
11. User separately approves push.

### 8. Add Tests

- Unit tests for `ProjectIndexer`.
- Unit tests for `CodeWorkspace` path safety.
- Tests for exact-match and ambiguous-match rejection.
- Tests for multi-file rollback behavior.
- Tests for Git sensitive-path protection.
- Tests for project validation output.
- Tests for music command routing and Gemini fallback behavior.

### 9. Add Better Diagnostics - Complete

- Add a startup log file that does not include secrets.
- Show AI provider and model status in Settings.
- Show microphone device and availability status.
- Show a clear error when the API key is missing or invalid.
- Avoid silently returning a generic greeting when the AI provider fails.

## Phase 2 Recommended Starting Task

The recommended Phase 2 starting task has been completed. The historical details below are retained for traceability.

Start with **Python AST symbol inspection**.

Suggested first user request tomorrow:

> Add AST-based code inspection so NIA can list Python classes, functions, imports, and line numbers before proposing edits.

Recommended files:

- Create `nia_agent/ast_indexer.py`
- Update `nia_agent/agent_orchestrator.py`
- Add `inspect_code_symbols` tool
- Add focused tests
- Run `python -m py_compile`
- Run `validate_project`
- Review with `review_git_changes`
- Commit only after approval
- Push only after a separate approval

## Phase 3 Preview

Phase 3 is now in progress after the Phase 2 changes were reviewed, committed, and pushed.

Phase 3 should begin only after Phase 2 has tests and stable validation.

### Telephony and Live Calls

- Twilio Voice or SIP integration
- Hindi/Hinglish live speech handling
- Call consent and privacy controls
- Call summaries and WhatsApp follow-ups
- Credential storage outside source control

### Self-Healing Diagnostics

- Read application logs and terminal output
- Detect Python tracebacks and common runtime failures
- Link errors to source files and symbols
- Generate a previewed fix
- Validate the fix
- Require approval before applying or committing

### Phase 3 Recommended Starting Task

Start with read-only runtime error collection: capture application logs and terminal output, detect Python tracebacks, and return the related file and line before proposing any fix.

Progress: bounded, read-only Python traceback extraction is implemented in `SystemDiagnostics.analyze_log_file()`, restricted to the diagnostics directory through `analyze_runtime_log()`, and exposed through the orchestrator. `collect_runtime_logs()` scans supported `.log` and `.txt` files with a file-count cap and returns structured failures only. `analyze_runtime_output()` classifies captured terminal text for tracebacks, missing dependencies, and timeouts without executing commands. `PythonASTIndexer.resolve_location()` and the `link_runtime_failure` tool connect a failure line to its nearest Python symbol. `CodeWorkspace.preview_runtime_fix()` and the `preview_runtime_fix` tool generate validated diffs with failure context and an explicit approval gate; they never write or commit changes. `validate_proposed_change()` and `validate_runtime_fix` compile proposed Python content in memory before any apply step. `apply_runtime_fix` requires explicit confirmation, applies through the existing backup/rollback writer, and runs project validation afterward. `review_runtime_fix` performs a read-only branch/staged/unstaged Git review after validation. `commit_runtime_fix` creates a local commit only after a separate explicit approval; push remains a separate approval. Focused regression tests cover parsing, dispatch, collection, classification, symbol linking, fix previews, validation, application, Git review, commit gating, and path safety.

### Advanced Automation

- Read-only local GitHub Actions workflow inspection is implemented through `GitHubAutomation.inspect_ci_workflows()` and the `inspect_github_ci` orchestrator tool. It reports workflow names, triggers, and job IDs without contacting GitHub or changing files.
- GitHub pull request creation after approval is implemented through `GitHubAutomation.create_pull_request()` and the `create_github_pr` orchestrator tool.
- Review comments and CI status
- Scheduled workflows
- Project-specific agent profiles
- Permission and command allowlists

## Daily Start Commands

From `E:\nia phase 1.0`:

```powershell
python -m py_compile nia_agent\*.py
python -c "import sys; sys.path.insert(0, 'nia_agent'); from project_validator import ProjectValidator; print(ProjectValidator('.').validate())"
git status
git log --oneline -5
```

To start NIA:

```powershell
Start-Process wscript.exe -ArgumentList '"E:\nia phase 1.0\nia_agent\Launch_Nia.vbs"'
```

To review changes:

```powershell
python -c "import sys; sys.path.insert(0, 'nia_agent'); from git_review import GitReview; print(GitReview('.').review())"
```

## Safety Rules

- Never expose API keys in chat, logs, diffs, or commits.
- Never commit local `config.json`.
- Never push automatically after a commit.
- Always preview code changes before applying them.
- Always validate after applying code changes.
- Always review Git changes before committing.
- Keep commits focused and easy to roll back.
