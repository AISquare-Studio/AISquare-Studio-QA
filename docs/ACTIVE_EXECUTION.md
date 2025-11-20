# Active Execution Mode - Technical Documentation

## Overview

Active Execution Mode is an advanced iterative test generation and execution system that generates, executes, and validates test steps one at a time with real-time context awareness. Unlike traditional single-pass generation, active execution discovers selectors from live pages, adapts to actual application behavior, and automatically retries failed steps with corrections.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────┐
│         IterativeTestOrchestrator                   │
│  (Coordinates step-by-step execution)               │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ExecutionContext│ │StepExecutor │
│(State Tracking)│ │   Agent     │
└──────┬─────────┘ └──────┬───────┘
       │                  │
       │         ┌────────┴────────┐
       │         │                 │
       │         ▼                 ▼
       │  ┌─────────────┐  ┌─────────────┐
       │  │DOMInspector │  │RetryHandler │
       │  │    Tool     │  │             │
       │  └─────────────┘  └─────────────┘
       │
       └──► Playwright Browser (Live Page Context)
```

### Component Responsibilities

#### 1. **IterativeTestOrchestrator** (`src/execution/iterative_orchestrator.py`)
- Main coordinator for step-by-step execution
- Manages browser lifecycle
- Compiles final test code from executed steps
- Handles failure modes and execution flow

#### 2. **ExecutionContext** (`src/execution/execution_context.py`)
- Tracks browser state between steps
- Maintains history of executed steps
- Stores discovered selectors
- Provides context for agent decision-making

#### 3. **StepExecutorAgent** (`src/agents/step_executor_agent.py`)
- Generates code for individual steps using LLM
- Uses real-time page state for context
- Executes generated code immediately
- Validates step success

#### 4. **DOMInspectorTool** (`src/tools/dom_inspector.py`)
- Extracts selectors from live pages
- Identifies interactive elements
- Ranks selectors by stability/reliability
- Suggests best selectors for element descriptions

#### 5. **RetryHandler** (`src/execution/retry_handler.py`)
- Analyzes step failures
- Suggests alternative selectors
- Modifies code for retry attempts
- Tracks retry statistics

## Execution Flow

### Step-by-Step Process

```
For each test step:
  1. Capture current page state (URL, title, DOM)
     │
     ▼
  2. Discover available selectors on page
     │
     ▼
  3. Generate code for THIS step only (with context)
     │
     ▼
  4. Execute code immediately
     │
     ├─ Success ──► Record result, continue to next step
     │
     └─ Failure ──► Analyze error
                    │
                    ├─ Retries remaining?
                    │  │
                    │  └─ Yes ──► Generate corrected code, retry
                    │
                    └─ No ──► Stop or continue based on failure_mode
```

### Example Execution Timeline

```
Time  | Step | Action
------|------|-------------------------------------------------------
0.0s  | 1    | Generate: page.goto(config['login_url'])
0.5s  | 1    | Execute: Navigate to login page
1.2s  | 1    | ✓ Success - Capture state (URL, discovered selectors)
      |      |
1.5s  | 2    | Inspect page: Found 5 inputs, 3 buttons
1.6s  | 2    | Best selector for "email input": input[name="email"]
1.8s  | 2    | Generate: page.fill("input[name='email']", config['email'])
2.0s  | 2    | Execute: Fill email field
2.3s  | 2    | ✓ Success
      |      |
2.5s  | 3    | Generate: page.fill("input[type='password']", config['password'])
2.7s  | 3    | Execute: Fill password field
2.9s  | 3    | ✓ Success
      |      |
3.1s  | 4    | Generate: page.click("button[type='submit']")
3.3s  | 4    | Execute: Click login button
3.5s  | 4    | ✗ Timeout - Button not found
      |      |
