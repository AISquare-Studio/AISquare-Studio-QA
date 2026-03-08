# AISquare Studio AutoQA

[![GitHub Action](https://img.shields.io/badge/GitHub%20Action-AutoQA-2088FF?logo=github-actions&logoColor=white)](https://github.com/AISquare-Studio/AISquare-Studio-QA)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Enabled-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF6B6B)](https://www.crewai.com/)

**AI-powered GitHub Action that converts natural language test descriptions in pull request bodies into fully automated Playwright tests.** Write what you want to test in plain English — AutoQA generates, executes, and commits production-ready test code using CrewAI multi-agent orchestration and OpenAI GPT-4.

---

## Features

- **AI-Powered Test Generation** — Natural language steps become executable Playwright Python tests
- **Active Execution Mode** — Iterative step-by-step generation with real-time browser context
- **Smart Selector Discovery** — Auto-discovers optimal selectors from live pages via DOMInspectorTool
- **Intelligent Retry** — Automatic error recovery with alternative selectors and failure analysis
- **AST-Based Security Validation** — Prevents unsafe code patterns before execution
- **Cross-Repository Architecture** — Deploys as a GitHub Action, runs in any repository
- **Comprehensive Reporting** — PR comments with screenshots, HTML reports, and JSON artifacts
- **ETag-Based Idempotency** — Prevents duplicate test generation for unchanged PR descriptions
- **Multi-Tier Test Organization** — Categorize tests into A/B/C tiers by criticality
- **Caching Strategy** — Pip and Playwright browser caching for fast CI runs

---

## How It Works

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

1. A developer writes numbered test steps in the PR description inside a fenced `autoqa` block
2. The GitHub Action triggers on PR open/edit/sync events
3. AutoQA parses the PR body for metadata (`flow_name`, `tier`, `area`) and test steps
4. CrewAI agents generate Playwright Python test code from the steps
5. Generated code is validated via AST analysis and executed against your staging environment
6. On success, the test file is committed to `tests/autoqa/{tier}/{area}/test_{flow_name}.py`
7. Results and screenshots are posted as a PR comment

---

## Quick Start

### 1. Add the workflow

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

### 2. Configure secrets

Add the following secrets in your repository's **Settings → Secrets and variables → Actions**:

| Secret             | Description                       |
| ------------------ | --------------------------------- |
| `OPENAI_API_KEY`   | OpenAI API key (GPT-4 access)     |
| `STAGING_URL`      | Staging environment login URL     |
| `STAGING_EMAIL`    | Test account email                |
| `STAGING_PASSWORD` | Test account password             |

### 3. Write test steps in a PR

Include a fenced `autoqa` block in your pull request description:

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

Open the PR and AutoQA takes care of the rest.

---

## PR Format Reference

The `autoqa` code block defines metadata. Numbered steps below it describe the test scenario.

````markdown
```autoqa
flow_name: <snake_case_test_name>
tier: <A|B|C>
area: <feature_area>
```

1. First test step in plain English
2. Second test step
3. ...
````

| Field       | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `flow_name` | Yes      | Snake-case identifier used for the generated file name    |
| `tier`      | Yes      | `A` (critical), `B` (important), or `C` (nice-to-have)   |
| `area`      | Yes      | Feature area used as subdirectory (e.g., `auth`, `billing`) |

---

## Configuration Reference

### Action Inputs

| Input               | Required | Default          | Description                                       |
| ------------------- | -------- | ---------------- | ------------------------------------------------- |
| `openai-api-key`    | **Yes**  | —                | OpenAI API key                                    |
| `staging-url`       | **Yes**  | —                | Staging environment URL                           |
| `qa-github-token`   | No       | `github.token`   | GitHub token (for private repo access)             |
| `staging-email`     | No       | `test@example.com` | Test account email                              |
| `staging-password`  | No       | —                | Test account password                             |
| `target-repo-path`  | No       | `.`              | Path to the target repository                     |
| `git-user-name`     | No       | `AutoQA Bot`     | Git user name for test commits                    |
| `git-user-email`    | No       | —                | Git user email for test commits                   |
| `pr-body`           | No       | *(auto-detected)* | PR description text                              |
| `test-directory`    | No       | `tests/autoqa`   | Base directory for generated tests                |
| `create-pr`         | No       | `false`          | Create a PR for tests instead of pushing directly |
| `execution-mode`    | No       | `generate`       | Execution mode: `generate`, `suite`, or `all`     |

### Action Outputs

| Output                | Description                             |
| --------------------- | --------------------------------------- |
| `test_generated`      | Whether a test was generated (`true`/`false`) |
| `test_file_path`      | Path to the generated test file         |
| `test_results`        | JSON object with execution results      |
| `generation_metadata` | JSON object with generation metadata    |
| `screenshot_path`     | Path to captured screenshots            |
| `etag`                | Idempotency hash of the PR description  |
| `flow_name`           | Parsed flow name                        |
| `tier`                | Parsed tier                             |
| `area`                | Parsed area                             |
| `error`               | Error message (if failed)               |

### Execution Modes

| Mode       | Behavior                                                          |
| ---------- | ----------------------------------------------------------------- |
| `generate` | Parse PR, generate a new test, execute it, and commit on success  |
| `suite`    | Run the existing test suite only (regression testing)             |
| `all`      | Generate a new test **and** run the full existing suite           |

---

## Project Structure

```
AISquare-Studio-QA/
├── action.yml                          # GitHub Action definition
├── qa_runner.py                        # Local test runner entry point
├── requirements.txt                    # Python dependencies
├── pyproject.toml                      # Python project configuration
├── pytest.ini                          # Pytest configuration
├── env.template                        # Environment variables template
├── config/
│   ├── autoqa_config.yaml              # AutoQA policy and settings
│   └── test_data.yaml                  # Test scenarios and selectors
├── src/
│   ├── agents/
│   │   ├── planner_agent.py            # Generates Playwright code via CrewAI
│   │   ├── executor_agent.py           # Validates and executes code (AST safety)
│   │   └── step_executor_agent.py      # Active execution step agent
│   ├── autoqa/
│   │   ├── action_runner.py            # Main GitHub Action orchestrator
│   │   ├── parser.py                   # PR body metadata parser
│   │   ├── action_reporter.py          # PR comment generator
│   │   └── cross_repo_manager.py       # Test file commits across repos
│   ├── crews/
│   │   └── qa_crew.py                  # CrewAI agent orchestration
│   ├── execution/
│   │   ├── iterative_orchestrator.py   # Step-by-step execution coordinator
│   │   ├── execution_context.py        # State tracking between steps
│   │   └── retry_handler.py            # Failure analysis and retry logic
│   ├── tools/
│   │   ├── playwright_executor.py      # Test code execution engine
│   │   └── dom_inspector.py            # Live page selector discovery
│   ├── templates/
│   │   └── test_execution_template.py  # Execution template
│   └── utils/
│       ├── logger.py                   # GitHub Actions-aware logging
│       ├── github_comment_client.py    # GitHub API client
│       ├── comment_builder.py          # Markdown comment builder
│       ├── screenshot_handler.py       # Screenshot capture
│       └── screenshot_embed_manager.py # Screenshot embedding
├── tests/                              # Pytest test suites
├── docs/                               # Documentation
├── examples/                           # Example workflows and configs
├── reports/                            # Generated test artifacts
└── scripts/                            # Utility scripts
```

---

## Local Development

### Prerequisites

- Python 3.11+
- An OpenAI API key with GPT-4 access

### Setup

```bash
# Clone the repository
git clone https://github.com/AISquare-Studio/AISquare-Studio-QA.git
cd AISquare-Studio-QA

# Install dependencies
pip install -r requirements.txt
playwright install --with-deps chromium

# Configure environment
cp env.template .env
# Edit .env with your staging URL, credentials, and OpenAI API key
```

### Running locally

```bash
# Run the test runner
python qa_runner.py

# Run with visible browser for debugging
HEADLESS_MODE=false python qa_runner.py

# Show detailed help
python qa_runner.py --help-detailed
```

### Running the test suite

```bash
pytest tests/ -v
```

---

## Architecture

AutoQA uses a multi-agent architecture powered by [CrewAI](https://www.crewai.com/):

- **Planner Agent** — Converts natural language steps into Playwright Python code
- **Executor Agent** — Validates generated code via AST analysis and runs it in a sandboxed browser
- **Step Executor Agent** — Handles Active Execution Mode, processing one step at a time with live browser context

The **Iterative Orchestrator** coordinates step-by-step execution, maintaining state via `ExecutionContext` and handling failures through `RetryHandler`.

For a detailed architecture walkthrough, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Security

All AI-generated code is validated before execution:

- **AST-based validation** — Blocks dangerous constructs (`eval`, `exec`, `open`, `subprocess`, file I/O)
- **Restricted imports** — Only `playwright.sync_api`, `time`, `datetime`, and `re` are permitted
- **Sandboxed execution** — Tests run in isolated Playwright browser contexts
- **Secret redaction** — Sensitive values are masked in logs and reports

See the [Security Model](docs/ARCHITECTURE.md#security-model) section in the architecture documentation for details.

---

## Performance and Caching

AutoQA caches dependencies to minimize CI run times:

| Layer                 | Cache Key                       | Typical Size |
| --------------------- | ------------------------------- | ------------ |
| Python pip packages   | Hash of `requirements.txt`      | ~200 MB      |
| Playwright browsers   | Playwright version              | ~100 MB      |
| Action repository     | Commit SHA                      | ~5 MB        |

| Scenario  | Approximate Time |
| --------- | ---------------- |
| Cold run  | 3–4 minutes      |
| Warm run  | 45–60 seconds    |

Caches automatically invalidate when `requirements.txt` changes.

---

## Code Quality and Linting

The project enforces consistent style via automated tooling:

| Tool      | Purpose                       | Configuration          |
| --------- | ----------------------------- | ---------------------- |
| **black** | Code formatting               | Line length: 100       |
| **isort** | Import sorting                | Black-compatible profile |
| **flake8**| PEP 8 compliance              | Standard rules         |

The `lint.yml` workflow runs on every push and pull request, auto-fixing formatting issues.

```bash
# Run locally
black . --line-length=100
isort . --profile=black --line-length=100
flake8 .
```

---

## Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure linting passes (`black`, `isort`, `flake8`)
5. Submit a pull request

Please review the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before contributing.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

Copyright 2025 AISquare Studio

---

Built by **AISquare Studio**
