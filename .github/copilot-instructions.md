# AISquare Studio AutoQA — Repository Custom Instructions

<!-- This file is automatically read by GitHub Copilot when working in this
     repository. It provides project-specific context so that Copilot and AI
     agents can work efficiently without redundant codebase exploration. -->



## Project Overview

**AISquare Studio AutoQA** is an AI-powered GitHub Action that converts natural
language test descriptions in pull request bodies into fully automated Playwright
tests. It uses CrewAI multi-agent orchestration and OpenAI GPT-4.

| Attribute        | Value                                            |
| ---------------- | ------------------------------------------------ |
| Language          | Python 3.11+                                     |
| Action type       | Composite (`action.yml`)                         |
| AI framework      | CrewAI (multi-agent)                             |
| LLM              | OpenAI GPT-4                                     |
| Browser engine    | Playwright (Chromium)                            |
| Test framework    | pytest                                           |
| License          | Apache 2.0                                       |
| Repository       | `AISquare-Studio/AISquare-Studio-QA`             |

### What it does

1. Developer writes numbered test steps in a PR description inside a fenced
   `` ```autoqa `` block with metadata (`flow_name`, `tier`, `area`).
2. The GitHub Action triggers on PR open/edit/sync.
3. AutoQA parses metadata and steps, generates Playwright Python tests via CrewAI agents.
4. Generated code is AST-validated and executed against the staging environment.
5. On pass, the test file is committed to `tests/autoqa/{tier}/{area}/test_{flow_name}.py`.
6. Results and screenshots are posted as a PR comment.

### Execution modes

| Mode             | Behavior                                                                   |
| ---------------- | -------------------------------------------------------------------------- |
| `generate`       | Parse PR, generate a new test, execute, commit on success (default)        |
| `suite`          | Run existing test suite only (regression)                                  |
| `all`            | Generate a new test **and** run the full suite                             |
| `auto-criteria`  | AI generates test criteria from PR diff for developer review               |
| `gap-driven`     | Uses memory coverage gaps to generate criteria for uncovered modules       |
| `gap-analysis`   | Scans for present/missing test workflows, persists to SQLite DB            |

---

## Repository Layout

```
AISquare-Studio-QA/
├── action.yml                     # GitHub Action composite definition (entry point for consumers)
├── qa_runner.py                   # Local test runner CLI entry point
├── requirements.txt               # Python runtime dependencies
├── pyproject.toml                 # Python project config (black, isort, pytest)
├── pytest.ini                     # Pytest config (markers, paths)
├── env.template                   # Environment variables template
├── .flake8                        # Flake8 linting config
│
├── config/
│   ├── autoqa_config.yaml         # Master AutoQA policy (tiers, quotas, execution, security)
│   └── test_data.yaml             # Test scenarios and selectors
│
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── planner_agent.py       # CrewAI agent: generates Playwright code from steps
│   │   ├── executor_agent.py      # CrewAI agent: validates (AST) and executes code
│   │   └── step_executor_agent.py # Active execution: one step at a time with live browser
│   ├── autoqa/
│   │   ├── action_runner.py       # Main GitHub Action orchestrator (reads env vars, drives flow)
│   │   ├── parser.py              # PR body parser: extracts autoqa block, metadata, steps
│   │   ├── action_reporter.py     # Generates PR comment with results/screenshots
│   │   ├── cross_repo_manager.py  # Commits generated test files across repos
│   │   ├── criteria_generator.py  # Proposal 16: auto-generates test criteria from PR diffs
│   │   ├── dashboard_results.py   # Produces dashboard JSON schema output
│   │   ├── gap_analysis_db.py     # SQLite-backed gap analysis persistence
│   │   ├── gap_driven_generator.py# Gap-driven test criteria generation
│   │   ├── memory_tracker.py      # Tracks test status and coverage over time
│   │   └── testid_scanner.py      # Scans for data-testid attributes
│   ├── crews/
│   │   └── qa_crew.py             # CrewAI agent orchestration / crew definition
│   ├── execution/
│   │   ├── iterative_orchestrator.py  # Step-by-step execution coordinator
│   │   ├── execution_context.py       # State tracking between execution steps
│   │   └── retry_handler.py           # Failure analysis and retry logic
│   ├── tools/
│   │   ├── playwright_executor.py     # Playwright test code execution engine
│   │   └── dom_inspector.py           # Live page selector discovery (DOMInspectorTool)
│   ├── templates/
│   │   └── test_execution_template.py # Runtime template injected into generated tests
│   └── utils/
│       ├── logger.py                  # GitHub Actions-aware structured logging
│       ├── github_comment_client.py   # GitHub API client for PR comments
│       ├── comment_builder.py         # Markdown PR comment builder
│       ├── screenshot_handler.py      # Screenshot capture utility
│       └── screenshot_embed_manager.py# Screenshot embedding in comments
│
├── tests/
│   ├── conftest.py                # Shared pytest fixtures
│   ├── test_memory_tracker.py     # Memory tracker unit tests
│   ├── test_criteria_generator.py # Criteria generator unit tests (51 tests)
│   ├── test_dashboard_results.py  # Dashboard output tests
│   ├── test_gap_analysis_db.py    # Gap analysis DB tests
│   ├── test_gap_driven_generator.py # Gap-driven generator tests
│   ├── test_login.py              # Login flow integration test
│   └── test_testid_scanner.py     # Test-ID scanner tests
│
├── docs/                          # Documentation (14 files)
│   ├── ARCHITECTURE.md            # Detailed architecture walkthrough
│   ├── ACTION_USAGE.md            # Action usage guide
│   ├── ACTIVE_EXECUTION.md        # Active execution mode docs
│   ├── AUTOQA_QUICK_START.md      # Quick start guide
│   ├── AUTOQA_ENHANCEMENT_ROADMAP.md # 16-proposal enhancement roadmap
│   ├── COMPLETE_AUTOMATION_QA_OVERVIEW.md
│   ├── DASHBOARD_JSON_SCHEMA.md   # Dashboard JSON output schema
│   ├── FE_REACT_INTEGRATION.md    # Frontend integration guide
│   ├── LINTING.md                 # Linting setup docs
│   ├── OPEN_SOURCE_ROADMAP.md     # OSS readiness status
│   ├── PHASE1_IMPLEMENTATION_SUMMARY.md
│   ├── RELEASE_PROCESS.md         # Release pipeline docs
│   ├── SCREENSHOT_FIX.md          # Screenshot handling docs
│   └── SINGLE_COMMENT_FIX.md     # PR comment strategy docs
│
├── examples/
│   ├── fe-react-autoqa-workflow.yml   # Full example workflow for FE-React repos
│   ├── auto-criteria-workflow.yml     # Auto-criteria workflow example
│   ├── playwright.config.js           # Example Playwright config
│   ├── EXAMPLE_PR_DESCRIPTION.md      # Example PR body with autoqa block
│   └── PR_TEMPLATE_WITH_AUTOQA.md     # PR template with autoqa section
│
├── reports/                       # Generated artifacts (gitignored contents)
│   ├── html/                      # HTML test reports
│   ├── json/                      # JSON test reports
│   └── screenshots/               # Failure screenshots
│
├── scripts/                       # Utility scripts
│
├── .github/
│   ├── copilot-instructions.md    # ← This file (Copilot custom instructions)
│   └── workflows/
│       ├── lint.yml               # Auto-fix linting on PRs (black, isort, flake8)
│       ├── test-action.yml        # Tests: parser, memory tracker, self-test, action.yml validation
│       └── release.yml            # Release pipeline: validate → lint → test → GitHub Release
│
├── CHANGELOG.md                   # Keep-a-Changelog format
├── README.md                      # Project documentation
├── CONTRIBUTING.md                # Contribution guidelines
├── CODE_OF_CONDUCT.md             # Contributor Covenant
├── SECURITY.md                    # Security policy
├── SUPPORT.md                     # Support channels
├── LICENSE                        # Apache 2.0
└── VALIDATION_CHECKLIST.md        # Manual validation checklist
```

---

## Architecture

### Agent System (CrewAI)

```
PR Body → AutoQAParser → PlannerAgent → ExecutorAgent → CommitResult
                              ↓                ↓
                         GPT-4 Code       AST Validate
                         Generation       + Playwright
                                          Execution