3.7s  | 4    | Analyze failure: Selector not found
3.8s  | 4    | Alternative selector: button:has-text("Login")
3.9s  | 4    | Generate (retry): page.click("button:has-text('Login')")
4.1s  | 4    | Execute (retry): Click login button
4.5s  | 4    | ✓ Success
```

## Configuration

### Environment Variables

```bash
# Active execution settings
USE_ACTIVE_EXECUTION=true          # Enable active execution mode
MAX_RETRIES=2                      # Max retries per step
HEADLESS_MODE=true                 # Run browser in headless mode

# Test environment
STAGING_URL=https://stg.example.com
STAGING_EMAIL=test@example.com
STAGING_PASSWORD=password123

# OpenAI settings
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=openai/gpt-4.1
```

### Config File (`config/autoqa_config.yaml`)

```yaml
autoqa:
  execution:
    use_active_execution: true
    active_execution:
      max_retries_per_step: 2
      step_timeout_ms: 30000
      slow_mo_ms: 500
      record_video: false
      selector_priority:
        - "data-testid"
        - "id"
        - "name"
        - "aria-label"
        - "placeholder"
      failure_mode: "stop_on_error"  # Options: stop_on_error, continue_on_error
```

## Usage

### Basic Usage in Action

When a PR includes an AutoQA block, active execution runs automatically:

```markdown
```autoqa
flow_name: user_login
tier: A
area: auth
```
1. Navigate to login page
2. Enter email in email field
3. Enter password in password field
4. Click login button
5. Verify successful login
```

### Programmatic Usage

```python
from src.crews.qa_crew import QACrew

# Initialize crew
qa_crew = QACrew()

# Define scenario
scenario = {
    "name": "User Login Flow",
    "steps": [
        "Navigate to login page",
        "Fill email field",
        "Fill password field",
        "Click submit",
        "Verify dashboard loads"
    ],
    "metadata": {
        "flow_name": "user_login",
        "tier": "A",
        "area": "auth"
    }
}

# Define config
config = {
    "base_url": "https://stg.example.com",
    "login_url": "https://stg.example.com/login",
    "email": "test@example.com",
    "password": "password123",
    "headless": True,
    "max_retries": 2,
}

# Run active execution
result = qa_crew.run_active_autoqa_scenario(scenario, config)

# Check results
if result["success"]:
    print(f"✓ Test generated successfully!")
    print(f"Completed: {result['successful_steps']}/{result['total_steps']} steps")
    print(f"Generated code:\n{result['generated_code']}")
else:
    print(f"✗ Test failed: {result.get('error')}")
```

## Features

### 1. Real-Time Selector Discovery

- Inspects live page DOM before each step
- Discovers all interactive elements
- Ranks selectors by reliability
- Suggests best selector for each action

### 2. Context-Aware Code Generation

Each step is generated with full knowledge of:
- Current page URL and title
- Previous step results
- Available selectors on current page
- Execution history

### 3. Automatic Retry with Intelligence

When a step fails:
1. Analyzes error type (timeout, selector not found, etc.)
2. Discovers alternative selectors
3. Generates corrected code
4. Retries with improvements

### 4. Progressive Execution

- Browser stays open throughout test generation
- Each step builds on previous state
- Real page transitions captured
- Actual application behavior observed

### 5. Comprehensive Reporting

Results include:
- Generated test code
- Step-by-step execution details
- Discovered selectors per page
- Retry statistics
- Screenshots at each step
- Execution timeline

## Output Format

### Generated Test Code

```python
# Auto-generated test with active execution
from playwright.sync_api import sync_playwright

def run_test(page, config):
    '''
    Test: User Login Flow
    Generated with active execution - 5 steps
    '''
    
    # Step 1: Navigate to login page
    page.goto(config['login_url'])
    page.wait_for_load_state('networkidle')
    
    # Step 2: Fill email field
    page.fill("input[name='email']", config['email'])
    
    # Step 3: Fill password field
    page.fill("input[type='password']", config['password'])
    
    # Step 4: Click submit
    page.click("button:has-text('Login')")
    page.wait_for_timeout(1000)
    
    # Step 5: Verify dashboard loads
    assert '/dashboard' in page.url, "Should redirect to dashboard"
