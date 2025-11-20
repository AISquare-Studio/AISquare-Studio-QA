# Execution Package

This package implements the **Active Execution Mode** - an iterative test generation and execution system.

## Quick Start

```python
from src.execution import IterativeTestOrchestrator

# Initialize orchestrator
orchestrator = IterativeTestOrchestrator(llm=your_llm, max_retries=2)

# Run active execution
result = orchestrator.run_active_execution(
    steps=["Navigate to page", "Click button", "Verify result"],
    config={"base_url": "https://example.com", ...},
    scenario={"name": "Test", ...}
)
```

## Components

### IterativeTestOrchestrator
Main coordinator that executes steps one-by-one with live browser context.

### ExecutionContext
Tracks browser state, discovered selectors, and execution history between steps.

### RetryHandler
Analyzes failures and generates corrected code for retry attempts.

## Features

- 🔄 **Step-by-step execution** with real-time context
- 🔍 **Live selector discovery** from actual pages
- 🔁 **Automatic retry** with intelligent corrections
- 📊 **Comprehensive reporting** of execution details
- 🎯 **Context-aware** code generation

## Documentation

See [ACTIVE_EXECUTION.md](../../docs/ACTIVE_EXECUTION.md) for full documentation.

## Usage in AutoQA

Active execution is automatically used when `USE_ACTIVE_EXECUTION=true` is set in the environment.

```bash
export USE_ACTIVE_EXECUTION=true
export MAX_RETRIES=2
export HEADLESS_MODE=true
```

## Architecture

```
IterativeTestOrchestrator
├── Manages browser lifecycle
├── Coordinates step execution
└── Compiles final test code

ExecutionContext
├── Tracks page state
├── Stores discovered selectors
└── Maintains execution history

RetryHandler
├── Analyzes failures
├── Suggests corrections
└── Tracks retry statistics
```

## Example Output

```python
# Auto-generated test with active execution
def run_test(page, config):
    # Step 1: Navigate to login page
    page.goto(config['login_url'])
    page.wait_for_load_state('networkidle')
    
    # Step 2: Fill email field
    page.fill("input[name='email']", config['email'])
    
    # Step 3: Click submit
    page.click("button:has-text('Login')")
```

## Testing

Run the test script:

```bash
python test_active_execution.py
```

## Configuration

Configure in `config/autoqa_config.yaml`:

```yaml
autoqa:
  execution:
    use_active_execution: true
    active_execution:
      max_retries_per_step: 2
      step_timeout_ms: 30000
      failure_mode: "stop_on_error"
```