```

- **PlannerAgent** (`src/agents/planner_agent.py`): Takes parsed steps and
  generates Playwright Python test code via GPT-4.
- **ExecutorAgent** (`src/agents/executor_agent.py`): Validates generated code
  using Python AST analysis (blocks `eval`, `exec`, `subprocess`, etc.) then
  executes it in a sandboxed Playwright browser.
- **StepExecutorAgent** (`src/agents/step_executor_agent.py`): Active execution
  mode — processes one step at a time with live browser context for better
  selector discovery.

### Execution Flow (Action)

1. `action.yml` → composite action, clones this repo into `.autoqa-action/`
2. Installs Python 3.11 + pip deps + Playwright Chromium
3. Runs `src/autoqa/action_runner.py` which:
   - Reads environment variables (secrets, config)
   - Parses PR body via `AutoQAParser`
   - Checks ETag for idempotency
   - Delegates to CrewAI agents for code generation
   - Validates via AST, executes via Playwright
   - Commits test file via `CrossRepoManager`
   - Posts PR comment via `ActionReporter`
4. Uploads artifacts (screenshots, reports, dashboard JSON)

### Key Entry Points

| Use case                | Entry point                        |
| ----------------------- | ---------------------------------- |
| GitHub Action (CI)      | `src/autoqa/action_runner.py`      |
| Local CLI runner        | `qa_runner.py`                     |
| PR body parsing         | `src/autoqa/parser.py`             |
| Test execution          | `src/tools/playwright_executor.py` |
| Memory scan             | `qa_runner.py --memory-scan`       |

---

## Key Files Quick Reference

| File / Path                          | Purpose                                             |
| ------------------------------------ | --------------------------------------------------- |
| `action.yml`                         | GitHub Action definition — inputs, outputs, steps    |
| `config/autoqa_config.yaml`          | Master config — tiers, quotas, execution, security   |
| `src/autoqa/parser.py`              | PR body parser (key class: `AutoQAParser`)           |
| `src/autoqa/action_runner.py`       | Main orchestrator (reads env, drives full pipeline)  |
| `src/agents/planner_agent.py`       | Code generation agent                                |
| `src/agents/executor_agent.py`      | Code validation + execution agent                    |
| `src/execution/iterative_orchestrator.py` | Step-by-step execution coordinator             |
| `src/tools/dom_inspector.py`        | Live DOM selector discovery                          |
| `requirements.txt`                   | Runtime dependencies                                 |
| `pyproject.toml`                     | Black/isort/pytest config                            |
| `.github/workflows/test-action.yml` | CI: parser tests, memory tracker, self-test          |
| `.github/workflows/lint.yml`        | CI: auto-fix formatting on PRs                       |
| `.github/workflows/release.yml`     | CI: validate → lint → test → GitHub Release          |

---

## GitHub Actions & CI/CD

### Workflows

| Workflow            | File                | Triggers                         | Purpose                                  |
| ------------------- | ------------------- | -------------------------------- | ---------------------------------------- |
| Fix Linting Issues  | `lint.yml`          | Push to main, all PRs, manual    | Auto-formats with black/isort, runs flake8, auto-commits fixes |
| Test AutoQA Action  | `test-action.yml`   | Push to main/develop, PRs, manual | 3 parallel jobs: component tests, self-test, action.yml validation |
| Release             | `release.yml`       | Push `v*.*.*` tags               | Validate → lint → test → create GitHub Release |

### CI jobs in test-action.yml

1. **test-action-components** — Tests AutoQA parser, runs memory tracker tests, updates memory
2. **test-self-autoqa** — Self-tests the action using `uses: ./` with a sample PR body
3. **validate-action-yml** — Validates action.yml structure and required inputs

---

## Current Action Versions

All GitHub Actions used across workflows, `action.yml`, examples, and docs
**must** stay in sync. Current versions:

| Action                              | Version | Used in                                      |
| ----------------------------------- | ------- | -------------------------------------------- |
| `actions/checkout`                  | `v6`    | All workflows, action.yml, examples, docs    |
| `actions/setup-python`              | `v6`    | All workflows, action.yml                    |
| `actions/cache`                     | `v5`    | test-action.yml, action.yml                  |
| `actions/upload-artifact`           | `v7`    | action.yml, examples                         |
| `stefanzweifel/git-auto-commit-action` | `v7` | lint.yml                                     |
| `softprops/action-gh-release`       | `v2`    | release.yml                                  |

> **When bumping action versions:** Update ALL references across workflows,
> `action.yml`, `examples/`, `docs/`, and `README.md`. Use `grep` to find
> every occurrence.

---

## Configuration

### `config/autoqa_config.yaml` — key sections

| Section                 | Controls                                                  |
| ----------------------- | --------------------------------------------------------- |
| `metadata`              | Required PR fields (`flow_name`, `tier`), defaults        |
| `quotas`                | Hard caps per tier (A:40, B:40, C:20, total:100)          |
| `autoqa.execution`      | Active execution, retries, timeouts, selector priority     |
| `autoqa.auto_criteria`  | Proposal 16: auto-generated criteria from diffs            |
| `autoqa.memory`         | Memory tracking for test status and coverage gaps          |
| `autoqa.gap_analysis`   | SQLite-backed gap analysis settings                        |
| `stability`             | CI retries (2), timeouts (action: 5s, nav: 10s, test: 90s)|
| `security`              | AST validation, restricted imports, sandboxing             |
| `logging`               | Safe logging, secret redaction patterns                    |

### Selector Priority Order

When discovering selectors from live pages, AutoQA tries in this order:
`data-testid` → `data-test` → `id` → `name` → `aria-label` → `placeholder` → `type` → `class` → `text`

---

## Development Setup

```bash
# Clone
git clone https://github.com/AISquare-Studio/AISquare-Studio-QA.git
cd AISquare-Studio-QA

