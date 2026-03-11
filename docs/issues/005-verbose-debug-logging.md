<!--
Title: [FEATURE] Add verbose debug logging mode for LLM interactions
Labels: enhancement, observability, help wanted
-->

# Add Verbose Debug Logging Mode for LLM Interactions

## Summary

When test generation fails, debugging is extremely difficult because LLM prompts and responses
are not logged. Adding an optional verbose/debug logging mode would capture the full
request-response cycle, making it possible to diagnose generation failures, tune prompts, and
understand why specific selectors or assertions were chosen.

## Problem

Currently, when a test fails to generate correctly:
- Only the final generated code is visible (not the prompt that produced it)
- Intermediate page states during active execution are not captured
- There are no timing metrics for each phase (parse → generate → execute → commit)
- Users have to guess why the LLM produced incorrect selectors or assertions

The existing logger (`src/utils/logger.py`) supports GitHub Actions annotations and emoji
formatting, but there is no mechanism to enable verbose output that includes LLM interaction
details.

## Proposed Solution

### 1. Add a `debug-mode` input to `action.yml`:

```yaml
inputs:
  debug-mode:
    description: 'Enable verbose debug logging including LLM prompts and responses'
    required: false
    default: 'false'
```

### 2. Add debug logging functions to `src/utils/logger.py`:

```python
import time

_debug_mode = os.getenv("AUTOQA_DEBUG", "false").lower() == "true"


def log_llm_request(prompt: str, model: str, logger: logging.Logger = None):
    """Log an LLM request when debug mode is enabled."""
    if not _debug_mode:
        return
    if logger is None:
        logger = get_logger()
    log_github_group(f"🤖 LLM Request → {model}")
    logger.debug(f"Prompt ({len(prompt)} chars):\n{prompt}")
    log_github_endgroup()


def log_llm_response(response: str, duration_s: float, logger: logging.Logger = None):
    """Log an LLM response when debug mode is enabled."""
    if not _debug_mode:
        return
    if logger is None:
        logger = get_logger()
    log_github_group(f"🤖 LLM Response ({duration_s:.1f}s)")
    logger.debug(f"Response ({len(response)} chars):\n{response}")
    log_github_endgroup()


def log_phase_timing(phase: str, duration_s: float, logger: logging.Logger = None):
    """Log phase timing information."""
    if logger is None:
        logger = get_logger()
    logger.info(f"⏱️  {phase}: {duration_s:.2f}s")
```

### 3. Instrument LLM calls in `src/crews/qa_crew.py`:

```python
from src.utils.logger import log_llm_request, log_llm_response
import time

# Before LLM call:
log_llm_request(prompt=task_description, model=self.model_name)
start = time.time()

# After LLM call:
duration = time.time() - start
log_llm_response(response=result, duration_s=duration)
```

### 4. Add phase timing in `src/autoqa/action_runner.py`:

```python
from src.utils.logger import log_phase_timing
import time

parse_start = time.time()
# ... parsing logic ...
log_phase_timing("Parse PR body", time.time() - parse_start)

gen_start = time.time()
# ... generation logic ...
log_phase_timing("Generate test code", time.time() - gen_start)
```

### 5. Pass the input through to the environment:

In `action.yml` runs section:
```yaml
env:
  AUTOQA_DEBUG: ${{ inputs.debug-mode }}
```

## Example Output (Debug Mode Enabled)

```
ℹ️  AutoQA starting for PR #42
⏱️  Parse PR body: 0.03s
::group::🤖 LLM Request → openai/gpt-4.1
Prompt (1247 chars):
Generate a Playwright Python test that performs the following steps...
::endgroup::
::group::🤖 LLM Response (4.2s)
Response (892 chars):
async def test_login_flow(page):
    await page.goto("https://...")
    ...
::endgroup::
⏱️  Generate test code: 4.25s
⏱️  Execute test: 2.10s
⏱️  Commit results: 0.45s
✅  AutoQA completed successfully
```

## Files to Modify

| File | Change |
|------|--------|
| `action.yml` | Add `debug-mode` input |
| `src/utils/logger.py` | Add `log_llm_request`, `log_llm_response`, `log_phase_timing` |
| `src/crews/qa_crew.py` | Instrument LLM calls with debug logging |
| `src/autoqa/action_runner.py` | Add phase timing around major operations |
| `README.md` | Document `debug-mode` input |

## Acceptance Criteria

- [ ] `action.yml` has a `debug-mode` input (default: `false`)
- [ ] Debug mode is disabled by default — no output changes for normal users
- [ ] When enabled, LLM prompts and responses are logged inside collapsible groups
- [ ] Phase timings are logged regardless of debug mode (they are lightweight)
- [ ] Sensitive data (API keys) is never logged even in debug mode
- [ ] Documentation updated to describe the new input
