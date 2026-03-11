<!--
Title: [FEATURE] Expose OpenAI model as a configurable action input
Labels: good first issue, enhancement, configuration
-->

# Expose OpenAI Model as a Configurable Action Input

## Summary

The OpenAI model is currently hardcoded to `openai/gpt-4.1` in two locations, with the only
override being an undocumented environment variable. Users should be able to select their
preferred model directly via the action's input parameters in their workflow YAML.

## Problem

### Hardcoded defaults in source code:

**`src/autoqa/action_runner.py` (line 40):**
```python
model_name = os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4.1")
```

**`src/crews/qa_crew.py` (line 31):**
```python
model = model_name or os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4.1")
```

### Why this is a problem:

- Users are locked to GPT-4.1 unless they know the undocumented `OPENAI_MODEL_NAME` env var
- GPT-4.1 may not be available in all regions or API plans
- Users may want cheaper models (GPT-3.5-turbo) for testing or more capable models as they
  become available
- The env var workaround is not documented in `action.yml` or `README.md`

## Proposed Solution

### 1. Add `openai-model` input to `action.yml`:

```yaml
inputs:
  openai-model:
    description: 'OpenAI model to use for test generation (e.g., openai/gpt-4.1, openai/gpt-4o, openai/gpt-3.5-turbo)'
    required: false
    default: 'openai/gpt-4.1'
```

### 2. Pass the input as an environment variable in the action's `runs` steps:

```yaml
env:
  OPENAI_MODEL_NAME: ${{ inputs.openai-model }}
```

### 3. Update documentation:

**In `README.md`**, add to the inputs table:
```markdown
| `openai-model` | OpenAI model for test generation | `openai/gpt-4.1` |
```

**In `docs/ACTION_USAGE.md`**, add a section explaining model selection:
```markdown
### Model Selection

You can specify which OpenAI model to use:

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@v0.1.0
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    openai-model: 'openai/gpt-4o'
```
```

## Files to Modify

| File | Change |
|------|--------|
| `action.yml` | Add `openai-model` input definition |
| `action.yml` (runs section) | Pass input as `OPENAI_MODEL_NAME` env var |
| `README.md` | Document new input in the inputs table |
| `docs/ACTION_USAGE.md` | Add model selection usage example |

## Acceptance Criteria

- [ ] `action.yml` has `openai-model` input with sensible default
- [ ] The input value is passed to the Python code via environment variable
- [ ] Default behavior is unchanged (still uses `openai/gpt-4.1` when not specified)
- [ ] `README.md` documents the new input
- [ ] `docs/ACTION_USAGE.md` has a usage example
