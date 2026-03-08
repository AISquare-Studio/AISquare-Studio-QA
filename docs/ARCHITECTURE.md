# Architecture

This document describes the internal architecture of AISquare Studio AutoQA — how its components connect, the data that flows between them, and the design decisions behind the system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Execution Flow](#execution-flow)
3. [Component Reference](#component-reference)
4. [Active Execution Mode](#active-execution-mode)
5. [Security Model](#security-model)
6. [Cross-Repository Architecture](#cross-repository-architecture)
7. [Reporting Pipeline](#reporting-pipeline)
8. [Configuration Hierarchy](#configuration-hierarchy)
9. [Caching Strategy](#caching-strategy)
10. [Data Schemas](#data-schemas)

---

## System Overview

AutoQA is a **composite GitHub Action** (`runs.using: composite`) that converts natural-language test descriptions in PR bodies into executable Playwright tests. It is designed to run inside _any_ repository that adds the action to a workflow, while the action's own source lives in this repository.

### High-Level Diagram

```
GitHub Pull Request
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  action.yml (Composite Action)                          │
│                                                         │
│  1. Cache pip & Playwright ─── actions/cache@v3         │
│  2. Checkout AutoQA repo   ─── actions/checkout@v4      │
│  3. Setup Python 3.11      ─── actions/setup-python@v4  │
│  4. Install dependencies   ─── pip install              │
│  5. Install browsers       ─── playwright install       │
│  6. Execute main runner    ─── python action_runner.py   │
│  7. Upload artifacts       ─── actions/upload-artifact@v4│
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  ActionRunner.execute()  (src/autoqa/action_runner.py)  │
│                                                         │
│  Parse PR ──▶ Validate ──▶ Generate ──▶ Execute ──▶     │
│  Commit ──▶ Report ──▶ Set Outputs                      │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer            | Technology              | Purpose                                |
| ---------------- | ----------------------- | -------------------------------------- |
| AI Orchestration | CrewAI                  | Multi-agent coordination               |
| Language Model   | OpenAI GPT-4.1          | Natural language → Playwright code     |
| Browser Engine   | Playwright (Chromium)   | Browser automation and testing         |
| Test Framework   | Pytest                  | Test organization and reporting        |
| CI Platform      | GitHub Actions          | Execution environment                  |
| API Layer        | GitHub REST API         | PR comments, status updates            |

---

## Execution Flow

### Generate Mode (Default)

This is the primary execution path triggered when a developer opens or updates a PR with an `autoqa` block.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        ActionRunner.execute()                        │
 │                                                                      │
 │  Step 1 ─ Check for AutoQA tag                                       │
 │           AutoQAParser.has_autoqa_tag(pr_body)                        │
 │           └─ If no tag found → exit early                             │
 │                                                                      │
 │  Step 2 ─ Extract AutoQA block                                       │
 │           AutoQAParser.extract_autoqa_block(pr_body)                  │
 │           └─ Returns { metadata: {flow_name, tier, area}, steps: [] } │
 │                                                                      │
 │  Step 3 ─ Validate metadata                                          │
 │           AutoQAParser.validate_metadata(metadata)                    │
 │           └─ Checks required fields, value constraints, lengths       │
 │                                                                      │
 │  Step 4 ─ Compute ETag                                               │
 │           AutoQAParser.compute_etag(metadata, steps)                  │
 │           └─ SHA-256 of canonicalized metadata + steps                │
 │                                                                      │
 │  Step 5 ─ Generate test code                                         │
 │           ┌─ Active Mode? ───────────────────────────┐                │
 │           │  Yes: QACrew.run_active_autoqa_scenario() │                │
 │           │       └─ IterativeTestOrchestrator        │                │
 │           │  No:  QACrew.run_autoqa_scenario()        │                │
 │           │       └─ PlannerAgent + ExecutorAgent      │                │
 │           └───────────────────────────────────────────┘                │
 │                                                                      │
 │  Step 6 ─ Execute test on staging                                    │
 │           (Active mode already executed during generation)            │
 │           Legacy mode: PlaywrightExecutor.execute_code()              │
 │                                                                      │
 │  Step 7 ─ Commit test file (only if execution passed)                │
 │           CrossRepoManager.commit_test_file(code, metadata)           │
 │           └─ Creates tests/autoqa/{tier}/{area}/test_{flow_name}.py   │
 │                                                                      │
 │  Step 8 ─ Run full suite (only in "all" mode)                        │
 │           pytest tests/ via subprocess                                │
 │                                                                      │
 │  Step 9 ─ Post PR comment                                            │
 │           ActionReporter.create_pr_comment(...)                       │
 │           └─ Embeds screenshots, logs, metadata, ETag                 │
 │                                                                      │
 │  Step 10 ─ Set GitHub Action outputs                                 │
 │            Writes to $GITHUB_OUTPUT                                   │
 └──────────────────────────────────────────────────────────────────────┘
```

### Suite Mode

When `execution-mode: suite`, the runner skips generation and runs only the existing test suite:

```
ActionRunner.execute()
  └─ _run_test_suite()        ← pytest tests/
       └─ ActionReporter.create_suite_comment()
```

### All Mode

Combines both paths: generate a new test, then run the full suite including the new test.

---

## Component Reference

### Core Components

#### `ActionRunner` — `src/autoqa/action_runner.py`

The top-level orchestrator. Reads environment variables set by `action.yml`, initializes all components, and drives the 10-step execution flow described above.

| Responsibility             | Delegated To                |
| -------------------------- | --------------------------- |
| Parse PR body              | `AutoQAParser`              |
| Generate test code         | `QACrew`                    |
| Execute legacy tests       | `PlaywrightExecutor`        |
| Commit test files          | `CrossRepoManager`          |
| Post PR comments           | `ActionReporter`            |
| Set GitHub Action outputs  | Internal `_set_outputs()`   |

#### `AutoQAParser` — `src/autoqa/parser.py`

Stateless parser for PR descriptions. Extracts the fenced `autoqa` metadata block and numbered test steps.

**Key Methods:**

| Method               | Input                | Output                                            |
| -------------------- | -------------------- | ------------------------------------------------- |
| `has_autoqa_tag()`   | PR body string       | `bool` — whether the tag is present               |
| `extract_autoqa_block()` | PR body string   | `{metadata: dict, steps: list}` or `None`         |
| `validate_metadata()`| Metadata dict        | `(is_valid: bool, errors: list[str])`             |
| `compute_etag()`     | Metadata + steps     | SHA-256 hex string                                |
| `steps_to_scenario()`| Steps list + metadata| Scenario dict for CrewAI                          |

**Metadata Block Pattern:**

```
```autoqa
flow_name: user_login_success    ← required, ≤50 chars, snake_case
tier: A                          ← required, one of A/B/C
area: auth                       ← optional, ≤30 chars, defaults to "general"
```​
```

#### `QACrew` — `src/crews/qa_crew.py`

Orchestrates CrewAI agents. Initializes the LLM, agent wrappers, and the iterative orchestrator. Provides two execution paths:

1. **`run_autoqa_scenario()`** — Legacy single-shot generation using `PlannerAgent` + `ExecutorAgent`
2. **`run_active_autoqa_scenario()`** — Active execution using `IterativeTestOrchestrator`

Uses `FileReadTool` and `DirectoryReadTool` from `crewai_tools` so agents can browse the target repo's source code for stable selectors.

### Agent Layer

#### `PlannerAgent` — `src/agents/planner_agent.py`

A CrewAI `Agent` with the role "QA Test Code Planner". Given a scenario (steps + selectors), it generates a complete `run_test(page, config)` function in Playwright Python.

**System prompt rules:**
- Only Playwright imports allowed
- Must produce a `run_test(page, config)` function
- Must use provided selectors
- Must include waits and assertions
- No file I/O, no `eval`/`exec`, no network calls outside page interactions

#### `ExecutorAgent` — `src/agents/executor_agent.py`

Validates generated code via **AST (Abstract Syntax Tree) parsing** before execution. Checks for:

- Forbidden imports (only `playwright.sync_api`, `time`, `datetime`, `re` allowed)
- Forbidden function calls (`eval`, `exec`, `open`, `__import__`)
- Forbidden method calls (`system`, `popen`, `spawn`)
- Presence of `run_test` function definition

#### `StepExecutorAgent` — `src/agents/step_executor_agent.py`

Used exclusively in Active Execution Mode. Generates code for a **single step** using:

- Current page state (URL, title)
- Discovered selectors from `DOMInspectorTool`
- Accumulated code from previous steps
- Optional existing test code for context

Executes each step immediately using `exec()` with a controlled namespace containing `page`, `config`, and `TimeoutError`.

### Execution Layer

#### `IterativeTestOrchestrator` — `src/execution/iterative_orchestrator.py`

Coordinates step-by-step test execution in Active Execution Mode:

```
For each step:
  1. Capture current page state (ExecutionContext)
  2. Discover selectors (DOMInspectorTool)
  3. Generate step code (StepExecutorAgent)
  4. Execute code immediately
  5. On failure → RetryHandler analyzes and retries
  6. Record result in ExecutionContext
  7. Append code to accumulated context
```

Maintains a persistent `Crew` with memory enabled so the LLM can benefit from context across steps. Compiles all successful step code into a final test function.

#### `ExecutionContext` — `src/execution/execution_context.py`

Stateful context tracker that maintains:

- Step history (description, code, success/failure, timing, URLs)
- Discovered selectors (by element type)
- Execution metadata (counts, timestamps)
- Current page state (URL, title)

Provides `get_context_for_agent()` to give the StepExecutorAgent a comprehensive view of the current test state.

#### `RetryHandler` — `src/execution/retry_handler.py`

Analyzes failures and generates modified retry code. Strategies include:

| Error Type      | Analysis                              | Retry Strategy                        |
| --------------- | ------------------------------------- | ------------------------------------- |
| Timeout         | Selector mismatch or slow page        | Alternative selectors, increased wait |
| Selector error  | Element not found                     | DOMInspector re-scan, alt selectors   |
| Assertion error | Condition not met                     | Review code syntax                    |
| Generic         | Code execution error                  | Add waits, review attributes          |

Maximum 2 retries per step (configurable).

### Tool Layer

#### `PlaywrightExecutor` — `src/tools/playwright_executor.py`

Executes generated test code in a Playwright browser:

1. Launches headless Chromium browser
2. Creates a controlled `exec()` namespace with `page`, `config`, and `safe_assert`
3. Calls the generated `run_test(page, config)` function
4. Captures screenshots on success, assertion failure, and error
5. Returns JSON results

#### `DOMInspectorTool` — `src/tools/dom_inspector.py`

Inspects live pages to discover interactive elements and rank selectors by stability:

| Priority | Selector Type   | Score |
| -------- | --------------- | ----- |
| 1        | `data-testid`   | 100   |
| 2        | `data-test`     | 95    |
| 3        | `id`            | 90    |
| 4        | `name`          | 80    |
| 5        | `aria-label`    | 70    |
| 6        | `placeholder`   | 60    |
| 7        | `type`          | 50    |
| 8        | `class`         | 40    |
| 9        | `tag`           | 30    |
| 10       | `text`          | 20    |

Discovers buttons, inputs, links, forms, and containers by evaluating JavaScript on the live page.

### Utility Layer

#### `ActionReporter` — `src/autoqa/action_reporter.py`

Orchestrates PR comment generation using three sub-components:

- **`CommentBuilder`** — Constructs markdown content
- **`ScreenshotEmbedManager`** — Embeds or links screenshots (inline if <100KB, artifact link otherwise)
- **`GitHubCommentClient`** — Posts/updates comments via GitHub API using a hidden marker (`<!-- AutoQA-Comment-Marker -->`) to find and update existing comments

#### `CrossRepoManager` — `src/autoqa/cross_repo_manager.py`

Handles committing generated test files to the **target** repository (not the action repository):

- Creates directory structure: `tests/autoqa/{tier}/{area}/`
- Generates `__init__.py` files for Python package discovery
- Adds `AutoQA-Generated` header with metadata, ETag, and step list
- Commits with descriptive message: `AutoQA: Add {flow_name} test [{tier}/{area}] (N steps)`
- Supports direct push or PR creation via `create-pr` input

#### `Logger` — `src/utils/logger.py`

Custom logging with:

- Emoji-enhanced formatting for readability
- GitHub Actions annotations (`::error::`, `::warning::`, `::notice::`)
- Log groups for collapsible output sections
- Optional file logging

---

## Active Execution Mode

Active Execution is the default and recommended mode. Instead of generating the entire test in one shot, it processes each step iteratively with feedback from the live browser.

### Why Active Execution?

| Single-Shot Generation         | Active Execution                        |
| ------------------------------ | --------------------------------------- |
| Generates all code at once     | Generates one step at a time            |
| No feedback from browser       | Uses live page state for each step      |
| Selectors guessed from prompt  | Selectors discovered from live DOM      |
| Failures require full re-gen   | Failures retried with alternatives      |
| No context between steps       | Full context accumulates across steps   |

### Step-by-Step Flow

```
┌─────────────┐     ┌────────────────┐     ┌──────────────────┐
│  Orchestrator│────▶│  StepExecutor  │────▶│  Playwright Page │
│              │     │  Agent (LLM)   │     │                  │
│  For each    │◀────│                │◀────│  Live Browser    │
│  step...     │     └────────────────┘     └──────────────────┘
│              │            │                       │
│              │     ┌──────▼──────┐        ┌───────▼─────────┐
│              │     │ DOMInspector │        │ ExecutionContext │
│              │     │ (selectors)  │        │ (state tracking) │
│              │     └─────────────┘        └─────────────────┘
│              │
│  On failure: │     ┌──────────────┐
│              │────▶│ RetryHandler  │
│              │◀────│ (analysis +   │
│              │     │  retry code)  │
└─────────────┘     └──────────────┘
```

1. **Orchestrator** launches Chromium and navigates to the staging URL
2. For each step, it captures the current page state via `ExecutionContext.capture_state()`
3. `DOMInspectorTool` scans the live page for interactive elements
4. `StepExecutorAgent` receives the step description, page state, discovered selectors, and all previously generated code
5. The LLM generates code for this single step (1–5 lines)
6. Code is executed immediately via `exec()` in a shared namespace (variables persist across steps)
7. On success, the code is added to the accumulated context
8. On failure, `RetryHandler` analyzes the error, discovers alternative selectors, and generates modified code
9. After all steps, the accumulated code is compiled into a final `run_test(page, config)` function

### Shared Execution Namespace

Steps share a single Python namespace (`execution_globals`) containing:

- `page` — Playwright page object
- `config` — Test configuration dict
- `TimeoutError` — Playwright timeout exception

Variables defined in one step (e.g., a timestamp string) are available in subsequent steps. This enables multi-step flows like filling a form across multiple steps.

---

## Security Model

### Code Validation Pipeline

```
Generated Code
      │
      ▼
┌──────────────────────────────────┐
│  AST Parsing (ast.parse)         │
│                                  │
│  Check 1: Import validation      │
│    ✓ playwright.sync_api         │
│    ✓ time, datetime, re          │
│    ✗ os, subprocess, sys, etc.   │
│                                  │
│  Check 2: Function call scan     │
│    ✗ eval, exec, open            │
│    ✗ __import__                   │
│    ✗ system, popen, spawn        │
│                                  │
│  Check 3: Function structure     │
│    ✓ Must define run_test()      │
│                                  │
│  Result: (is_safe, message)      │
└──────────────────────────────────┘
      │
      ▼
 Execute only if safe
```

### Log Redaction

Configured in `config/autoqa_config.yaml`:

```yaml
logging:
  safe_logging: true
  redact_patterns:
    - "password="
    - "token="
    - "Bearer "
    - "@example.com"
```

### Sandbox Boundaries

- Tests run in isolated Chromium browser contexts
- No filesystem access from generated code
- No network access beyond Playwright page interactions
- Generated code cannot import arbitrary modules

---

## Cross-Repository Architecture

AutoQA is designed to be consumed as a GitHub Action by other repositories. Here is how the repositories interact:

```
┌─────────────────────────────────────────────────┐
│  Target Repository (e.g., FE-REACT)             │
│                                                 │
│  .github/workflows/autoqa.yml                   │
│    └─ uses: AISquare-Studio/AISquare-Studio-QA  │
│                                                 │
│  tests/autoqa/                                  │
│    ├── A/auth/test_login.py    ← committed      │
│    ├── B/billing/test_pay.py   ← by AutoQA      │
│    └── ...                                      │
└─────────────────────────────────────────────────┘
                     │
                     │ Checked out to .autoqa-action/
                     ▼
┌─────────────────────────────────────────────────┐
│  AISquare-Studio-QA (This Repository)           │
│                                                 │
│  action.yml        ← Action definition          │
│  src/              ← All Python logic            │
│  config/           ← Policy and settings         │
│  requirements.txt  ← Dependencies                │
└─────────────────────────────────────────────────┘
```

During action execution:

1. `action.yml` checks out **this repository** into `.autoqa-action/` in the target workspace
2. Python runs inside `.autoqa-action/` but operates on files in the target workspace
3. `CrossRepoManager` creates test files in the **target** repository and commits them
4. `ActionReporter` posts comments on the **target** repository's PR

### Path Resolution

| Path                              | Description                              |
| --------------------------------- | ---------------------------------------- |
| `$GITHUB_WORKSPACE`              | Target repository root                   |
| `$GITHUB_WORKSPACE/.autoqa-action` | AutoQA action repository checkout      |
| `$ACTION_PATH`                    | Same as above — set by action.yml        |
| `$TARGET_REPO_PATH`              | Relative path within workspace (usually `.`) |

---

## Reporting Pipeline

```
ActionReporter
    ├── ScreenshotHandler
    │     └── Captures screenshots (success/failure/error)
    │
    ├── ScreenshotEmbedManager
    │     ├── Inline base64 if file < 100 KB
    │     └── Artifact link if larger
    │
    ├── CommentBuilder
    │     └── Constructs full markdown comment with:
    │           - Generation result header (✅/❌)
    │           - Metadata (flow_name, tier, area, ETag)
    │           - Generated code block
    │           - Execution logs
    │           - Screenshot sections
    │           - Artifact links
    │
    └── GitHubCommentClient
          ├── Searches for existing comment by marker
          │     <!-- AutoQA-Comment-Marker -->
          ├── Updates existing comment (PATCH)
          └── Creates new comment (POST)
```

Comments are **idempotent**: the same PR always shows a single AutoQA comment that gets updated on each re-run.

---

## Configuration Hierarchy

Configuration values are resolved in this order (highest priority first):

1. **Environment variables** set by `action.yml` from workflow inputs
2. **`config/autoqa_config.yaml`** — policy defaults and execution settings
3. **Hardcoded defaults** in source code

### Key Configuration File: `config/autoqa_config.yaml`

| Section              | Purpose                                        |
| -------------------- | ---------------------------------------------- |
| `metadata`           | Required/optional fields, validation rules     |
| `quotas`             | Per-tier test count limits (A:40, B:40, C:20)  |
| `naming`             | File path and class/function naming patterns   |
| `stability`          | Retry counts, wait times, timeouts             |
| `security`           | AST validation, import restrictions            |
| `logging`            | Redaction patterns, safe logging               |
| `autoqa.execution`   | Active execution settings, selector priority   |
| `cross_repo`         | Target repository settings, commit config      |

---

## Caching Strategy

The action uses three cache layers to avoid redundant work:

```
┌─────────────────────────────────────────┐
│  Layer 1: AutoQA Repository             │
│  Key: runner-autoqa-repo-{sha}-v1       │
│  Path: .autoqa-action/                  │
│  Saves: ~30s clone time                 │
├─────────────────────────────────────────┤
│  Layer 2: Python pip packages           │
│  Key: hash of requirements.txt          │
│  Path: ~/.cache/pip                     │
│  Saves: ~60s install time               │
├─────────────────────────────────────────┤
│  Layer 3: Playwright browsers           │
│  Key: runner-autoqa-playwright-{hash}   │
│  Path: ~/.cache/ms-playwright           │
│  Saves: ~120s download time (~100 MB)   │
└─────────────────────────────────────────┘
```

Cache keys include version suffixes (`-v1`, `-v2`) that can be bumped to force invalidation.

---

## Data Schemas

### AutoQA Block (PR Body)

```
{
  "metadata": {
    "flow_name": "user_login_success",   // string, ≤50 chars, snake_case
    "tier": "A",                          // "A" | "B" | "C"
    "area": "auth"                        // string, ≤30 chars, default "general"
  },
  "steps": [
    "Navigate to the login page",
    "Enter valid email address",
    "Enter valid password",
    "Click the login button",
    "Verify the dashboard appears"
  ]
}
```

### ETag

```
SHA-256(JSON.stringify({
  flow_name: "user_login_success",
  tier: "A",
  area: "auth",
  steps: [
    "navigate to the login page",    // canonicalized: lowercase, collapsed whitespace
    "enter valid email address",
    ...
  ]
}, sort_keys=True))
```

### Execution Result

```
{
  "success": true,
  "generated_code": "def run_test(page, config): ...",
  "total_steps": 5,
  "completed_steps": 5,
  "successful_steps": 5,
  "failed_steps": 0,
  "total_execution_time": 12.34,
  "final_screenshot": "reports/screenshots/final_state_1234.png",
  "retry_summary": {
    "total_retries": 1,
    "steps_retried": 1,
    "retry_details": { "3": 1 }
  },
  "discovered_selectors": {
    "buttons": [...],
    "inputs": [...]
  }
}
```

### Generated Test File Header

```python
"""
# AutoQA-Generated
# Generated: 2025-01-15T10:30:00+00:00
# Flow: user_login_success
# Tier: A
# Area: auth
# ETag: abc123def456...

Test Steps:
1. Navigate to the login page
2. Enter valid email address
3. Enter valid password
4. Click the login button
5. Verify the dashboard appears

This test was automatically generated by AISquare Studio AutoQA.
"""
```

### Test File Structure

```python
class TestUserLoginSuccess:
    @pytest.mark.autoqa
    @pytest.mark.tier_a
    @pytest.mark.area_auth
    def test_user_login_success(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                # Generated test code (run_test function)
                ...
                run_test(page, config)
            finally:
                browser.close()
```