```

### Execution Result

```json
{
  "success": true,
  "generated_code": "...",
  "execution_summary": {
    "total_steps": 5,
    "successful_steps": 5,
    "failed_steps": 0,
    "success_rate": 1.0,
    "final_url": "https://stg.example.com/dashboard"
  },
  "total_execution_time": 8.42,
  "step_details": [
    {
      "step_number": 1,
      "description": "Navigate to login page",
      "code": "page.goto(config['login_url'])...",
      "success": true,
      "execution_time": 1.2,
      "attempts": 1
    }
  ],
  "retry_summary": {
    "total_retries": 1,
    "steps_retried": 1
  },
  "discovered_selectors": {
    "buttons": ["button[type='submit']", "button:has-text('Login')"],
    "inputs": ["input[name='email']", "input[type='password']"]
  }
}
```

## Benefits

### Quality Improvements

1. **Higher Success Rate**: Real selectors from live pages
2. **Better Reliability**: Adapts to actual application behavior
3. **Self-Correcting**: Automatic retry with alternative approaches
4. **Context-Aware**: Each step aware of application state

### Development Benefits

1. **Faster Debugging**: Know exactly which step failed
2. **Better Visibility**: See execution progress in real-time
3. **Learning System**: Discovers selectors for future use
4. **Reduced Manual Fixing**: Automatic corrections for common issues

## Limitations & Considerations

### Performance

- **Slower than single-pass**: Each step requires LLM call and execution
- **Resource intensive**: Browser must stay open throughout
- **Network dependent**: Requires stable connection to staging environment

### Current Limitations

1. Single browser context (no multi-tab support yet)
2. English-only step descriptions
3. Limited to Chromium browser
4. No iframe support in DOM inspector
5. Selector ranking heuristics are basic

## Future Enhancements

### Planned Features

1. **Selector Learning**: Build database of successful selectors
2. **Visual Validation**: AI-powered screenshot comparison
3. **Multi-page Flows**: Better support for complex navigation
4. **Performance Optimization**: Parallel selector discovery
5. **Enhanced Retry Logic**: ML-based failure prediction
6. **Context Repository**: Shared knowledge across tests

### Experimental Ideas

1. **Interactive Mode**: Human-in-the-loop for ambiguous steps
2. **Visual Programming**: Generate steps from screenshots
3. **Test Healing**: Auto-fix broken tests on page changes
4. **Smart Waits**: ML-predicted wait times based on page complexity

## Troubleshooting

### Common Issues

#### "No selector found for element"
- Check page is fully loaded before step execution
- Increase `step_timeout_ms`
- Verify element description matches actual page

#### "Timeout waiting for selector"
- Element may be dynamically loaded
- Add explicit wait in step description
- Check if element is in iframe (not supported yet)

#### "Code generation failed"
- Check OpenAI API key is valid
- Verify network connectivity
- Review step description clarity

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Legacy Mode

### Differences

| Feature | Legacy Mode | Active Execution |
|---------|-------------|------------------|
| Generation | Single-pass | Step-by-step |
| Selectors | Hardcoded/guessed | Discovered from live page |
| Execution | After generation | During generation |
| Context | Static | Dynamic, cumulative |
| Retry | Manual | Automatic |
| Speed | Fast (~5s) | Slower (~10-30s) |
| Accuracy | Lower | Higher |

### When to Use Each Mode

**Use Active Execution when:**
- Test accuracy is critical
- Application has dynamic elements
- Selectors are unknown
- Complex multi-step flows
- Debugging test generation

**Use Legacy Mode when:**
- Speed is priority
- Selectors are well-known
- Simple, static pages
- Batch test generation
- CI/CD time constraints

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Adding new selector strategies
- Improving retry logic
- Enhancing DOM inspection
- Performance optimization

## License

See [LICENSE](../LICENSE)