# Virtual environment
python -m venv venv && source venv/bin/activate

# Install runtime deps
pip install -r requirements.txt

# Install dev/linting tools
pip install flake8==7.0.0 black==24.4.2 isort==5.13.2

# Install Playwright
playwright install --with-deps chromium

# Configure environment
cp env.template .env   # Then edit .env with your secrets
```

---

## Linting & Formatting

| Tool       | Config                      | Command                                     |
| ---------- | --------------------------- | -------------------------------------------- |
| **black**  | `pyproject.toml` (line=100) | `black . --line-length=100 --preview --enable-unstable-feature=string_processing` |
| **isort**  | `pyproject.toml`            | `isort . --profile=black --line-length=100`  |
| **flake8** | `.flake8`                   | `flake8 --max-line-length=100 --extend-ignore=E203,W503,E501` |

The `lint.yml` workflow auto-commits formatting fixes on PRs. If you see the
"Linting Bot" commit after pushing, that's normal.

**Excluded from linting:** `__pycache__`, `venv`, `reports`, `test-results`,
`playwright-report`, `src/templates/test_execution_template.py`

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory_tracker.py -v --tb=short

# Run by marker
pytest -m smoke
pytest -m "not slow"
```

### pytest configuration

- **Config files:** `pytest.ini` and `pyproject.toml` (`[tool.pytest.ini_options]`)
- **Test paths:** `tests/`
- **Naming:** Files `test_*.py`, classes `Test*`, functions `test_*`
- **Options:** `-v --tb=short --disable-warnings --color=yes --durations=10 --maxfail=3`

