# AutoQA — Detailed Usage Guide

> **Version:** 0.1.0 · **License:** Apache 2.0 · **Python:** 3.11+

AutoQA is an AI-powered GitHub Action that converts natural language test descriptions in pull request bodies into fully automated Playwright tests. It uses CrewAI multi-agent orchestration with OpenAI GPT-4 to generate, validate, execute, and commit production-ready test code.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [PR Body Format](#3-pr-body-format)
4. [Execution Modes](#4-execution-modes)
5. [GitHub Action Reference](#5-github-action-reference)
6. [Local CLI Usage](#6-local-cli-usage)
7. [Configuration](#7-configuration)
8. [Architecture](#8-architecture)
9. [Active Execution Mode](#9-active-execution-mode)
10. [Auto-Criteria Generation](#10-auto-criteria-generation)
11. [Memory Tracking](#11-memory-tracking)
12. [Gap-Driven Test Generation](#12-gap-driven-test-generation)
13. [Gap Analysis Database](#13-gap-analysis-database)
14. [Test Organization and File Structure](#14-test-organization-and-file-structure)
15. [Security Model](#15-security-model)
16. [Reporting](#16-reporting)
17. [Caching and Performance](#17-caching-and-performance)
18. [Environment Variables](#18-environment-variables)
19. [Troubleshooting](#19-troubleshooting)
20. [FAQ](#20-faq)

---

## 1. Overview

AutoQA bridges the gap between manual test descriptions and automated test code. Developers write numbered test steps in plain English inside a PR description, and AutoQA handles the rest:

```
PR Description          AutoQA Action              Your Repository
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  ```autoqa   │     │ 1. Parse PR body │     │ tests/autoqa/    │
│  flow: login │────▶│ 2. Generate code │────▶│   A/auth/        │
│  tier: A     │     │ 3. Validate AST  │     │     test_login.py│
│  area: auth  │     │ 4. Execute tests │     └──────────────────┘
│  ```         │     │ 5. Commit on pass│
│              │     │ 6. Comment on PR │
│  1. Go to /  │     └──────────────────┘
│  2. Login    │
│  3. Verify   │
└──────────────┘
```

### Key Capabilities

| Capability | Description |
|---|---|
| **AI-Powered Test Generation** | Natural language steps become executable Playwright Python tests |
| **Active Execution Mode** | Iterative step-by-step generation with real-time browser context |
| **Smart Selector Discovery** | Auto-discovers optimal selectors from live pages via DOMInspectorTool |
| **Intelligent Retry** | Automatic error recovery with alternative selectors and failure analysis |
| **AST-Based Security** | Prevents unsafe code patterns before execution |
| **Cross-Repository Architecture** | Deploys as a GitHub Action, runs in any repository |
| **Comprehensive Reporting** | PR comments with screenshots, HTML reports, and JSON artifacts |
| **ETag-Based Idempotency** | Prevents duplicate test generation for unchanged PR descriptions |
| **Multi-Tier Organization** | Categorize tests into A/B/C tiers by criticality |
| **Auto-Criteria Generation** | Analyzes PR diffs to suggest test criteria automatically |
| **Memory Tracking** | Persistent tracking of test status and coverage gaps |
| **Gap-Driven Generation** | Generates tests for uncovered source modules |
| **Gap Analysis Database** | SQLite-backed scanning and persistence of test coverage |

---

## 2. Quick Start

### Step 1 — Add the workflow file

Create `.github/workflows/autoqa.yml` in your repository:

```yaml
name: AutoQA Test Generation

on:
  pull_request:
    types: [opened, synchronize, edited]

jobs:
  autoqa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate and Execute Tests
        uses: AISquare-Studio/AISquare-Studio-QA@main
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          staging-url: ${{ secrets.STAGING_URL }}
          staging-email: ${{ secrets.STAGING_EMAIL }}
          staging-password: ${{ secrets.STAGING_PASSWORD }}
```

### Step 2 — Configure secrets

In your repository go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key with GPT-4 access |
| `STAGING_URL` | Staging environment login URL |
| `STAGING_EMAIL` | Test account email |
| `STAGING_PASSWORD` | Test account password |

If the AutoQA repository is private, also add `QA_GITHUB_TOKEN` — a Personal Access Token with `repo` scope.

### Step 3 — Write test steps in a PR

Include a fenced `autoqa` block in the pull request description:

````markdown
```autoqa
flow_name: user_login_success
tier: A
area: auth
```

1. Navigate to the login page
2. Enter valid email address
3. Enter valid password
4. Click the login button
5. Verify the dashboard appears
````

Open the PR and AutoQA takes care of the rest — generating, validating, executing, and committing the test file.

---

## 3. PR Body Format

The PR description must contain a fenced `autoqa` code block followed by numbered test steps.

### Metadata Block

````markdown
```autoqa
flow_name: <snake_case_test_name>
tier: <A|B|C>
area: <feature_area>
```
````

| Field | Required | Constraints | Default | Description |
|---|---|---|---|---|
| `flow_name` | **Yes** | snake_case, max 50 chars | — | Unique identifier used as the generated file name |
| `tier` | **Yes** | `A`, `B`, or `C` | `B` | Criticality tier |
| `area` | No | snake_case, max 30 chars | `general` | Feature area used as subdirectory |

### Tier Definitions

| Tier | Name | Description | Quota |
|---|---|---|---|
| **A** | Critical | Core functionality that breaks the app if it fails (login, signup, payments) | 40 tests |
| **B** | Important | Major features and common user flows (forms, navigation, CRUD) | 40 tests |
| **C** | Nice-to-have | Edge cases, tooltips, animations | 20 tests |

Total quota: **100 curated tests per repository**.

### Test Steps

Steps are written as a numbered list below the metadata block. Each step describes one action or assertion in plain English.

````markdown
```autoqa
flow_name: contact_form_validation
tier: B
area: forms
```

1. Navigate to contact form at "/contact"
2. Click submit button without filling any fields
3. Verify error message "Email is required" appears
4. Enter invalid email "notanemail"
5. Verify error message "Please enter a valid email" appears
6. Enter valid email "user@example.com"
7. Verify error message disappears
````

### Writing Effective Steps

| Practice | Good ✅ | Bad ❌ |
|---|---|---|
| Be specific | `Navigate to login page at "/login"` | `Go to the login screen` |
| Use quotes for UI text | `Verify error "Email is required" appears` | `Verify error message appears` |
| Include verifications | `Click "Submit"` then `Verify success message appears` | `Click "Submit"` (no verification) |
| One action per step | Two separate steps for email and password | `Enter email and password` |

### ETag-Based Idempotency

AutoQA computes an **ETag** (SHA-256 hash) from `flow_name`, `tier`, `area`, and the canonical test steps. If the same combination is seen again, regeneration is skipped. Changing any metadata field or step text produces a new ETag and triggers regeneration.

---

## 4. Execution Modes

AutoQA supports six execution modes, configured via the `execution-mode` input.

| Mode | Description |
|---|---|
| `generate` | **(Default)** Parse PR body, generate a new test, validate via AST, execute against staging, and commit on success |
| `suite` | Run the existing test suite only (regression testing) |
| `all` | Generate a new test **and** run the full existing suite |
| `auto-criteria` | Analyze the PR code diff and generate test criteria for developer review (see [§10](#10-auto-criteria-generation)) |
| `gap-driven` | Use memory coverage gaps to generate test criteria for uncovered modules (see [§12](#12-gap-driven-test-generation)) |
| `gap-analysis` | Scan for present/missing test workflows and persist to SQLite database (see [§13](#13-gap-analysis-database)) |

### Example: Running in `suite` mode

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@main
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    staging-url: ${{ secrets.STAGING_URL }}
    execution-mode: suite
```

### Example: Running in `auto-criteria` mode

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@main
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    staging-url: ${{ secrets.STAGING_URL }}
    execution-mode: auto-criteria
    auto-criteria-mode: suggest        # or "auto"
    auto-criteria-threshold: '85'
    auto-criteria-approval: reaction   # or "comment" or "label"
```

---

## 5. GitHub Action Reference

### Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `openai-api-key` | **Yes** | — | OpenAI API key for test generation |
| `staging-url` | **Yes** | — | Staging environment URL |
| `qa-github-token` | No | `github.token` | GitHub token (needed for private repos) |
| `staging-email` | No | `test@example.com` | Test account email |
| `staging-password` | No | `password123` | Test account password |
| `target-repo-path` | No | `.` | Path to the target repository |
| `git-user-name` | No | `AutoQA Bot` | Git user name for commits |
| `git-user-email` | No | `rabia.tahirr@opengrowth.com` | Git user email for commits |
| `pr-body` | No | *(auto-detected from PR event)* | PR description text |
| `test-directory` | No | `tests/autoqa` | Base directory for generated tests |
| `create-pr` | No | `false` | Create a PR for tests instead of pushing directly |
| `execution-mode` | No | `generate` | `generate`, `suite`, `all`, `auto-criteria`, `gap-driven`, or `gap-analysis` |
| `action-ref` | No | *(derived from invocation)* | Git ref (branch/tag/SHA) for AutoQA action repository |
| `auto-criteria-fallback` | No | `false` | If no autoqa block found, auto-generate criteria from PR diff |
| `auto-criteria-mode` | No | `suggest` | `suggest` (post for review) or `auto` (proceed if high confidence) |
| `auto-criteria-threshold` | No | `85` | Confidence score threshold (0–100) for auto-proceed |
| `auto-criteria-approval` | No | `reaction` | Approval mechanism: `reaction` (👍), `comment` (`/autoqa approve`), or `label` (`autoqa:approved`) |

### Outputs

| Output | Description |
|---|---|
| `test_generated` | Whether a test was generated (`true`/`false`) |
| `test_file_path` | Path to the generated test file |
| `test_results` | JSON string of execution results |
| `generation_metadata` | JSON with `flow_name`, `tier`, `area`, `etag`, `steps` |
| `screenshot_path` | Path to captured screenshots |
| `etag` | SHA-256 idempotency hash |
| `flow_name` | Parsed flow name |
| `tier` | Parsed tier (`A`, `B`, or `C`) |
| `area` | Parsed area |
| `error` | Error message if failed |
| `auto_criteria_results` | JSON of auto-criteria results (auto-criteria mode) |
| `criteria` | JSON of generated test criteria before approval |
| `gap_analysis_results` | JSON of gap analysis results with present/missing workflows |

### Artifacts

The action automatically uploads:

| Artifact | Content | Retention |
|---|---|---|
| `autoqa-screenshots-{run_number}` | Screenshot PNG files from test execution | 30 days |
| `autoqa-reports-{run_number}` | HTML reports, JSON reports, generated test files | 30 days |

---

## 6. Local CLI Usage

The `qa_runner.py` script provides a local entry point for running tests and managing AutoQA features.

### Prerequisites

```bash
# Python 3.11+
pip install -r requirements.txt
playwright install --with-deps chromium
```

### Environment Setup

```bash
cp env.template .env
# Edit .env with your configuration
```

The `.env` file supports the following variables:

```bash
# Staging environment
STAGING_LOGIN_URL=https://stg-home.aisquare.studio/login
STAGING_URL=https://stg-home.aisquare.studio
STAGING_EMAIL=test@example.com
STAGING_PASSWORD=your_test_password

# Alternative credentials for negative tests
INVALID_EMAIL=invalid@example.com
INVALID_PASSWORD=wrongpassword123

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Browser settings
HEADLESS_MODE=true          # false to see browser during tests
BROWSER_TYPE=chromium       # chromium, firefox, or webkit
DEFAULT_TIMEOUT=30000       # Page operation timeout (ms)

# Screenshots
CAPTURE_SCREENSHOTS=true
SCREENSHOT_ON_FAILURE=true
```

### Commands

| Command | Description |
|---|---|
| `python qa_runner.py` | Run all tests against the staging environment |
| `python qa_runner.py --memory-scan` | Scan tests and source files to identify coverage gaps (no test execution) |
| `python qa_runner.py --memory-update` | Run tests and update the memory tracker with results |
| `python qa_runner.py --memory-report` | Print a markdown coverage report from current memory |
| `python qa_runner.py --gap-driven` | Generate test criteria for uncovered source modules |
| `python qa_runner.py --gap-analysis` | Run gap analysis and persist results to SQLite database |
| `python qa_runner.py --help-detailed` | Show comprehensive documentation |

### Examples

```bash
# Run tests with visible browser for debugging
HEADLESS_MODE=false python qa_runner.py

# Scan for coverage gaps, then generate criteria
python qa_runner.py --memory-scan
python qa_runner.py --gap-driven

# Full cycle: run tests, update memory, view report
python qa_runner.py --memory-update
python qa_runner.py --memory-report

# Persist gap analysis to database
python qa_runner.py --gap-analysis
```

### Running the Test Suite Directly

```bash
pytest tests/ -v
```

Reports are generated in `reports/html/` (HTML) and `reports/json/` (JSON) with timestamped filenames.

---

## 7. Configuration

AutoQA is configured through three layers: the GitHub Action inputs (`action.yml`), the central configuration file (`config/autoqa_config.yaml`), and environment variables.

### `config/autoqa_config.yaml`

This file controls policies, quotas, execution settings, and feature toggles.

#### Metadata

```yaml
metadata:
  required: ["flow_name", "tier"]
  optional: ["area"]
  tier_values: ["A", "B", "C"]
  defaults:
    tier: "B"
    area: "general"
  validation:
    flow_name_max_length: 50
    area_max_length: 30
    min_steps: 1
```

#### Quotas

```yaml
quotas:
  total_curated: 100
  per_tier:
    A: 40
    B: 40
    C: 20
```

#### Versioning and Branching

```yaml
versioning:
  branch_pattern: "autoqa/{source_pr}-{flow_name}"
  etag:
    algo: "sha256"
    no_op_on_match: true
```

#### Edit Policy

```yaml
edit_policy:
  allow_auto_edit_only_if_header: true   # File must have "AutoQA-Generated" header
  version_bump_creates_v2: true          # Major UI changes create _v2.py
  human_paths_protected:
    - "tests/**/human/**"
```

#### Active Execution Settings

```yaml
autoqa:
  execution:
    use_active_execution: true
    active_execution:
      max_retries_per_step: 2
      step_timeout_ms: 30000
      slow_mo_ms: 500
      selector_priority:
        - "data-testid"
        - "data-test"
        - "id"
        - "name"
        - "aria-label"
        - "placeholder"
        - "type"
        - "class"
        - "text"
      failure_mode: "stop_on_error"   # stop_on_error | continue_on_error | partial_commit
```

#### Auto-Criteria

```yaml
autoqa:
  auto_criteria:
    enabled: true
    mode: "suggest"                    # "suggest" or "auto"
    auto_proceed_threshold: 85
    max_flows_per_pr: 5
    max_diff_length: 12000
    approval_mechanism: "reaction"     # "reaction" | "comment" | "label"
    tier_inference:
      critical_paths: ["auth", "payment", "checkout", "signup", "login"]
      important_paths: ["dashboard", "settings", "profile", "search", "account"]
```

#### Memory Tracking

```yaml
autoqa:
  memory:
    enabled: true
    memory_file: "reports/autoqa_memory.json"
    test_dir: "tests"
    source_dirs: ["src"]
    history_limit: 10
```

#### Gap-Driven Generation

```yaml
autoqa:
  gap_driven:
    enabled: true
    max_modules_per_run: 10
    max_source_length: 8000
    max_criteria_per_module: 3
    mode: "suggest"
    auto_proceed_threshold: 85
    approval_mechanism: "reaction"
```

#### Gap Analysis

```yaml
autoqa:
  gap_analysis:
    enabled: true
    db_path: "reports/gap_analysis.db"
    test_dir: "tests"
    source_dirs: ["src"]
```

#### Stability and Retries

```yaml
stability:
  retries_ci: 2
  waits:
    action_ms: 5000
    navigation_ms: 10000
    test_timeout_ms: 90000
  screenshots_on: "failures"
```

#### Security

```yaml
security:
  secrets_source: "github_actions_secrets"
  ast_validation: true
  restricted_imports: true
  sandbox_execution: true
  mask_secrets_in_logs: true
```

#### Labels

```yaml
labels:
  allow_edit: "autoqa:allow-edit"
  retire: "autoqa:retire"
  frozen: "autoqa:frozen"
```

### `config/test_data.yaml`

Defines reusable test scenarios and selector mappings:

```yaml
test_scenarios:
  login:
    valid_login:
      name: "Valid Login Test"
      steps:
        - "Navigate to the login page"
        - "Enter valid email address"
        - "Enter valid password"
        - "Click login button"
        - "Verify successful login"
      expected_result: "User should be logged in successfully"

selectors:
  login_page:
    email_input: "input[name='email'], input[type='email'], #email"
    password_input: "input[type='password'], input[name='password'], #password"
    login_button: "button[type='submit'], button:has-text('Login'), button:has-text('Sign In')"
    error_message: "#errorMessage, .error, .alert-danger, [data-testid='error']"
```

---

## 8. Architecture

AutoQA uses a multi-agent architecture powered by [CrewAI](https://www.crewai.com/).

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Action (action.yml)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  action_runner.py — Main orchestrator                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │   │
│  │  │ parser.py│  │qa_crew.py│  │ cross_repo_manager.py │  │   │
│  │  └────┬─────┘  └────┬─────┘  └───────────┬───────────┘  │   │
│  │       │              │                    │              │   │
│  │       ▼              ▼                    ▼              │   │
│  │  Parse PR body  CrewAI agents    Commit to target repo   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────── Agents ─────────────────────────────┐   │
│  │  planner_agent.py      → Generates Playwright code       │   │
│  │  executor_agent.py     → Validates via AST & executes    │   │
│  │  step_executor_agent.py→ Active execution (per step)     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────── Tools ──────────────────────────────┐   │
│  │  playwright_executor.py → Browser automation engine      │   │
│  │  dom_inspector.py       → Live selector discovery        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────── Execution ──────────────────────────┐   │
│  │  iterative_orchestrator.py → Step-by-step coordinator    │   │
│  │  execution_context.py      → State between steps         │   │
│  │  retry_handler.py          → Failure analysis & retry    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────── Reporting & Utils ───────────────────┐  │
│  │  action_reporter.py         → PR comment generation      │  │
│  │  github_comment_client.py   → GitHub API client          │  │
│  │  comment_builder.py         → Markdown builder           │  │
│  │  screenshot_handler.py      → Screenshot capture         │  │
│  │  screenshot_embed_manager.py→ Embed screenshots in PRs   │  │
│  │  logger.py                  → GitHub Actions-aware logs   │  │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────── Coverage & Analysis ────────────────────┐   │
│  │  memory_tracker.py       → Test status & coverage gaps   │   │
│  │  criteria_generator.py   → Auto-criteria from PR diffs   │   │
│  │  gap_driven_generator.py → Tests for uncovered modules   │   │
│  │  gap_analysis_db.py      → SQLite gap persistence        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | Role | Key Behavior |
|---|---|---|
| **Planner Agent** | QA Test Code Planner (SDET) | Generates robust Playwright Python code from natural language steps. Uses `FileReadTool` and `DirectoryReadTool` for source-code context. Enforces strict code style: only `playwright.sync_api` imports, `run_test(page, config)` signature, proper waits, assertions, and exact selectors. |
| **Executor Agent** | Code Validator & Runner | Validates generated code via AST analysis. Blocks dangerous constructs (`eval`, `exec`, `open`, `subprocess`). Restricts imports to safe modules. Executes code in isolated Playwright browser contexts. |
| **Step Executor Agent** | Active Execution Step Handler | Processes test steps one at a time with live browser context. Uses DOMInspectorTool to discover selectors from the live page. Accumulates code across steps. |

### Orchestration Flow (Default `generate` Mode)

1. `action_runner.py` reads environment variables and validates configuration
2. `parser.py` extracts the `autoqa` metadata block and numbered steps from the PR body
3. The ETag is computed; if it matches a previous run, generation is skipped
4. `qa_crew.py` initializes CrewAI with OpenAI GPT-4 (configurable via `OPENAI_MODEL_NAME`)
5. The **Planner Agent** generates Playwright Python code
6. The **Executor Agent** validates the code through AST analysis
7. The validated code is executed against the staging environment
8. On success, `cross_repo_manager.py` commits the test file to the target repository
9. `action_reporter.py` posts a PR comment with results and screenshots
10. GitHub Action outputs are set for downstream steps

---

## 9. Active Execution Mode

Active Execution Mode is an advanced feature that generates and executes test code **step-by-step** with a persistent live browser context. Instead of generating all code at once and executing it in bulk, each test step is:

1. Sent to the **Step Executor Agent** with the current browser state
2. The agent uses **DOMInspectorTool** to discover stable selectors from the live page
3. Code for that specific step is generated and executed immediately
4. Screenshots are captured on failure
5. On error, the **Retry Handler** analyzes the failure and suggests alternatives
6. Context and generated code accumulate for subsequent steps

### Configuration

```yaml
autoqa:
  execution:
    use_active_execution: true
    active_execution:
      max_retries_per_step: 2
      step_timeout_ms: 30000
      slow_mo_ms: 500
      failure_mode: "stop_on_error"
```

### Failure Modes

| Mode | Behavior |
|---|---|
| `stop_on_error` | Stop execution on the first failed step |
| `continue_on_error` | Continue to the next step after a failure |
| `partial_commit` | Commit the code for steps that passed |

### Selector Priority

When discovering selectors from the live DOM, the following priority order is used:

1. `data-testid`
2. `data-test`
3. `id`
4. `name`
5. `aria-label`
6. `placeholder`
7. `type`
8. `class`
9. `text`

---

## 10. Auto-Criteria Generation

Auto-criteria generation (Proposal 16) analyzes PR code diffs and automatically suggests test criteria — eliminating the need to manually write the `autoqa` metadata block.

### How It Works

1. The **DiffAnalyzer** fetches the PR diff via the GitHub API
2. The diff is sent to the LLM along with the PR title
3. The LLM generates a JSON array of criteria, each containing:
   - `flow_name`, `tier`, `area`, `steps[]`, `confidence` (0–100)
4. Criteria are posted as a PR comment for developer review
5. The developer approves via the configured approval mechanism
6. Approved criteria are processed as if they were written manually

### Tier Inference from File Paths

| Detected Path Keywords | Inferred Tier |
|---|---|
| `auth`, `payment`, `checkout`, `signup`, `login` | **A** (Critical) |
| `dashboard`, `settings`, `profile`, `search`, `account` | **B** (Important) |
| Everything else | **C** (Nice-to-have) |

### Approval Mechanisms

| Mechanism | How to Approve |
|---|---|
| `reaction` | Add a 👍 reaction to the criteria comment |
| `comment` | Reply with `/autoqa approve` |
| `label` | Add the `autoqa:approved` label to the PR |

### Action Inputs for Auto-Criteria

| Input | Default | Description |
|---|---|---|
| `auto-criteria-fallback` | `false` | When `true` and no `autoqa` block is found, auto-generate criteria from the PR diff |
| `auto-criteria-mode` | `suggest` | `suggest` (post for review) or `auto` (proceed if confidence ≥ threshold) |
| `auto-criteria-threshold` | `85` | Confidence score threshold for auto-proceed |
| `auto-criteria-approval` | `reaction` | `reaction`, `comment`, or `label` |

### Limits

- Maximum **5 flows** per PR
- Maximum **12,000 characters** of diff sent to the LLM

---

## 11. Memory Tracking

The memory tracker provides persistent tracking of test execution results and coverage gaps.

### How It Works

The `AutoQAMemoryTracker` class:

1. Scans test directories to find existing test files
2. Optionally runs tests via pytest
3. Records results per test: `passed`, `failed`, `error`, or `skipped`
4. Tracks execution duration, error messages, and run history
5. Identifies source modules that lack corresponding test files
6. Persists state to `reports/autoqa_memory.json`

### CLI Commands

```bash
# Identify coverage gaps without running tests
python qa_runner.py --memory-scan

# Run tests and update the memory tracker
python qa_runner.py --memory-update

# Print a markdown coverage report
python qa_runner.py --memory-report
```

### Configuration

```yaml
autoqa:
  memory:
    enabled: true
    memory_file: "reports/autoqa_memory.json"
    test_dir: "tests"
    source_dirs: ["src"]
    history_limit: 10
    update_on_ci: true
    report_on_pr: true
```

### Output Example

```
📋 AutoQA Memory Scan Complete
   Source modules:  25
   Covered:         18
   Missing tests:   7
   Coverage:        72%
   Memory saved to: reports/autoqa_memory.json
```

---

## 12. Gap-Driven Test Generation

Gap-driven generation uses the memory tracker's coverage gaps to automatically create test criteria for uncovered source modules.

### How It Works

1. The `GapDrivenGenerator` loads the memory tracker and identifies uncovered modules
2. Source code for each uncovered module is read (up to 8,000 characters)
3. The source code is sent to the LLM with a request to generate test criteria
4. Each criterion includes: `flow_name`, `tier`, `area`, `steps[]`, `confidence`
5. Criteria are posted as a PR comment for developer review (in `suggest` mode)
6. In `auto` mode, criteria with confidence ≥ threshold proceed automatically

### CLI

```bash
python qa_runner.py --gap-driven
```

### Configuration

```yaml
autoqa:
  gap_driven:
    enabled: true
    max_modules_per_run: 10
    max_source_length: 8000
    max_criteria_per_module: 3
    mode: "suggest"
    auto_proceed_threshold: 85
    approval_mechanism: "reaction"
```

### Output Example

```
📋 AutoQA Gap-Driven Test Criteria
   Uncovered modules: 7
   Criteria generated: 5

   1. test_parser_edge_cases (Tier B, Area: autoqa)
      Source: src/autoqa/parser.py
      Confidence: 92/100
      Steps: 4

   2. test_retry_handler_backoff (Tier B, Area: execution)
      Source: src/execution/retry_handler.py
      Confidence: 78/100
      Steps: 3
```

---

## 13. Gap Analysis Database

The gap analysis feature scans for present and missing test workflows and persists the results to a local SQLite database for historical tracking.

### How It Works

The `GapAnalysisDB` class:

1. Scans configured source and test directories
2. Identifies which source modules have corresponding tests (**present**)
3. Identifies which source modules lack tests (**missing**)
4. Persists results to `reports/gap_analysis.db`
5. Each run is timestamped and stored as a separate analysis record

### Database Schema

| Table | Description |
|---|---|
| `analysis_runs` | Metadata per run: timestamp, total modules, present/missing counts, coverage % |
| `workflows_present` | Modules with existing tests: module name, source path, test file, tier, area |
| `workflows_missing` | Modules without tests: module name, source path, reason, suggested test file |

### CLI

```bash
python qa_runner.py --gap-analysis
```

### Output Example

```
📋 AutoQA Gap Analysis Complete
   Database:        reports/gap_analysis.db
   Total modules:   25
   Present:         18
   Missing:         7
   Coverage:        72%

   ✅ Workflows Present:
      • parser (src/autoqa/parser.py) → tests/test_parser.py
      • memory_tracker (src/autoqa/memory_tracker.py) → tests/test_memory_tracker.py

   ❌ Workflows Missing:
      • retry_handler (src/execution/retry_handler.py) → tests/test_retry_handler.py
      • dom_inspector (src/tools/dom_inspector.py) → tests/test_dom_inspector.py
```

---

## 14. Test Organization and File Structure

### Directory Layout

Generated tests are organized by tier and area:

```
tests/autoqa/
├── A/                          # Critical tests
│   ├── auth/
│   │   └── test_user_login_success.py
│   └── commerce/
│       └── test_checkout_flow.py
├── B/                          # Important tests
│   ├── forms/
│   │   └── test_contact_form_validation.py
│   └── general/
│       └── test_add_remove_cart_items.py
└── C/                          # Nice-to-have tests
    └── general/
        └── test_dashboard_sidebar_navigation.py
```

### File Path Pattern

```
tests/autoqa/{tier}/{area}/test_{flow_name}.py
```

### Generated File Contents

Each generated file includes:

- `# AutoQA-Generated` header (used by the edit policy)
- ISO 8601 timestamp with timezone
- Flow name, tier, area, and ETag
- All test steps as comments
- Pytest markers: `@pytest.mark.autoqa`, `@pytest.mark.tier_a`, `@pytest.mark.area_auth`

### Example Generated Test

```python
# AutoQA-Generated
# Timestamp: 2026-03-15T10:30:00+00:00
# Flow: user_login_success | Tier: A | Area: auth
# ETag: a1b2c3d4e5f6...

import pytest

@pytest.mark.autoqa
@pytest.mark.tier_a
@pytest.mark.area_auth
def test_user_login_success(page, config):
    # Step 1: Navigate to login page
    page.goto(config['login_url'])
    page.wait_for_load_state('networkidle')

    # Step 2: Enter valid email address
    page.fill('input[data-testid="email"]', config['staging_email'])

    # Step 3: Enter valid password
    page.fill('input[data-testid="password"]', config['staging_password'])

    # Step 4: Click the login button
    page.click('button[type="submit"]')
    page.wait_for_timeout(5000)

    # Step 5: Verify the dashboard appears
    assert '/dashboard' in page.url
```

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| File name | `test_{flow_name}.py` | `test_user_login_success.py` |
| Class name | `Test{FlowCamel}` | `TestUserLoginSuccess` |
| Function name | `test_{flow_name}` | `test_user_login_success` |
| Branch name | `autoqa/{source_pr}-{flow_name}` | `autoqa/42-user_login_success` |

---

## 15. Security Model

All AI-generated code is validated before execution through multiple layers.

### AST-Based Validation

The Executor Agent parses generated code into an Abstract Syntax Tree and blocks dangerous patterns:

| Blocked Pattern | Description |
|---|---|
| `eval()` / `exec()` | Dynamic code execution |
| `open()` | File system access |
| `subprocess` | System command execution |
| `os.*` | Operating system operations |
| File I/O | Any read/write operations |

### Restricted Imports

Only the following imports are permitted in generated test code:

| Module | Purpose |
|---|---|
| `playwright.sync_api` | Browser automation |
| `time` | Sleep and timing |
| `datetime` | Date/time operations |
| `re` | Regular expressions |

### Sandboxed Execution

- Tests run in isolated Playwright browser contexts
- Each test gets its own browser instance
- No access to the file system or network outside of page interactions

### Secret Redaction

Sensitive values are masked in logs and PR comments using configurable patterns:

```yaml
logging:
  redact_patterns:
    - "password="
    - "token="
    - "Bearer "
    - "@example.com"
```

---

## 16. Reporting

AutoQA generates reports at multiple levels.

### PR Comments

On each run, AutoQA posts (or updates) a single PR comment containing:

- Execution status (success/failure)
- Generated test file path
- Execution time
- Screenshots (embedded or linked)
- Execution logs
- Metadata (flow name, tier, area, ETag)

The comment is identified by a `AUTOQA_CONTROL` anchor to ensure idempotent updates (no duplicate comments).

### HTML Reports

Generated by pytest with the `--html` flag:

```
reports/html/test_execution_{timestamp}.html
```

### JSON Reports

Machine-readable test results:

```
reports/json/test_execution_{timestamp}.json
```

### Screenshots

Captured automatically on test failures:

```
reports/screenshots/*.png
```

Screenshots are uploaded as GitHub Actions artifacts and optionally embedded in PR comments.

---

## 17. Caching and Performance

AutoQA uses a multi-layer caching strategy to minimize CI run times.

### Cache Layers

| Layer | Cache Key | Typical Size |
|---|---|---|
| Python pip packages | Hash of `requirements.txt` | ~200 MB |
| Playwright browsers | Playwright version + `requirements.txt` hash | ~100 MB |
| AutoQA repository | Commit SHA | ~5 MB |

### Performance

| Scenario | Approximate Time |
|---|---|
| Cold run (no caches) | 3–4 minutes |
| Warm run (all cached) | 45–60 seconds |

### How Caching Works in the Action

1. **AutoQA repository** — Cached to avoid repeated clones
2. **pip packages** — Cached via `actions/setup-python` based on `requirements.txt` hash
3. **Playwright browsers** — Cached via `actions/cache`; browser installation is skipped on cache hit (saves 2–3 minutes)
4. On cache hit for browsers, only system dependencies are installed (`playwright install-deps chromium`)

Caches automatically invalidate when `requirements.txt` changes.

---

## 18. Environment Variables

The following environment variables are used by `action_runner.py` during GitHub Action execution:

### Core

| Variable | Source | Description |
|---|---|---|
| `GITHUB_TOKEN` | `github.token` | GitHub API token |
| `OPENAI_API_KEY` | Action input | OpenAI API key |
| `STAGING_URL` | Action input | Staging environment URL |
| `STAGING_EMAIL` | Action input | Test account email |
| `STAGING_PASSWORD` | Action input | Test account password |

### Paths and Git

| Variable | Source | Description |
|---|---|---|
| `TARGET_REPO_PATH` | Action input | Path to target repository |
| `TARGET_REPOSITORY` | `github.repository` | Full repo name (`owner/repo`) |
| `TEST_DIRECTORY` | Action input | Base test directory |
| `GIT_USER_NAME` | Action input | Git commit user name |
| `GIT_USER_EMAIL` | Action input | Git commit user email |

### Execution

| Variable | Source | Description |
|---|---|---|
| `EXECUTION_MODE` | Action input | Execution mode |
| `PR_BODY` | Action input / event | PR description text |
| `PR_NUMBER` | `github.event.pull_request.number` | PR number |
| `CREATE_PR` | Action input | Whether to create a PR |

### Auto-Criteria

| Variable | Source | Description |
|---|---|---|
| `AUTO_CRITERIA_FALLBACK` | Action input | Enable auto-criteria fallback |
| `AUTO_CRITERIA_MODE` | Action input | `suggest` or `auto` |
| `AUTO_CRITERIA_THRESHOLD` | Action input | Confidence threshold |
| `AUTO_CRITERIA_APPROVAL` | Action input | Approval mechanism |

### OpenAI Model

| Variable | Default | Description |
|---|---|---|
| `OPENAI_MODEL_NAME` | `openai/gpt-4.1` | LLM model for code generation |

### Local Development

| Variable | Default | Description |
|---|---|---|
| `HEADLESS_MODE` | `true` | Run browser in headless mode |
| `BROWSER_TYPE` | `chromium` | Browser engine |
| `DEFAULT_TIMEOUT` | `30000` | Page operation timeout (ms) |
| `CAPTURE_SCREENSHOTS` | `true` | Enable screenshot capture |
| `SCREENSHOT_ON_FAILURE` | `true` | Capture screenshots on failure |

---

## 19. Troubleshooting

### Common Issues

| Issue | Solution |
|---|---|
| **No `.env` file found** | Copy `env.template` to `.env` and fill in your values |
| **OpenAI API key invalid** | Verify the key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and ensure GPT-4 access |
| **Playwright browsers not installed** | Run `playwright install --with-deps chromium` |
| **Test generation skipped (ETag match)** | The PR description has not changed since the last run. Modify the steps or metadata to trigger regeneration |
| **AST validation failed** | The generated code contains unsafe patterns. Check the PR comment for details. This usually resolves on retry |
| **Staging URL unreachable** | Verify the staging environment is running and accessible from the CI runner |
| **Permission denied on commit** | Ensure the GitHub token has `contents: write` permission. For private AutoQA repos, provide `qa-github-token` |
| **Test execution timeout** | Increase `timeout_per_test` in `autoqa_config.yaml` or check staging responsiveness |
| **Quota exceeded** | You have reached the per-tier test limit. Retire old tests with the `autoqa:retire` label |

### Debugging Locally

```bash
# Run with visible browser
HEADLESS_MODE=false python qa_runner.py

# Check HTML reports for detailed failure information
ls reports/html/

# Check screenshots for visual context
ls reports/screenshots/
```

### Checking CI Logs

Review the GitHub Actions run logs for the **Execute AutoQA Workflow** step. AutoQA uses emoji prefixes for quick visual scanning:

- 🤖 — AutoQA action messages
- ✅ — Success
- ❌ — Failure
- 📸 — Screenshot captured
- 📊 — Report generated

---

## 20. FAQ

**Q: Can I use AutoQA with a private repository?**
A: Yes. Provide a `qa-github-token` input with a Personal Access Token that has `repo` scope to access the private AutoQA action repository.

**Q: Can I use a different OpenAI model?**
A: Yes. Set the `OPENAI_MODEL_NAME` environment variable. The default is `openai/gpt-4.1`.

**Q: What happens if I edit the PR description?**
A: AutoQA triggers on `edited` events. If the metadata or steps change, a new ETag is computed and the test is regenerated. If nothing changed, it is a no-op.

**Q: Can I manually edit generated test files?**
A: Yes, but be aware of the edit policy. Files with the `AutoQA-Generated` header may be overwritten on the next run if the ETag changes. To protect a file, remove the header or move it to a `human/` directory.

**Q: How do I retire a generated test?**
A: Add the `autoqa:retire` label to the PR that created the test. AutoQA will open a delete PR for the test file.

**Q: Can I run AutoQA locally without GitHub Actions?**
A: Yes. Use `qa_runner.py` for local test execution, memory tracking, and gap analysis. Test generation from PR bodies requires the GitHub Action context.

**Q: What browsers are supported?**
A: AutoQA uses Playwright with Chromium by default. Firefox and WebKit can be configured via the `BROWSER_TYPE` environment variable for local runs.

**Q: How do I prevent test bloat?**
A: AutoQA enforces per-tier quotas (A: 40, B: 40, C: 20, total: 100). Use the `autoqa:retire` label to remove obsolete tests.

**Q: Is generated code safe to run?**
A: Yes. All generated code passes through AST-based validation that blocks dangerous patterns (`eval`, `exec`, `open`, `subprocess`, file I/O) and restricts imports to a safe allow-list before execution.

**Q: Can I use AutoQA across multiple repositories?**
A: Yes. AutoQA is designed as a cross-repository GitHub Action. Add the workflow file to each repository and configure the required secrets.

---

## Additional Resources

| Resource | Path |
|---|---|
| Architecture deep dive | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| Active execution details | [`docs/ACTIVE_EXECUTION.md`](ACTIVE_EXECUTION.md) |
| Action usage guide | [`docs/ACTION_USAGE.md`](ACTION_USAGE.md) |
| Enhancement roadmap (16 proposals) | [`docs/AUTOQA_ENHANCEMENT_ROADMAP.md`](AUTOQA_ENHANCEMENT_ROADMAP.md) |
| Quick start reference | [`docs/AUTOQA_QUICK_START.md`](AUTOQA_QUICK_START.md) |
| FE-REACT integration | [`docs/FE_REACT_INTEGRATION.md`](FE_REACT_INTEGRATION.md) |
| Linting and code quality | [`docs/LINTING.md`](LINTING.md) |
| Release process | [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md) |
| Open-source readiness | [`docs/OPEN_SOURCE_ROADMAP.md`](OPEN_SOURCE_ROADMAP.md) |
| Example PR description | [`examples/EXAMPLE_PR_DESCRIPTION.md`](../examples/EXAMPLE_PR_DESCRIPTION.md) |
| PR template with examples | [`examples/PR_TEMPLATE_WITH_AUTOQA.md`](../examples/PR_TEMPLATE_WITH_AUTOQA.md) |
| Example FE-REACT workflow | [`examples/fe-react-autoqa-workflow.yml`](../examples/fe-react-autoqa-workflow.yml) |
| Changelog | [`CHANGELOG.md`](../CHANGELOG.md) |
| Contributing guide | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
