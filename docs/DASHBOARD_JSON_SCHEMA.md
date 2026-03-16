# 📊 AutoQA Dashboard JSON Schema Reference

> **Version:** 1.0 · **Output:** `dashboard_results` · **File:** `reports/dashboard_results.json`

This document is the definitive reference for the `dashboard_results` JSON payload produced by AutoQA on every PR run. Use it to populate the **AutoQA Dashboard** (Phase 1) with gap analysis, test summaries, and per-test details.

---

## Table of Contents

- [Overview](#overview)
- [How to Access the Data](#how-to-access-the-data)
- [Complete JSON Schema](#complete-json-schema)
- [Section Reference](#section-reference)
  - [gap_analysis](#gap_analysis)
  - [summary](#summary)
  - [test_cases](#test_cases)
- [Full Example Payload](#full-example-payload)
- [Field Reference Tables](#field-reference-tables)
- [Execution Modes &amp; Data Availability](#execution-modes--data-availability)
- [Frontend Integration Prompt](#frontend-integration-prompt)

---

## Overview

Every AutoQA run (suite, gap-analysis, or generate mode) now outputs a **`dashboard_results`** JSON string as a GitHub Action output **and** writes it to `reports/dashboard_results.json` as a build artifact.

The payload has **three top-level keys**:

| Key | Purpose | Source |
|-----|---------|--------|
| `gap_analysis` | Coverage info — which workflows have tests, which don't | `GapAnalysisDB.run_analysis()` |
| `summary` | Run metadata — PR number, commit, pass/fail counts, duration | `ActionRunner._run_test_suite()` |
| `test_cases` | Per-test details — status, duration, error messages, screenshots | `ActionRunner._run_test_suite()` detailed results |

---

## How to Access the Data

### 1. GitHub Action Output (recommended for workflows)

```yaml
- name: 🤖 Run AutoQA
  id: autoqa
  uses: AISquare-Studio/AISquare-Studio-QA@main
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    staging-url: ${{ secrets.STAGING_URL }}
    execution-mode: 'suite'  # or 'gap-analysis', 'generate', 'all'

- name: Use Dashboard Results
  run: |
    echo '${{ steps.autoqa.outputs.dashboard_results }}' | jq .
```

### 2. Build Artifact (recommended for dashboard upload)

The file `reports/dashboard_results.json` is uploaded as the artifact **`autoqa-dashboard-{run_number}`** on every run. Download it via:

```bash
# GitHub CLI
gh run download <run-id> -n autoqa-dashboard-<run-number>

# Or use the GitHub API
GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts
```

### 3. Workflow Step: Upload to Dashboard API

```yaml
- name: 📤 Upload to Dashboard
  if: steps.autoqa.outputs.dashboard_results != ''
  run: |
    curl -X POST https://autoqa.aisquare.studio/api/results \
      -H "Content-Type: application/json" \
      -d '${{ steps.autoqa.outputs.dashboard_results }}'
```

---

## Complete JSON Schema

```jsonc
{
  // ── Gap Analysis ──────────────────────────────────────────
  "gap_analysis": {
    "coverage_percent": 68.5,           // float — overall coverage %
    "total_workflows": 127,             // int   — total source modules scanned
    "tested_workflows": 87,             // int   — modules that have test files
    "missing_workflows": 40,            // int   — modules without test files
    "present_workflows": [              // array — details of covered modules
      {
        "module": "user_workflows.registration",
        "source_path": "src/user_workflows/registration.py",
        "test_file": "tests/test_user_workflows_registration.py",
        "tier": "A",                    // "A" | "B" | "C" — inferred
        "area": "authentication"        // string — inferred from path
      }
    ],
    "missing_workflows_list": [         // array — modules lacking tests
      {
        "module": "user_workflows.password_reset",
        "source_path": "src/user_workflows/password_reset.py"
      }
    ]
  },

  // ── Summary ───────────────────────────────────────────────
  "summary": {
    "timestamp": "2026-03-03T14:30:00Z",  // ISO-8601
    "execution_mode": "pr_validation",     // "pr_validation" | "suite" | "gap-analysis" | "all"
    "pr_number": 42,                       // int | null
    "commit_sha": "abc123def456",          // string
    "total_tests": 22,                     // int
    "passed": 19,                          // int
    "failed": 3,                           // int
    "skipped": 0,                          // int
    "duration_seconds": 145.2              // float
  },

  // ── Test Cases ────────────────────────────────────────────
  "test_cases": [
    {
      "test_id": "tests/autoqa/A/auth/test_registration.py::TestRegistration::test_successful_registration",
      "flow_name": "registration",         // derived from test file name
      "tier": "A",                         // from path or keyword inference
      "area": "auth",                      // from path
      "status": "passed",                  // "passed" | "failed" | "skipped" | "unknown"
      "duration_seconds": 3.2,             // float, rounded to 2 decimals
      "screenshots": []                    // array of URL strings
    },
    {
      "test_id": "tests/autoqa/A/auth/test_login.py::test_login_with_invalid_password",
      "flow_name": "login",
      "tier": "A",
      "area": "auth",
      "status": "failed",
      "duration_seconds": 5.1,
      "screenshots": [
        "https://storage.googleapis.com/autoqa-screenshots/run123/step1.png"
      ],
      "error_message": "AssertionError: Expected error message not displayed",
      "error_type": "AssertionError"       // extracted from error_message
    }
  ]
}
```

---

## Section Reference

### `gap_analysis`

Shows current test coverage — which workflows have tests and which are missing.

| Field | Type | Description |
|-------|------|-------------|
| `coverage_percent` | `float` | Overall coverage percentage (0.0–100.0) |
| `total_workflows` | `int` | Total source modules scanned |
| `tested_workflows` | `int` | Modules with corresponding test files |
| `missing_workflows` | `int` | Modules without test files |
| `present_workflows` | `array` | List of covered workflow objects |
| `missing_workflows_list` | `array` | List of uncovered workflow objects |

#### Present Workflow Object

| Field | Type | Description |
|-------|------|-------------|
| `module` | `string` | Module name (e.g. `"parser"`) |
| `source_path` | `string` | Relative path to source file |
| `test_file` | `string` | Relative path to test file |
| `tier` | `string` | `"A"`, `"B"`, or `"C"` — inferred from path keywords |
| `area` | `string` | Functional area — inferred from directory structure |

**Tier inference rules:**
- **A (Critical):** Path contains `auth`, `payment`, `checkout`, `signup`, or `login`
- **B (Important):** Path contains `dashboard`, `settings`, `profile`, `search`, or `account`
- **C (Default):** Everything else

#### Missing Workflow Object

| Field | Type | Description |
|-------|------|-------------|
| `module` | `string` | Module name |
| `source_path` | `string` | Relative path to source file |

---

### `summary`

Run-level metadata and aggregate pass/fail counts.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `string` | ISO-8601 timestamp of the run |
| `execution_mode` | `string` | One of: `"pr_validation"`, `"suite"`, `"gap-analysis"`, `"all"`, `"generate"`, `"auto-criteria"`, `"gap-driven"` |
| `pr_number` | `int \| null` | Pull request number, or `null` if not a PR context |
| `commit_sha` | `string` | Git commit SHA |
| `total_tests` | `int` | Total test cases executed |
| `passed` | `int` | Count of passed tests |
| `failed` | `int` | Count of failed tests |
| `skipped` | `int` | Count of skipped tests |
| `duration_seconds` | `float` | Total execution duration in seconds |

---

### `test_cases`

Per-test details. Each entry represents one pytest test case.

| Field | Type | Presence | Description |
|-------|------|----------|-------------|
| `test_id` | `string` | Always | Full pytest node ID (e.g. `tests/path/test_file.py::TestClass::test_method`) |
| `flow_name` | `string` | Always | Derived from file name (`test_user_login.py` → `"user_login"`) |
| `tier` | `string` | Always | `"A"`, `"B"`, or `"C"` |
| `area` | `string` | Always | Functional area (e.g. `"auth"`, `"general"`) |
| `status` | `string` | Always | `"passed"`, `"failed"`, `"skipped"`, or `"unknown"` |
| `duration_seconds` | `float` | Always | Execution time, rounded to 2 decimals |
| `screenshots` | `array` | Always | List of screenshot URLs (empty if none) |
| `error_message` | `string` | Failed only | Full error message text |
| `error_type` | `string` | Failed only | Exception class name (e.g. `"AssertionError"`, `"TypeError"`) |

**Status mapping from pytest outcomes:**

| pytest outcome | Dashboard status |
|---------------|-----------------|
| `passed` | `"passed"` |
| `failed` | `"failed"` |
| `error` | `"failed"` |
| `skipped` | `"skipped"` |
| `xfailed` | `"skipped"` |
| `xpassed` | `"passed"` |

---

## Full Example Payload

```json
{
  "gap_analysis": {
    "coverage_percent": 68.5,
    "total_workflows": 127,
    "tested_workflows": 87,
    "missing_workflows": 40,
    "present_workflows": [
      {
        "module": "registration",
        "source_path": "src/user_workflows/registration.py",
        "test_file": "tests/test_registration.py",
        "tier": "A",
        "area": "authentication"
      },
      {
        "module": "dashboard_views",
        "source_path": "src/dashboard/dashboard_views.py",
        "test_file": "tests/test_dashboard_views.py",
        "tier": "B",
        "area": "dashboard"
      },
      {
        "module": "parser",
        "source_path": "src/autoqa/parser.py",
        "test_file": "tests/test_parser.py",
        "tier": "C",
        "area": "autoqa"
      }
    ],
    "missing_workflows_list": [
      {
        "module": "password_reset",
        "source_path": "src/user_workflows/password_reset.py"
      },
      {
        "module": "logger",
        "source_path": "src/utils/logger.py"
      }
    ]
  },
  "summary": {
    "timestamp": "2026-03-03T14:30:00Z",
    "execution_mode": "pr_validation",
    "pr_number": 42,
    "commit_sha": "abc123def456",
    "total_tests": 22,
    "passed": 19,
    "failed": 3,
    "skipped": 0,
    "duration_seconds": 145.2
  },
  "test_cases": [
    {
      "test_id": "tests/autoqa/A/auth/test_registration.py::TestRegistration::test_successful_registration",
      "flow_name": "registration",
      "tier": "A",
      "area": "auth",
      "status": "passed",
      "duration_seconds": 3.2,
      "screenshots": []
    },
    {
      "test_id": "tests/autoqa/A/auth/test_login.py::TestLogin::test_login_success",
      "flow_name": "login",
      "tier": "A",
      "area": "auth",
      "status": "passed",
      "duration_seconds": 2.1,
      "screenshots": []
    },
    {
      "test_id": "tests/autoqa/A/auth/test_login.py::test_login_with_invalid_password",
      "flow_name": "login",
      "tier": "A",
      "area": "auth",
      "status": "failed",
      "duration_seconds": 5.1,
      "screenshots": [
        "https://storage.googleapis.com/autoqa-screenshots/run123/step1.png"
      ],
      "error_message": "AssertionError: Expected error message not displayed",
      "error_type": "AssertionError"
    },
    {
      "test_id": "tests/autoqa/B/dashboard/test_dashboard.py::test_dashboard_load",
      "flow_name": "dashboard",
      "tier": "B",
      "area": "dashboard",
      "status": "passed",
      "duration_seconds": 1.8,
      "screenshots": []
    }
  ]
}
```

---

## Execution Modes & Data Availability

Not every execution mode populates all three sections. Here's what you get:

| Mode | `gap_analysis` | `summary` | `test_cases` |
|------|:-:|:-:|:-:|
| `suite` | ❌ empty | ✅ populated | ✅ populated |
| `gap-analysis` | ✅ populated | ❌ empty (zeros) | ❌ empty |
| `generate` | ❌ empty | ❌ empty (zeros) | ❌ empty |
| `all` | ❌ empty | ✅ populated | ✅ populated |
| `auto-criteria` | ❌ empty | ❌ empty (zeros) | ❌ empty |
| `gap-driven` | ❌ empty | ❌ empty (zeros) | ❌ empty |

> **Tip:** To get a fully populated payload, run `gap-analysis` mode first (for coverage data), then `suite` mode (for test results). The dashboard can merge both payloads client-side by taking `gap_analysis` from the first and `summary` + `test_cases` from the second.

---

## Frontend Integration Prompt

The following prompt can be given to a **frontend React agent** to build the dashboard UI that consumes this JSON:

---

### 🤖 Copy-Paste Prompt for FE React Agent

```
Build an AutoQA Dashboard as a React + Vite + Tailwind CSS application that
consumes a JSON file upload (results.json). The JSON conforms to the schema
documented below. The app should be client-side only (no backend).

## JSON Schema

The uploaded file has three top-level keys:

1. "gap_analysis" — coverage data
   - coverage_percent (float)
   - total_workflows (int)
   - tested_workflows (int)
   - missing_workflows (int)
   - present_workflows: array of { module, source_path, test_file, tier, area }
   - missing_workflows_list: array of { module, source_path }

2. "summary" — run metadata
   - timestamp (ISO-8601)
   - execution_mode (string)
   - pr_number (int | null)
   - commit_sha (string)
   - total_tests (int)
   - passed (int)
   - failed (int)
   - skipped (int)
   - duration_seconds (float)

3. "test_cases" — per-test details, array of:
   - test_id (string — full pytest node ID)
   - flow_name (string)
   - tier ("A" | "B" | "C")
   - area (string)
   - status ("passed" | "failed" | "skipped" | "unknown")
   - duration_seconds (float)
   - screenshots (array of URL strings)
   - error_message (string, present only when status is "failed")
   - error_type (string, present only when status is "failed")

## Pages / Views

### 1. Upload Page (Landing)
- Drag-and-drop zone: "Upload your AutoQA results.json"
- Validate: must be valid JSON, max 10 MB
- Error toast on invalid file
- Loading spinner while parsing
- On success, navigate to /dashboard with parsed data in React state

### 2. Gap Analysis View (/dashboard/coverage)
- Top summary card: coverage percentage (circular progress bar), tested/total count, missing count
- Side-by-side tables:
  - LEFT: "✅ Present Workflows" (green header) — columns: Module, Tier, Area, Test File
  - RIGHT: "❌ Missing Workflows" (red header) — columns: Module, Source Path
- Both tables: searchable, sortable, "Export CSV" button

### 3. Test Results View (/dashboard/results)
- Summary header: PR #{pr_number} ({commit_sha}) · timestamp · ✅ {passed} passed · ❌ {failed} failed · ⏱ {duration_seconds}s
- Test results table: Status (icon), Test ID, Tier, Area, Duration, View (→ arrow)
- Filters: Status dropdown (all/passed/failed/skipped), Tier checkboxes (A/B/C), Area text search
- Sort by: Status, Duration, Test ID
- Click row → modal with: test_id, status, duration, error_message, screenshot carousel
- "Copy Error" button in modal copies error_message to clipboard

### 4. Screenshot Viewer (in modal)
- Lightbox/carousel for screenshots array
- Zoom and full-screen support
- Step number captions ("Step 1 of 3")
- "Download All" button

## Design
- Dark mode: background #0a0a0a, primary #3b82f6, success #10b981, error #ef4444, text #f9fafb
- Font: Inter (Google Fonts), headings 600 weight, body 400
- Icons: Lucide React
- Responsive: tables collapse to cards on mobile

## Tech Stack
- React + Vite
- Tailwind CSS
- react-dropzone (file upload)
- Recharts or Chart.js (coverage progress)
- TanStack Table (sortable/filterable tables)
- react-image-lightbox or yet-another-react-lightbox (screenshot viewer)

## Important
- All processing client-side, no data sent to any server
- Optional: cache last upload in localStorage for revisit
- File validation: must have gap_analysis, summary, and test_cases keys
- Handle partial data gracefully (some sections may have empty arrays or zero counts)
```

---

## Source Code Reference

| File | Description |
|------|-------------|
| `src/autoqa/dashboard_results.py` | `DashboardResultsBuilder` class — builds the JSON payload |
| `src/autoqa/action_runner.py` | Integration — calls `_generate_dashboard_results()` in suite, gap-analysis, and generate modes |
| `src/autoqa/gap_analysis_db.py` | Gap analysis data source — `run_analysis()` returns coverage data |
| `action.yml` | GitHub Action output definition and artifact upload |
| `tests/test_dashboard_results.py` | 58 tests covering all builder methods |