### Markers

| Marker        | Description                            |
| ------------- | -------------------------------------- |
| `login`       | Login functionality tests              |
| `signup`      | Signup functionality tests             |
| `smoke`       | Smoke tests for basic functionality    |
| `regression`  | Full regression test suite             |
| `slow`        | Long-running tests                     |
| `integration` | Integration tests with external services |

---

## Security Model

- **AST-based validation** — Blocks dangerous constructs (`eval`, `exec`, `open`, `subprocess`, file I/O)
- **Restricted imports** — Only `playwright.sync_api`, `time`, `datetime`, `re` are permitted
- **Sandboxed execution** — Tests run in isolated Playwright browser contexts
- **Secret redaction** — Patterns: `password=`, `token=`, `Bearer `, `@example.com`
- **Secrets source** — GitHub Actions secrets only (never hardcoded)

---

## Session Checklist

**Every agent session that makes changes MUST complete these steps:**

### Before making changes

- [ ] Read this `.github/copilot-instructions.md` file
- [ ] Understand the area of code you're modifying
- [ ] Run existing tests/lint to establish a baseline

### After making changes

- [ ] **Update `CHANGELOG.md`** — Add entry under `[Unreleased]` with appropriate
      category (`Added`, `Changed`, `Fixed`, `Removed`)
- [ ] **Update `README.md`** — If the change affects usage, configuration, project
      structure, or examples, update the relevant README section
- [ ] **Update `examples/`** — If the change affects workflow syntax, action inputs,
      or versions, update example files to stay consistent
- [ ] **Update `.github/copilot-instructions.md`** — If the change affects architecture, file
      layout, versions, or conventions documented here, update this file
- [ ] **Update `docs/`** — If the change affects a topic covered by a specific
      doc file, update that doc
- [ ] Run linting: `black . --line-length=100 && isort . --profile=black --line-length=100 && flake8 .`
- [ ] Run relevant tests: `pytest tests/ -v`
- [ ] Verify action versions are consistent across all files (use `grep`)

### Version reference consistency

When changing GitHub Action versions, update **all** of these locations:

1. `.github/workflows/lint.yml`
2. `.github/workflows/test-action.yml`
3. `.github/workflows/release.yml`
4. `action.yml`
5. `examples/fe-react-autoqa-workflow.yml`
6. `examples/auto-criteria-workflow.yml`
7. `docs/ARCHITECTURE.md`
8. `docs/ACTION_USAGE.md`
9. `docs/COMPLETE_AUTOMATION_QA_OVERVIEW.md`
10. `docs/SCREENSHOT_FIX.md`
11. `README.md`

---

*Last updated: 2026-03-16 — Migrated from `INSTRUCTIONS.md` to `.github/copilot-instructions.md` per GitHub best practices.*
