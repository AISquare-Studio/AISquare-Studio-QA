# Open-Source Readiness: Weak Points, Improvements, and Roadmap

This document catalogues the current limitations of AISquare Studio AutoQA and proposes improvements organized by priority. It is intended to guide contributors and inform potential adopters about what works well, what needs attention, and where the largest opportunities for contribution lie.

> **See also**: [`AUTOQA_ENHANCEMENT_ROADMAP.md`](AUTOQA_ENHANCEMENT_ROADMAP.md) for the comprehensive feature enhancement roadmap with 16 proposals inspired by Lucent AI and Meticulous AI.

---

## Table of Contents

1. [Current Strengths](#current-strengths)
2. [Weak Points and Risks](#weak-points-and-risks)
3. [Improvement Areas](#improvement-areas)
4. [Open-Source Readiness Checklist](#open-source-readiness-checklist)
5. [Contributor Opportunities](#contributor-opportunities)

---

## Current Strengths

These aspects of the system work well and represent defensible design decisions:

| Area                         | What Works                                                                 |
| ---------------------------- | -------------------------------------------------------------------------- |
| **Active Execution Mode**    | Step-by-step generation with live browser context is a genuine differentiator. The iterative loop with retry logic produces more reliable tests than single-shot generation. |
| **Security Validation**      | AST-based code validation is solid. The import allowlist and function call blocklist prevent the most dangerous code patterns. |
| **Cross-Repo Architecture**  | The composite action design cleanly separates the action's source from the target repository's test files. |
| **Selector Priority System** | The DOMInspectorTool's ranked selector strategy (data-testid > id > name > aria-label > ...) mirrors real-world best practices. |
| **PR Comment Integration**   | Single-comment idempotency via HTML markers is a good UX pattern. Screenshot embedding with size-based fallback to artifacts is practical. |
| **Caching**                  | Multi-layer caching (pip, Playwright, repo) with hash-based keys provides meaningful CI speedups. |
| **ETag Idempotency**         | SHA-256 hashing of canonicalized metadata + steps prevents redundant regeneration. |

---

## Weak Points and Risks

### 1. Security: `exec()` Usage in Step Execution

**Risk: HIGH**

The `StepExecutorAgent.execute_step()` method uses Python's `exec()` to run LLM-generated code:

```python
exec(step_code, exec_namespace)
```

While the AST validator catches many dangerous patterns, `exec()` is inherently risky. The validator only runs on the **initial generation path** (via `ExecutorAgent.validate_code_safety()`), but step-by-step code in Active Execution Mode bypasses this validation entirely — each step is executed directly without AST checking.

**Recommendation:**
- Apply AST validation to every step before execution, not just the final assembled code
- Consider a more restrictive execution sandbox (e.g., RestrictedPython, subprocess isolation)
- Add runtime monitoring for suspicious behavior (filesystem access, network calls)
- Document the threat model explicitly

---

### 2. Test Reliability: Non-Deterministic AI Output

**Risk: MEDIUM**

LLM-generated test code is non-deterministic. The same PR description can produce different selectors, different wait strategies, and different assertion approaches on each run. This leads to:

- Flaky test generation (works on one run, fails on the next)
- Inconsistent test quality
- Difficulty reproducing issues

**Recommendation:**
- Add a validation execution step that re-runs the generated test before committing
- Implement a "confidence score" based on retry count and selector stability
- Consider caching successful generations and reusing them when the ETag matches
- Add temperature controls for the LLM (currently using defaults)

---

### 3. Error Handling: Broad Exception Catching

**Risk: MEDIUM**

Many components catch `Exception` broadly, which can mask bugs:

```python
except Exception as e:
    logger.error(f"Failed: {str(e)}")
    return {"success": False, "error": str(e)}
```

This pattern appears in `ActionRunner.execute()`, `QACrew.run_active_autoqa_scenario()`, `IterativeTestOrchestrator.run_active_execution()`, and others.

**Recommendation:**
- Catch specific exception types where possible
- Distinguish between recoverable errors (retry-worthy) and fatal errors
- Add structured error codes rather than relying on string matching
- Consider a custom exception hierarchy (e.g., `AutoQAParseError`, `AutoQAExecutionError`, `AutoQASecurityError`)

---

### 4. Testing: Insufficient Unit Test Coverage

**Risk: HIGH**

The repository has minimal automated tests:

- `tests/test_login.py` — Only login test examples
- `test_active_execution.py` and `test_complete_flow.py` — Integration tests that require live services
- No unit tests for core components (parser, retry handler, DOM inspector, cross-repo manager)

For an open-source project, this is a significant barrier to contributions — developers cannot verify their changes don't break existing functionality.

**Recommendation:**
- Add unit tests for `AutoQAParser` (metadata extraction, validation, ETag computation)
- Add unit tests for `RetryHandler` (failure analysis, code modification)
- Add unit tests for `DOMInspectorTool` (selector ranking, element matching)
- Add unit tests for `CrossRepoManager` (path generation, file content creation)
- Add unit tests for `ExecutorAgent` (AST validation)
- Mock external dependencies (Playwright, OpenAI, GitHub API)
- Set up CI to run tests on every PR (the `test-action.yml` workflow exists but needs proper test targets)
- Aim for >80% coverage of core modules

---

### 5. Configuration: Hardcoded Values

**Risk: LOW**

Several values are hardcoded that should be configurable:

| Hardcoded Value                | Location                          | Issue                                |
| ------------------------------ | --------------------------------- | ------------------------------------ |
| `openai/gpt-4.1` model        | `action_runner.py`, `qa_crew.py`  | Users locked to specific model       |
| `rabia.tahirr@opengrowth.com`  | `action.yml`, `cross_repo_manager.py` | Personal email as default       |
| `stg-home.aisquare.studio`     | Multiple files                    | AISquare-specific staging URL        |
| `password123` default password | `action.yml`                      | Insecure default                     |
| `slow_mo=500`                  | `iterative_orchestrator.py`       | Fixed browser slowdown               |

**Recommendation:**
- Make the OpenAI model configurable via action input (partially done via `OPENAI_MODEL_NAME` env var, but not exposed as action input)
- Remove personal email defaults — require explicit configuration or use a generic default
- Remove AISquare-specific URLs from defaults
- Remove insecure password defaults
- Expose `slow_mo` as a configuration option

---

### 6. Documentation: Scattered and Partially Outdated

**Risk: MEDIUM**

The `docs/` directory contains 9 markdown files, many with overlapping content. Some reference features that may no longer exist (e.g., "Week 1 Demo"), and the original README had duplicated sections.

**Recommendation:**
- ✅ (Addressed) Rewrite README.md with clean, consistent structure
- ✅ (Addressed) Create `docs/ARCHITECTURE.md` as the single source of truth for architecture
- Consolidate or archive legacy docs (`PHASE1_IMPLEMENTATION_SUMMARY.md`, `SCREENSHOT_FIX.md`, `SINGLE_COMMENT_FIX.md`)
- Add a `docs/CHANGELOG.md` for tracking releases
- Add inline code documentation (docstrings are present but could be more detailed)

---

### 7. Dependency Management

**Risk: LOW**

Dependencies in `requirements.txt` have no version pins:

```
crewai[tools]
playwright
pytest
...
```

This means builds can break when upstream packages release breaking changes.

**Recommendation:**
- Pin major versions at minimum (e.g., `crewai[tools]>=0.30,<1.0`)
- Use a lockfile or `pip-compile` for deterministic builds
- Add Dependabot or Renovate for automated dependency updates
- Document minimum Python version requirement (currently 3.11+ implied by `setup-python`)

---

### 8. Observability and Debugging

**Risk: LOW**

When test generation fails, debugging is difficult:

- LLM prompts and responses are not logged (only the final code is)
- Intermediate page states during active execution are not captured
- No structured telemetry or metrics

**Recommendation:**
- Add optional verbose mode that logs full LLM prompts and responses
- Capture DOM snapshots at each step (not just selectors) for post-mortem analysis
- Add timing metrics for each phase (parse, generate, execute, commit, report)
- Consider structured JSON logging alongside human-readable output
- Save execution traces as artifacts for failed runs

---

### 9. Scalability

**Risk: LOW (current), MEDIUM (future)**

Current design limitations that may become issues at scale:

| Limitation                          | Impact                                                  |
| ----------------------------------- | ------------------------------------------------------- |
| Single browser instance             | Cannot parallelize step execution                       |
| Sequential test suite execution     | Full suite runs may become slow with many tests         |
| No test deduplication               | Similar PRs could generate near-identical tests         |
| Single LLM provider (OpenAI only)   | No fallback if OpenAI is down or rate-limited           |
| No caching of generated code        | Same PR body regenerates code on every push             |

**Recommendation:**
- Implement ETag-based no-op (skip regeneration if ETag unchanged — partially implemented in config but not enforced)
- Support multiple LLM providers (Anthropic, Google, local models via Ollama)
- Add test deduplication by comparing generated code similarity
- Consider parallel test execution for suite mode

---

### 10. Licensing and Legal

**Risk: HIGH for open-source**

No license file exists. Without a license, the code is technically all-rights-reserved by default, which prevents legal use by the community.

**Recommendation:**
- Add a `LICENSE` file (MIT or Apache 2.0 recommended for open-source tools)
- Review all dependencies for license compatibility
- Add license headers to source files if required by chosen license
- Update `README.md` license section

---

## Improvement Areas

### High Priority (Before Open-Source Release)

1. **Add license file** — Legal requirement for open-source
2. **Add unit tests for core modules** — Essential for contributor confidence
3. **Apply AST validation to active execution steps** — Security gap
4. **Pin dependency versions** — Build reproducibility
5. **Remove hardcoded personal/company-specific values** — Generic defaults
6. **Add CI test workflow that runs on PRs** — Quality gate

### Medium Priority (First Quarter After Release)

7. **Support multiple LLM providers** — Reduce OpenAI lock-in
8. **Add structured error types** — Better error handling and debugging
9. **Implement ETag no-op enforcement** — Skip redundant regeneration
10. **Add execution trace artifacts** — Debug failed runs
11. **Consolidate legacy documentation** — Reduce confusion
12. **Add contributor quick-start guide** — Lower contribution barrier

### Lower Priority (Ongoing)

13. **Parallel test execution in suite mode** — Performance at scale
14. **Test deduplication** — Prevent test bloat
15. **DOM snapshot capture at each step** — Post-mortem analysis
16. **Support for non-Chromium browsers** — Firefox, WebKit
17. **Plugin architecture for custom agents** — Extensibility
18. **Web UI for test management** — Optional test review interface

---

## Open-Source Readiness Checklist

| Item                                          | Status  | Notes                                      |
| --------------------------------------------- | ------- | ------------------------------------------ |
| License file added                            | ❌ TODO | Choose MIT or Apache 2.0                   |
| README is clean and comprehensive             | ✅ Done | Rewritten in this PR                       |
| Architecture documented                       | ✅ Done | `docs/ARCHITECTURE.md`                     |
| Contributing guide exists                     | ✅ Done | `CONTRIBUTING.md` present                  |
| Code of Conduct exists                        | ✅ Done | `CODE_OF_CONDUCT.md` present               |
| Issue templates exist                         | ✅ Done | Bug report + feature request               |
| CI runs on PRs                                | ⚠️ Partial | Lint workflow runs, test workflow needs expansion |
| Unit tests exist for core modules             | ❌ TODO | Critical gap                               |
| Dependencies version-pinned                   | ❌ TODO | Currently unpinned                         |
| No hardcoded secrets or personal info         | ⚠️ Partial | Default email should be genericized    |
| Security model documented                     | ✅ Done | In `docs/ARCHITECTURE.md`                  |
| Personal/company references removed from defaults | ❌ TODO | Staging URLs, email defaults           |
| Changelog exists                              | ❌ TODO | Add `CHANGELOG.md`                         |
| Release process documented                    | ❌ TODO | Tag-based releases recommended             |

---

## Contributor Opportunities

Good first issues for new contributors:

| Area                  | Task                                                    | Difficulty |
| --------------------- | ------------------------------------------------------- | ---------- |
| Testing               | Add unit tests for `AutoQAParser`                       | Easy       |
| Testing               | Add unit tests for `RetryHandler`                       | Easy       |
| Testing               | Add unit tests for `ExecutorAgent.validate_code_safety()`| Easy       |
| Security              | Apply AST validation to step execution in active mode   | Medium     |
| Configuration         | Add `openai-model` as an action input                   | Easy       |
| Configuration         | Remove hardcoded personal email/URLs from defaults      | Easy       |
| Dependencies          | Pin versions in `requirements.txt`                      | Easy       |
| Documentation         | Add `CHANGELOG.md`                                      | Easy       |
| Documentation         | Archive/consolidate legacy docs                         | Easy       |
| Feature               | Support Anthropic Claude as alternative LLM             | Medium     |
| Feature               | Add DOM snapshot artifact for failed steps               | Medium     |
| Feature               | Implement ETag-based skip for unchanged PRs             | Medium     |
| Performance           | Parallel test execution in suite mode                   | Hard       |
| Architecture          | Plugin system for custom agent types                    | Hard       |
