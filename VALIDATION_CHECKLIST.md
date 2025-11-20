# Active Execution - Validation Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Python 3.9+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Playwright browsers installed: `playwright install chromium`
- [ ] OpenAI API key configured: `export OPENAI_API_KEY=sk-...`
- [ ] Staging environment accessible

### 2. File Verification
- [ ] All new files created in `src/execution/`
- [ ] `src/tools/dom_inspector.py` exists
- [ ] `src/agents/step_executor_agent.py` exists
- [ ] Updated files: `qa_crew.py`, `action_runner.py`
- [ ] Config updated: `autoqa_config.yaml`
- [ ] Documentation created: `docs/ACTIVE_EXECUTION.md`

### 3. Configuration Check
```bash
# Verify config settings
grep -A 10 "use_active_execution" config/autoqa_config.yaml
```

Expected output:
```yaml
use_active_execution: true
active_execution:
  max_retries_per_step: 2
  step_timeout_ms: 30000
  ...
```

### 4. Import Validation
```python
# Test imports
python -c "from src.execution import ExecutionContext, IterativeTestOrchestrator, RetryHandler; print('✓ Imports OK')"
python -c "from src.tools.dom_inspector import DOMInspectorTool; print('✓ DOM Inspector OK')"
python -c "from src.agents.step_executor_agent import StepExecutorAgent; print('✓ Step Executor OK')"
```

### 5. Unit Test (Quick)
```bash
# Run test script
export OPENAI_API_KEY=your_key_here
export USE_ACTIVE_EXECUTION=true
python test_active_execution.py
```

Expected: Test should run and either succeed or fail with clear error messages.

### 6. Integration Test (with QA Crew)
```python
# Test integration
python -c "
from src.crews.qa_crew import QACrew
crew = QACrew()
print('✓ QACrew initialized')
print('✓ Active execution available:', hasattr(crew, 'run_active_autoqa_scenario'))
print('✓ Orchestrator initialized:', crew.iterative_orchestrator is not None)
"
```

### 7. GitHub Action Validation
- [ ] `.github/workflows` has AutoQA workflow
- [ ] Workflow uses updated `action_runner.py`
- [ ] Environment variables configured in repo secrets
- [ ] Test with a sample PR

### 8. Smoke Test Scenarios

#### Scenario A: Simple Navigation
```markdown
```autoqa
flow_name: smoke_test_navigation
tier: C
area: testing
```
1. Navigate to https://example.com
2. Verify page title contains "Example"
```

Expected: Should generate and execute successfully.

#### Scenario B: Form Interaction
```markdown
```autoqa
flow_name: smoke_test_form
tier: B
area: testing
```
1. Navigate to staging login page
2. Fill email field with test email
3. Fill password field with test password
4. Click login button
```

Expected: Should discover selectors and execute steps.

#### Scenario C: Failure Recovery
```markdown
```autoqa
flow_name: smoke_test_retry
tier: C
area: testing
```
1. Navigate to staging homepage
2. Click on non-existent button
3. Verify error handling
```

Expected: Should retry with alternative selectors or fail gracefully.

## 🔍 Verification Commands

### Check File Structure
```bash
tree src/execution/
tree src/tools/
ls -la src/agents/step_executor_agent.py
```

### Verify Config
```bash
# Check active execution settings
python -c "
import yaml
with open('config/autoqa_config.yaml') as f:
    config = yaml.safe_load(f)
    print('Active Execution Enabled:', config['autoqa']['execution'].get('use_active_execution'))
    print('Max Retries:', config['autoqa']['execution']['active_execution']['max_retries_per_step'])
"
```

### Test Component Initialization
```python
# Test each component individually
python -c "
from src.execution.execution_context import ExecutionContext
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    ctx = ExecutionContext(page, {})
    print('✓ ExecutionContext works')
    browser.close()
"
```

```python
# Test DOM Inspector
python -c "
from src.tools.dom_inspector import DOMInspectorTool
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://example.com')
    inspector = DOMInspectorTool(page)
    selectors = inspector.discover_selectors()
    print('✓ DOMInspectorTool works')
    print('Found selectors:', len(selectors))
    browser.close()
"
```

## 🐛 Common Issues & Solutions

### Issue: "Import playwright.sync_api could not be resolved"
**Solution**: These are lint warnings. Install playwright:
```bash
pip install playwright
playwright install chromium
```

### Issue: "OpenAI API key not found"
**Solution**: Set environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Browser launch failed"
**Solution**: Install browser dependencies:
```bash
playwright install-deps chromium
```

### Issue: "Step generation timeout"
**Solution**: 
- Check OpenAI API connectivity
- Increase timeout in config
- Use a simpler step description

### Issue: "No selectors found"
**Solution**:
- Verify page loaded correctly
- Check if elements are in iframes (not supported yet)
- Try more specific element descriptions

## 📊 Success Metrics

After running tests, verify:

- [ ] **Generation Success Rate**: >80% steps succeed on first try
- [ ] **Retry Success Rate**: >90% steps succeed after retry
- [ ] **Execution Time**: <30s for 5-step test
- [ ] **Selector Discovery**: >0 selectors found per page
- [ ] **Code Quality**: Generated code is valid Python
- [ ] **Error Handling**: Failures report clear messages

## 🚦 Go/No-Go Decision

### ✅ GO if:
- All imports resolve at runtime
- Test script runs without crashes
- Selectors discovered from live pages
- Steps execute and retry works
- Generated code is valid

### ❌ NO-GO if:
- Import errors at runtime
- Browser launch fails
- No selectors discovered
- All steps fail without retry
- Generated code has syntax errors

## 📝 Post-Deployment Monitoring

### Week 1
- Monitor PR executions daily
- Track success/failure rates
- Collect user feedback
- Review generated test quality

### Week 2-4
- Analyze retry patterns
- Tune retry strategies
- Optimize selector discovery
- Performance improvements

### Metrics to Track
- Average execution time per test
- Retry rate per step
- Selector discovery rate
- Test stability over time
- User satisfaction score

---

**Status**: Ready for validation ✅

Run through this checklist before deploying to production!
